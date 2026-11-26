#!/usr/bin/env python3
# Read-only readiness and freshness diagnostics based on training logs,
# Slurm state, checkpoint timestamps and live/archived hypothesis timestamps.
# Readiness recommendations are not a measure of evaluation completeness.
# The caller, not this script, decides whether to replace models.ready.


import argparse
import csv
import re
import subprocess
import sys
import tarfile

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


TZ = ZoneInfo("Europe/Helsinki")

TAIL_BYTES = 256 * 1024

LOG_RE = re.compile(r"train\.(\d+)\.(err|out)$")

TIME_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
)

ACTIVE_STATES = {
    "RUNNING",
    "PENDING",
    "COMPLETING",
    "CONFIGURING",
    "SUSPENDED",
    "RESIZING",
    "REQUEUED",
    "REQUEUE_FED",
    "REQUEUE_HOLD",
    "SIGNALING",
    "STAGE_OUT",
}


# ============================================================
# Timestamp utilities
# ============================================================

def timestamp(text):
    match = TIME_RE.search(text)

    if not match:
        return None

    return datetime.fromisoformat(
        match.group()
    ).replace(tzinfo=TZ).timestamp()


def fmt(ts):
    if ts is None:
        return "-"

    return datetime.fromtimestamp(
        ts, TZ
    ).strftime("%m-%d %H:%M:%S")


