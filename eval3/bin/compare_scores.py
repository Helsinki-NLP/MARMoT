#!/usr/bin/env python3

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


def die(msg):
    print("compare_scores.py: ERROR: " + msg, file=sys.stderr)
    raise SystemExit(1)


def log(msg):
    print("compare_scores.py: " + msg, file=sys.stderr)


# ----------------------------------------------------------------------
# Hand-crafted comparison groups
# ----------------------------------------------------------------------

HAND_GROUPS = {
    "task-pivots": {
        "title": "Number of central/pivot languages",
        "description": (
            "Closest controlled comparison available among the summer models: "
            "transformer-base, half-shared encoder, denoising; "
            "1-pivot vs 4-pivot vs 10-pivot."
        ),
        "models": [
            "d_halfsharedenc",
            "docmt4denhalfbase",
            "docmt10denhalf",
        ],
        "labels": {
            "d_halfsharedenc": "1 pivot",
            "docmt4denhalfbase": "4 pivots",
            "docmt10denhalf": "10 pivots",
        },
    },

    "model-size": {
        "title": "Model size",
        "description": (
            "4-pivot + denoising, half-shared encoder; "
            "small/base/big/XL model size."
        ),
        "models": [
            "docmt4denhalfsmall",
            "docmt4denhalfbase",
            "docmt4denhalfbig",
            "docmt4denhalfxl",
        ],
        "labels": {
            "docmt4denhalfsmall": "small",
            "docmt4denhalfbase": "base",
            "docmt4denhalfbig": "big",
            "docmt4denhalfxl": "XL",
        },
    },

    "sharing-legacy": {
        "title": "Encoder sharing architecture - summer models",
        "description": (
            "English-centric + denoising, transformer-base. "
            "This is the closest controlled sharing comparison in the "
            "summer model set; it is not yet the forthcoming full "
            "4-pivot sharing experiment."
        ),
        "models": [
            "denoise",
            "d_sharedenc",
            "d_halfsharedenc",
            "LGAenc",
        ],
        "labels": {
            "denoise": "language-specific",
            "d_sharedenc": "fully shared encoder",
            "d_halfsharedenc": "half-shared encoder",
            "LGAenc": "language-group/shared encoder",
        },
    },
}


# ----------------------------------------------------------------------
# Evaluation-mode handling
# ----------------------------------------------------------------------

def mode_matches(row, mode):
    """
    Decide whether one TSV row belongs to the requested evaluation mode.

    sacre.tsv convention:
        zeroshot == "1"  -> zero-shot
        zeroshot == "0"  -> supervised
    """
    zeroshot = row["zeroshot"] == "1"

    if mode == "zeroshot":
        return zeroshot

    if mode == "supervised":
        return not zeroshot

    return True


def mode_display(mode):
    if mode == "zeroshot":
        return "zeroshot"
    if mode == "supervised":
        return "supervised"
    return "all (supervised + zeroshot)"


# ----------------------------------------------------------------------
# Language utilities
# ----------------------------------------------------------------------

def language_from_xcode(xcode):
    """
    Examples:
        XX.fin      -> fin
        CA.fra      -> fra
        XX.srp_Cyrl -> srp
    """
    if "." in xcode:
        lang = xcode.split(".", 1)[1]
    else:
        lang = xcode

    return lang.split("_", 1)[0]


def languages_in_tasks(tasks):
    langs = set()

    for dataset, src_xcode, tgt_xcode, zeroshot in tasks:
        langs.add(language_from_xcode(src_xcode))
        langs.add(language_from_xcode(tgt_xcode))

    return langs


# ----------------------------------------------------------------------
# Makefile parsing
# ----------------------------------------------------------------------

def join_makefile_lines(text):
    result = []
    buf = ""

    for raw in text.splitlines():
        line = raw.rstrip()

        if line.endswith("\\"):
            buf += line[:-1] + " "
        else:
            result.append(buf + line)
            buf = ""

    if buf:
        result.append(buf)

    return result


