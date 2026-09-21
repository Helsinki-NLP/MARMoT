#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import get_dataset_config_names, load_dataset


DATASET = "csebuetnlp/xlsum"

FIELDS = ["id", "text", "summary"]


# XL-Sum language configuration -> ISO 639-3 code


LANGUAGE_CODES = {
    "amharic": "amh",
    "arabic": "ara",
    "azerbaijani": "aze",
    "bengali": "ben",
    "burmese": "mya",
    "chinese_simplified": "zho_Hans",
    "chinese_traditional": "zho_Hant",
    "croatian": "hrv",
    "czech": "ces",
    "dutch": "nld",
    "english": "eng",
    "estonian": "est",
    "finnish": "fin",
    "french": "fra",
    "georgian": "kat",
    "german": "deu",
    "greek": "ell",
    "gujarati": "guj",
    "hausa": "hau",
    "hebrew": "heb",
    "hindi": "hin",
    "hungarian": "hun",
    "icelandic": "isl",
    "igbo": "ibo",
    "indonesian": "ind",
    "italian": "ita",
    "japanese": "jpn",
    "kannada": "kan",
    "kirundi": "run",
    "korean": "kor",
    "kyrgyz": "kir",
    "marathi": "mar",
    "nepali": "nep",
    "norwegian": "nor",
    "oromo": "orm",
    "pashto": "pus",
    "persian": "fas",
    "pidgin": "pcm",
    "polish": "pol",
    "portuguese": "por",
    "punjabi": "pan",
    "romanian": "ron",
    "russian": "rus",
    "scottish_gaelic": "gla",
    "serbian_cyrillic": "srp_Cyrl",
    "serbian_latin": "srp_Latn",
    "sinhala": "sin",
    "slovak": "slk",
    "slovenian": "slv",
    "somali": "som",
    "spanish": "spa",
    "swahili": "swa",
    "swedish": "swe",
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
    """Write a Hugging Face split to TSV."""
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(FIELDS) + "\n")

        for row in dataset:
            values = [
                clean_tsv_value(row[field])
                for field in FIELDS
            ]
            f.write("\t".join(values) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Download all XL-Sum languages and convert "
            "them to TSV using ISO-639-3 directories."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="xlsum_tsv",
        help="Output directory (default: xlsum_tsv)",
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional list of XL-Sum language configs to download. "
            "If omitted, download all languages."
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Getting XL-Sum language configurations "
        f"from {DATASET}..."
    )

    languages = get_dataset_config_names(DATASET)

    # Check that every available XL-Sum configuration
    # has an ISO-639-3 mapping.
    missing_codes = [
        lang for lang in languages
        if lang not in LANGUAGE_CODES
    ]

    if missing_codes:
        raise ValueError(
            "No ISO-639-3 code defined for:\n"
            + "\n".join(sorted(missing_codes))
        )

    if args.languages:
        requested = set(args.languages)

        unknown = requested - set(languages)

        if unknown:
            raise ValueError(
                "Unknown XL-Sum language(s): "
                + ", ".join(sorted(unknown))
                + "\n\nAvailable languages:\n"
                + "\n".join(sorted(languages))
            )

        languages = [
            lang for lang in languages
            if lang in requested
        ]

    print(f"Found {len(languages)} language(s).")
    print()

    for i, language in enumerate(languages, start=1):
        iso_code = LANGUAGE_CODES[language]

        print(
            f"[{i}/{len(languages)}] "
            f"Downloading {language} ({iso_code})..."
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

            split_names = {
                "train": "train",
                "validation": "dev",
                "test": "test",
            }

            for hf_split, output_name in split_names.items():

                if hf_split not in dataset:
                    print(
                        f"  WARNING: {language} has no "
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
                f"  ERROR downloading {language}: {e}"
            )

    print()
    print("Done.")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()

