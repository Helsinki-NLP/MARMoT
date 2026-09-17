#!/usr/bin/env python3
# summarize_sacre.py
#
# Purpose
# -------
# Read SacreBLEU result files and summarize them as human-readable ASCII tables
# or machine-readable TSV.
#
# This script scans a directory of *.sacre files, parses the embedded JSON score
# payloads, groups the files by dataset and language pair, and prints summary
# matrices or tables to stdout.
#
# Supported datasets:
#   - WMT24++
#   - Flores+
#   - Bouquet
#   - Bouquet-par
#
# Supported metrics:
#   - BLEU
#   - chrF2
#
# The script currently expects score files whose names encode:
#   - task kind: mt / sentmt / docmt
#   - source localized language code
#   - target localized language code
#   - dataset tag
#
# Typical use
# -----------
#   python summarize_sacre.py INF_SCORES --kind mt
#
# Example:
#   python summarize_sacre.py inf_scores --kind docmt
#
# Single metric only:
#   python summarize_sacre.py inf_scores --kind mt --metric BLEU
#
# Wide table output:
#   python summarize_sacre.py inf_scores --kind mt --wide
#
# Machine-readable TSV:
#   python summarize_sacre.py inf_scores --kind mt --tsv --model MODEL_ALIAS
#
# TSV task identity
# -----------------
# The TSV preserves both:
#
#   src_xcode / tgt_xcode
#       Exact localized task identifiers from the filename, e.g.
#           XX.fin
#           CA.fra
#           FR.fra
#           BR.por
#           PT.por
#
#   src / tgt
#       Coarser language-level display codes used by the existing tables.
#
# This distinction is important because several localized evaluation tasks can
# map to the same language pair.  Comparison and coverage tools should therefore
# use src_xcode/tgt_xcode as task identity and use src/tgt only for summaries.
#
# Inputs
# ------
# Positional:
#   indir
#       Directory containing *.sacre files
#
# Required option:
#   --kind
#       One of: mt, sentmt, docmt
#
# Optional:
#   --metric
#       Restrict output to one metric
#   --codes
#       Use language codes instead of names in labels
#   --wide
#       Also print one wide table per dataset with all metrics
#   --tsv
#       Print machine-readable TSV instead of ASCII matrices
#   --model
#       Model alias to include in TSV output
#
# Reads
# -----
#   - *.sacre files in the input directory
#
# Writes
# ------
#   - no files directly
#
# Output
# ------
#   - ASCII matrices/tables or TSV printed to stdout
#   - warnings and diagnostics printed to stderr
#
# Notes
# -----
# The script expects each .sacre file to contain a JSON array with metric items.
# It extracts only recognized metrics and ignores unknown entries.

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from typing import Optional


DATASET_NAMES = {
    "wmt": "WMT24++",
    "flo": "Flores+",
    "bqt": "Bouquet",
    "bqtpar": "Bouquet-par",
}

# METRICS = ["BLEU", "chrF2", "TER"]
METRICS = ["BLEU", "chrF2"]


# Language-name map for the codes that appear in your files.
# Fallback is the code itself if something is missing.
LANG_NAMES = {
    "eng": "English",
    "por": "Portuguese",
    "fra": "French",
    "bos": "Bosnian",
    "bul": "Bulgarian",
    "cat": "Catalan",
    "ces": "Czech",
    "dan": "Danish",
    "deu": "German",
    "ell": "Greek",
    "est": "Estonian",
    "eus": "Basque",
    "fin": "Finnish",
    "gle": "Irish",
    "glg": "Galician",
    "hrv": "Croatian",
    "hun": "Hungarian",
    "isl": "Icelandic",
    "ita": "Italian",
    "kat": "Georgian",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "mkd": "Macedonian",
    "mlt": "Maltese",
    "nld": "Dutch",
    "nno": "Norwegian Nynorsk",
    "nob": "Norwegian Bokmal",
    "pol": "Polish",
    "ron": "Romanian",
    "slk": "Slovak",
    "slv": "Slovenian",
    "spa": "Spanish",
    "sqi": "Albanian",
    "srp": "Serbian",
    "swe": "Swedish",
    "tur": "Turkish",
    "ukr": "Ukrainian",
}


