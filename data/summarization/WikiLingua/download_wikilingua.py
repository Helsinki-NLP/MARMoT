#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from langcodes import Language


DATASET = "GEM/wiki_lingua"


def iso639_3(language_code):
    """
    Convert a language code/tag to ISO 639-3.

    Examples:
        en      -> eng
        fr      -> fra
        de      -> deu
        zh      -> zho
        pt      -> por
        id      -> ind
    """
    try:
        return Language.get(language_code).to_alpha3()
    except LookupError as e:
        raise ValueError(
            f"Could not convert language code {language_code!r} "
            f"to ISO 639-3"
        ) from e


def clean_tsv_value(value):
    """Make a value safe for a single TSV row."""
    if value is None:
        return ""

    value = str(value)
#    value = value.replace("\t", " ")
#    value = value.replace("\r\n", " ")
#    value = value.replace("\n", " ")
#    value = value.replace("\r", " ")
    value = value.replace("\t", "\\t")
    value = value.replace("\r\n", "\\r\\n")
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")

    return value.strip()


def write_tsv(dataset, output_file):
    """Write source/target pairs to TSV."""
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        f.write("source\ttarget\n")

        for row in dataset:
            source = clean_tsv_value(row["source"])
            target = clean_tsv_value(row["target"])

            f.write(f"{source}\t{target}\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download WikiLingua and convert each language "
            "to train/dev/test TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="wikilingua_tsv",
        help="Output directory (default: wikilingua_tsv)",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional list of WikiLingua language configurations. "
            "Example: en fr de es"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Discover available WikiLingua configurations
    # ------------------------------------------------------------------

    print(f"Getting configurations from {DATASET}...")

    languages = get_dataset_config_names(DATASET)

    print(f"Found {len(languages)} language configuration(s).")

    # ------------------------------------------------------------------
    # Optionally restrict languages
    # ------------------------------------------------------------------

    if args.languages:
        requested = set(args.languages)
        available = set(languages)

        unknown = requested - available

        if unknown:
            raise ValueError(
                "Unknown WikiLingua language(s):\n"
                + "\n".join(sorted(unknown))
                + "\n\nAvailable languages:\n"
                + "\n".join(sorted(languages))
            )

        languages = [
            language
            for language in languages
            if language in requested
        ]

    # ------------------------------------------------------------------
    # Convert HF split names to our preferred names
    # ------------------------------------------------------------------

    split_names = {
        "train": "train",
        "validation": "dev",
        "test": "test",
    }

    # ------------------------------------------------------------------
    # Download and convert
    # ------------------------------------------------------------------

    for i, language in enumerate(languages, start=1):

        iso_code = iso639_3(language)

        print(
            f"[{i}/{len(languages)}] "
            f"{language} -> {iso_code}"
        )

        try:
            dataset = load_dataset(
                DATASET,
                language,
            )

            language_dir = output_dir / iso_code
            language_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            for hf_split, output_name in split_names.items():

                if hf_split not in dataset:
                    print(
                        f"  WARNING: "
                        f"{language} has no {hf_split} split"
                    )
                    continue

                data = dataset[hf_split]

                output_file = (
                    language_dir / f"{output_name}.tsv"
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
                f"  ERROR downloading {language}: {e}"
            )

    print()
    print("Done.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
