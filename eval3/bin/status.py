#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from collections import Counter
from pathlib import Path


def count_selected_tasks(path: Path) -> int:
    if not path.is_file():
        return 0

    with path.open("r", errors="replace") as f:
        return sum(
            1
            for line in f
            if line.strip() and not line.lstrip().startswith("#")
        )


def evaluation_paths(model_dir: Path) -> dict[str, Path]:
    """
    Match mk-paths.mk:

    - new layout:    <model>/evaluation/{configs,tasks,hypotheses,logs,scores,flags}
    - legacy layout: <model>/{inf_out,inf_logs,inf_scores}, with flags in <model>
    """
    new_root = model_dir / "evaluation"

    if new_root.is_dir():
        return {
            "root": new_root,
            "configs": new_root / "configs",
            "tasks": new_root / "tasks",
            "hypotheses": new_root / "hypotheses",
            "logs": new_root / "logs",
            "scores": new_root / "scores",
            "flags": new_root / "flags",
        }

    return {
        "root": model_dir,
        "configs": model_dir / "inf_out",
        "tasks": model_dir / "inf_out",
        "hypotheses": model_dir / "inf_out",
        "logs": model_dir / "inf_logs",
        "scores": model_dir / "inf_scores",
        "flags": model_dir,
    }


def read_jobid(path: Path) -> str:
    if not path.is_file():
        return ""

    text = path.read_text(errors="replace").strip()
    m = re.search(r"(?:Submitted batch job\s+)?([0-9]+)", text)
    return m.group(1) if m else ""


def submitted_flag(flags_dir: Path, kind: str) -> Path:
    if kind == "inference":
        return flags_dir / "inference.submitted"

    if kind == "scoring":
        return flags_dir / "metrics.submitted"

    raise ValueError(kind)


def collect_jobids(model_paths: list[dict[str, Path]]) -> set[str]:
    jobids = set()

    for paths in model_paths:
        for kind in ("inference", "scoring"):
            flag_file = submitted_flag(
                paths["flags"],
                kind,
            )

            jobid = read_jobid(flag_file)

            if jobid:
                jobids.add(jobid)

    return jobids


