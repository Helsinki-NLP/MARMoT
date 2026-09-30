#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from langcodes import Language


DATASET = "AmazonScience/mintaka"


def iso639_3(language_code):
    """Convert a language code/tag to ISO 639-3."""
    try:
        return Language.get(language_code).to_alpha3()
    except LookupError as e:
        raise ValueError(
            f"Could not convert language code "
            f"{language_code!r} to ISO 639-3"
        ) from e


def clean_tsv_value(value):
    """Make a value safe for a single TSV field."""
    if value is None:
        return ""

    value = str(value)

    # Keep each example on exactly one TSV line.
    value = value.replace("\t", " ")
    value = value.replace("\r\n", " ")
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    return value.strip()


def write_tsv(dataset, output_file):
    """
    Write Mintaka as:

        question<TAB>answer
    """
    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("question\tanswer\n")

        for row in dataset:

            question = clean_tsv_value(
                row.get("question", "")
            )

            answer = clean_tsv_value(
                row.get("answerText", "")
            )

            f.write(
                f"{question}\t{answer}\n"
            )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download Mintaka and convert each "
            "language to train/dev/test TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="mintaka_tsv",
        help=(
            "Output directory "
            "(default: mintaka_tsv)"
        ),
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional ISO-639-1 language codes. "
            "Examples: en fi ja"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Discover available Mintaka configurations
    # ---------------------------------------------------------------

    print(
        f"Getting configurations from {DATASET}..."
    )

    languages = get_dataset_config_names(
        DATASET
    )

    print(
        f"Found {len(languages)} "
        f"language configuration(s):"
    )

    for language in languages:
        iso3 = iso639_3(language)
        print(f"  {language} -> {iso3}")

    # ---------------------------------------------------------------
    # Optional language selection
    # ---------------------------------------------------------------

    if args.languages:

        requested = set(args.languages)
        available = set(languages)

        unknown = requested - available

        if unknown:
            raise ValueError(
                "Unknown Mintaka language(s):\n"
                + "\n".join(sorted(unknown))
                + "\n\nAvailable languages:\n"
                + "\n".join(sorted(languages))
            )

        languages = [
            language
            for language in languages
            if language in requested
        ]

    # ---------------------------------------------------------------
    # Hugging Face split -> our split names
    # ---------------------------------------------------------------

    split_names = {
        "train": "train",
        "validation": "dev",
        "test": "test",
    }

    # ---------------------------------------------------------------
    # Download and convert
    # ---------------------------------------------------------------

    for i, language in enumerate(
        languages,
        start=1,
    ):

        iso_code = iso639_3(language)

        print(
            f"\n[{i}/{len(languages)}] "
            f"{language} -> {iso_code}"
        )

        try:

            dataset = load_dataset(
                DATASET,
                language,
            )

            language_dir = (
                output_dir / iso_code
            )

            language_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            for hf_split, output_name in (
                split_names.items()
            ):

                if hf_split not in dataset:
                    print(
                        f"  WARNING: "
                        f"{language} has no "
                        f"{hf_split} split"
                    )
                    continue

                data = dataset[hf_split]

                output_file = (
                    language_dir
                    / f"{output_name}.tsv"
                )

                write_tsv(
                    data,
                    output_file,
                )

                print(
                    f"  {output_name:5s}: "
                    f"{len(data):,} examples -> "
                    f"{output_file}"
                )

        except Exception as e:

            print(
                f"  ERROR downloading "
                f"{language}: {e}"
            )

    print()
    print("Done.")
    print(
        f"Output directory: {output_dir}"
    )


if __name__ == "__main__":
    main()

