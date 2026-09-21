#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset
from langcodes import Language


# ---------------------------------------------------------------------
# Dataset identifiers
# ---------------------------------------------------------------------

DATASETS = {
    "tapaco": "community-datasets/tapaco",
    "opusparcus": "GEM/opusparcus",
    "pawsx": "juletxara/pawsx_mt",
    # ParaBank2 and ParaNMT are handled separately below because
    # they are English-only resources in the versions we use.
    "parabank2": "parabank2",
    "paranmt": "paranmt",
}


# ---------------------------------------------------------------------
# Language conversion
# ---------------------------------------------------------------------

def iso639_3(language_code):
    """
    Convert a language code/tag to ISO 639-3.

    Examples:
        en -> eng
        de -> deu
        fi -> fin
        zh -> zho
    """
    try:
        return Language.get(language_code).to_alpha3()
    except LookupError as e:
        raise ValueError(
            f"Could not convert language code "
            f"{language_code!r} to ISO 639-3"
        ) from e


def language_to_iso3(language):
    """
    Try to extract a standard language code from a dataset
    configuration/language name.

    Handles examples such as:

        en
        en_US
        de
        fi
        french
        German

    Dataset-specific normalization can be added here if needed.
    """

    # First try the value directly.
    try:
        return iso639_3(language)
    except ValueError:
        pass

    # Then try the first part of identifiers such as en_US.
    base = language.split("_")[0]

    try:
        return iso639_3(base)
    except ValueError:
        pass

    # Finally try language names.
    try:
        return Language.find(language).to_alpha3()
    except LookupError:
        pass

    # A few common dataset-specific names.
    aliases = {
        "english": "eng",
        "german": "deu",
        "french": "fra",
        "finnish": "fin",
        "russian": "rus",
        "swedish": "swe",
        "spanish": "spa",
        "chinese": "zho",
        "japanese": "jpn",
        "korean": "kor",
    }

    if language.lower() in aliases:
        return aliases[language.lower()]

    raise ValueError(
        f"Could not determine ISO-639-3 code for "
        f"{language!r}"
    )


# ---------------------------------------------------------------------
# TSV utilities
# ---------------------------------------------------------------------

def clean_tsv_value(value):
    """Make a value safe for one TSV field."""

    if value is None:
        return ""

    value = str(value)

    value = value.replace("\t", " ")
    value = value.replace("\r\n", " ")
    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    return value.strip()


def write_pair_tsv(
    dataset,
    output_file,
    source_column,
    target_column,
):
    """
    Write:

        source<TAB>target
    """

    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("source\ttarget\n")

        for row in dataset:

            source = clean_tsv_value(
                row.get(source_column, "")
            )

            target = clean_tsv_value(
                row.get(target_column, "")
            )

            f.write(
                f"{source}\t{target}\n"
            )


def write_pawsx_tsv(
    dataset,
    output_file,
):
    """
    Write PAWS-X as:

        source<TAB>target<TAB>label
    """

    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("source\ttarget\tlabel\n")

        for row in dataset:

            source = clean_tsv_value(
                row.get("sentence1", "")
            )

            target = clean_tsv_value(
                row.get("sentence2", "")
            )

            label = clean_tsv_value(
                row.get("label", "")
            )

            f.write(
                f"{source}\t{target}\t{label}\n"
            )


# ---------------------------------------------------------------------
# TaPaCo
# ---------------------------------------------------------------------

