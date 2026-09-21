#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import load_dataset
from langcodes import Language


DATASET = "tasksource/mtop"


def iso639_3(language_code):
    """Convert an ISO language code/tag to ISO 639-3."""
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
    Write MTOP as:

        question<TAB>logical_form
    """

    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("question\tlogical_form\n")

        for row in dataset:

            question = clean_tsv_value(
                row.get("question", "")
            )

            logical_form = clean_tsv_value(
                row.get("logical_form", "")
            )

            f.write(
                f"{question}\t{logical_form}\n"
            )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download MTOP and convert each "
            "language to train/dev/test TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="mtop_tsv",
        help=(
            "Output directory "
            "(default: mtop_tsv)"
        ),
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional ISO-639-1 language codes. "
            "Examples: en de fr"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # MTOP contains all languages in one dataset configuration.
    # The language is stored in the "lang" field.
    # ---------------------------------------------------------------

    print(
        f"Downloading {DATASET}..."
    )

    dataset = load_dataset(DATASET)

    # The source dataset uses:
    #   train
    #   validation
    #   test
    #
    # We expose validation as "dev" in the output.

    split_names = {
        "train": "train",
        "validation": "dev",
        "test": "test",
    }

    # ---------------------------------------------------------------
    # Determine which languages are present.
    # ---------------------------------------------------------------

    available_languages = set()

    for split in dataset.values():

        if "lang" not in split.column_names:
            raise ValueError(
                "Expected MTOP dataset to contain "
                "a 'lang' column."
            )

        available_languages.update(
            split.unique("lang")
        )

    print(
        "Languages found in dataset:"
    )

    for language in sorted(available_languages):
        # MTOP uses language-region identifiers such as
        # en_XX, de_XX, etc.
        base_language = language.split("_")[0]

        try:
            iso3 = iso639_3(base_language)
        except ValueError:
            iso3 = "UNKNOWN"

        print(
            f"  {language:6s} -> {iso3}"
        )

    # ---------------------------------------------------------------
    # Optional language selection.
    # ---------------------------------------------------------------

    if args.languages:

        requested = set(
            language.lower()
            for language in args.languages
        )

        # Allow either:
        #
        #   en
        #   de
        #
        # or the actual MTOP identifiers:
        #
        #   en_XX
        #   de_XX
        #
        requested_full = set()

        for language in requested:

            if language in available_languages:
                requested_full.add(language)
                continue

            matches = [
                available
                for available in available_languages
                if available.split("_")[0] == language
            ]

            if not matches:
                raise ValueError(
                    f"Unknown MTOP language: {language}\n\n"
                    f"Available languages:\n"
                    + "\n".join(
                        sorted(available_languages)
                    )
                )

            requested_full.update(matches)

        available_languages = requested_full

    # ---------------------------------------------------------------
    # Convert each language separately.
    # ---------------------------------------------------------------

    for language in sorted(
        available_languages
    ):

        base_language = language.split("_")[0]
        iso_code = iso639_3(base_language)

        print(
            f"\n{language} -> {iso_code}"
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
                    f"  {output_name:5s}: "
                    f"not available"
                )
                continue

            # Filter the split to the selected language.
            data = dataset[hf_split].filter(
                lambda row: row["lang"] == language
            )

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

    print()
    print("Done.")
    print(
        f"Output directory: {output_dir}"
    )


if __name__ == "__main__":
    main()