def parse_lang_token(token: str):
    """
    Parse one side of a pair like:
      XX.eng
      BR.por
      XX.srp_Cyrl

    Returns:
      (lang_code, country_code_or_None)

    Rules:
      - drop country XX
      - drop script suffixes like _Cyrl

    Note:
      The caller also preserves the original token separately as src_xcode /
      tgt_xcode, so this normalization does not destroy task identity.
    """
    m = re.fullmatch(r"([A-Z]{2})\.([A-Za-z_]+)", token)
    if not m:
        raise ValueError(f"Cannot parse language token: {token}")

    country, lang = m.groups()
    lang = lang.split("_", 1)[0]
    country = None if country == "XX" else country
    return lang, country


def lang_display(
    lang: str,
    country: Optional[str],
    use_names: bool = True,
):
    base = LANG_NAMES.get(lang, lang) if use_names else lang

    if country:
        return f"{base} ({country})"

    return base


def pair_display(
    src_lang,
    src_country,
    tgt_lang,
    tgt_country,
    use_names=True,
):
    src = lang_display(
        src_lang,
        src_country,
        use_names=use_names,
    )
    tgt = lang_display(
        tgt_lang,
        tgt_country,
        use_names=use_names,
    )

    return f"{src} -> {tgt}"


def sort_key_for_pair(
    src_lang,
    src_country,
    tgt_lang,
    tgt_country,
    use_names=True,
):
    src = lang_display(
        src_lang,
        src_country,
        use_names=use_names,
    )
    tgt = lang_display(
        tgt_lang,
        tgt_country,
        use_names=use_names,
    )

    return (src.lower(), tgt.lower())


def parse_filename(filename: str, kind: str):
    """
    Parse filenames such as:

        mt_XX.fin-XX.eng.flo.sacre
        mt_BR.por-XX.eng.wmt.sacre
        mt_CA.fra-XX.ron.bqtpar.0ssacre

    Keep the original source/target tokens because they identify the localized
    evaluation task exactly.
    """
    base = os.path.basename(filename)

    m = re.fullmatch(
        rf"{re.escape(kind)}_"
        rf"([A-Z]{{2}}\.[A-Za-z_]+)-"
        rf"([A-Z]{{2}}\.[A-Za-z_]+)"
        rf"\.(wmt|flo|bqt|bqtpar)"
        rf"\.(0s)?sacre",
        base,
    )

    if not m:
        return None

    src_tok, tgt_tok, dataset, zs = m.groups()

    src_lang, src_country = parse_lang_token(src_tok)
    tgt_lang, tgt_country = parse_lang_token(tgt_tok)

    return {
        "dataset": dataset,

        # Exact localized task identifiers.
        "src_xcode": src_tok,
        "tgt_xcode": tgt_tok,

        # Normalized language information for display and summaries.
        "src_lang": src_lang,
        "src_country": src_country,
        "tgt_lang": tgt_lang,
        "tgt_country": tgt_country,

        "zeroshot": zs is not None,
    }