def parse_make_models(path):
    """
    Read all MODEL_<alias> definitions.

    This deliberately does NOT restrict the result to MODEL_ALIASES.
    Thus a defined model such as MODEL_docmt4denhalfbig is usable even
    if it is temporarily absent from MODEL_ALIASES.
    """
    path = Path(path)

    if not path.is_file():
        die("model Makefile not found: {}".format(path))

    variables = {}

    for raw in join_makefile_lines(path.read_text()):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        m = re.match(
            r"^([A-Za-z0-9_]+)\s*:?=\s*(.*)$",
            line,
        )

        if m:
            name, value = m.groups()
            variables[name] = value.strip()

    def expand(value):
        previous = None

        while value != previous:
            previous = value

            for name, replacement in variables.items():
                value = value.replace(
                    "$({})".format(name),
                    replacement,
                )

        return value

    models = {}

    for name, value in variables.items():
        if not name.startswith("MODEL_"):
            continue

        alias = name[len("MODEL_"):]

        if not alias:
            continue

        models[alias] = Path(expand(value))

    return models


def parse_explicit_models(specs):
    """
    Parse:
        --models A=/path/a B=/path/b
    """
    models = {}

    for spec in specs:
        if "=" not in spec:
            die(
                "explicit models must be MODEL=DIR; got {!r}".format(
                    spec
                )
            )

        alias, directory = spec.split("=", 1)

        alias = alias.strip()
        directory = directory.strip()

        if not alias:
            die("empty model alias in {!r}".format(spec))

        if not directory:
            die("empty directory for model {}".format(alias))

        if alias in models:
            die("duplicate model alias: {}".format(alias))

        models[alias] = Path(directory)

    return models


# ----------------------------------------------------------------------
# sacre.tsv loading
# ----------------------------------------------------------------------

def load_coverage_tasks(
    path,
    metric=None,
    dataset=None,
    mode="all",
):
    """
    Task identity uses localized xcodes:

        dataset, src_xcode, tgt_xcode, zeroshot

    src/tgt alone are NOT sufficient because, for example,
    CA.fra and FR.fra are distinct evaluation tasks.
    """
    path = Path(path)

    if not path.is_file():
        return set()

    tasks = set()

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        required = {
            "dataset",
            "src_xcode",
            "tgt_xcode",
            "zeroshot",
            "metric",
        }

        missing = required - set(reader.fieldnames or [])

        if missing:
            die(
                "{} is missing columns: {}".format(
                    path,
                    ", ".join(sorted(missing)),
                )
            )

        for row in reader:
            if metric and row["metric"] != metric:
                continue

            if dataset and row["dataset"] != dataset:
                continue

            if not mode_matches(row, mode):
                continue

            tasks.add((
                row["dataset"],
                row["src_xcode"],
                row["tgt_xcode"],
                row["zeroshot"],
            ))

    return tasks


def load_scores(
    path,
    metric,
    dataset,
    mode="all",
):
    """
    Load scores for one model.

    Comparison key:

        (src_xcode, tgt_xcode, zeroshot)

    Dataset and metric have already been filtered.
    """
    path = Path(path)

    if not path.is_file():
        die("score TSV not found: {}".format(path))

    scores = {}

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        required = {
            "dataset",
            "src_xcode",
            "tgt_xcode",
            "src",
            "tgt",
            "zeroshot",
            "metric",
            "score",
        }

        missing = required - set(reader.fieldnames or [])

        if missing:
            die(
                "{} is missing columns: {}".format(
                    path,
                    ", ".join(sorted(missing)),
                )
            )

        for row in reader:
            if row["dataset"] != dataset:
                continue

            if row["metric"] != metric:
                continue

            if not mode_matches(row, mode):
                continue

            try:
                score = float(row["score"])
            except ValueError:
                log(
                    "ignoring invalid score {!r} in {}".format(
                        row["score"],
                        path,
                    )
                )
                continue

            key = (
                row["src_xcode"],
                row["tgt_xcode"],
                row["zeroshot"],
            )

            if key in scores:
                die(
                    "true duplicate task in {}: "
                    "{} -> {} zeroshot={}".format(
                        path,
                        key[0],
                        key[1],
                        key[2],
                    )
                )

            scores[key] = {
                "score": score,
                "src": row["src"],
                "tgt": row["tgt"],
                "src_xcode": row["src_xcode"],
                "tgt_xcode": row["tgt_xcode"],
                "zeroshot": row["zeroshot"],
            }

    return scores


