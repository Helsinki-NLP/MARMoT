from pathlib import Path
import csv

from datasets import load_dataset


# ============================================================
# Configuration
# ============================================================

DATASET = "redis/langcache-sentencepairs-v3"
CONFIG = "parabank2"

OUTPUT_DIR = Path("parabank2_tsv")

LANG = "eng"

RANDOM_SEED = 42

TRAIN_SIZE = 0.90
DEV_SIZE = 0.05
TEST_SIZE = 0.05


# ============================================================
# Write TSV
# ============================================================

def write_tsv(dataset, path):

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        writer = csv.writer(
            f,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writerow(
            [
                "source",
                "target",
            ]
        )

        for row in dataset:

            source = str(
                row["sentence1"]
            ).strip()

            target = str(
                row["sentence2"]
            ).strip()

            if not source or not target:
                continue

            writer.writerow(
                [
                    source.replace(
                        "\t",
                        " ",
                    ).replace(
                        "\n",
                        " ",
                    ),
                    target.replace(
                        "\t",
                        " ",
                    ).replace(
                        "\n",
                        " ",
                    ),
                ]
            )


# ============================================================
# Main
# ============================================================

def main():

    print(
        f"Loading {DATASET} / {CONFIG} ..."
    )

    dataset = load_dataset(
        DATASET,
        CONFIG,
    )

    print(dataset)

    # ParaBank2 is distributed as paraphrase pairs.
    # We only need positive pairs.
    if "label" in dataset["train"].column_names:
        dataset["train"] = dataset["train"].filter(
            lambda x: x["label"] == 1
        )

    # --------------------------------------------------------
    # Original dataset has no train/dev/test split suitable
    # for this format, so create one deterministically.
    # --------------------------------------------------------

    print(
        f"Total pairs: {len(dataset['train']):,}"
    )

    split_1 = dataset["train"].train_test_split(
        test_size=(
            DEV_SIZE + TEST_SIZE
        ),
        seed=RANDOM_SEED,
    )

    split_2 = split_1["test"].train_test_split(
        test_size=(
            TEST_SIZE /
            (DEV_SIZE + TEST_SIZE)
        ),
        seed=RANDOM_SEED,
    )

    train = split_1["train"]
    dev = split_2["train"]
    test = split_2["test"]

    print(
        f"Train: {len(train):,}"
    )

    print(
        f"Dev:   {len(dev):,}"
    )

    print(
        f"Test:  {len(test):,}"
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    output_dir = (
        OUTPUT_DIR / LANG
    )

    write_tsv(
        train,
        output_dir / "train.tsv",
    )

    write_tsv(
        dev,
        output_dir / "dev.tsv",
    )

    write_tsv(
        test,
        output_dir / "test.tsv",
    )

    print(
        f"\nFinished: {output_dir}"
    )


if __name__ == "__main__":
    main()
