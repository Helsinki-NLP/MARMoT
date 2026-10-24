#!/usr/bin/env python3
# summarize_sacre.py
#
# Summarize eval3 SacreBLEU result files.
#
# Eval3 score filename convention:
#
#   <taskname>.<testset>.<testset_src>.<testset_tgt>.sacre
#
# Example:
#
#   mt_por-eng.wmt24pp.por_BR.eng.sacre
#
# TSV output:
#
#   modelname  taskname  testset  testset_src  testset_tgt  metric  score
#
# The model name is supplied with --model.  The remaining identity fields
# come directly from the filename.  Metric names and scores come from the
# JSON array embedded in each .sacre file.
#
# The script intentionally does not interpret language identifiers such as
# por_BR or srp_Cyrl.  They are test-set identifiers and are preserved exactly.
# Likewise, taskname is kept intact rather than being reconstructed from its
# source and target languages.
#
# Task families
# -------------
# Task names currently use prefixes such as:
#
#   mt_...       mt2_...
#   zero_...     zero2_...
#   sentmt_...   sentmt2_...
#   docmt_...    docmt2_...
#
# --kind mt preserves the old reporting semantics: it includes both ordinary
# mt tasks and zero-shot tasks.  --kind zero selects only zero-shot tasks.
# --kind sentmt and --kind docmt select their respective families.
# --kind all includes every recognized task family.
#
# Typical use
# -----------
#
#   python3 summarize_sacre.py SCORES --kind mt
#   python3 summarize_sacre.py SCORES --kind mt --metric BLEU
#   python3 summarize_sacre.py SCORES --kind mt --wide
#   python3 summarize_sacre.py SCORES --kind mt --tsv --model MODEL_ALIAS
#
# The script writes summaries to stdout and diagnostics to stderr.  It does
# not create files itself; callers can redirect stdout to a temporary file and
# atomically rename that file after validating it.

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple


METRICS = ["BLEU", "chrF2"]

# A task family is the alphabetic family name immediately before an optional
# one-digit variant number and the first underscore.
TASK_FAMILY_RE = re.compile(r"^(mt|zero|sentmt|docmt)[0-9]?_")


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------


def parse_filename(filename: str) -> Optional[dict]:
    """Parse one eval3 score filename.

    Expected form:

        <taskname>.<testset>.<testset_src>.<testset_tgt>.sacre

    Example:

        mt_por-eng.wmt24pp.por_BR.eng.sacre

    The split is deliberately performed from the right.  This keeps taskname
    opaque and avoids encoding assumptions about the internal syntax of task
    names or language identifiers.
    """
    base = os.path.basename(filename)

    if not base.endswith(".sacre"):
        return None

    stem = base[: -len(".sacre")]

    try:
        taskname, testset, testset_src, testset_tgt = stem.rsplit(".", 3)
    except ValueError:
        return None

    if not all((taskname, testset, testset_src, testset_tgt)):
        return None

    return {
        "taskname": taskname,
        "testset": testset,
        "testset_src": testset_src,
        "testset_tgt": testset_tgt,
    }



def task_family(taskname: str) -> Optional[str]:
    """Return the recognized family of taskname, or None."""
    m = TASK_FAMILY_RE.match(taskname)
    return m.group(1) if m else None



def task_matches_kind(taskname: str, kind: str) -> bool:
    """Return whether taskname belongs in the requested report kind.

    Historically zero-shot MT scores were part of the MT report and were
    distinguished by the old .0ssacre naming convention.  In eval3 zero-shot
    status is represented by the task name itself.  Therefore --kind mt
    includes both the mt and zero families.
    """
    family = task_family(taskname)

    if kind == "all":
        return family is not None
    if kind == "mt":
        return family in {"mt", "zero"}
    return family == kind


# ---------------------------------------------------------------------------
# SacreBLEU payload parsing
# ---------------------------------------------------------------------------


