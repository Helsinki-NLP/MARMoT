#!/usr/bin/env python3
"""Sum task weights per compute node and per GPU from a task YAML file.

Reads a YAML file with the structure:

    tasks:
      task_name:
        weight: 20507.9678...
        node_gpu: "0:0"
        ...

`node_gpu` is "<node>:<gpu>"; the first component identifies the compute
node, the second the GPU on that node. Weights are summed exactly using
Decimal arithmetic (the YAML values carry many fractional digits).

Usage:
    ./sum_task_weights.py train-weights.yaml
    ./sum_task_weights.py train-weights.yaml --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required (pip install pyyaml)")


def parse_node_gpu(value: object) -> tuple[int, int]:
    """Split a node_gpu value like '0:0' (or '0 0') into (node, gpu)."""
    text = str(value).strip().strip('"').strip("'")
    for sep in (":", ",", "/", " ", "\t"):
        if sep in text:
            parts = text.split(sep)
            break
    else:
        parts = [text]
    parts = [p for p in parts if p != ""]
    if len(parts) != 2:
        raise ValueError(
            f"cannot parse node_gpu {value!r} (expected '<node>:<gpu>')"
        )
    try:
        node, gpu = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(
            f"non-integer node/gpu in node_gpu {value!r}"
        ) from None
    return node, gpu


def load_totals(path: str):
    """Return (gpu_totals, gpu_counts, node totals) keyed by node/gpu."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except OSError as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    except yaml.YAMLError as exc:
        sys.exit(f"error: {path}: invalid YAML: {exc}")

    if not isinstance(data, dict) or "tasks" not in data:
        sys.exit(f"error: {path}: no top-level 'tasks' mapping")
    tasks = data["tasks"]
    if not isinstance(tasks, dict):
        sys.exit(f"error: {path}: 'tasks' is not a mapping")

    gpu_totals: dict[tuple[int, int], Decimal] = defaultdict(Decimal)
    gpu_counts: dict[tuple[int, int], int] = defaultdict(int)
    skipped: list[str] = []

    for name, spec in tasks.items():
        if not isinstance(spec, dict):
            skipped.append(f"{name} (not a mapping)")
            continue
        if "weight" not in spec or "node_gpu" not in spec:
            skipped.append(f"{name} (missing weight or node_gpu)")
            continue
        try:
            weight = Decimal(str(spec["weight"]))
        except InvalidOperation:
            skipped.append(f"{name} (bad weight {spec['weight']!r})")
            continue
        try:
            node, gpu = parse_node_gpu(spec["node_gpu"])
        except ValueError as exc:
            skipped.append(f"{name} ({exc})")
            continue
        gpu_totals[(node, gpu)] += weight
        gpu_counts[(node, gpu)] += 1

    return gpu_totals, gpu_counts, skipped


def fmt(value: Decimal, precision: int) -> str:
    return f"{value:,.{precision}f}"


def print_table(gpu_totals, gpu_counts, precision: int) -> None:
    nodes = sorted({n for n, _ in gpu_totals})
    gpus = sorted({g for _, g in gpu_totals})

    # Per-GPU table.
    width = max(
        [len(fmt(t, precision)) for t in gpu_totals.values()]
        + [len(f"gpu {g}") for g in gpus]
    )
    header = "node |" + "".join(f" {'gpu ' + str(g):<{width}} " for g in gpus)
    print("Weight per GPU")
    print(header)
    print("-" * len(header))

    node_totals: dict[int, Decimal] = defaultdict(Decimal)
    gpu_totals_by_gpu: dict[int, Decimal] = defaultdict(Decimal)
    for node in nodes:
        cells = []
        for gpu in gpus:
            total = gpu_totals.get((node, gpu))
            if total is None:
                cells.append(" " * (width + 2))
            else:
                node_totals[node] += total
                gpu_totals_by_gpu[gpu] += total
                cells.append(f" {fmt(total, precision):>{width}} ")
        print(f"{node:>4} |" + "".join(cells))

    grand = sum(node_totals.values(), Decimal(0))
    print("-" * len(header))
    total_cells = "".join(
        f" {fmt(gpu_totals_by_gpu[g], precision):>{width}} " for g in gpus
    )
    print(f"{'all':>4} |" + total_cells)

    # Per-node summary.
    print("\nWeight per node")
    print(f"{'node':>4} | {'tasks':>5} | {'total weight':>20} | {'share':>7}")
    print("-" * 44)
    for node in nodes:
        tasks = sum(c for (n, _), c in gpu_counts.items() if n == node)
        share = (node_totals[node] / grand * 100) if grand else Decimal(0)
        print(f"{node:>4} | {tasks:>5} | {fmt(node_totals[node], precision):>20} | {share:>6.2f}%")
    print("-" * 44)
    total_tasks = sum(gpu_counts.values())
    print(f"{'all':>4} | {total_tasks:>5} | {fmt(grand, precision):>20} | {'100.00%':>7}")

    # Balance check.
    if gpu_totals:
        lo = min(gpu_totals.values())
        hi = max(gpu_totals.values())
        mean = grand / len(gpu_totals)
        print(
            f"\nGPU balance: min {fmt(lo, precision)}, max {fmt(hi, precision)}, "
            f"mean {fmt(mean, precision)}, max/min ratio {hi / lo:.3f}"
        )


def to_json(gpu_totals, gpu_counts) -> dict:
    per_node: dict[str, dict] = defaultdict(lambda: {"total": "0", "gpus": {}})
    for (node, gpu), total in sorted(gpu_totals.items()):
        entry = per_node[str(node)]
        entry["gpus"][str(gpu)] = {
            "weight": str(total),
            "tasks": gpu_counts[(node, gpu)],
        }
    for entry in per_node.values():
        entry["total"] = str(sum(Decimal(g["weight"]) for g in entry["gpus"].values()))
    return {
        "per_node": dict(per_node),
        "grand_total": str(sum(Decimal(e["total"]) for e in per_node.values())),
        "total_tasks": sum(gpu_counts.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sum task weights per compute node and per GPU."
    )
    parser.add_argument("yaml_file", help="task YAML file (e.g. train-weights.yaml)")
    parser.add_argument(
        "--precision", type=int, default=2,
        help="decimal places for printed weights (default: 2)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args()

    gpu_totals, gpu_counts, skipped = load_totals(args.yaml_file)

    if not gpu_totals:
        sys.exit(f"error: {args.yaml_file}: no tasks with weight and node_gpu found")

    if args.json:
        print(json.dumps(to_json(gpu_totals, gpu_counts), indent=2))
    else:
        print(f"{args.yaml_file}: {sum(gpu_counts.values())} tasks\n")
        print_table(gpu_totals, gpu_counts, args.precision)

    if skipped:
        print(f"\nskipped {len(skipped)} task(s):", file=sys.stderr)
        for entry in skipped:
            print(f"  - {entry}", file=sys.stderr)


if __name__ == "__main__":
    main()
