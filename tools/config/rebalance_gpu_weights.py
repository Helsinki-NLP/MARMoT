#!/usr/bin/env python3
"""Rebalance task GPU assignments to equalize the total weight per GPU.

Each task in the YAML carries:

    weight:            sampling weight of the task
    node_gpu:          "<node>:<gpu>" placement
    enc_sharing_group: encoder components used by the task
    dec_sharing_group: decoder components used by the task

Components are identified by (kind, name): an encoder component and a
decoder component with the same name are *different* components. The set
of components "living" on a GPU is the union of the components of the
tasks placed on that GPU (the same component used by several tasks on
one GPU counts once).

The script greedily moves tasks between GPUs - and swaps pairs of tasks
when a single move is blocked - to minimize the variance of the total
weight per GPU (equivalently the sum of squared deviations from the
mean), subject to the component constraint:

  * by default every GPU must keep at most ``--limit`` components, where
    the limit defaults to the largest per-GPU component count of the
    input configuration, so the *maximum* number of components on any
    GPU never increases;
  * with ``--strict`` no single GPU may increase its own component
    count either.

Only the ``node_gpu`` lines inside the ``tasks:`` block of the output
YAML are rewritten; every other byte of the file is preserved.

Usage:
    ./rebalance_gpu_weights.py train-weights.yaml               # writes train-weights_rebalanced.yaml
    ./rebalance_gpu_weights.py train-weights.yaml --dry-run     # report only
    ./rebalance_gpu_weights.py train-weights.yaml -o out.yaml --verbose
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.exit("error: PyYAML is required (pip install pyyaml)")

COMPONENT_KEYS = {"enc_sharing_group": "enc", "dec_sharing_group": "dec"}

TASK_KEY_RE = re.compile(r"^(\s*)([^\s:#][^:]*):[ \t]*(?:#.*)?$")
NODE_GPU_RE = re.compile(r"^(\s*)node_gpu:[ \t]*(.*?)$")


def parse_node_gpu(value: object) -> tuple[int, int]:
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
        raise ValueError(f"cannot parse node_gpu {value!r} (expected '<node>:<gpu>')")
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(f"non-integer node/gpu in node_gpu {value!r}") from None


def fmt(value: float, precision: int) -> str:
    return f"{value:,.{precision}f}"


# --------------------------------------------------------------------------- #
# input
# --------------------------------------------------------------------------- #

@dataclass
class Task:
    name: str
    weight: float
    gpu: tuple[int, int]
    comps: frozenset[tuple[str, str]]


def task_components(spec: dict, name: str) -> frozenset[tuple[str, str]]:
    comps: set[tuple[str, str]] = set()
    for key, kind in COMPONENT_KEYS.items():
        if key not in spec:
            continue
        value = spec[key]
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValueError(f"task {name!r}: {key} is not a list")
        comps.update((kind, str(c)) for c in value)
    return frozenset(comps)


def load_tasks(path: str) -> list[Task]:
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

    tasks: list[Task] = []
    problems: list[str] = []
    for name, spec in data["tasks"].items():
        if not isinstance(spec, dict) or "weight" not in spec or "node_gpu" not in spec:
            problems.append(f"{name} (missing weight or node_gpu)")
            continue
        try:
            weight = float(spec["weight"])
            gpu = parse_node_gpu(spec["node_gpu"])
            comps = task_components(spec, name)
        except (TypeError, ValueError) as exc:
            problems.append(f"{name} ({exc})")
            continue
        tasks.append(Task(name, weight, gpu, comps))

    if problems:
        print(f"error: {path}: cannot use {len(problems)} task(s):", file=sys.stderr)
        for entry in problems:
            print(f"  - {entry}", file=sys.stderr)
        sys.exit(1)
    if not tasks:
        sys.exit(f"error: {path}: no usable tasks")
    return tasks


# --------------------------------------------------------------------------- #
# assignment / local search
# --------------------------------------------------------------------------- #

class Assignment:
    """Per-GPU weight and component bookkeeping for a task placement."""

    def __init__(
        self,
        tasks: list[Task],
        limit: int | None = None,
        strict: bool = False,
    ) -> None:
        self.tasks = tasks
        self.gpus: list[tuple[int, int]] = sorted({t.gpu for t in tasks})
        self.weight: dict[tuple[int, int], float] = defaultdict(float)
        self.comp: dict[tuple[int, int], Counter] = {
            g: Counter() for g in self.gpus
        }
        self.by_gpu: dict[tuple[int, int], list[Task]] = defaultdict(list)
        for task in tasks:
            self.weight[task.gpu] += task.weight
            self.by_gpu[task.gpu].append(task)
            for c in task.comps:
                self.comp[task.gpu][c] += 1
        self.base_size = {g: len(self.comp[g]) for g in self.gpus}
        self.peak_components = max(self.base_size.values(), default=0)
        self.limit = self.peak_components if limit is None else limit
        self.strict = strict
        self.total = sum(self.weight.values())
        self.mean = self.total / len(self.gpus) if self.gpus else 0.0
        # improvements below this (squared-weight units) are float noise
        self.eps = max(1.0, 1e-12 * self.total ** 2)

    # -- component bookkeeping ------------------------------------------- #

    def size_after(self, gpu: tuple[int, int], comps: Iterable[tuple[str, str]]) -> int:
        counter = self.comp[gpu]
        size = len(counter)
        for c in comps:
            if counter[c] == 0:
                size += 1
        return size

    def can_place(self, gpu: tuple[int, int], comps: Iterable[tuple[str, str]]) -> bool:
        size = self.size_after(gpu, comps)
        if size > self.limit:
            return False
        if self.strict and size > self.base_size[gpu]:
            return False
        return True

    def relocate(self, task: Task, dst: tuple[int, int]) -> None:
        """Move a task to dst. Feasibility is the caller's responsibility."""
        src = task.gpu
        if src == dst:
            return
        src_counter = self.comp[src]
        for c in task.comps:
            src_counter[c] -= 1
            if src_counter[c] == 0:
                del src_counter[c]
        for c in task.comps:
            self.comp[dst][c] += 1
        self.weight[src] -= task.weight
        self.weight[dst] += task.weight
        self.by_gpu[src].remove(task)
        self.by_gpu[dst].append(task)
        task.gpu = dst

    # -- objective -------------------------------------------------------- #

    def objective(self) -> float:
        return sum((self.weight[g] - self.mean) ** 2 for g in self.gpus)

    def move_delta(self, task: Task, dst: tuple[int, int]) -> float:
        """Change of the objective if `task` moves to `dst`."""
        x = task.weight
        u = self.weight[task.gpu] - self.mean
        v = self.weight[dst] - self.mean
        return 2.0 * x * (v - u) + 2.0 * x * x

    def swap_delta(
        self,
        a: Task,
        b: Task,
        src: tuple[int, int],
        dst: tuple[int, int],
    ) -> float:
        u = self.weight[src] - self.mean
        v = self.weight[dst] - self.mean
        du = b.weight - a.weight   # change of src
        dv = a.weight - b.weight   # change of dst
        return (u + du) ** 2 - u * u + (v + dv) ** 2 - v * v

    def swap_feasible(
        self,
        a: Task,
        b: Task,
        src: tuple[int, int],
        dst: tuple[int, int],
    ) -> bool:
        """Check a simultaneous exchange: a src->dst, b dst->src."""
        cs = Counter(self.comp[src])
        cd = Counter(self.comp[dst])
        for c in a.comps:
            cs[c] -= 1
            cd[c] += 1
        for c in b.comps:
            cs[c] += 1
            cd[c] -= 1
        size_s = sum(1 for n in cs.values() if n > 0)
        size_d = sum(1 for n in cd.values() if n > 0)
        if size_s > self.limit or size_d > self.limit:
            return False
        if self.strict and (
            size_s > self.base_size[src] or size_d > self.base_size[dst]
        ):
            return False
        return True

    # -- greedy passes ---------------------------------------------------- #

    def improve_moves(self) -> bool:
        """One sweep of single-task moves; returns True if any was made."""
        found = False
        sources = sorted(self.gpus, key=lambda g: -self.weight[g])
        targets = sorted(self.gpus, key=lambda g: self.weight[g])
        for src in sources:
            for task in sorted(self.by_gpu[src], key=lambda t: -t.weight):
                for dst in targets:
                    if dst == src:
                        continue
                    if self.move_delta(task, dst) >= -self.eps:
                        continue
                    if not self.can_place(dst, task.comps):
                        continue
                    self.relocate(task, dst)
                    found = True
                    break
        return found

    def improve_swaps(self, candidates: int = 8) -> bool:
        """Exchange two tasks between a heavy and a light GPU."""
        order = sorted(self.gpus, key=lambda g: -self.weight[g])
        for src in order:
            light = sorted(
                (g for g in self.gpus if self.weight[g] < self.weight[src]),
                key=lambda g: self.weight[g],
            )
            for dst in light:
                a_cands = sorted(self.by_gpu[src], key=lambda t: -t.weight)
                a_cands = a_cands[:candidates]
                for a in a_cands:
                    for b in list(self.by_gpu[dst]):
                        if not self.swap_feasible(a, b, src, dst):
                            continue
                        if self.swap_delta(a, b, src, dst) >= -self.eps:
                            continue
                        self.relocate(a, dst)
                        self.relocate(b, src)
                        return True
        return False

    def rebalance(self, max_passes: int) -> tuple[int, int]:
        """Run greedy passes; returns (passes_run, swaps_used)."""
        passes = swaps = 0
        for _ in range(max_passes):
            passes += 1
            before = self.objective()
            if self.improve_moves():
                continue
            if self.improve_swaps():
                swaps += 1
                continue
            assert abs(self.objective() - before) < 1e-6
            break
        return passes, swaps

    # -- reporting -------------------------------------------------------- #

    def weight_stats(self) -> dict[str, float]:
        values = [self.weight[g] for g in self.gpus]
        return {
            "max": max(values),
            "min": min(values),
            "mean": statistics.fmean(values),
            "stdev": statistics.pstdev(values),
            "ratio": max(values) / min(values) if min(values) > 0 else float("inf"),
        }

    def component_stats(self) -> dict[str, float]:
        values = [len(self.comp[g]) for g in self.gpus]
        return {
            "max": max(values),
            "min": min(values),
            "mean": statistics.fmean(values),
        }


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