def parse_sacre_file(path: str) -> Dict[str, float]:
    """Read recognized metric scores from one .sacre file.

    The existing MARMoT score files contain some text followed by a JSON array.
    We locate the outermost array exactly as the previous summarizer did and
    extract numeric values for metrics listed in METRICS.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    start = text.find("[")
    end = text.rfind("]")

    if start < 0 or end < 0 or end < start:
        raise ValueError("No JSON array found")

    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON array: {e}") from e

    if not isinstance(payload, list):
        raise ValueError("JSON payload is not an array")

    scores: Dict[str, float] = {}

    for item in payload:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        score = item.get("score")

        if name in METRICS and isinstance(score, (int, float)) and not isinstance(score, bool):
            scores[name] = float(score)

    return scores


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


def collect_scores(
    indir: str,
    kind: str,
    verbose: bool = True,
) -> List[dict]:
    """Collect score records from indir.

    Each returned record contains filename identity plus a dictionary of
    recognized metric scores.
    """
    rows: List[dict] = []
    skipped_bad_name: List[str] = []
    skipped_unknown_task: List[str] = []
    skipped_bad_content: List[Tuple[str, str]] = []

    try:
        filenames = sorted(os.listdir(indir))
    except OSError as e:
        raise RuntimeError(f"Cannot read score directory {indir}: {e}") from e

    for fn in filenames:
        if not fn.endswith(".sacre"):
            continue

        meta = parse_filename(fn)
        if meta is None:
            skipped_bad_name.append(fn)
            continue

        family = task_family(meta["taskname"])
        if family is None:
            skipped_unknown_task.append(fn)
            continue

        if not task_matches_kind(meta["taskname"], kind):
            continue

        fullpath = os.path.join(indir, fn)

        try:
            scores = parse_sacre_file(fullpath)
        except Exception as e:
            skipped_bad_content.append((fn, str(e)))
            continue

        if not scores:
            skipped_bad_content.append((fn, "No recognized metrics"))
            continue

        rows.append(
            {
                **meta,
                "family": family,
                "scores": scores,
                "filename": fn,
            }
        )

    rows.sort(
        key=lambda item: (
            item["testset"],
            item["taskname"],
            item["testset_src"],
            item["testset_tgt"],
            item["filename"],
        )
    )

    if verbose:
        if skipped_bad_name:
            print(
                f"Skipped {len(skipped_bad_name)} .sacre files with "
                "unrecognized eval3 filenames:",
                file=sys.stderr,
            )
            for fn in skipped_bad_name:
                print(f"  {fn}", file=sys.stderr)

        if skipped_unknown_task:
            print(
                f"Skipped {len(skipped_unknown_task)} .sacre files with "
                "unrecognized task families:",
                file=sys.stderr,
            )
            for fn in skipped_unknown_task:
                print(f"  {fn}", file=sys.stderr)

        if skipped_bad_content:
            print(
                f"Skipped {len(skipped_bad_content)} malformed or incomplete "
                "score files:",
                file=sys.stderr,
            )
            for fn, err in skipped_bad_content:
                print(f"  {fn}: {err}", file=sys.stderr)

    return rows


# ---------------------------------------------------------------------------
# TSV output
# ---------------------------------------------------------------------------


def print_tsv(
    rows: Iterable[dict],
    modelname: str = "",
    only_metric: Optional[str] = None,
) -> None:
    """Print the eval3 long-form TSV."""
    headers = [
        "modelname",
        "taskname",
        "testset",
        "testset_src",
        "testset_tgt",
        "metric",
        "score",
    ]
    print("\t".join(headers))

    metrics = [only_metric] if only_metric else METRICS

    for item in rows:
        for metric in metrics:
            score = item["scores"].get(metric)
            if score is None:
                continue

            print(
                "\t".join(
                    [
                        modelname,
                        item["taskname"],
                        item["testset"],
                        item["testset_src"],
                        item["testset_tgt"],
                        metric,
                        f"{score:.6f}",
                    ]
                )
            )


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------


def format_score(value: Optional[float]) -> str:
    return "" if value is None else f"{value:.1f}"



def ascii_table(headers: List[str], rows: List[List[str]], title: Optional[str] = None) -> str:
    """Render a simple ASCII table."""
    widths = [len(str(h)) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_row(row: List[str]) -> str:
        return (
            "| "
            + " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
            + " |"
        )

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"

    lines: List[str] = []
    if title:
        lines.append(title)

    lines.append(sep)
    lines.append(fmt_row(headers))
    lines.append(sep)
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)

    return "\n".join(lines)



def grouped_by_testset(rows: Iterable[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for item in rows:
        grouped[item["testset"]].append(item)
    return grouped



def print_metric_tables(rows: List[dict], only_metric: Optional[str] = None) -> None:
    """Print one long table per test set and metric.

    Task name is included explicitly, so different tasks evaluated on the same
    test-set language pair cannot silently overwrite each other.
    """
    metrics = [only_metric] if only_metric else METRICS
    grouped = grouped_by_testset(rows)

    for testset in sorted(grouped):
        test_rows = grouped[testset]

        for metric in metrics:
            table_rows: List[List[str]] = []

            for item in test_rows:
                score = item["scores"].get(metric)
                if score is None:
                    continue

                table_rows.append(
                    [
                        item["taskname"],
                        item["testset_src"],
                        item["testset_tgt"],
                        format_score(score),
                    ]
                )

            if not table_rows:
                continue

            print(
                ascii_table(
                    ["task", "src", "tgt", metric],
                    table_rows,
                    title=f"{testset} -- {metric}",
                )
            )
            print()



def print_wide_tables(rows: List[dict]) -> None:
    """Print one table per test set with all enabled metrics side by side."""
    grouped = grouped_by_testset(rows)

    for testset in sorted(grouped):
        table_rows: List[List[str]] = []

        for item in grouped[testset]:
            table_rows.append(
                [
                    item["taskname"],
                    item["testset_src"],
                    item["testset_tgt"],
                ]
                + [format_score(item["scores"].get(metric)) for metric in METRICS]
            )

        if not table_rows:
            continue

        print(
            ascii_table(
                ["task", "src", "tgt"] + METRICS,
                table_rows,
                title=f"{testset} -- all metrics",
            )
        )
        print()


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Summarize eval3 SacreBLEU score files into human-readable tables "
            "or machine-readable TSV."
        )
    )

    ap.add_argument(
        "indir",
        help="Directory containing eval3 *.sacre files",
    )

    ap.add_argument(
        "--metric",
        choices=METRICS,
        help="Only print one metric",
    )

    ap.add_argument(
        "--kind",
        default="all",
        choices=["all", "mt", "zero", "sentmt", "docmt"],
        help=(
            "Task family to include. 'mt' includes both mt and zero tasks "
            "to preserve the historical MT-report semantics. Default: all."
        ),
    )

    ap.add_argument(
        "--wide",
        action="store_true",
        help="Print one wide human-readable table per test set",
    )

    ap.add_argument(
        "--tsv",
        action="store_true",
        help="Print machine-readable TSV instead of human-readable tables",
    )

    ap.add_argument(
        "--model",
        default="",
        help="Model alias written to the modelname column in TSV output",
    )

    # Kept as an accepted compatibility option because older commands may still
    # contain it.  Eval3 preserves test-set language identifiers exactly, so
    # there is no longer a separate language-name rendering mode.
    ap.add_argument(
        "--codes",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    args = ap.parse_args()

    if not os.path.isdir(args.indir):
        print(f"ERROR: not a directory: {args.indir}", file=sys.stderr)
        return 2

    try:
        rows = collect_scores(
            args.indir,
            kind=args.kind,
            verbose=True,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    # TSV mode must write only TSV to stdout.  All diagnostics are on stderr.
    if args.tsv:
        print_tsv(
            rows,
            modelname=args.model,
            only_metric=args.metric,
        )
        return 0

    if args.wide:
        print_wide_tables(rows)
    else:
        print_metric_tables(
            rows,
            only_metric=args.metric,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

