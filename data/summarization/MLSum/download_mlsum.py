#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from langcodes import Language


DATASET = "reciTAL/mlsum"


# MLSUM uses "tu" for Turkish in its configuration name.
# langcodes does not interpret "tu" as Turkish, so normalize
# this one dataset-specific name before ISO-639-3 conversion.
LANGUAGE_NORMALIZATION = {
    "tu": "tr",
}


def iso639_3(language_code):
    """
    Convert a language code/tag to ISO 639-3.

    Examples:
        de -> deu
        es -> spa
        fr -> fra
        ru -> rus
        tr -> tur
    """
    language_code = LANGUAGE_NORMALIZATION.get(
        language_code,
        language_code,
    )

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

    # Keep one example on exactly one TSV line.
    value = value.replace("\t", " ")
    value = value.replace("\r\n", " ")
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    return value.strip()


def write_tsv(dataset, output_file):
    """
    Write:

        text<TAB>summary
    """
    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("text\tsummary\n")

        for row in dataset:

            text = clean_tsv_value(
                row.get("text", "")
            )

            summary = clean_tsv_value(
                row.get("summary", "")
            )

            f.write(
                f"{text}\t{summary}\n"
            )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download MLSUM and convert each "
            "language to train/dev/test TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="mlsum_tsv",
        help=(
            "Output directory "
            "(default: mlsum_tsv)"
        ),
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional MLSUM language configurations. "
            "Examples: de fr es ru tu"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Discover configurations from Hugging Face
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
        print(f"  {language}")

    # ---------------------------------------------------------------
    # Optional language selection
    # ---------------------------------------------------------------

    if args.languages:

        requested = set(args.languages)
        available = set(languages)

        unknown = requested - available

        if unknown:
            raise ValueError(
                "Unknown MLSUM language(s):\n"
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
    # HF split -> our split names
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