def query_squeue(
    jobids: set[str],
) -> dict[str, tuple[str, str, str]] | None:
    """
    Return current Slurm states for the requested job IDs.

    An empty dictionary means that the query succeeded but none of the
    recorded jobs is currently in squeue.

    None means that Slurm could not be queried reliably.  In that case
    status.py must not remove any .submitted flags.
    """
    if not jobids:
        return {}

    try:
        result = subprocess.run(
            [
                "squeue",
                "-h",
                "-j",
                ",".join(sorted(jobids)),
                "-o",
                "%i|%T|%M|%R",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None

    statuses = {}

    for line in result.stdout.splitlines():
        parts = line.strip().split("|", 3)

        if len(parts) != 4:
            continue

        jobid, state, runtime, reason = parts
        statuses[jobid] = (state, runtime, reason)

    return statuses


def job_status(
    flags_dir: Path,
    kind: str,
    slurm_status: dict[str, tuple[str, str, str]] | None,
) -> str:
    """
    Report only current Slurm state.

    If a .submitted flag contains a job ID and a successful squeue query
    shows that the job is no longer present, the flag is stale and is
    removed.

    .done flags are deliberately ignored.  Evaluation completeness is
    determined from the actual hypothesis and score artifacts.
    """
    flag_file = submitted_flag(
        flags_dir,
        kind,
    )

    jobid = read_jobid(flag_file)

    if not jobid:
        return "-"

    # Slurm could not be queried reliably.  Preserve the flag.
    if slurm_status is None:
        return "?"

    status = slurm_status.get(jobid)

    if status is None:
        # The squeue query succeeded, but this job is no longer present.
        # Its .submitted flag is therefore stale.
        try:
            flag_file.unlink()
        except FileNotFoundError:
            pass

        return "-"

    state, _runtime, _reason = status

    if state == "RUNNING":
        return "RUN"

    if state == "PENDING":
        return "PEND"

    return state


def read_plan_outputs(plan_file: Path) -> list[str]:
    """
    Return the hypothesis basenames named by the current plan.out.

    The plan is the authoritative inventory of evaluation cases.  Files
    in the hypothesis or score directories that are not represented in
    this plan are deliberately ignored by status reporting.
    """
    outputs = []

    if not plan_file.is_file():
        return outputs

    output_re = re.compile(r'--output\s+"([^"]+)"')

    with plan_file.open("r", errors="replace") as f:
        for line in f:
            m = output_re.search(line)

            if m:
                outputs.append(
                    Path(m.group(1)).name
                )

    return outputs


def test_type_counts(outputs: list[str]) -> Counter[str]:
    """
    Count planned dataset tests by task prefix.

    Examples:

    - mt_BR.por-XX.eng.flo.hyp       -> mt
    - mt2_BR.por-XX.eng.flo.hyp      -> mt
    - zero_FI.fin-XX.eng.flo.hyp     -> zero
    - sentmt1_...                    -> sentmt

    The counts are over plan.out outputs, so their sum is the value shown
    in the tests column.
    """
    counts: Counter[str] = Counter()

    for name in outputs:
        task_name = name.split("_", 1)[0]
        prefix = re.sub(r"[0-9]+$", "", task_name)
        counts[prefix or task_name] += 1

    return counts


def format_test_types(counts: Counter[str]) -> str:
    if not counts:
        return "-"

    return ", ".join(
        f"{prefix} ({count})"
        for prefix, count in sorted(counts.items())
    )


def directory_names(
    path: Path,
    suffix: str,
) -> set[str]:
    try:
        return {
            entry.name
            for entry in path.iterdir()
            if entry.name.endswith(suffix)
        }
    except (FileNotFoundError, NotADirectoryError):
        return set()


def row(
    alias: str,
    paths: dict[str, Path],
    slurm_status: dict[str, tuple[str, str, str]] | None,
) -> tuple:
    task_count = count_selected_tasks(
        paths["root"] / "inf_tasks.txt"
    )

    outputs = read_plan_outputs(
        paths["tasks"] / "plan.out"
    )

    test_count = len(outputs)
    type_counts = test_type_counts(outputs)

    hyp_names = directory_names(
        paths["hypotheses"],
        ".hyp",
    )

    sacre_names = directory_names(
        paths["scores"],
        ".sacre",
    )

    # Count only hypotheses belonging to the current plan.
    hyp_count = sum(
        1
        for name in outputs
        if name in hyp_names
    )

    # Planned evaluation cases still waiting for inference.
    inf_left = test_count - hyp_count

    # Count only SacreBLEU files belonging to the current plan.
    sacre_count = sum(
        1
        for name in outputs
        if name[:-4] + ".sacre" in sacre_names
    )

    # Scoring work currently possible and still unfinished:
    # an existing hypothesis without its corresponding SacreBLEU file.
    #
    # Calculate this explicitly rather than as hyp_count - sacre_count,
    # so an unusual orphan score file cannot make the count negative.
    score_left = sum(
        1
        for name in outputs
        if (
            name in hyp_names
            and name[:-4] + ".sacre" not in sacre_names
        )
    )

    inf_job = job_status(
        paths["flags"],
        "inference",
        slurm_status,
    )

    score_job = job_status(
        paths["flags"],
        "scoring",
        slurm_status,
    )

    return (
        alias,
        task_count,
        test_count,
        hyp_count,
        inf_left,
        sacre_count,
        score_left,
        inf_job,
        score_job,
        type_counts,
    )


def summarize_jobs(statuses: list[str]) -> str:
    running = sum(
        1
        for status in statuses
        if status == "RUN"
    )

    pending = sum(
        1
        for status in statuses
        if status == "PEND"
    )

    unknown = sum(
        1
        for status in statuses
        if status == "?"
    )

    parts = []

    if running:
        parts.append(f"{running}R")

    if pending:
        parts.append(f"{pending}P")

    if unknown:
        parts.append(f"{unknown}?")

    return "/".join(parts) if parts else "-"


def print_table(rows):
    fmt = (
        "{:<42} "
        "{:>5} "
        "{:>5} "
        "{:>6} "
        "{:>8} "
        "{:>6} "
        "{:>10} "
        "{:<8} "
        "{:<9} "
        "{}"
    )

    print(
        fmt.format(
            "model",
            "tasks",
            "tests",
            "hyp",
            "inf left",
            "sacre",
            "score left",
            "inf job",
            "score job",
            "test types",
        )
    )

    print(
        fmt.format(
            "-" * 42,
            "-" * 5,
            "-" * 5,
            "-" * 6,
            "-" * 8,
            "-" * 6,
            "-" * 10,
            "-" * 8,
            "-" * 9,
            "-" * 30,
        )
    )

    for (
        alias,
        task_count,
        test_count,
        hyp_count,
        inf_left,
        sacre_count,
        score_left,
        inf_job,
        score_job,
        type_counts,
    ) in rows:
        print(
            fmt.format(
                alias,
                task_count,
                test_count,
                hyp_count,
                inf_left,
                sacre_count,
                score_left,
                inf_job,
                score_job,
                format_test_types(type_counts),
            )
        )

    print(
        fmt.format(
            "-" * 42,
            "-" * 5,
            "-" * 5,
            "-" * 6,
            "-" * 8,
            "-" * 6,
            "-" * 10,
            "-" * 8,
            "-" * 9,
            "-" * 30,
        )
    )

    total_tasks = sum(
        r[1]
        for r in rows
    )

    total_tests = sum(
        r[2]
        for r in rows
    )

    total_hyp = sum(
        r[3]
        for r in rows
    )

    total_inf_left = sum(
        r[4]
        for r in rows
    )

    total_sacre = sum(
        r[5]
        for r in rows
    )

    total_score_left = sum(
        r[6]
        for r in rows
    )

    total_type_counts: Counter[str] = Counter()

    for r in rows:
        total_type_counts.update(r[9])

    print(
        fmt.format(
            "TOTAL",
            total_tasks,
            total_tests,
            total_hyp,
            total_inf_left,
            total_sacre,
            total_score_left,
            summarize_jobs(
                [r[7] for r in rows]
            ),
            summarize_jobs(
                [r[8] for r in rows]
            ),
            format_test_types(total_type_counts),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="ALIAS=DIR",
        help="Model alias and model directory. May be repeated.",
    )

    args = parser.parse_args()

    models: list[tuple[str, str]] = []

    for item in args.model:
        if "=" not in item:
            raise SystemExit(
                f"Bad --model value: {item!r}; expected ALIAS=DIR"
            )

        alias, model_dir = item.split(
            "=",
            1,
        )

        models.append(
            (
                alias,
                model_dir,
            )
        )

    model_paths = [
        (
            alias,
            evaluation_paths(
                Path(model_dir)
            ),
        )
        for alias, model_dir in models
    ]

    slurm_status = query_squeue(
        collect_jobids(
            [
                paths
                for _alias, paths in model_paths
            ]
        )
    )

    rows = [
        row(
            alias,
            paths,
            slurm_status,
        )
        for alias, paths in model_paths
    ]

    print_table(rows)


if __name__ == "__main__":
    main()