def read_tail(path):
    with path.open("rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - TAIL_BYTES))

        return f.read().decode(
            "utf-8", errors="replace"
        )


# ============================================================
# Slurm status
# ============================================================

def active_jobs():
    try:
        result = subprocess.run(
            ["squeue", "-h", "-o", "%A|%T"],
            capture_output=True,
            text=True,
            check=True
        )

        return dict(
            line.split("|", 1)
            for line in result.stdout.splitlines()
            if "|" in line
        )

    except (OSError, subprocess.CalledProcessError) as exc:
        print(
            f"ERROR: squeue unavailable: {exc}",
            file=sys.stderr
        )

        # Do not recommend evaluation if active training
        # jobs cannot be checked.
        sys.exit(1)


# ============================================================
# Training status
# ============================================================

def training_status(model, active):
    mammoth = model / "mammoth"

    jobs = {}

    for path in mammoth.glob("train.*"):
        match = LOG_RE.fullmatch(path.name)

        if match and path.is_file():
            job = match.group(1)
            jobs.setdefault(job, []).append(path)

    if not jobs:
        return "NO_LOG", "-", None, None

    # Select the most recently modified job logs.
    # Job IDs alone are not reliable across clusters.
    job = max(
        jobs,
        key=lambda j: max(
            p.stat().st_mtime for p in jobs[j]
        )
    )

    paths = jobs[job]

    last_modified = max(
        p.stat().st_mtime for p in paths
    )

    text = "\n".join(
        read_tail(p) for p in paths
    )

    lines = text.splitlines()

    # Check whether any known training job is still active.
    for active_job in jobs:
        if active_job in active:
            return (
                active[active_job],
                active_job,
                None,
                last_modified
            )

    # --------------------------------------------------------
    # Explicit Slurm termination messages
    # --------------------------------------------------------

    cancellations = []

    for line in lines:
        upper = line.upper()

        if "CANCELLED AT" not in upper:
            continue

        ts = timestamp(
            re.split(
                r"CANCELLED AT",
                line,
                flags=re.I,
                maxsplit=1
            )[1]
        )

        if "TIME LIMIT" in upper:
            status = "TIMEOUT"

        elif "NODE FAILURE" in upper:
            status = "NODE_FAILURE"

        elif "TASK FAILURE" in upper:
            status = "TASK_FAILURE"

        else:
            status = "CANCELLED"

        cancellations.append(
            (status, ts or last_modified)
        )

    if cancellations:
        priority = {
            "TIMEOUT": 4,
            "NODE_FAILURE": 3,
            "TASK_FAILURE": 2,
            "CANCELLED": 1
        }

        status, end = max(
            cancellations,
            key=lambda x: (
                priority[x[0]], x[1]
            )
        )

        return status, job, end, last_modified

    # --------------------------------------------------------
    # Out-of-memory termination
    # --------------------------------------------------------

    if re.search(
        r"OutOfMemoryError|oom.kill|out of memory",
        text,
        re.I
    ):
        return (
            "OOM",
            job,
            last_modified,
            last_modified
        )

    # --------------------------------------------------------
    # Explicit failure marker
    # --------------------------------------------------------

    if "train.slurmjob.failed" in text:
        return (
            "FAILED",
            job,
            last_modified,
            last_modified
        )

    # --------------------------------------------------------
    # Normal completion
    # --------------------------------------------------------

    if "Finishing at " in text:
        times = []

        for match in re.finditer(
            r"Finishing at (.+)", text
        ):
            value = match.group(1).strip("'\" \r")

            for zone in ("EEST", "EET", "UTC"):
                if not value.endswith(" " + zone):
                    continue

                try:
                    dt = datetime.strptime(
                        value[:-(len(zone) + 1)],
                        "%a %d %b %Y %H:%M:%S"
                    )

                    tz = (
                        ZoneInfo("UTC")
                        if zone == "UTC"
                        else TZ
                    )

                    times.append(
                        dt.replace(
                            tzinfo=tz
                        ).timestamp()
                    )

                except ValueError:
                    pass

        end = max(times) if times else last_modified

        return (
            "COMPLETED",
            job,
            end,
            last_modified
        )

    # --------------------------------------------------------
    # Other termination messages
    # --------------------------------------------------------

    if (
        "Force Terminated" in text
        or re.search(
            r"srun: error:.*"
            r"(?:Terminated|exit code [1-9])",
            text
        )
    ):
        return (
            "TERMINATED",
            job,
            last_modified,
            last_modified
        )

    # Training completion without confirmed job termination.

    if "Training complete, shutting down producers" in text:
        return (
            "SHUTDOWN",
            job,
            None,
            last_modified
        )

    return (
        "UNKNOWN",
        job,
        None,
        last_modified
    )


# ============================================================
# Best checkpoint timestamp
# ============================================================

def checkpoint_time(model):
    times = []

    mammoth = model / "mammoth"

    for path in mammoth.glob("model_best*"):
        if not path.is_file():
            continue

        times.append(
            path.stat().st_mtime
        )

        if path.is_symlink():
            times.append(
                path.lstat().st_mtime
            )

    return max(times, default=None)


# ============================================================
# Hypothesis timestamps
# ============================================================

def hypothesis_times(model):
    evaluation = model / "mammoth" / "evaluation"
    hypotheses = evaluation / "hypotheses"

    times = {}
    errors = []

    # --------------------------------------------------------
    # Unarchived hypotheses
    # --------------------------------------------------------

    if hypotheses.is_dir():
        for path in hypotheses.rglob("*.hyp"):
            if not path.is_file():
                continue

            key = path.relative_to(
                hypotheses
            ).as_posix()

            times[key] = path.stat().st_mtime

    # --------------------------------------------------------
    # Archived hypotheses
    #
    # Archives are opened in read-only mode.
    # Nothing is extracted.
    # --------------------------------------------------------

    for archive in sorted(
        evaluation.glob("hypotheses.tar*")
    ):
        if not archive.is_file():
            continue

        try:
            with tarfile.open(archive, "r:*") as tar:
                for member in tar:
                    if not member.isfile():
                        continue

                    if not member.name.endswith(".hyp"):
                        continue

                    key = member.name.removeprefix("./")
                    key = key.removeprefix("hypotheses/")

                    times[key] = min(
                        times.get(key, member.mtime),
                        member.mtime
                    )

        except (OSError, tarfile.TarError) as exc:
            errors.append(str(archive))

            print(
                f"WARNING: {archive}: {exc}",
                file=sys.stderr
            )

    values = list(times.values())

    return (
        min(values, default=None),
        max(values, default=None),
        len(values),
        errors
    )


# ============================================================
# Evaluation recommendation
# ============================================================

def evaluation_decision(
    status,
    end,
    checkpoint,
    first,
    margin,
    errors
):
    # Do not evaluate models undergoing training.

    if status in ACTIVE_STATES:
        return "NO", "REMOVE_FROM_READY"

    # A usable best checkpoint is required.

    if checkpoint is None:
        return "NO", "REMOVE_FROM_READY"

    # Training termination must be established.

    if end is None:
        return "REVIEW", "REVIEW_TRAINING"

    # Archive errors prevent reliable evaluation decisions,
    # but do not invalidate an otherwise ready model.

    if errors:
        return "YES", "REVIEW_ARCHIVE"

    # No existing hypotheses.

    if first is None:
        return "YES", "EVALUATE_NOW"

    # Evaluation started before training ended,
    # or within the configured safety margin.

    if first <= end + margin:
        return "YES", "REEVALUATE_NOW"

    # Hypotheses predate the current best checkpoint.

    if first < checkpoint:
        return "YES", "REEVALUATE_NOW"

    # No detected snapshot timing problem.

    return "YES", "KEEP_EVALUATION"


# ============================================================
# Compare recommendation against models.ready
# ============================================================

def ready_status(model, ready, ready_models):
    listed = model.name in ready_models

    if ready == "YES":
        consistency = (
            "OK"
            if listed
            else "MISSING_FROM_READY"
        )

    elif ready == "NO":
        consistency = (
            "UNEXPECTED_IN_READY"
            if listed
            else "OK"
        )

    else:
        consistency = (
            "REVIEW_LISTED"
            if listed
            else "REVIEW_UNLISTED"
        )

    return (
        "YES" if listed else "NO",
        consistency
    )


# ============================================================
# Inspect one model
# ============================================================

def inspect(model, active, margin, ready_models):
    status, job, end, last_log = training_status(
        model, active
    )

    checkpoint = checkpoint_time(model)

    first, last, count, errors = hypothesis_times(
        model
    )

    warnings = []
    delay = None

    # --------------------------------------------------------
    # Diagnostic warnings
    # --------------------------------------------------------

    if errors:
        warnings.append("ARCHIVE_READ_ERROR")

    if status in ACTIVE_STATES:
        warnings.append("TRAINING_ACTIVE")

    elif end is None:
        warnings.append("UNKNOWN_TRAINING_END")

    if checkpoint is None:
        warnings.append("NO_BEST_CHECKPOINT")

    if first is None:
        warnings.append("NO_HYPOTHESES")

    else:
        if end is not None:
            delay = first - end

            if delay < 0:
                warnings.append(
                    "OLD_SNAPSHOT_RISK"
                )

            elif delay <= margin:
                warnings.append(
                    "SNAPSHOT_RISK"
                )

        if checkpoint is not None:
            if first < checkpoint:
                warnings.append(
                    "HYP_BEFORE_CHECKPOINT"
                )

                if last >= checkpoint:
                    warnings.append(
                        "MIXED_SNAPSHOT_RISK"
                    )

    # --------------------------------------------------------
    # Recommended readiness and evaluation action
    # --------------------------------------------------------

    ready, action = evaluation_decision(
        status,
        end,
        checkpoint,
        first,
        margin,
        errors
    )

    # --------------------------------------------------------
    # Actual membership in models.ready
    # --------------------------------------------------------

    listed, consistency = ready_status(
        model,
        ready,
        ready_models
    )
    if ready == "NO" and listed == "NO":
        action = "KEEP_EXCLUDED"
        
    return [
        model.name, #str(model),
        ready,
        listed,
        consistency,
        action,
        status,
        job,
        fmt(last_log),
        fmt(end),
        fmt(checkpoint),
        fmt(first),
        fmt(last),
        count,
        (
            f"{delay / 3600:+.2f}"
            if delay is not None
            else "-"
        ),
        ",".join(warnings) or "OK"
    ]


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inspection of training status, "
            "evaluation freshness and models.ready consistency."
        )
    )

    parser.add_argument(
        "--roots",
        nargs="+",
        required=True,
        help="Model root directories"
    )

    parser.add_argument(
        "--margin",
        type=int,
        default=3600,
        help="Snapshot safety margin in seconds"
    )

    parser.add_argument(
        "--ready-file",
        required=True,
        help="Path to models.ready (read-only)"
    )

    args = parser.parse_args()

    if args.margin < 0:
        parser.error("--margin must be non-negative")

    # --------------------------------------------------------
    # Validate model roots
    # --------------------------------------------------------

    roots = list(map(Path, args.roots))

    for root in roots:
        if not root.is_dir():
            parser.error(
                f"Missing model root: {root}"
            )

    # --------------------------------------------------------
    # Read models.ready
    # --------------------------------------------------------

    ready_file = Path(args.ready_file)

    if not ready_file.is_file():
        parser.error(
            f"Ready models file not found: {ready_file}"
        )

    with ready_file.open("r") as f:
        ready_models = {
            line.strip()
            for line in f
            if line.strip()
        }

    # --------------------------------------------------------
    # Obtain active Slurm jobs
    # --------------------------------------------------------

    active = active_jobs()

    seen_models = set()

    writer = csv.writer(
        sys.stdout,
        delimiter="\t",
        lineterminator="\n"
    )

    writer.writerow([
        "MODEL",
        "SHOULD_BE_READY",
        "IN_READY",
        "READY_CONSISTENCY",
        "ACTION",
        "TRAIN_STATUS",
        "JOB_ID",
        "LAST_LOG",
        "TRAIN_END",
        "BEST_CHECKPOINT",
        "FIRST_HYP",
        "LAST_HYP",
        "HYP_COUNT",
        "DELAY_HOURS",
        "WARNING"
    ])

    # --------------------------------------------------------
    # Inspect model directories
    # --------------------------------------------------------

    for root in roots:
        for model in sorted(root.iterdir()):
            if not model.is_dir():
                continue

            if not (model / "mammoth").is_dir():
                continue

            seen_models.add(model.name)

            writer.writerow(
                inspect(
                    model,
                    active,
                    args.margin,
                    ready_models
                )
            )

    # --------------------------------------------------------
    # Detect stale or otherwise unresolved models.ready entries
    # --------------------------------------------------------

    for name in sorted(ready_models - seen_models):
        writer.writerow([
            name,
            "REVIEW",
            "YES",
            "NOT_FOUND_IN_ROOTS",
            "REVIEW_MISSING_MODEL",
            "NOT_FOUND",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            0,
            "-",
            "MODEL_NOT_FOUND"
        ])


if __name__ == "__main__":
    main()
