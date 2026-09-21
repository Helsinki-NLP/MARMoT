#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from langcodes import Language


DATASET = "QCRI/MultiNativQA"


def iso639_3(language_code):
    """Convert an ISO language code/tag to ISO 639-3."""
    try:
        return Language.get(language_code).to_alpha3()
    except LookupError as e:
        raise ValueError(
            f"Could not convert language code "
            f"{language_code!r} to ISO 639-3"
        ) from e


def config_to_iso3(config_name):
    """
    Convert a MultiNativQA configuration name to an
    ISO-639-3-based directory name.

    Examples:
        arabic_qa  -> ara
        assamese_in -> asm
        bangla_bd -> ben-bd
        bangla_in -> ben-in
        english_bd -> eng-bd
        english_qa -> eng-qa
        hindi_in -> hin
        nepali_np -> nep
        turkish_tr -> tur

    The regional suffix is retained for configurations where
    multiple datasets exist for the same language.
    """

    # MultiNativQA configuration -> ISO-639-1
    language_codes = {
        "arabic_qa": "ar",
        "assamese_in": "as",
        "bangla_bd": "bn",
        "bangla_in": "bn",
        "english_bd": "en",
        "english_qa": "en",
        "hindi_in": "hi",
        "nepali_np": "ne",
        "turkish_tr": "tr",
    }

    if config_name not in language_codes:
        raise ValueError(
            f"No language normalization defined for "
            f"MultiNativQA configuration {config_name!r}"
        )

    iso3 = iso639_3(
        language_codes[config_name]
    )

    # Keep the geographic distinction where the same
    # language occurs in multiple configurations.
    regional_configs = {
        "bangla_bd": f"{iso3}-bd",
        "bangla_in": f"{iso3}-in",
        "english_bd": f"{iso3}-bd",
        "english_qa": f"{iso3}-qa",
    }

    return regional_configs.get(
        config_name,
        iso3,
    )


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
                row.get("answer", "")
            )

            f.write(
                f"{question}\t{answer}\n"
            )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download MultiNativQA and convert "
            "each configuration to train/dev/test TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="multinativqa_tsv",
        help=(
            "Output directory "
            "(default: multinativqa_tsv)"
        ),
    )

    parser.add_argument(
        "--configs",
        nargs="+",
        default=None,
        help=(
            "Optional MultiNativQA configurations. "
            "Examples: arabic_qa bangla_bd english_qa"
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

    configs = get_dataset_config_names(
        DATASET
    )

    print(
        f"Found {len(configs)} "
        f"configuration(s):"
    )

    for config in configs:
        print(
            f"  {config:15s} -> "
            f"{config_to_iso3(config)}"
        )

    # ---------------------------------------------------------------
    # Optional configuration selection
    # ---------------------------------------------------------------

    if args.configs:

        requested = set(args.configs)
        available = set(configs)

        unknown = requested - available

        if unknown:
            raise ValueError(
                "Unknown MultiNativQA configuration(s):\n"
                + "\n".join(sorted(unknown))
                + "\n\nAvailable configurations:\n"
                + "\n".join(sorted(configs))
            )

        configs = [
            config
            for config in configs
            if config in requested
        ]

    # ---------------------------------------------------------------
    # Download and convert
    # ---------------------------------------------------------------

    for i, config in enumerate(
        configs,
        start=1,
    ):

        output_code = config_to_iso3(
            config
        )

        print(
            f"\n[{i}/{len(configs)}] "
            f"{config} -> {output_code}"
        )

        try:

            dataset = load_dataset(
                DATASET,
                name=config,
            )

            language_dir = (
                output_dir / output_code
            )

            language_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            # MultiNativQA already uses "dev", unlike
            # datasets that call the split "validation".
            split_names = {
                "train": "train",
                "dev": "dev",
                "test": "test",
            }

            for hf_split, output_name in (
                split_names.items()
            ):

                if hf_split not in dataset:
                    print(
                        f"  {output_name:5s}: "
                        f"not available"
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
                f"{config}: {e}"
            )

    print()
    print("Done.")
    print(
        f"Output directory: {output_dir}"
    )


if __name__ == "__main__":
    main()