# ----------------------------------------------------------------------
# Dynamic coverage groups
# ----------------------------------------------------------------------

def build_partitions(model_tasks):
    all_tasks = set()

    for tasks in model_tasks.values():
        all_tasks.update(tasks)

    partitions = defaultdict(list)

    for task in sorted(all_tasks):
        covering = tuple(
            model
            for model, tasks in model_tasks.items()
            if task in tasks
        )

        partitions[covering].append(task)

    return partitions


def sorted_partitions(partitions):
    """
    Stable group ordering:

      1. largest number of covering models first
      2. largest task group first
      3. model tuple for deterministic tie breaking
    """
    return sorted(
        partitions.items(),
        key=lambda item: (
            -len(item[0]),
            -len(item[1]),
            item[0],
        ),
    )


def assign_group_ids(partitions):
    groups = []

    for i, (models, tasks) in enumerate(
        sorted_partitions(partitions),
        start=1,
    ):
        groups.append((
            "G{:02d}".format(i),
            models,
            tasks,
        ))

    return groups


def recompute_coverage_groups(
    model_dirs,
    metric,
    partition_dataset=None,
    mode="all",
):
    """
    Compute G01, G02, ... afresh from the current sacre.tsv files.

    Metric and mode are part of the coverage definition.

    By default the partition uses all datasets.  This means, for example,
    that G06 does not silently change just because the later comparison
    happens to use bqtpar rather than flo.

    Use --partition-dataset if dataset-specific coverage groups are wanted.
    """
    model_tasks = {}

    for model, model_dir in model_dirs.items():
        tsv = model_dir / "eval3" / "sacre.tsv"

        if not tsv.is_file():
            continue

        tasks = load_coverage_tasks(
            tsv,
            metric=metric,
            dataset=partition_dataset,
            mode=mode,
        )

        if tasks:
            model_tasks[model] = tasks

    if not model_tasks:
        die(
            "no models with usable eval3/sacre.tsv files "
            "for metric={} mode={}".format(
                metric,
                mode,
            )
        )

    return assign_group_ids(
        build_partitions(model_tasks)
    )


def resolve_dynamic_group(
    wanted,
    model_dirs,
    metric,
    partition_dataset=None,
    mode="all",
):
    groups = recompute_coverage_groups(
        model_dirs,
        metric,
        partition_dataset=partition_dataset,
        mode=mode,
    )

    for gid, models, tasks in groups:
        if gid == wanted:
            return {
                "name": gid,
                "title": "Coverage group {}".format(gid),
                "description": (
                    "Models having exactly this coverage signature "
                    "for metric={} and mode={}.".format(
                        metric,
                        mode_display(mode),
                    )
                ),
                "models": list(models),
                "labels": {
                    model: model
                    for model in models
                },
                "coverage_tasks": tasks,
            }

    die(
        "unknown coverage group {}. Available groups: {}".format(
            wanted,
            ", ".join(
                gid
                for gid, _, _ in groups
            ),
        )
    )


# ----------------------------------------------------------------------
# Hand-crafted group resolution
# ----------------------------------------------------------------------

def resolve_hand_group(name, model_dirs):
    spec = HAND_GROUPS[name]

    available = []
    unavailable = []

    for model in spec["models"]:
        if model not in model_dirs:
            unavailable.append(
                (model, "not defined")
            )
            continue

        tsv = (
            model_dirs[model]
            / "eval3"
            / "sacre.tsv"
        )

        if not tsv.is_file():
            unavailable.append(
                (model, "sacre.tsv missing")
            )
            continue

        available.append(model)

    if unavailable:
        log(
            "group {} has unavailable models: {}".format(
                name,
                ", ".join(
                    "{} ({})".format(
                        model,
                        reason,
                    )
                    for model, reason in unavailable
                ),
            )
        )

    if len(available) < 2:
        die(
            "hand-crafted group {} has fewer than two "
            "available models".format(
                name
            )
        )

    return {
        "name": name,
        "title": spec["title"],
        "description": spec["description"],
        "models": available,
        "labels": {
            model: spec["labels"].get(
                model,
                model,
            )
            for model in available
        },
        "coverage_tasks": None,
    }