def rewrite_node_gpu(text: str, new_values: dict[str, str]) -> tuple[str, int, int]:
    """Replace node_gpu values inside the top-level `tasks:` block only.

    Returns (new_text, lines_handled, lines_changed).
    """
    out: list[str] = []
    in_tasks = False
    task_indent = 0
    current: str | None = None
    handled = 0
    changed = 0

    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        keep = line
        if stripped and not stripped.startswith("#"):
            indent = len(line) - len(line.lstrip())
            if indent == 0:
                in_tasks = stripped.startswith("tasks:")
                current = None
            elif in_tasks:
                if current is None or indent <= task_indent:
                    match = TASK_KEY_RE.match(line)
                    if match:
                        task_indent = len(match.group(1))
                        current = match.group(2)
                elif current in new_values:
                    body = line.rstrip("\r\n")
                    eol = line[len(body):]
                    match = NODE_GPU_RE.match(body)
                    if match:
                        prefix, value = match.group(1), match.group(2).strip()
                        if value[:1] in ("'", '"'):
                            quote = value[0]
                            end = value.find(quote, 1)
                            raw = value[1:end] if end != -1 else value[1:]
                            comment = value[end + 1:] if end != -1 else ""
                        else:
                            quote = ""
                            raw, _, tail = value.partition("#")
                            comment = ("# " + tail.strip()) if tail.strip() else ""
                            raw = raw.strip()
                        handled += 1
                        if raw != new_values[current]:
                            separator = " " + comment if comment else ""
                            keep = (
                                f"{prefix}node_gpu: {quote}"
                                f"{new_values[current]}{quote}{separator}{eol}"
                            )
                            changed += 1
        out.append(keep)
    return "".join(out), handled, changed