def download_tapaco(output_dir):
    """
    Download TaPaCo.

    TaPaCo is language-configured. We discover the available
    configurations from Hugging Face and convert their language
    identifiers to ISO-639-3 directory names.
    """

    dataset_name = DATASETS["tapaco"]

    print()
    print("=" * 70)
    print("TaPaCo")
    print("=" * 70)

    configs = get_dataset_config_names(
        dataset_name
    )

    print(
        f"Found {len(configs)} configuration(s)."
    )

    for config in configs:

        try:
            iso_code = language_to_iso3(config)
        except ValueError:
            print(
                f"  WARNING: cannot determine ISO code "
                f"for {config!r}; skipping"
            )
            continue

        print(
            f"\n{config} -> {iso_code}"
        )

        try:

            dataset = load_dataset(
                dataset_name,
                config,
            )

            language_dir = (
                output_dir / "tapaco" / iso_code
            )

            language_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            for split in (
                "train",
                "validation",
                "test",
            ):

                if split not in dataset:
                    continue

                output_name = (
                    "dev"
                    if split == "validation"
                    else split
                )

                data = dataset[split]

                output_file = (
                    language_dir
                    / f"{output_name}.tsv"
                )

                # TaPaCo versions commonly expose
                # paraphrase pairs under different names.
                columns = set(
                    data.column_names
                )

                if {
                    "paraphrase",
                    "paraphrase2",
                }.issubset(columns):

                    source_column = "paraphrase"
                    target_column = "paraphrase2"

                elif {
                    "sentence1",
                    "sentence2",
                }.issubset(columns):

                    source_column = "sentence1"
                    target_column = "sentence2"

                elif {
                    "source",
                    "target",
                }.issubset(columns):

                    source_column = "source"
                    target_column = "target"

                else:
                    raise ValueError(
                        "Could not identify TaPaCo "
                        "sentence-pair columns. "
                        f"Available columns: "
                        f"{sorted(columns)}"
                    )

                write_pair_tsv(
                    data,
                    output_file,
                    source_column,
                    target_column,
                )

                print(
                    f"  {output_name:5s}: "
                    f"{len(data):,} -> "
                    f"{output_file}"
                )

        except Exception as e:

            print(
                f"  ERROR: {config}: {e}"
            )


# ---------------------------------------------------------------------
# Opusparcus
# ---------------------------------------------------------------------

def download_opusparcus(
    output_dir,
    quality,
):
    """
    Download Opusparcus.

    Opusparcus supports:
        de, en, fi, fr, ru, sv

    Training data is selected using the quality parameter.
    Higher quality = smaller/cleaner training set.
    """

    dataset_name = DATASETS["opusparcus"]

    print()
    print("=" * 70)
    print(
        f"Opusparcus "
        f"(training quality={quality})"
    )
    print("=" * 70)

    languages = [
        "de",
        "en",
        "fi",
        "fr",
        "ru",
        "sv",
    ]

    for language in languages:

        iso_code = iso639_3(language)

        print(
            f"\n{language} -> {iso_code}"
        )

        try:

            # The quality argument controls training data.
            dataset = load_dataset(
                dataset_name,
                lang=language,
                quality=quality,
            )

            language_dir = (
                output_dir
                / "opusparcus"
                / iso_code
            )

            language_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            split_names = {
                "train": "train",
                "validation": "dev",
                "test": "test",
            }

            for hf_split, output_name in (
                split_names.items()
            ):

                if hf_split not in dataset:
                    continue

                data = dataset[hf_split]

                output_file = (
                    language_dir
                    / f"{output_name}.tsv"
                )

                # GEM/Opusparcus exposes input/target.
                write_pair_tsv(
                    data,
                    output_file,
                    "input",
                    "target",
                )

                print(
                    f"  {output_name:5s}: "
                    f"{len(data):,} -> "
                    f"{output_file}"
                )

        except Exception as e:

            print(
                f"  ERROR: {language}: {e}"
            )


# ---------------------------------------------------------------------
# PAWS-X
# ---------------------------------------------------------------------