def resolve_group(
    name,
    model_dirs,
    metric,
    partition_dataset=None,
    mode="all",
):
    if name in HAND_GROUPS:
        return resolve_hand_group(
            name,
            model_dirs,
        )

    if re.fullmatch(r"G[0-9]+", name):
        return resolve_dynamic_group(
            name,
            model_dirs,
            metric,
            partition_dataset=partition_dataset,
            mode=mode,
        )

    die(
        "unknown group {!r}. Use --list-groups or a dynamic "
        "coverage group such as G06.".format(
            name
        )
    )


# ----------------------------------------------------------------------
# Help / group listing
# ----------------------------------------------------------------------

def print_all_groups(
    model_dirs,
    metric,
    partition_dataset=None,
    mode="all",
):
    print("Hand-crafted comparison groups")
    print()

    for name, spec in HAND_GROUPS.items():
        print("{}:".format(name))
        print("  {}".format(spec["title"]))
        print("  {}".format(spec["description"]))

        available = []
        unavailable = []

        for model in spec["models"]:
            if model not in model_dirs:
                unavailable.append(
                    (model, "not defined")
                )
                continue

            tsv = (
                model_dirs[model]
                / "eval3"
                / "sacre.tsv"
            )

            if not tsv.is_file():
                unavailable.append(
                    (model, "sacre.tsv missing")
                )
                continue

            available.append(model)

        print()

        for model in spec["models"]:
            label = spec["labels"].get(
                model,
                model,
            )

            if model in available:
                status = ""
            else:
                reason = next(
                    reason
                    for m, reason in unavailable
                    if m == model
                )
                status = "  [{}]".format(
                    reason
                )

            print(
                "    {:24} {}{}".format(
                    model,
                    label,
                    status,
                )
            )

        print()

    print("Dynamic coverage groups")
    print()

    print(
        "Metric used for coverage: {}".format(
            metric
        )
    )

    print(
        "Mode used for coverage:   {}".format(
            mode_display(mode)
        )
    )

    if partition_dataset:
        print(
            "Dataset restriction:     {}".format(
                partition_dataset
            )
        )
    else:
        print(
            "Dataset restriction:     all datasets"
        )

    print()

    groups = recompute_coverage_groups(
        model_dirs,
        metric,
        partition_dataset=partition_dataset,
        mode=mode,
    )

    print(
        "{:<5} {:>7} {:>7} {:>7} {}".format(
            "group",
            "tasks",
            "langs",
            "models",
            "model aliases",
        )
    )

    print(
        "{:<5} {:>7} {:>7} {:>7} {}".format(
            "-----",
            "-------",
            "-------",
            "-------",
            "-" * 60,
        )
    )

    for gid, models, tasks in groups:
        langs = languages_in_tasks(
            tasks
        )

        print(
            "{:<5} {:>7} {:>7} {:>7} {}".format(
                gid,
                len(tasks),
                len(langs),
                len(models),
                ",".join(models),
            )
        )


# ----------------------------------------------------------------------
# Common score utilities
# ----------------------------------------------------------------------

def common_tasks(scores_by_model):
    sets = [
        set(scores)
        for scores in scores_by_model.values()
    ]

    if not sets:
        return set()

    return set.intersection(
        *sets
    )


def union_tasks(scores_by_model):
    result = set()

    for scores in scores_by_model.values():
        result.update(scores)

    return result


def score_value(
    scores_by_model,
    model,
    task,
):
    return scores_by_model[
        model
    ][task]["score"]


# ----------------------------------------------------------------------
# Metric direction
# ----------------------------------------------------------------------

def higher_is_better(metric):
    """
    BLEU, chrF2 and COMET: higher is better.
    TER: lower is better.
    """
    return metric.upper() != "TER"


def better_than(a, b, metric, epsilon):
    if higher_is_better(metric):
        return a > b + epsilon

    return a < b - epsilon


def best_score(values, metric):
    if higher_is_better(metric):
        return max(values)

    return min(values)


def score_sort_key(item, metric):
    value = item[1]

    if higher_is_better(metric):
        return -value

    return value


