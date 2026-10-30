#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DATASETS = ("flo", "bqt", "bqtpar", "wmt")
DATASET_ORDER = {name: i for i, name in enumerate(DATASETS)}

METRIC_ALIASES = {
    "bleu": "BLEU",
    "BLEU": "BLEU",
    "chrf": "chrF2",
    "chrF": "chrF2",
    "chrf2": "chrF2",
    "chrF2": "chrF2",
}

DEBUG = False

def debug(msg):
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)
        
# ----------------------------------------------------------------------
# Experimental layouts
#
# Each table has:
#   - columns = main controlled contrast
#   - rows    = secondary distinction
#   - cells   = exact model names
# ----------------------------------------------------------------------

LAYOUTS = [
    {
        "title": "A. English-centric 1p+d — encoder sharing",
        "columns": [
            "Lenc-Ldec",
            "Aenc-Ldec",
            "Genc-Ldec",
            "LAenc-Ldec",
            "GAenc-Ldec",
            "LGAenc-Ldec",
        ],
        "rows": [
            (
                "small / 320k",
                {
                    "Lenc-Ldec": "small-1p+d-Lenc-Ldec-320k",
                    "LAenc-Ldec": "small-1p+d-LAenc-Ldec-320k",
                },
            ),
            (
                "base / 320k",
                {
                    "Lenc-Ldec": "base-1p+d-Lenc-Ldec-320k",
                    "Aenc-Ldec": "base-1p+d-Aenc-Ldec-320k",
                    "Genc-Ldec": "base-1p+d-Genc-Ldec-320k",
                    "LAenc-Ldec": "base-1p+d-LAenc-Ldec-320k",
                    "GAenc-Ldec": "base-1p+d-GAenc-Ldec-320k",
                    "LGAenc-Ldec": "base-1p+d-LGAenc-Ldec-320k",
                },
            ),
            (
                "base / 640k",
                {
                    "Lenc-Ldec": "base-1p+d-Lenc-Ldec-640k",
                    "Aenc-Ldec": "base-1p+d-Aenc-Ldec-640k",
                },
            ),
            (
                "big / 100k",
                {
                    "Lenc-Ldec": "big-1p+d-Lenc-Ldec-100k",
                },
            ),
            (
                "big / 320k",
                {
                    "Lenc-Ldec": "big-1p+d-Lenc-Ldec-320k",
                },
            ),
            (
                "xl / 100k",
                {
                    "Aenc-Ldec": "xl-1p+d-Aenc-Ldec-100k",
                },
            ),
        ],
    },

    {
        "title": "B. Four-pivot 4p+d — size × encoder sharing",
        "columns": [
            "Lenc-Ldec",
            "Aenc-Ldec",
            "Genc-Ldec",
            "LAenc-Ldec",
            "GAenc-Ldec",
        ],
        "rows": [
            (
                "small / 20k",
                {
                    "Aenc-Ldec": "small-4p+d-Aenc-Ldec-20k",
                },
            ),
            (
                "small / 960k",
                {
                    "Lenc-Ldec": "small-4p+d-Lenc-Ldec-960k",
                    "Aenc-Ldec": "small-4p+d-Aenc-Ldec-960k",
                    "Genc-Ldec": "small-4p+d-Genc-Ldec-960k",
                },
            ),
            (
                "base / 640k",
                {
                    "Lenc-Ldec": "base-4p+d-Lenc-Ldec-640k",
                    "Aenc-Ldec": "base-4p+d-Aenc-Ldec-640k",
                    "Genc-Ldec": "base-4p+d-Genc-Ldec-640k",
                    "LAenc-Ldec": "base-4p+d-LAenc-Ldec-640k",
                    "GAenc-Ldec": "base-4p+d-GAenc-Ldec-640k",
                },
            ),
            (
                "big / 160k",
                {
                    "Lenc-Ldec": "big-4p+d-Lenc-Ldec-160k",
                    "Aenc-Ldec": "big-4p+d-Aenc-Ldec-160k",
                    "Genc-Ldec": "big-4p+d-Genc-Ldec-160k",
                },
            ),
            (
                "xl / 20k",
                {
                    "Lenc-Ldec": "xl-4p+d-Lenc-Ldec-20k",
                    "Genc-Ldec": "xl-4p+d-Genc-Ldec-20k",
                },
            ),
        ],
    },

    {
        "title": "C. Two-/three-pivot models",
        "columns": [
            "Lenc-Ldec",
            "Aenc-Ldec",
            "GAenc-Ldec",
            "GAenc-LALdec",
        ],
        "rows": [
            (
                "2p Eng/Fra base / 320k",
                {
                    "Lenc-Ldec": "base-2p+d-Lenc-Ldec-320k",
                },
            ),
            (
                "2p Eng/Fra base / 640k",
                {
                    "Lenc-Ldec": "base-2p+d-Lenc-Ldec-640k",
                    "Aenc-Ldec": "base-2p+d-Aenc-Ldec-640k",
                },
            ),
            (
                "2p Eng/Spa base / 320k",
                {
                    "GAenc-Ldec": "base-2p-GAenc-Ldec-320k",
                    "GAenc-LALdec": "base-2p-GAenc-LALdec-320k",
                },
            ),
            (
                "2p Eng/Spa big / 320k +d",
                {
                    "GAenc-Ldec": "big-2p+d-GAenc-Ldec-320k",
                },
            ),
            (
                "2p Eng/Spa big / 320k",
                {
                    "GAenc-Ldec": "big-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "3p Eng/Fra/Spa base / 640k",
                {
                    "Lenc-Ldec": "base-3p+d-Lenc-Ldec-640k",
                },
            ),
            (
                "3p Eng/Fra/Spa base / 320k",
                {
                    "GAenc-LALdec": "base-3p-GAenc-LALdec-320k",
                },
            ),
        ],
    },

    {
        "title": "D. H / D architecture ablations",
        "columns": [
            "base",
            "H1",
            "H4",
            "H16",
            "D1K",
            "XT+D1K",
        ],
        "rows": [
            (
                "2p GAenc-Ldec / 320k",
                {
                    "base": "base-2p-GAenc-Ldec-320k",
                    "H1": "baseH1-2p-GAenc-Ldec-320k",
                    "H4": "baseH4-2p-GAenc-Ldec-320k",
                    "H16": "baseH16-2p-GAenc-Ldec-320k",
                    "D1K": "baseD1K-2p-GAenc-Ldec-320k",
                    "XT+D1K": "XTbaseD1K-2p-GAenc-Ldec-320k",
                },
            ),
        ],
    },

    {
        "title": "E. Explicit encoder / decoder depth",
        "columns": [
            "H4/D768",
            "H4/D1K",
            "H8/D512",
        ],
        "rows": [
            (
                "Enc3 / Dec2",
                {
                    "H4/D768": "Enc3Dec2H4D768-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc6 / Dec3",
                {
                    "H4/D768": "Enc6Dec3H4D768-2p-GAenc-Ldec-320k",
                    "H4/D1K": "Enc6Dec3H4D1K-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc6 / Dec3 +d",
                {
                    "H4/D768": "Enc6Dec3H4D768-2p+d-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc12 / Dec3",
                {
                    "H4/D768": "Enc12Dec3H4D768-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc12 / Dec6",
                {
                    "H8/D512": "Enc12Dec6H8D512-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc6 / Dec12",
                {
                    "H8/D512": "Enc6Dec12H8D512-2p-GAenc-Ldec-320k",
                },
            ),
            (
                "Enc12 / Dec12",
                {
                    "H8/D512": "Enc12Dec12H8D512-2p-GAenc-Ldec-320k",
                },
            ),
        ],
    },
]


# ----------------------------------------------------------------------
# Data representation
# ----------------------------------------------------------------------

@dataclass(frozen=True)
class ScoreRecord:
    score: float
    zeroshot: bool
    path: Path


# ----------------------------------------------------------------------
# Score file handling
# ----------------------------------------------------------------------

SCORE_RE = re.compile(
    r"^(?P<task>.+)\."
    r"(?P<dataset>wmt|flo|bqt|bqtpar)\."
    r"(?P<suffix>sacre)$"
)


def score_directory(model_dir: Path) -> Path:
    new = model_dir / "evaluation" / "scores"
    legacy = model_dir / "inf_scores"

    debug(f"checking score directory for {model_dir}")
    debug(f"  new:    {new} exists={new.is_dir()}")
    debug(f"  legacy: {legacy} exists={legacy.is_dir()}")

    if new.is_dir():
        return new

    return legacy


def parse_sacre_file(path: Path, metric: str) -> float:
    """
    Files may contain a textual preamble before the JSON array.
    """
    text = path.read_text(encoding="utf-8", errors="replace")

    start = text.find("[")
    end = text.rfind("]")

    if start < 0 or end < start:
        raise ValueError("no JSON array found")

    payload = json.loads(text[start:end + 1])

    for item in payload:
        if item.get("name") == metric:
            score = item.get("score")

            if isinstance(score, (int, float)):
                return float(score)

    raise ValueError(f"metric {metric!r} not found")


def remove_xcode(side: str) -> str:
    """
    Legacy:
        XX.eng    -> eng
        FR.fra    -> fra
        XX.srp_Cyrl -> srp_Cyrl

    New task syntax already has plain language codes.
    """
    if "." in side:
        return side.split(".", 1)[1]

    return side


def coarse_task(task: str) -> str:
    """
    Normalize score-file task identity to the TASKS= spelling.

    Legacy:
        mt_XX.eng-XX.fin -> mt_eng-fin

    Proposed/new:
        mt_eng-fin -> mt_eng-fin
        mt_swe-fra__swe-FR.fra -> mt_swe-fra
    """
    base = task.split("__", 1)[0]

    m = re.match(
        r"^(?P<kind>[^_]+)_(?P<src>[^-]+)-(?P<tgt>.+)$",
        base,
    )

    if not m:
        return base

    kind = m.group("kind")
    src = remove_xcode(m.group("src"))
    tgt = remove_xcode(m.group("tgt"))

    return f"{kind}_{src}-{tgt}"


def load_model_scores(
    model_dir: Path,
    tasks: set[str],
    metric: str,
    dataset_filter: Optional[str],
) -> Dict[Tuple[str, str, str], List[ScoreRecord]]:

    result: Dict[Tuple[str, str, str], List[ScoreRecord]] = {}

    score_dir = score_directory(model_dir)

    debug("")
    debug(f"MODEL DIR: {model_dir}")
    debug(f"SCORE DIR: {score_dir}")
    debug(f"requested tasks: {sorted(tasks)}")
    debug(f"requested metric: {metric}")
    debug(f"dataset filter: {dataset_filter}")

    if not score_dir.is_dir():
        debug("  -> score directory DOES NOT EXIST")
        return result

    paths = sorted(score_dir.iterdir())

    debug(f"  -> {len(paths)} directory entries")

    for path in paths:
        if not path.is_file():
            continue

        # Print interesting por-eng files even before regex matching.
        if "por" in path.name and "eng" in path.name:
            debug(f"candidate por-eng file: {path.name}")

        m = SCORE_RE.match(path.name)

        if not m:
            if "por" in path.name and "eng" in path.name:
                debug(f"  REJECTED BY SCORE_RE: {path.name}")
            continue

        exact_task = m.group("task")
        dataset = m.group("dataset")
        suffix = m.group("suffix")
        requested_task = coarse_task(exact_task)

        if "por" in path.name and "eng" in path.name:
            debug(
                f"  parsed: exact_task={exact_task!r} "
                f"coarse={requested_task!r} "
                f"dataset={dataset!r} suffix={suffix!r}"
            )

        if requested_task not in tasks:
            if "por" in path.name and "eng" in path.name:
                debug(
                    f"  REJECT task: {requested_task!r} "
                    f"not in {sorted(tasks)!r}"
                )
            continue

        if dataset_filter and dataset != dataset_filter:
            debug(
                f"  REJECT dataset: {dataset!r} != "
                f"{dataset_filter!r}"
            )
            continue

        debug(f"  MATCHED FILE: {path}")

        try:
            score = parse_sacre_file(path, metric)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(
                f"hpo_score_tables.py: WARNING: {path}: {exc}",
                file=sys.stderr,
            )
            debug(f"  SCORE PARSE FAILED: {exc}")
            continue

        debug(f"  SCORE = {score}")

        key = (requested_task, dataset, exact_task)

        result.setdefault(key, []).append(
            ScoreRecord(
                score=score,
                zeroshot=(suffix == "0ssacre"),
                path=path,
            )
        )

        debug(f"  STORED AS KEY: {key!r}")

    debug(f"  result contains {len(result)} score key(s)")
    return result


# ----------------------------------------------------------------------
# Table rendering
# ----------------------------------------------------------------------

def cell_value(
    model_name,
    models,
    scores_by_path,
    key,
):
    if not model_name:
        return ""

    model_dir = models.get(model_name)

    if model_dir is None:
        debug(f"CELL {model_name}: model not found in model mapping")
        return "?"

    records = scores_by_path.get(model_dir, {}).get(key, [])

    if DEBUG and model_name == "Enc12Dec3H4D768-2p-GAenc-Ldec-320k":
        debug(
            f"TARGET CELL lookup:"
            f"\n  model={model_name}"
            f"\n  dir={model_dir}"
            f"\n  key={key!r}"
            f"\n  records={records!r}"
        )

    if not records:
        return "-"

    if len(records) > 1:
        return "AMB"

    record = records[0]
    value = f"{record.score:.1f}"

    if record.zeroshot:
        value += "*"

    return value


def layout_model_names():
    names = set()

    for layout in LAYOUTS:
        for _, cells in layout["rows"]:
            for model_name in cells.values():
                if model_name:
                    names.add(model_name)

    return sorted(names)


def make_hpo_models(root: Path) -> Dict[str, Path]:
    models = {}

    for name in layout_model_names():
        model_dir = root / name / "mammoth"
        models[name] = model_dir

        debug(
            f"HPO model: {name} -> {model_dir} "
            f"exists={model_dir.is_dir()}"
        )

    return models

def layout_has_data(
    layout,
    models,
    scores_by_path,
    key,
) -> bool:
    for _, cells in layout["rows"]:
        for model_name in cells.values():
            value = cell_value(
                model_name,
                models,
                scores_by_path,
                key,
            )

            if value not in ("", "-", "?"):
                return True

    return False


def print_table(
    layout,
    models,
    scores_by_path,
    key,
) -> None:
    columns = layout["columns"]

    rendered_rows = []

    for row_name, model_cells in layout["rows"]:
        cells = []

        for column in columns:
            model_name = model_cells.get(column)

            cells.append(
                cell_value(
                    model_name,
                    models,
                    scores_by_path,
                    key,
                )
            )

        rendered_rows.append((row_name, cells))

    row_width = max(
        len("setting"),
        *(len(row_name) for row_name, _ in rendered_rows),
    )

    col_widths = []

    for i, column in enumerate(columns):
        width = len(column)

        for _, cells in rendered_rows:
            width = max(width, len(cells[i]))

        col_widths.append(width)

    print(layout["title"])

    header = (
        "setting".ljust(row_width)
        + " | "
        + " | ".join(
            column.ljust(col_widths[i])
            for i, column in enumerate(columns)
        )
    )

    separator = (
        "-" * row_width
        + "-+-"
        + "-+-".join("-" * width for width in col_widths)
    )

    print(header)
    print(separator)

    for row_name, cells in rendered_rows:
        print(
            row_name.ljust(row_width)
            + " | "
            + " | ".join(
                cells[i].ljust(col_widths[i])
                for i in range(len(columns))
            )
        )

    print()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Show HPO model score tables for selected evaluation tasks."
        )
    )

    parser.add_argument(
        "--hpo-root",
        required=True,
        type=Path,
        help="Root containing HPO model directories",
    )

    parser.add_argument(
        "--task",
        action="append",
        required=True,
        help="Task such as mt_eng-fin; may be repeated",
    )

    parser.add_argument(
      "--debug",
        action="store_true",
        help="Print detailed model/file matching diagnostics",
    )
    
    parser.add_argument(
        "--metric",
        required=True,
        help="BLEU or chrF2",
    )

    parser.add_argument(
        "--dataset",
        choices=DATASETS,
        help="Restrict output to one dataset",
    )

    args = parser.parse_args()

    global DEBUG
    DEBUG = args.debug
    debug(f"arguments: {args}")
    
    metric = METRIC_ALIASES.get(args.metric)

    if metric is None:
        parser.error(
            f"unknown metric {args.metric!r}; "
            "expected BLEU or chrF2"
        )

    requested_tasks = set(args.task)
    models = make_hpo_models(args.hpo_root)

    # Only read each physical model directory once.
    model_dirs = sorted(set(models.values()), key=str)

    scores_by_path = {
        model_dir: load_model_scores(
            model_dir=model_dir,
            tasks=requested_tasks,
            metric=metric,
            dataset_filter=args.dataset,
        )
        for model_dir in model_dirs
    }

    keys = set()

    for model_scores in scores_by_path.values():
        keys.update(model_scores.keys())

    matched_tasks = {task for task, _, _ in keys}

    for task in args.task:
        if task not in matched_tasks:
            print(
                f"hpo_score_tables.py: WARNING: "
                f"no {metric} scores found for {task}",
                file=sys.stderr,
            )

    def key_sort(key):
        task, dataset, exact_task = key

        try:
            task_index = args.task.index(task)
        except ValueError:
            task_index = len(args.task)

        return (
            task_index,
            DATASET_ORDER.get(dataset, 999),
            exact_task,
        )

    if not keys:
        print(
            "hpo_score_tables.py: ERROR: "
            "no matching score files were found",
            file=sys.stderr,
        )
        return 1

    for key in sorted(keys, key=key_sort):
        task, dataset, exact_task = key

        print("=" * 78)
        print(
            f"{task}  dataset={dataset}  metric={metric}"
        )

        if exact_task != task:
            print(f"evaluation task: {exact_task}")

        print("=" * 78)
        print()

        any_layout = False

        for layout in LAYOUTS:
            if not layout_has_data(
                layout,
                models,
                scores_by_path,
                key,
            ):
                continue

            print_table(
                layout,
                models,
                scores_by_path,
                key,
            )
            any_layout = True

        if not any_layout:
            print("(no scores among the HPO table models)")
            print()

    print("* = legacy .0ssacre score (zero-shot marker)")
    print("- = model exists, score missing")
    print("? = model not defined in mk-model.mk")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

