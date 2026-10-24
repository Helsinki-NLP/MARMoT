#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from pathlib import Path


def line_count(path: Path) -> int | None:
    try:
        with path.open("r", encoding="utf-8", errors="strict") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeError):
        return None


def valid_hyp(path: Path, expected_lines: int) -> bool:
    return line_count(path) == expected_lines


p = argparse.ArgumentParser()
p.add_argument("--mammoth", required=True)
p.add_argument("--config", required=True)
p.add_argument("--model", required=True)
p.add_argument("--task-id", required=True)
p.add_argument("--src", required=True)
p.add_argument("--expected-lines", required=True, type=int)
p.add_argument("--output", required=True)
p.add_argument("--log", required=True)
args = p.parse_args()

src = Path(args.src)
out = Path(args.output)
log = Path(args.log)
expected_lines = args.expected_lines

if expected_lines <= 0:
    raise SystemExit(f"invalid --expected-lines: {expected_lines}")

# Planning may be old. Recheck the canonical result at execution time.
if out.exists():
    n = line_count(out)
    if n == expected_lines:
        print(f"SKIP valid hypothesis " f"({n} lines): {out}")
        sys.exit(0)
    raise SystemExit(
        f"REFUSE existing incomplete hypothesis: "
        f"{out}: {n} lines, expected {expected_lines}")

job = os.environ.get("SLURM_JOB_ID", "noslurm")
tmp = Path(f"{out}.tmp.job-{job}.pid-{os.getpid()}")

tmp.unlink(missing_ok=True)
log.parent.mkdir(parents=True, exist_ok=True)

cmd = [
    sys.executable, "-u",
    str(Path(args.mammoth) / "translate.py"),
    "--config", args.config,
    "--model", args.model,
    "--task_id", args.task_id,
    "--src", str(src),
    "--output", str(tmp),
]

try:
    with log.open("ab") as err:
        proc = subprocess.run(cmd, stderr=err)

    if proc.returncode:
        raise RuntimeError(
            f"translate.py exited {proc.returncode}; see {log}"
        )
    n = line_count(tmp)
    if n != expected_lines:
        raise RuntimeError(
            f"inference produced invalid hypothesis: "
            f"{n} lines, expected {expected_lines}: {tmp}"
        )
    # Make file contents durable before publication.
    with tmp.open("r+b") as f:
        os.fsync(f.fileno())
        
    try:
        os.link(tmp, out)
    except FileExistsError:
        # Somebody else published while we were translating.
        n = line_count(out)
        if n == expected_lines:
            print(f"SKIP publication; another process completed: {out}")
            sys.exit(0)
        raise RuntimeError(
            f"REFUSE existing hypothesis after inference: "
            f"{out}: {n} lines, expected {expected_lines}"
        )
    print(f"PUBLISHED {out}")

finally:
    tmp.unlink(missing_ok=True)