# ----------------------------------------------------------------------
# Model summaries
# ----------------------------------------------------------------------

def calculate_summary(
    scores_by_model,
    tasks,
    tie_epsilon,
    metric,
):
    models = list(
        scores_by_model
    )

    stats = {}

    for model in models:
        stats[model] = {
            "wins": 0,
            "ties": 0,
            "sum": 0.0,
            "rank_sum": 0.0,
            "n": 0,
        }

    for task in tasks:
        values = {
            model: score_value(
                scores_by_model,
                model,
                task,
            )
            for model in models
        }

        ordered = sorted(
            values.items(),
            key=lambda item: score_sort_key(
                item,
                metric,
            ),
        )

        best = best_score(
            values.values(),
            metric,
        )

        winners = [
            model
            for model, value in ordered
            if abs(value - best) <= tie_epsilon
        ]

        if len(winners) == 1:
            stats[
                winners[0]
            ]["wins"] += 1
        else:
            for model in winners:
                stats[
                    model
                ]["ties"] += 1

        for model, value in values.items():
            stats[model]["sum"] += value
            stats[model]["n"] += 1

        #
        # Rank models while respecting the same tie epsilon.
        #
        rank_groups = []
        current = []

        for model, value in ordered:
            if not current:
                current = [
                    (model, value)
                ]
                continue

            reference_value = current[0][1]

            if abs(
                value - reference_value
            ) <= tie_epsilon:
                current.append(
                    (model, value)
                )
            else:
                rank_groups.append(
                    current
                )
                current = [
                    (model, value)
                ]

        if current:
            rank_groups.append(
                current
            )

        position = 1

        for group in rank_groups:
            first = position
            last = (
                position
                + len(group)
                - 1
            )

            rank = (
                first + last
            ) / 2.0

            for model, _value in group:
                stats[
                    model
                ]["rank_sum"] += rank

            position += len(group)

    rows = []

    for model in models:
        s = stats[model]

        average = (
            s["sum"] / s["n"]
            if s["n"]
            else float("nan")
        )

        average_rank = (
            s["rank_sum"] / s["n"]
            if s["n"]
            else float("nan")
        )

        rows.append({
            "model": model,
            "wins": s["wins"],
            "ties": s["ties"],
            "covered": s["n"],
            "average": average,
            "average_rank": average_rank,
        })

    rows.sort(
        key=lambda row: (
            -row["wins"],
            row["average_rank"],
            (
                -row["average"]
                if higher_is_better(metric)
                else row["average"]
            ),
        )
    )

    return rows


def calculate_dominance(
    scores_by_model,
    tasks,
    tie_epsilon,
    metric,
):
    models = list(
        scores_by_model
    )

    wins = {}

    for a in models:
        for b in models:
            if a != b:
                wins[(a, b)] = 0

    for task in tasks:
        for a in models:
            va = score_value(
                scores_by_model,
                a,
                task,
            )

            for b in models:
                if a == b:
                    continue

                vb = score_value(
                    scores_by_model,
                    b,
                    task,
                )

                if better_than(
                    va,
                    vb,
                    metric,
                    tie_epsilon,
                ):
                    wins[
                        (a, b)
                    ] += 1

    return wins


# ----------------------------------------------------------------------
# Text output
# ----------------------------------------------------------------------

def print_selection(
    group_spec,
    metric,
    dataset,
    mode,
    common_count,
    union_count,
):
    models = group_spec["models"]
    labels = group_spec["labels"]

    print("Comparison")
    print()

    print(
        "Group:       {}".format(
            group_spec["name"]
        )
    )

    print(
        "Title:       {}".format(
            group_spec["title"]
        )
    )

    print(
        "Description: {}".format(
            group_spec["description"]
        )
    )

    print(
        "Dataset:     {}".format(
            dataset
        )
    )

    print(
        "Metric:      {}".format(
            metric
        )
    )

    print(
        "Mode:        {}".format(
            mode_display(mode)
        )
    )

    print(
        "Models:      {}".format(
            len(models)
        )
    )

    print(
        "Tasks:       {} common / {} union".format(
            common_count,
            union_count,
        )
    )

    print()

    print("Legend:")

    for model in models:
        print(
            "  {:24} {}".format(
                model,
                labels.get(
                    model,
                    model,
                ),
            )
        )

    print()


