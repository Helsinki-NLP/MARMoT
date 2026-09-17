#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


def parse_input(spec):
    """
    ALIAS=PATH
    """
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            "input must be MODEL=PATH"
        )

    model, path = spec.split("=", 1)

    if not model:
        raise argparse.ArgumentTypeError("empty model alias")

    p = Path(path)
    if not p.is_file():
        raise argparse.ArgumentTypeError(
            f"TSV file does not exist: {p}"
        )

    return model, p


def read_tasks(model, path, metric=None, dataset=None):
    """
    Return the set of evaluation tasks covered by one model.

    A task is identified by:

        dataset, src, tgt, zeroshot

    Metric is deliberately NOT part of the task identity.

    If --metric is given, only rows containing that metric establish
    coverage. This is useful later for COMET, TER, etc.
    """

    tasks = set()

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        required = {
            "dataset",
            "src",
            "tgt",
            "zeroshot",
            "metric",
        }

        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"{path}: missing TSV columns: "
                + ", ".join(sorted(missing))
            )

        for row in reader:
            if metric and row["metric"] != metric:
                continue

            if dataset and row["dataset"] != dataset:
                continue

            task = (
                row["dataset"],
                row["src"],
                row["tgt"],
                row["zeroshot"],
            )

            tasks.add(task)

    return tasks


def build_partitions(model_tasks):
    """
    Map coverage signature -> tasks.

    Coverage signature is a tuple of model aliases.
    """

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
    Largest model coverage first, then largest task group.
    """

    return sorted(
        partitions.items(),
        key=lambda x: (
            -len(x[0]),
            -len(x[1]),
            x[0],
        ),
    )


def assign_group_ids(partitions):
    result = []

    for i, (models, tasks) in enumerate(
        sorted_partitions(partitions), start=1
    ):
        result.append(
            (f"G{i:02d}", models, tasks)
        )

    return result


def language_statistics(tasks):
    """
    language -> [source_count, target_count, union_task_count]
    """

    src_count = defaultdict(int)
    tgt_count = defaultdict(int)
    task_sets = defaultdict(set)

    for task in tasks:
        dataset, src, tgt, zeroshot = task

        src_count[src] += 1
        tgt_count[tgt] += 1

        task_sets[src].add(task)
        task_sets[tgt].add(task)

    languages = sorted(task_sets)

    return [
        (
            lang,
            src_count[lang],
            tgt_count[lang],
            len(task_sets[lang]),
        )
        for lang in languages
    ]


def print_summary(groups, model_order):
    print("Coverage partition summary")
    print()
    print("Legend:")
    print("  group   = tasks having exactly the same model coverage")
    print("  models  = models having scores for every task in the group")
    print("  tasks   = number of evaluation tasks in the group")
    print("  langs   = number of distinct source/target languages")
    print()

    print(
        f"{'group':<5} "
        f"{'tasks':>4} "
        f"{'langs':>4} "
        f"{'models':<55} "
    )

    print(
        f"{'-' * 6:<5} "
        f"{'-' * 7:>4} "
        f"{'-' * 7:>4} "
        f"{'-' * 54:<55}"
    )

    for gid, models, tasks in groups:
        langs = language_statistics(tasks)

        print(
            f"{gid:<5} "
            f"{len(tasks):>4} "
            f"{len(langs):>4} "
            f"{','.join(models):<55}"
        )


def print_tasks_tsv(groups):
    writer = csv.writer(
        sys.stdout,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writerow([
        "group",
        "model_count",
        "models",
        "dataset",
        "src",
        "tgt",
        "zeroshot",
    ])

    for gid, models, tasks in groups:
        model_string = ",".join(models)

        for dataset, src, tgt, zeroshot in tasks:
            writer.writerow([
                gid,
                len(models),
                model_string,
                dataset,
                src,
                tgt,
                zeroshot,
            ])


def print_languages_tsv(groups):
    writer = csv.writer(
        sys.stdout,
        delimiter="\t",
        lineterminator="\n",
    )

    writer.writerow([
        "group",
        "model_count",
        "models",
        "language",
        "source_tasks",
        "target_tasks",
        "all_tasks",
    ])

    for gid, models, tasks in groups:
        model_string = ",".join(models)

        for lang, src_n, tgt_n, all_n in language_statistics(tasks):
            writer.writerow([
                gid,
                len(models),
                model_string,
                lang,
                src_n,
                tgt_n,
                all_n,
            ])


def print_language_report(groups):
    print("Languages by coverage partition")
    print()

    print("Legend:")
    print("  Gxx       coverage partition")
    print("  models    exactly the models covering tasks in this partition")
    print("  src       number of tasks where language occurs as source")
    print("  tgt       number of tasks where language occurs as target")
    print("  tasks     distinct tasks involving the language")
    print()

    for gid, models, tasks in groups:
        stats = language_statistics(tasks)

        print(f"{gid}: {', '.join(models)}")
        print(f"  tasks:     {len(tasks)}")
        print(f"  languages: {len(stats)}")
        print()

        if not stats:
            continue

        print(
            f"  {'language':<12}"
            f"{'src':>7}"
            f"{'tgt':>7}"
            f"{'tasks':>8}"
        )

        print(
            f"  {'-' * 11:<12}"
            f"{'-' * 6:>7}"
            f"{'-' * 6:>7}"
            f"{'-' * 7:>8}"
        )

        for lang, src_n, tgt_n, all_n in stats:
            print(
                f"  {lang:<12}"
                f"{src_n:>7}"
                f"{tgt_n:>7}"
                f"{all_n:>8}"
            )

        print()


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Partition evaluation tasks according to which models "
            "have them covered."
        )
    )

    ap.add_argument(
        "--input",
        action="append",
        type=parse_input,
        required=True,
        metavar="MODEL=TSV",
        help=(
            "Model alias and eval3/sacre.tsv file. "
            "Repeat for every model."
        ),
    )

    ap.add_argument(
        "--metric",
        help=(
            "Use coverage for one metric only, "
            "for example BLEU or chrF2."
        ),
    )

    ap.add_argument(
        "--dataset",
        choices=[
            "wmt",
            "flo",
            "bqt",
            "bqtpar",
        ],
        help="Restrict to one evaluation dataset.",
    )

    ap.add_argument(
        "--view",
        choices=[
            "summary",
            "tasks",
            "languages",
            "language-report",
        ],
        default="summary",
        help="Output format.",
    )

    args = ap.parse_args()

    model_tasks = {}

    for model, path in args.input:
        if model in model_tasks:
            raise SystemExit(
                f"Duplicate model alias: {model}"
            )

        model_tasks[model] = read_tasks(
            model,
            path,
            metric=args.metric,
            dataset=args.dataset,
        )

    partitions = build_partitions(model_tasks)
    groups = assign_group_ids(partitions)

    if args.view == "summary":
        print_summary(
            groups,
            list(model_tasks),
        )

    elif args.view == "tasks":
        print_tasks_tsv(groups)

    elif args.view == "languages":
        print_languages_tsv(groups)

    elif args.view == "language-report":
        print_language_report(groups)


if __name__ == "__main__":
    main()
