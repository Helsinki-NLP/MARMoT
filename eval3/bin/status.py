#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
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


def job_files(flags_dir: Path, kind: str) -> tuple[Path, Path]:
    if kind == "inference":
        return (
            flags_dir / "inference.done",
            flags_dir / "inference.submitted",
        )

    if kind == "scoring":
        return (
            flags_dir / "metrics.done",
            flags_dir / "metrics.submitted",
        )

    raise ValueError(kind)


def collect_jobids(model_paths: list[dict[str, Path]]) -> set[str]:
    jobids = set()

    for paths in model_paths:
        for kind in ("inference", "scoring"):
            done_file, flag_file = job_files(paths["flags"], kind)

            if done_file.exists():
                continue

            jobid = read_jobid(flag_file)
            if jobid:
                jobids.add(jobid)

    return jobids


def query_squeue(jobids: set[str]) -> dict[str, tuple[str, str, str]]:
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
        return {}

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
    slurm_status: dict[str, tuple[str, str, str]],
) -> str:
    done_file, flag_file = job_files(flags_dir, kind)

    if done_file.exists():
        return "DONE"

    jobid = read_jobid(flag_file)

    if not jobid:
        return "-"

    status = slurm_status.get(jobid)

    if status is None:
        return "LEFT"

    state, runtime, reason = status

    if state == "RUNNING":
        return "RUN"

    if state == "PENDING":
        return "PEND"

    return state


def read_plan_outputs(plan_file: Path) -> list[str]:
    outputs = []

    if not plan_file.is_file():
        return outputs

    output_re = re.compile(r'--output\s+"([^"]+)"')

    with plan_file.open("r", errors="replace") as f:
        for line in f:
            m = output_re.search(line)

            if m:
                outputs.append(Path(m.group(1)).name)

    return outputs


def directory_names(path: Path, suffix: str) -> set[str]:
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
    slurm_status: dict[str, tuple[str, str, str]],
) -> tuple:
    task_count = count_selected_tasks(
        paths["root"] / "inf_tasks.txt"
    )

    outputs = read_plan_outputs(
        paths["tasks"] / "plan.out"
    )

    test_count = len(outputs)

    hyp_names = directory_names(
        paths["hypotheses"],
        ".hyp",
    )

    inf_completed = sum(
        1
        for name in outputs
        if name in hyp_names
    )

    sacre_names = directory_names(
        paths["scores"],
        ".sacre",
    )

    score_completed = sum(
        1
        for name in outputs
        if name[:-4] + ".sacre" in sacre_names
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

    # A stale .done flag must not claim that work is complete.
    if inf_completed < test_count and inf_job == "DONE":
        inf_job = "-"

    if score_completed < test_count and score_job == "DONE":
        score_job = "-"

    return (
        alias,
        task_count,
        test_count,
        inf_completed,
        inf_job,
        score_completed,
        score_job,
    )



def compact_job_status(status: str) -> str:
    if status.startswith("RUN"):
        return "RUN"

    if status.startswith("PEND"):
        return "PEND"

    if status == "LEFT QUEUE":
        return "LEFT"

    return status


def summarize_jobs(statuses: list[str]) -> str:
    pending = sum(
        1
        for status in statuses
        if compact_job_status(status) == "PEND"
    )
    return str(pending) if pending else "-"


def print_table(rows):
    fmt = "{:<37} {:>5} {:>5} {:>14} {:>8} {:>12} {:>8}"

    print(
        fmt.format(
            "model",
            "tasks",
            "tests",
            "inference",
            "pending?",
            "scoring",
            "pending?",
        )
    )

    print(
        fmt.format(
            "-" * 37,
            "-" * 5,
            "-" * 5,
            "-" * 12,
            "-" * 8,
            "-" * 12,
            "-" * 8,
        )
    )

    for (
        alias,
        task_count,
        test_count,
        inf_completed,
        inf_job,
        score_completed,
        score_job,
    ) in rows:
        print(
            fmt.format(
                alias,
                task_count,
                test_count,
                f"{test_count - inf_completed} > {inf_completed}",
                compact_job_status(inf_job),
                f"{test_count - score_completed} > {score_completed}",
                compact_job_status(score_job),
            )
        )

    print(
        fmt.format(
            "-" * 37,
            "-" * 5,
            "-" * 5,
            "-" * 12,
            "-" * 8,
            "-" * 12,
            "-" * 8,
        )
    )

    total_tasks = sum(r[1] for r in rows)
    total_tests = sum(r[2] for r in rows)
    total_inf = sum(r[3] for r in rows)
    total_scores = sum(r[5] for r in rows)

    print(
        fmt.format(
            "TOTAL",
            total_tasks,
            total_tests,
            f"{total_tests - total_inf} > {total_inf}",
            summarize_jobs([r[4] for r in rows]),
            f"{total_tests - total_scores} > {total_scores}",
            summarize_jobs([r[6] for r in rows]),
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

        alias, model_dir = item.split("=", 1)
        models.append(
            (alias, model_dir)
        )

    model_paths = [
        (
            alias,
            evaluation_paths(Path(model_dir)),
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