def print_medal_table(
    rows,
    metric,
    labels,
):
    print(
        "Model summary ({})".format(
            metric
        )
    )

    print()

    print(
        "{:<4} {:<24} {:<34} {:>6} {:>6} {:>10} {:>9}".format(
            "Rank",
            "Model",
            "Legend",
            "Wins",
            "Ties",
            "Average",
            "Avg rank",
        )
    )

    print(
        "{:<4} {:<24} {:<34} {:>6} {:>6} {:>10} {:>9}".format(
            "----",
            "-" * 24,
            "-" * 34,
            "-" * 6,
            "-" * 6,
            "-" * 10,
            "-" * 9,
        )
    )

    for rank, row in enumerate(
        rows,
        1,
    ):
        model = row["model"]

        print(
            "{:<4} {:<24} {:<34} {:>6} {:>6} {:>10.2f} {:>9.2f}".format(
                rank,
                model,
                labels.get(
                    model,
                    model,
                ),
                row["wins"],
                row["ties"],
                row["average"],
                row["average_rank"],
            )
        )

    print()


def print_dominance(
    models,
    dominance,
    labels,
):
    names = [
        labels.get(
            model,
            model,
        )
        for model in models
    ]

    width = max(
        10,
        max(
            len(name)
            for name in names
        ) + 2,
    )

    print("Pairwise wins")
    print(
        "Legend: row model beats column model"
    )
    print()

    print(
        "{:<{w}}".format(
            "",
            w=width,
        ),
        end="",
    )

    for name in names:
        print(
            "{:>{w}}".format(
                name,
                w=width,
            ),
            end="",
        )

    print()

    print(
        "-" * (
            width
            * (
                len(models) + 1
            )
        )
    )

    for a, aname in zip(
        models,
        names,
    ):
        print(
            "{:<{w}}".format(
                aname,
                w=width,
            ),
            end="",
        )

        for b in models:
            if a == b:
                value = "---"
            else:
                value = str(
                    dominance[
                        (a, b)
                    ]
                )

            print(
                "{:>{w}}".format(
                    value,
                    w=width,
                ),
                end="",
            )

        print()

    print()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    hand_help = "\n".join(
        "  {:20} {}".format(
            name,
            spec["title"],
        )
        for name, spec
        in HAND_GROUPS.items()
    )

    epilog = (
        "Hand-crafted groups:\n"
        + hand_help
        + "\n\n"
        + "Dynamic groups such as G06 are recomputed from the available "
          "eval3/sacre.tsv files.\n"
        + "Use --list-groups for detailed descriptions."
    )

    ap = argparse.ArgumentParser(
        description=(
            "Compare eval3 SacreBLEU TSV files across models."
        ),
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    model_source = (
        ap.add_mutually_exclusive_group(
            required=False
        )
    )

    model_source.add_argument(
        "--mk-models",
        help=(
            "Makefile containing MODEL_* definitions"
        ),
    )

    model_source.add_argument(
        "--models",
        nargs="+",
        metavar="MODEL=DIR",
        help=(
            "Explicit model definitions. "
            "Example: --models "
            "base=/path/base xl=/path/xl"
        ),
    )

    ap.add_argument(
        "--group",
        help=(
            "Comparison group. May be a dynamic coverage group "
            "such as G06 or a hand-crafted group such as model-size."
        ),
    )

    ap.add_argument(
        "--list-groups",
        action="store_true",
        help=(
            "List hand-crafted and dynamic comparison groups and exit"
        ),
    )

    ap.add_argument(
        "--metric",
        default="BLEU",
        help=(
            "Metric to compare, e.g. BLEU, chrF2 or TER"
        ),
    )

    ap.add_argument(
        "--dataset",
        required=False,
        choices=[
            "wmt",
            "flo",
            "bqt",
            "bqtpar",
        ],
        default="bqtpar",
    )

    ap.add_argument(
        "--partition-dataset",
        choices=[
            "wmt",
            "flo",
            "bqt",
            "bqtpar",
        ],
        default=None,
        help=(
            "Optional dataset restriction when recomputing Gxx "
            "coverage groups. By default coverage grouping uses "
            "all datasets."
        ),
    )

    ap.add_argument(
        "--tie-epsilon",
        type=float,
        default=0.05,
        help=(
            "Scores within this difference count as tied"
        ),
    )

    ap.add_argument(
        "--mode",
        choices=[
            "all",
            "supervised",
            "zeroshot",
        ],
        default="all",
        help=(
            "Restrict comparison to supervised or zero-shot tasks"
        ),
    )

    args = ap.parse_args()

    # ------------------------------------------------------------------
    # Resolve model universe exactly once.
    # ------------------------------------------------------------------

    if args.mk_models:
        model_dirs = parse_make_models(
            args.mk_models
        )

    elif args.models:
        model_dirs = parse_explicit_models(
            args.models
        )

    else:
        die(
            "give either --mk-models FILE or "
            "--models MODEL=DIR ..."
        )

    if not model_dirs:
        die("no models found")

    # ------------------------------------------------------------------
    # Group discovery.
    # Dynamic groups depend on metric + mode.
    # ------------------------------------------------------------------

    if args.list_groups:
        print_all_groups(
            model_dirs,
            metric=args.metric,
            partition_dataset=args.partition_dataset,
            mode=args.mode,
        )
        return

    # ------------------------------------------------------------------
    # Resolve comparison selection.
    # ------------------------------------------------------------------

    if args.group:
        group_spec = resolve_group(
            args.group,
            model_dirs,
            metric=args.metric,
            partition_dataset=args.partition_dataset,
            mode=args.mode,
        )

    else:
        available = []

        for model, model_dir in model_dirs.items():
            tsv = (
                model_dir
                / "eval3"
                / "sacre.tsv"
            )

            if tsv.is_file():
                available.append(
                    model
                )

        if len(available) < 2:
            die(
                "fewer than two supplied models "
                "have eval3/sacre.tsv"
            )

        group_spec = {
            "name": "explicit",
            "title": "Explicit model set",
            "description": (
                "All supplied models with available sacre.tsv."
            ),
            "models": available,
            "labels": {
                model: model
                for model in available
            },
            "coverage_tasks": None,
        }

    selected_models = (
        group_spec["models"]
    )

    # ------------------------------------------------------------------
    # Load actual scores for requested dataset / metric / mode.
    # ------------------------------------------------------------------

    scores_by_model = {}

    for model in selected_models:
        if model not in model_dirs:
            die(
                "unknown model alias {!r}".format(
                    model
                )
            )

        tsv = (
            model_dirs[model]
            / "eval3"
            / "sacre.tsv"
        )

        log(
            "loading {}: {}".format(
                model,
                tsv,
            )
        )

        scores = load_scores(
            tsv,
            metric=args.metric,
            dataset=args.dataset,
            mode=args.mode,
        )

        if not scores:
            die(
                "{} has no {} scores for dataset {} "
                "and mode {}".format(
                    model,
                    args.metric,
                    args.dataset,
                    mode_display(
                        args.mode
                    ),
                )
            )

        scores_by_model[
            model
        ] = scores

    common = common_tasks(
        scores_by_model
    )

    union = union_tasks(
        scores_by_model
    )

    if not common:
        die(
            "selected models have no common {} / {} "
            "tasks in mode {}".format(
                args.dataset,
                args.metric,
                mode_display(
                    args.mode
                ),
            )
        )

    # ------------------------------------------------------------------
    # Human-readable summary.
    # ------------------------------------------------------------------

    print_selection(
        group_spec,
        args.metric,
        args.dataset,
        args.mode,
        len(common),
        len(union),
    )

    summary = calculate_summary(
        scores_by_model,
        common,
        args.tie_epsilon,
        args.metric,
    )

    print_medal_table(
        summary,
        args.metric,
        group_spec["labels"],
    )

    dominance = calculate_dominance(
        scores_by_model,
        common,
        args.tie_epsilon,
        args.metric,
    )

    print_dominance(
        selected_models,
        dominance,
        group_spec["labels"],
    )


if __name__ == "__main__":
    main()
    
