#!/usr/bin/env python3

"""
Download knkarthick/samsum from Hugging Face and
write train/dev/test TSV files.

Output columns:
    id    dialogue    summary

The Hugging Face "validation" split is written as "dev.tsv".
"""

import argparse
from pathlib import Path

from datasets import load_dataset


DATASET = "knkarthick/samsum"


def write_tsv(dataset, output_file):
    """Write a Hugging Face Dataset to TSV."""

    fields = ["id", "dialogue", "summary"]

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(fields) + "\n")

        for row in dataset:
            values = []

            for field in fields:
                value = row[field]

                # TSV-safe representation.
                # Keep the dialogue itself intact except for
                # tabs/newlines, which would otherwise break rows.
                value = str(value)
                value = value.replace("\t", " ")
                value = value.replace("\r\n", " ")
                value = value.replace("\n", " ")
                value = value.replace("\r", " ")

                values.append(value)

            f.write("\t".join(values) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Download SAMSum and convert it to TSV."
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="samsum_tsv",
        help="Directory for the TSV files.",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {DATASET}...")

    dataset = load_dataset(DATASET)

    # Hugging Face uses "validation"; we call it "dev".
    splits = {
        "train": "train",
        "validation": "dev",
        "test": "test",
    }

    for hf_split, output_name in splits.items():

        data = dataset[hf_split]

        output_file = output_dir / f"{output_name}.tsv"

        write_tsv(data, output_file)

        print(
            f"{output_name:5s}: "
            f"{len(data):,} examples -> {output_file}"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()