def verify(path: str, tasks: list[Task]) -> None:
    """Re-read the written file and check weights/components match."""
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    seen = 0
    for task in tasks:
        spec = data["tasks"].get(task.name)
        if spec is None:
            sys.exit(f"error: verification failed: task {task.name!r} missing in {path}")
        if parse_node_gpu(spec["node_gpu"]) != task.gpu:
            sys.exit(
                f"error: verification failed: {task.name} is "
                f"{spec['node_gpu']!r} in {path}, expected "
                f"{task.gpu[0]}:{task.gpu[1]}"
            )
        if float(spec["weight"]) != task.weight:
            sys.exit(f"error: verification failed: weight of {task.name} changed")
        if task_components(spec, task.name) != task.comps:
            sys.exit(f"error: verification failed: components of {task.name} changed")
        seen += 1
    if seen != len(data["tasks"]):
        print(
            f"warning: {path} contains {len(data['tasks'])} tasks, "
            f"{seen} tracked here",
            file=sys.stderr,
        )


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def snapshot(a: Assignment) -> dict:
    """Freeze the state of an assignment for before/after reporting."""
    return {
        "gpus": list(a.gpus),
        "n_tasks": len(a.tasks),
        "limit": a.limit,
        "strict": a.strict,
        "weights": {g: a.weight[g] for g in a.gpus},
        "comps": {g: len(a.comp[g]) for g in a.gpus},
        "wstats": a.weight_stats(),
        "cstats": a.component_stats(),
    }