def parse_sacre_file(path: str):
    """
    SacreBLEU file has a header, then a JSON array.

    Return a dict of scores, or raise ValueError if the file is malformed.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    start = text.find("[")
    end = text.rfind("]")

    if start < 0 or end < 0 or end < start:
        raise ValueError("No JSON array found")

    payload = json.loads(text[start:end + 1])

    scores = {}

    for item in payload:
        name = item.get("name")
        score = item.get("score")

        if name in METRICS and isinstance(score, (int, float)):
            scores[name] = float(score)

    return scores


def lang_code_display(
    lang: str,
    country: Optional[str],
    dataset: str,
):
    """
    Language-level display used by the original ASCII tables.

    Keep country variants only for WMT.

    This is deliberately NOT used as the identity of an evaluation task in the
    machine-readable TSV.
    """
    if dataset == "wmt" and country:
        return f"{lang}+{country}"

    return lang


def build_matrix(dataset_rows, metric, dataset):
    """
    Build a display matrix:

      rows    = source language labels
      columns = target language labels
      cells   = metric scores

    This intentionally remains language-level and may therefore collapse
    localized variants.  The TSV output preserves exact localized identities.
    """
    row_labels = set()
    col_labels = set()
    values = {}

    for item in dataset_rows:
        val = item["scores"].get(metric)

        if val is None:
            continue

        src = lang_code_display(
            item["src_lang"],
            item["src_country"],
            dataset,
        )
        tgt = lang_code_display(
            item["tgt_lang"],
            item["tgt_country"],
            dataset,
        )

        row_labels.add(src)
        col_labels.add(tgt)

        key = (src, tgt)

        # The human-readable matrix is intentionally coarse-grained.
        # Localized variants may map to the same cell.
        values[key] = (val, item["zeroshot"])

    row_labels = sorted(
        row_labels,
        key=str.lower,
    )
    col_labels = sorted(
        col_labels,
        key=str.lower,
    )

    return row_labels, col_labels, values


def ascii_matrix(
    row_labels,
    col_labels,
    values,
    title=None,
    cell_fmt="{:.1f}",
):
    headers = ["src \\ tgt"] + col_labels

    def cell_value(r, c):
        cell = values.get((r, c))

        if cell is None:
            return ("|", "")

        score, zeroshot = cell

        # Replace the ordinary column boundary:
        #   ? = zero-shot
        #   ! = supervised
        boundary = "?" if zeroshot else "!"

        return (
            boundary,
            cell_fmt.format(score),
        )

    rows = []

    for r in row_labels:
        row = [(None, r)]

        for c in col_labels:
            row.append(
                cell_value(r, c)
            )

        rows.append(row)

    widths = [
        len(str(h))
        for h in headers
    ]

    for row in rows:
        for i, (_boundary, cell) in enumerate(row):
            widths[i] = max(
                widths[i],
                len(str(cell)),
            )

    def fmt_header():
        return (
            "|"
            + "|".join(
                str(h).ljust(widths[i])
                for i, h in enumerate(headers)
            )
            + "|"
        )

    def fmt_row(row):
        out = "|"

        for i, (boundary, cell) in enumerate(row):
            if i == 0:
                out += str(cell).ljust(widths[i])
            else:
                out += (
                    (boundary or "|")
                    + str(cell).ljust(widths[i])
                )

        out += "|"

        return out

    sep = (
        "+"
        + "+".join(
            "-" * w
            for w in widths
        )
        + "+"
    )

    lines = []

    if title:
        lines.append(title)

    lines.append(sep)
    lines.append(fmt_header())
    lines.append(sep)

    for row in rows:
        lines.append(
            fmt_row(row)
        )

    lines.append(sep)

    return "\n".join(lines)


def old_ascii_matrix(
    row_labels,
    col_labels,
    values,
    title=None,
    cell_fmt="{:.1f}",
):
    """
    Older renderer where ?/! were inside the cells rather than replacing
    column boundaries.
    """
    headers = ["src \\ tgt"] + col_labels

    def cell_value(r, c):
        cell = values.get((r, c))

        if cell is None:
            return ""

        score, zeroshot = cell
        prefix = "?" if zeroshot else "!"

        return prefix + cell_fmt.format(score)

    rows = []

    for r in row_labels:
        rows.append(
            [r]
            + [
                cell_value(r, c)
                for c in col_labels
            ]
        )

    widths = [
        len(str(h))
        for h in headers
    ]

    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(
                widths[i],
                len(str(cell)),
            )

    def fmt_row(row):
        return (
            "|"
            + "|".join(
                str(cell).ljust(widths[i])
                for i, cell in enumerate(row)
            )
            + "|"
        )

    sep = (
        "+"
        + "+".join(
            "-" * w
            for w in widths
        )
        + "+"
    )

    lines = []

    if title:
        lines.append(title)

    lines.append(sep)
    lines.append(fmt_row(headers))
    lines.append(sep)

    for row in rows:
        lines.append(fmt_row(row))

    lines.append(sep)

    return "\n".join(lines)


def print_metric_matrices(
    dataset_to_rows,
    only_metric=None,
):
    metrics = (
        [only_metric]
        if only_metric
        else METRICS
    )

    for dataset in [
        "wmt",
        "flo",
        "bqt",
        "bqtpar",
    ]:
        dataset_name = DATASET_NAMES.get(
            dataset,
            dataset,
        )

        rows_for_dataset = dataset_to_rows.get(
            dataset,
            [],
        )

        for metric in metrics:
            (
                row_labels,
                col_labels,
                values,
            ) = build_matrix(
                rows_for_dataset,
                metric,
                dataset,
            )

            title = (
                f"{dataset_name} — {metric}"
            )

            print(
                ascii_matrix(
                    row_labels,
                    col_labels,
                    values,
                    title=title,
                )
            )
            print()


def print_tsv(
    dataset_to_rows,
    model=None,
    only_metric=None,
):
    """
    Print machine-readable long-form TSV.

    IMPORTANT:
      src_xcode and tgt_xcode identify the actual localized evaluation task.

      src and tgt are coarser language-level fields intended for aggregation
      and human-readable summaries.
    """
    metrics = (
        [only_metric]
        if only_metric
        else METRICS
    )

    headers = [
        "model",
        "dataset",
        "src_xcode",
        "tgt_xcode",
        "src",
        "tgt",
        "zeroshot",
        "metric",
        "score",
        "filename",
    ]

    print(
        "\t".join(headers)
    )

    for dataset in [
        "wmt",
        "flo",
        "bqt",
        "bqtpar",
    ]:
        for item in dataset_to_rows.get(
            dataset,
            [],
        ):
            src = lang_code_display(
                item["src_lang"],
                item["src_country"],
                dataset,
            )

            tgt = lang_code_display(
                item["tgt_lang"],
                item["tgt_country"],
                dataset,
            )

            for metric in metrics:
                score = item["scores"].get(metric)

                if score is None:
                    continue

                print(
                    "\t".join([
                        model or "",
                        dataset,
                        item["src_xcode"],
                        item["tgt_xcode"],
                        src,
                        tgt,
                        "1" if item["zeroshot"] else "0",
                        metric,
                        f"{score:.6f}",
                        item["filename"],
                    ])
                )


def ascii_table(
    headers,
    rows,
    title=None,
):
    widths = [
        len(h)
        for h in headers
    ]

    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(
                widths[i],
                len(str(cell)),
            )

    def fmt_row(row):
        return (
            "| "
            + " | ".join(
                str(cell).ljust(widths[i])
                for i, cell in enumerate(row)
            )
            + " |"
        )

    sep = (
        "+-"
        + "-+-".join(
            "-" * w
            for w in widths
        )
        + "-+"
    )

    lines = []

    if title:
        lines.append(title)

    lines.append(sep)
    lines.append(fmt_row(headers))
    lines.append(sep)

    for row in rows:
        lines.append(
            fmt_row(row)
        )

    lines.append(sep)

    return "\n".join(lines)


def collect_scores(
    indir: str,
    kind: str,
    use_names=True,
    verbose=True,
):
    dataset_to_rows = defaultdict(list)

    skipped_bad_name = []
    skipped_bad_content = []

    prefix = f"{kind}_"

    for fn in sorted(
        os.listdir(indir)
    ):
        if (
            not fn.endswith(".sacre")
            and not fn.endswith(".0ssacre")
        ):
            continue

        if not fn.startswith(prefix):
            print(
                f"file: found file {fn} "
                f"but it does not have prefix: {prefix}",
                file=sys.stderr,
            )
            continue

        print(
            f"file: found file {fn}",
            file=sys.stderr,
        )

        meta = parse_filename(
            fn,
            kind,
        )

        if meta is None:
            skipped_bad_name.append(fn)
            continue

        fullpath = os.path.join(
            indir,
            fn,
        )

        try:
            scores = parse_sacre_file(
                fullpath
            )
        except Exception as e:
            skipped_bad_content.append(
                (fn, str(e))
            )
            continue

        if not scores:
            skipped_bad_content.append(
                (
                    fn,
                    "No recognized metrics",
                )
            )
            continue

        pair_label = pair_display(
            meta["src_lang"],
            meta["src_country"],
            meta["tgt_lang"],
            meta["tgt_country"],
            use_names=use_names,
        )

        skey = sort_key_for_pair(
            meta["src_lang"],
            meta["src_country"],
            meta["tgt_lang"],
            meta["tgt_country"],
            use_names=use_names,
        )

        dataset_to_rows[
            meta["dataset"]
        ].append({
            "pair_label": pair_label,
            "sort_key": skey,
            "scores": scores,
            "filename": fn,

            # Exact localized evaluation task.
            "src_xcode": meta["src_xcode"],
            "tgt_xcode": meta["tgt_xcode"],

            # Coarse language-level representation.
            "src_lang": meta["src_lang"],
            "src_country": meta["src_country"],
            "tgt_lang": meta["tgt_lang"],
            "tgt_country": meta["tgt_country"],

            "zeroshot": meta["zeroshot"],
        })

    for dataset in dataset_to_rows:
        dataset_to_rows[
            dataset
        ].sort(
            key=lambda x: x["sort_key"]
        )

    if verbose:
        if skipped_bad_name:
            print(
                f"Skipped {len(skipped_bad_name)} "
                f"{kind} files with unrecognized filenames:",
                file=sys.stderr,
            )

            for fn in skipped_bad_name:
                print(
                    f"  {fn}",
                    file=sys.stderr,
                )

        if skipped_bad_content:
            print(
                f"Skipped {len(skipped_bad_content)} "
                f"malformed or incomplete {kind} score files:",
                file=sys.stderr,
            )

            for fn, err in skipped_bad_content:
                print(
                    f"  {fn}: {err}",
                    file=sys.stderr,
                )

    return dataset_to_rows


def old_collect_scores(
    indir: str,
    use_names=True,
    verbose=True,
):
    """
    Legacy collector retained for reference.

    The active code uses collect_scores(), which preserves src_xcode/tgt_xcode.
    """
    dataset_to_rows = defaultdict(list)

    skipped_bad_name = []
    skipped_bad_content = []

    for fn in sorted(
        os.listdir(indir)
    ):
        if not fn.endswith(".sacre"):
            continue

        # Legacy function no longer has enough information to call the current
        # parse_filename(), because kind is now required.
        skipped_bad_name.append(fn)

    if verbose and skipped_bad_name:
        print(
            "old_collect_scores is deprecated; "
            "use collect_scores(indir, kind, ...) instead.",
            file=sys.stderr,
        )

    return dataset_to_rows


def format_score(x):
    return (
        ""
        if x is None
        else f"{x:.1f}"
    )


def print_metric_tables(
    dataset_to_rows,
):
    for dataset in [
        "wmt",
        "flo",
        "bqt",
        "bqtpar",
    ]:
        dataset_name = DATASET_NAMES.get(
            dataset,
            dataset,
        )

        rows_for_dataset = dataset_to_rows.get(
            dataset,
            [],
        )

        for metric in METRICS:
            headers = [
                "Pair",
                metric,
            ]

            rows = []

            for item in rows_for_dataset:
                val = item[
                    "scores"
                ].get(metric)

                if val is not None:
                    rows.append([
                        item["pair_label"],
                        format_score(val),
                    ])

            title = (
                f"{dataset_name} — {metric}"
            )

            print(
                ascii_table(
                    headers,
                    rows,
                    title=title,
                )
            )
            print()


def print_wide_tables(
    dataset_to_rows,
):
    """
    One table per dataset with all currently enabled metrics side-by-side.
    """
    for dataset in [
        "wmt",
        "flo",
        "bqt",
        "bqtpar",
    ]:
        dataset_name = DATASET_NAMES.get(
            dataset,
            dataset,
        )

        rows_for_dataset = dataset_to_rows.get(
            dataset,
            [],
        )

        headers = [
            "Pair"
        ] + METRICS

        rows = []

        for item in rows_for_dataset:
            row = [
                item["pair_label"]
            ]

            for metric in METRICS:
                row.append(
                    format_score(
                        item["scores"].get(metric)
                    )
                )

            rows.append(row)

        print(
            ascii_table(
                headers,
                rows,
                title=f"{dataset_name} — all metrics",
            )
        )
        print()


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Summarize SacreBLEU score files into ASCII matrices "
            "or machine-readable TSV."
        )
    )

    ap.add_argument(
        "indir",
        help="Directory containing *.sacre files",
    )

    ap.add_argument(
        "--metric",
        choices=METRICS,
        help="Only print one metric",
    )

    ap.add_argument(
        "--kind",
        required=True,
        choices=[
            "docmt",
            "sentmt",
            "mt",
        ],
        help="Which score-file family to read",
    )

    ap.add_argument(
        "--codes",
        action="store_true",
        help="Use language codes instead of language names in pair labels",
    )

    ap.add_argument(
        "--wide",
        action="store_true",
        help="Also print one wide table per dataset with all metrics",
    )

    ap.add_argument(
        "--tsv",
        action="store_true",
        help="Print machine-readable TSV instead of ASCII matrices",
    )

    ap.add_argument(
        "--model",
        default="",
        help="Model alias to include in TSV output",
    )

    args = ap.parse_args()

    dataset_to_rows = collect_scores(
        args.indir,
        kind=args.kind,
        use_names=not args.codes,
        verbose=True,
    )

    # TSV mode must produce ONLY TSV on stdout.
    if args.tsv:
        print_tsv(
            dataset_to_rows,
            model=args.model,
            only_metric=args.metric,
        )
        return

    print_metric_matrices(
        dataset_to_rows,
        only_metric=args.metric,
    )

    if args.wide:
        print_wide_tables(
            dataset_to_rows
        )


if __name__ == "__main__":
    main()

