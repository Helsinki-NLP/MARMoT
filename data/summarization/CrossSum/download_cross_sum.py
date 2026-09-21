#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset


DATASET = "csebuetnlp/CrossSum"

# CrossSum language configuration -> ISO 639-3 code
LANGUAGE_CODES = {
    "amharic": "amh",
    "arabic": "ara",
    "azerbaijani": "aze",
    "bengali": "ben",
    "burmese": "mya",
    "chinese_simplified": "zho_Hans",
    "chinese_traditional": "zho_Hant",
    "english": "eng",
    "french": "fra",
    "georgian": "kat",
    "gujarati": "guj",
    "hausa": "hau",
    "hindi": "hin",
    "igbo": "ibo",
    "indonesian": "ind",
    "japanese": "jpn",
    "kirundi": "run",
    "korean": "kor",
    "kyrgyz": "kir",
    "marathi": "mar",
    "nepali": "nep",
    "oromo": "orm",
    "pashto": "pus",
    "persian": "fas",
    "pidgin": "pcm",
    "portuguese": "por",
    "punjabi": "pan",
    "russian": "rus",
    "scottish_gaelic": "gla",
    "serbian_cyrillic": "srp_Cyrl",
    "serbian_latin": "srp_Latn",
    "sinhala": "sin",
    "somali": "som",
    "spanish": "spa",
    "swahili": "swa",
    "tamil": "tam",
    "telugu": "tel",
    "thai": "tha",
    "tigrinya": "tir",
    "turkish": "tur",
    "ukrainian": "ukr",
    "urdu": "urd",
    "uzbek": "uzb",
    "vietnamese": "vie",
    "welsh": "cym",
    "yoruba": "yor",
}


def short_code(language):
    """
    Return a directory-safe language code.
    """
    
    return LANGUAGE_CODES[language]


def clean_tsv_value(value):
    """Keep each example on one TSV line."""
    if value is None:
        return ""

    value = str(value)

    #value = value.replace("\t", " ")
    #value = value.replace("\r\n", " ")
    #value = value.replace("\n", " ")
    #value = value.replace("\r", " ")
    value = value.replace("\t", "\\t")
    value = value.replace("\r\n", "\\r\\n")
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")


    return value.strip()


def write_tsv(dataset, output_file):
    """
    Write CrossSum data as:

        text<TAB>summary
    """
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        f.write("text\tsummary\n")

        for row in dataset:
            text = clean_tsv_value(row["text"])
            summary = clean_tsv_value(row["summary"])

            f.write(f"{text}\t{summary}\n")


def parse_pair(pair):
    """
    Convert a pair such as:

        english-finnish

    into:

        ("english", "finnish")
    """
    parts = pair.split("-", 1)

    if len(parts) != 2:
        raise ValueError(
            f"Invalid language pair: {pair}\n"
            "Expected format: source-target"
        )

    return parts[0], parts[1]


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download CrossSum language pairs and convert "
            "them to TSV."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="crosssum_tsv",
        help="Output directory (default: crosssum_tsv)",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Download all language pairs involving these "
            "languages. Example: english finnish french"
        ),
    )

    parser.add_argument(
        "--pairs",
        nargs="+",
        default=None,
        help=(
            "Download specific language pairs. "
            "Example: english-finnish english-french "
            "french-german"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Getting CrossSum configurations "
        f"from {DATASET}..."
    )

    # CrossSum defines one HF configuration per
    # source-target language pair.
    configs = get_dataset_config_names(DATASET)

    print(f"Found {len(configs):,} language-pair configurations.")

    # Extract languages from configuration names.
    languages = set()

    for config in configs:
        src, tgt = parse_pair(config)
        languages.add(src)
        languages.add(tgt)

    # Validate our ISO mapping.
    missing_codes = [
        lang for lang in languages
        if lang not in LANGUAGE_CODES
    ]

    if missing_codes:
        raise ValueError(
            "No ISO-639-3 code defined for:\n"
            + "\n".join(sorted(missing_codes))
        )

    # --------------------------------------------------
    # Select language pairs
    # --------------------------------------------------

    selected = None

    if args.pairs:
        selected = set(args.pairs)

        unknown = selected - set(configs)

        if unknown:
            raise ValueError(
                "Unknown CrossSum language pair(s):\n"
                + "\n".join(sorted(unknown))
            )

    elif args.languages:
        requested = set(args.languages)

        unknown = requested - languages

        if unknown:
            raise ValueError(
                "Unknown CrossSum language(s):\n"
                + "\n".join(sorted(unknown))
                + "\n\nAvailable languages:\n"
                + "\n".join(sorted(languages))
            )

        selected = set()

        for config in configs:
            src, tgt = parse_pair(config)

            if src in requested or tgt in requested:
                selected.add(config)

    else:
        # No filter: download everything.
        selected = set(configs)

    selected = [
        config
        for config in configs
        if config in selected
    ]

    print(
        f"Selected {len(selected):,} "
        f"language-pair configurations."
    )
    print()

    # --------------------------------------------------
    # Download
    # --------------------------------------------------

    split_names = {
        "train": "train",
        "validation": "dev",
        "test": "test",
    }

    for i, pair in enumerate(selected, start=1):

        src_lang, tgt_lang = parse_pair(pair)

        src_code = short_code(src_lang)
        tgt_code = short_code(tgt_lang)

        # Directory structure:
        #
        # crosssum_tsv/
        #   eng/
        #     fin/
        #       train.tsv
        #       dev.tsv
        #       test.tsv
        #
        pair_dir = (
            output_dir
            / src_code
            / tgt_code
        )

        print(
            f"[{i}/{len(selected)}] "
            f"{src_lang} -> {tgt_lang}"
        )

        try:
            dataset = load_dataset(
                DATASET,
                pair,
            )

            pair_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            for hf_split, output_name in split_names.items():

                if hf_split not in dataset:
                    print(
                        f"  WARNING: no {hf_split} split"
                    )
                    continue

                data = dataset[hf_split]

                output_file = (
                    pair_dir
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
                f"  ERROR: {pair}: {e}"
            )

    print()
    print("Done.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()

