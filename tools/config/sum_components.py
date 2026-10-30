#!/usr/bin/env python3
"""Summarize the encoder/decoder components hosted on each GPU and node.

Components come from a task's `enc_sharing_group` / `dec_sharing_group`
and are namespaced, i.e. "enc:<name>" and "dec:<name>" are different
components even when the names match.

  * components on a GPU  = union of the components of the tasks placed on it
  * components on a node = union over all GPUs of that node

A component shared by several tasks on the same GPU (or by several GPUs
of a node) is counted once for that GPU/node.

Usage:
    ./sum_components.py train-weights.yaml
    ./sum_components.py train-weights.yaml --verbose   # names + per-component spread
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter, defaultdict

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required (pip install pyyaml)")

COMPONENT_KEYS = (("enc_sharing_group", "enc"), ("dec_sharing_group", "dec"))


def parse_node_gpu(value: object, task_name: str = "?") -> tuple[int, int]:
    """Split a node_gpu value like '0:0' (or '0 0') into (node, gpu)."""
    text = str(value).strip().strip('"').strip("'")
    parts: list[str] = []
    for sep in (":", ",", "/", " ", "\t"):
        if sep in text:
            parts = [p for p in text.split(sep) if p != ""]
            break
    if not parts:
        parts = [text]
    if len(parts) != 2:
        raise ValueError(
            f"task {task_name!r}: cannot parse node_gpu {value!r} "
            "(expected '<node>:<gpu>')"
        )
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(
            f"task {task_name!r}: non-integer node/gpu in node_gpu {value!r}"
        ) from None


def task_components(spec: dict, name: str) -> set[str]:
    comps: set[str] = set()
    for key, kind in COMPONENT_KEYS:
        if key not in spec:
            continue
        value = spec[key]
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError(f"task {name!r}: {key} is not a list")
        comps.update(f"{kind}:{c}" for c in value)
    return comps


def load(path: str) -> tuple[list[tuple[str, tuple[int, int], set[str]]], int]:
    """Return ([(task, gpu, components)], skipped_count)."""
    try:
        with open(path, encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except OSError as exc:
        sys.exit(f"error: cannot read {path}: {exc}")
    except yaml.YAMLError as exc:
        sys.exit(f"error: {path}: invalid YAML: {exc}")

    if not isinstance(data, dict) or not isinstance(data.get("tasks"), dict):
        sys.exit(f"error: {path}: no top-level 'tasks' mapping")

    tasks: list[tuple[str, tuple[int, int], set[str]]] = []
    skipped: list[str] = []
    for name, spec in data["tasks"].items():
        if not isinstance(spec, dict) or "node_gpu" not in spec:
            skipped.append(f"{name} (missing node_gpu)")
            continue
        try:
            gpu = parse_node_gpu(spec["node_gpu"], name)
            comps = task_components(spec, name)
        except ValueError as exc:
            skipped.append(str(exc))
            continue
        tasks.append((name, gpu, comps))

    if not tasks:
        sys.exit(f"error: {path}: no tasks with a usable node_gpu")
    if skipped:
        print(f"warning: skipped {len(skipped)} task(s):", file=sys.stderr)
        for entry in skipped[:10]:
            print(f"  - {entry}", file=sys.stderr)
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more", file=sys.stderr)
    return tasks, len(skipped)


def fmt_stats(values: list[int]) -> str:
    if not values:
        return "n/a"
    return (
        f"min {min(values)} / median {statistics.median(values):g} "
        f"/ max {max(values)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize enc/dec components per GPU and per compute node."
    )
    parser.add_argument("yaml_file", help="task YAML file (e.g. train-weights.yaml)")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="also list component names per GPU/node and the spread of each component",
    )
    args = parser.parse_args()

    tasks, _ = load(args.yaml_file)

    # --- aggregate ------------------------------------------------------- #
    gpu_comps: dict[tuple[int, int], set[str]] = defaultdict(set)
    gpu_tasks: Counter = Counter()
    for _, gpu, comps in tasks:
        gpu_comps[gpu] |= comps
        gpu_tasks[gpu] += 1

    node_comps: dict[int, set[str]] = defaultdict(set)
    node_gpus: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for gpu in sorted(gpu_comps):
        node_comps[gpu[0]] |= gpu_comps[gpu]
        node_gpus[gpu[0]].append(gpu)

    comp_gpus: dict[str, set] = defaultdict(set)
    comp_nodes: dict[str, set] = defaultdict(set)
    comp_tasks: Counter = Counter()
    for _, gpu, comps in tasks:
        for c in comps:
            comp_gpus[c].add(gpu)
            comp_nodes[c].add(gpu[0])
            comp_tasks[c] += 1

    gpus = sorted(gpu_comps)
    nodes = sorted(node_comps)
    enc_total = sum(1 for c in comp_gpus if c.startswith("enc:"))
    dec_total = len(comp_gpus) - enc_total

    # --- header ---------------------------------------------------------- #
    print(
        f"{args.yaml_file}: {len(tasks)} tasks, {len(gpus)} GPUs, "
        f"{len(nodes)} nodes"
    )
    print(
        f"components: {len(comp_gpus)} distinct "
        f"({enc_total} enc, {dec_total} dec), "
        f"{sum(len(s) for s in gpu_comps.values())} per-GPU placements, "
        f"{sum(len(s) for s in node_comps.values())} per-node placements"
    )

    # --- per-GPU table --------------------------------------------------- #
    gpu_totals = [len(gpu_comps[g]) for g in gpus]
    print(f"\ncomponents per GPU ({fmt_stats(gpu_totals)}):")
    header = f"{'gpu':>6} | {'tasks':>5} | {'enc':>3} | {'dec':>3} | {'total':>5}"
    print(header)
    print("-" * len(header))
    for gpu in gpus:
        comps = gpu_comps[gpu]
        n_enc = sum(1 for c in comps if c.startswith("enc:"))
        print(
            f"{gpu[0]}:{gpu[1]:>4} | {gpu_tasks[gpu]:>5} | {n_enc:>3} "
            f"| {len(comps) - n_enc:>3} | {len(comps):>5}"
        )
    print("-" * len(header))
    n_enc_all = sum(
        1 for g in gpus for c in gpu_comps[g] if c.startswith("enc:")
    )
    print(
        f"{'all':>6} | {len(tasks):>5} | {n_enc_all:>3} "
        f"| {sum(gpu_totals) - n_enc_all:>3} | {sum(gpu_totals):>5}"
    )
    print(
        f"sum of per-GPU totals: {sum(gpu_totals)} distinct placements of "
        f"{len(comp_gpus)} components "
        f"({sum(gpu_totals) / len(comp_gpus):.1f}x replication)"
    )

    # --- per-node table -------------------------------------------------- #
    node_totals = [len(node_comps[n]) for n in nodes]
    print(f"\ncomponents per compute node ({fmt_stats(node_totals)}):")
    header = (
        f"{'node':>4} | {'gpus':>4} | {'tasks':>5} | {'enc':>3} | {'dec':>3} "
        f"| {'union':>5} | {'sum/GPU':>7}"
    )
    print(header)
    print("-" * len(header))
    for node in nodes:
        comps = node_comps[node]
        n_enc = sum(1 for c in comps if c.startswith("enc:"))
        per_gpu_sum = sum(len(gpu_comps[g]) for g in node_gpus[node])
        print(
            f"{node:>4} | {len(node_gpus[node]):>4} "
            f"| {sum(gpu_tasks[g] for g in node_gpus[node]):>5} "
            f"| {n_enc:>3} | {len(comps) - n_enc:>3} | {len(comps):>5} "
            f"| {per_gpu_sum:>7}"
        )
    print("-" * len(header))
    print(
        f"sum of per-node unions: {sum(node_totals)} "
        f"({sum(node_totals) / len(comp_gpus):.1f}x replication of the "
        f"{len(comp_gpus)} distinct components)"
    )

    # --- universal components -------------------------------------------- #
    universal_gpu = sorted(c for c, g in comp_gpus.items() if len(g) == len(gpus))
    universal_node = sorted(c for c, n in comp_nodes.items() if len(n) == len(nodes))
    print(
        f"\non every GPU ({len(universal_gpu)}): "
        + (", ".join(universal_gpu) or "-")
    )
    print(
        f"on every node ({len(universal_node)}): "
        + (", ".join(universal_node) or "-")
    )

    if not args.verbose:
        return

    # --- component names per GPU ----------------------------------------- #
    print("\ncomponents per GPU (names):")
    for gpu in gpus:
        names = ", ".join(sorted(gpu_comps[gpu]))
        print(f"  {gpu[0]}:{gpu[1]:<4} ({len(gpu_comps[gpu]):>2}) {names}")

    print("\ncomponents per node (names):")
    for node in nodes:
        names = ", ".join(sorted(node_comps[node]))
        print(f"  {node:>4} ({len(node_comps[node]):>2}) {names}")

    # --- spread of each component ---------------------------------------- #
    print("\ncomponent spread (rarest first):")
    header = (
        f"{'component':<16} | {'tasks':>5} | {'gpus':>4} | {'nodes':>5}"
    )
    print(header)
    print("-" * len(header))
    ordered = sorted(
        comp_gpus, key=lambda c: (len(comp_gpus[c]), len(comp_nodes[c]), c)
    )
    for comp in ordered:
        print(
            f"{comp:<16} | {comp_tasks[comp]:>5} | {len(comp_gpus[comp]):>4} "
            f"| {len(comp_nodes[comp]):>5}"
        )


if __name__ == "__main__":
    main()