def print_report(
    path: str,
    pre: dict,
    post: dict,
    moves: list[tuple[Task, tuple[int, int]]],
    precision: int,
    verbose: bool,
) -> None:
    bw, aw = pre["wstats"], post["wstats"]
    bc, ac = pre["cstats"], post["cstats"]
    n_gpus = len(pre["gpus"])

    print(f"{path}: {pre['n_tasks']} tasks on {n_gpus} GPUs")
    print(f"constraint: max components per GPU must stay <= {pre['limit']}"
          + (" (strict: no GPU may increase its own count)" if pre["strict"] else ""))
    print("objective:  minimize variance of the total weight per GPU\n")

    print(f"{'':>18} {'before':>16} {'after':>16} {'change':>12}")
    rows = [
        ("max GPU weight", bw["max"], aw["max"], True),
        ("min GPU weight", bw["min"], aw["min"], True),
        ("mean GPU weight", bw["mean"], aw["mean"], True),
        ("stdev GPU weight", bw["stdev"], aw["stdev"], True),
        ("max/min ratio", bw["ratio"], aw["ratio"], False),
        ("max components", bc["max"], ac["max"], False),
        ("min components", bc["min"], ac["min"], False),
    ]
    for label, old, new, is_weight in rows:
        if is_weight:
            change = f"{(new - old) / old * 100:+.2f}%" if old else "n/a"
            print(f"{label:>18} {fmt(old, precision):>16} {fmt(new, precision):>16} {change:>12}")
        else:
            change = f"{new - old:+.0f}"
            print(f"{label:>18} {old:>16.2f} {new:>16.2f} {change:>12}")

    ok = "OK" if ac["max"] <= pre["limit"] else "VIOLATED"
    print(f"\ncomponent limit: peak {bc['max']:.0f} -> {ac['max']:.0f} "
          f"(limit {pre['limit']}) {ok}")
    print(f"tasks moved: {len(moves)} / {pre['n_tasks']}\n")

    # per-GPU table
    width = max(len(fmt(bw["max"], precision)), len(fmt(aw["max"], precision)), 10)
    header = (
        f"{'gpu':>6} | {'weight before':>{width}} | {'weight after':>{width}} "
        f"| {'change':>9} | {'comps':>11}"
    )
    print(header)
    print("-" * len(header))
    for gpu in pre["gpus"]:
        old_w, new_w = pre["weights"][gpu], post["weights"][gpu]
        change = f"{(new_w - old_w) / old_w * 100:+.1f}%" if old_w else "n/a"
        old_c, new_c = pre["comps"][gpu], post["comps"][gpu]
        marker = "" if new_c <= pre["limit"] else " !"
        print(
            f"{gpu[0]}:{gpu[1]:>4} | {fmt(old_w, precision):>{width}} "
            f"| {fmt(new_w, precision):>{width}} | {change:>9} "
            f"| {old_c:>4} -> {new_c:<4}{marker}"
        )
    print("-" * len(header))
    print(
        f"{'all':>6} | {fmt(bw['mean'] * n_gpus, precision):>{width}} "
        f"| {fmt(aw['mean'] * n_gpus, precision):>{width}} |"
    )

    # moved tasks
    print(f"\nmoved tasks ({len(moves)}):")
    shown = moves if verbose else moves[:20]
    for task, old_gpu in shown:
        print(
            f"  {task.name:<28} {old_gpu[0]}:{old_gpu[1]} -> "
            f"{task.gpu[0]}:{task.gpu[1]}  ({fmt(task.weight, precision)})"
        )
    if len(moves) > len(shown):
        print(f"  ... and {len(moves) - len(shown)} more (use --verbose)")


# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rebalance task -> GPU assignments to equalize per-GPU weight "
            "without increasing the peak number of components per GPU."
        )
    )
    parser.add_argument("yaml_file", help="task YAML file (e.g. train-weights.yaml)")
    parser.add_argument(
        "-o", "--output",
        help="output YAML (default: <input>_rebalanced.yaml, same file if -o is the input)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="only report the new assignment, do not write a file",
    )
    parser.add_argument(
        "--limit", type=int, metavar="N",
        help="max components allowed on any GPU (default: peak of the input)",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="additionally forbid any single GPU from increasing its own component count",
    )
    parser.add_argument(
        "--precision", type=int, default=2,
        help="decimal places for printed weights (default: 2)",
    )
    parser.add_argument(
        "--max-passes", type=int, default=500,
        help="safety cap on greedy passes (default: 500)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="list every moved task",
    )
    args = parser.parse_args()

    tasks = load_tasks(args.yaml_file)
    assignment = Assignment(tasks, limit=args.limit, strict=args.strict)
    pre = snapshot(assignment)

    # remember original placements for the report
    original = {t.name: t.gpu for t in tasks}

    _, swaps_used = assignment.rebalance(args.max_passes)
    post = snapshot(assignment)

    moves: list[tuple[Task, tuple[int, int]]] = [
        (t, original[t.name]) for t in tasks if t.gpu != original[t.name]
    ]
    moves.sort(key=lambda m: -m[0].weight)

    print_report(args.yaml_file, pre, post, moves, args.precision, args.verbose)
    if swaps_used:
        print(f"\n({swaps_used} pairwise swap pass(es) were needed to unblock moves)")

    if post["cstats"]["max"] > pre["limit"]:
        sys.exit(
            f"\nerror: result violates the component limit "
            f"({post['cstats']['max']:.0f} > {pre['limit']})"
        )

    if args.dry_run:
        print("\ndry run: no file written")
        return

    output = args.output
    if not output:
        stem = args.yaml_file
        output = (
            stem[: -len(".yaml")] + "_rebalanced.yaml"
            if stem.endswith(".yaml")
            else stem + "_rebalanced.yaml"
        )

    with open(args.yaml_file, encoding="utf-8") as handle:
        text = handle.read()
    new_values = {t.name: f"{t.gpu[0]}:{t.gpu[1]}" for t in tasks}
    new_text, handled, changed = rewrite_node_gpu(text, new_values)
    if handled != len(tasks):
        print(
            f"warning: found {handled} node_gpu line(s) for {len(tasks)} tasks",
            file=sys.stderr,
        )
    with open(output, "w", encoding="utf-8") as handle:
        handle.write(new_text)

    verify(output, tasks)
    print(f"\nwrote {output} ({changed} node_gpu value(s) changed); verified OK")


if __name__ == "__main__":
    main()