def download_pawsx(output_dir):
    """
    Download PAWS-X.

    PAWS-X has:
        en, fr, es, de, zh, ja, ko

    We retain the label because PAWS-X is a
    paraphrase-identification dataset.
    """

    dataset_name = DATASETS["pawsx"]

    print()
    print("=" * 70)
    print("PAWS-X")
    print("=" * 70)

    dataset = load_dataset(
        dataset_name
    )

    for split_name, data in dataset.items():

        # Some releases expose language-specific
        # validation/test splits, while others provide
        # language as a column. Handle both cases.

        if "lang" in data.column_names:

            languages = sorted(
                set(data.unique("lang"))
            )

            for language in languages:

                iso_code = iso639_3(
                    language
                )

                language_data = data.filter(
                    lambda row:
                    row["lang"] == language
                )

                language_dir = (
                    output_dir
                    / "pawsx"
                    / iso_code
                )

                language_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                output_name = (
                    "dev"
                    if split_name == "validation"
                    else split_name
                )

                output_file = (
                    language_dir
                    / f"{output_name}.tsv"
                )

                write_pawsx_tsv(
                    language_data,
                    output_file,
                )

                print(
                    f"{language} "
                    f"{output_name}: "
                    f"{len(language_data):,} -> "
                    f"{output_file}"
                )

        else:

            # Language-specific configuration.
            # Infer language from the configuration if possible.

            print(
                f"Processing PAWS-X split "
                f"{split_name}"
            )

            # This branch is mainly a fallback for
            # alternative HF packaging.
            #
            # If the dataset is configured differently,
            # inspect its configs and use the
            # --datasets/--configs mechanism below.

            if {
                "sentence1",
                "sentence2",
                "label",
            }.issubset(data.column_names):

                print(
                    "  WARNING: PAWS-X split has no "
                    "'lang' column; saving under eng/"
                )

                language_dir = (
                    output_dir
                    / "pawsx"
                    / "eng"
                )

                language_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                output_name = (
                    "dev"
                    if split_name == "validation"
                    else split_name
                )

                write_pawsx_tsv(
                    data,
                    language_dir
                    / f"{output_name}.tsv",
                )


# ---------------------------------------------------------------------
# English-only large-scale datasets
# ---------------------------------------------------------------------

def download_english_pair_dataset(
    dataset_name,
    source_column,
    target_column,
    output_dir,
    output_name,
):
    """
    Generic helper for English-only pair datasets.

    This is intentionally separated from the multilingual
    datasets because ParaNMT and ParaBank2 are English-English.
    """

    print()
    print("=" * 70)
    print(output_name)
    print("=" * 70)

    try:

        dataset = load_dataset(
            dataset_name
        )

        language_dir = (
            output_dir
            / output_name
            / "eng"
        )

        language_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for hf_split, data in dataset.items():

            output_split = (
                "dev"
                if hf_split == "validation"
                else hf_split
            )

            output_file = (
                language_dir
                / f"{output_split}.tsv"
            )

            write_pair_tsv(
                data,
                output_file,
                source_column,
                target_column,
            )

            print(
                f"  {output_split:5s}: "
                f"{len(data):,} -> "
                f"{output_file}"
            )

    except Exception as e:

        print(
            f"  ERROR loading {dataset_name}: "
            f"{e}"
        )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download and prepare multilingual "
            "paraphrase datasets."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="paraphrase_tsv",
        help=(
            "Output directory "
            "(default: paraphrase_tsv)"
        ),
    )

    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=[
            "tapaco",
            "opusparcus",
            "pawsx",
            "parabank2",
            "paranmt",
        ],
        default=[
            "tapaco",
            "opusparcus",
            "pawsx",
        ],
        help=(
            "Datasets to download. "
            "Default: tapaco opusparcus pawsx"
        ),
    )

    parser.add_argument(
        "--opusparcus-quality",
        type=int,
        choices=[
            60,
            65,
            70,
            75,
            80,
            85,
            90,
            95,
        ],
        default=90,
        help=(
            "Opusparcus training quality. "
            "Higher means smaller/cleaner data. "
            "Default: 90"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(
        args.output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for dataset_name in args.datasets:

        if dataset_name == "tapaco":
            download_tapaco(
                output_dir
            )

        elif dataset_name == "opusparcus":
            download_opusparcus(
                output_dir,
                args.opusparcus_quality,
            )

        elif dataset_name == "pawsx":
            download_pawsx(
                output_dir
            )

        elif dataset_name == "parabank2":

            # The exact HF packaging of ParaBank2 has
            # changed across releases. We intentionally
            # do not silently guess its columns here.
            #
            # Use a known local/HF version and adjust the
            # source/target column names if necessary.
            print()
            print(
                "ParaBank2 is an English-only resource. "
                "Its current packaging is not included "
                "in the default download because its "
                "Hugging Face dataset interface varies."
            )

        elif dataset_name == "paranmt":

            print()
            print(
                "ParaNMT is an English-only resource. "
                "Its full 50M-pair version is very large "
                "and is not downloaded by default."
            )

    print()
    print("=" * 70)
    print("Done.")
    print("=" * 70)
    print(
        f"Output directory: {output_dir}"
    )


if __name__ == "__main__":
    main()

