#!/usr/bin/env python3

import argparse
from pathlib import Path

from datasets import load_dataset
from langcodes import Language


# Hugging Face dataset
DATASET = "khalidalt/tydiqa-goldp"


def iso639_3(language_code):
    """
    Convert an ISO 639-1/2/BCP-47 language code to ISO 639-3.

    Examples:
        en -> eng
        fi -> fin
        id -> ind
        sw -> swa
        te -> tel
    """
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
    #value = value.replace("\t", " ")
    #value = value.replace("\r\n", " ")
    #value = value.replace("\n", " ")
    #value = value.replace("\r", " ")
    value = value.replace("\t", "\\t")
    value = value.replace("\r\n", "\\r\\n")
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")


    return value.strip()


def extract_answer(row):
    """
    Extract the first gold answer.

    TyDi QA GoldP stores answers as:
        {
            "text": [...],
            "answer_start": [...]
        }

    Some examples may contain multiple annotations.
    For a simple seq2seq TSV, we use the first answer.
    """
    answers = row.get("answers")

    if not answers:
        return ""

    texts = answers.get("text", [])

    if not texts:
        return ""

    return texts[0]


def write_tsv(dataset, output_file):
    """
    Write:

        context<TAB>question<TAB>answer
    """
    with open(
        output_file,
        "w",
        encoding="utf-8",
        newline="",
    ) as f:

        f.write("context\tquestion\tanswer\n")

        for row in dataset:

            context = clean_tsv_value(
                row.get("context", "")
            )

            question = clean_tsv_value(
                row.get("question", "")
            )

            answer = clean_tsv_value(
                extract_answer(row)
            )

            f.write(
                f"{context}\t{question}\t{answer}\n"
            )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Download TyDi QA GoldP and convert "
            "it to per-language TSV files."
        )
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="tydiqa_tsv",
        help=(
            "Output directory "
            "(default: tydiqa_tsv)"
        ),
    )

    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help=(
            "Optional languages to download. "
            "Examples: english finnish arabic"
        ),
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------
    # TyDi QA GoldP language configurations
    # ------------------------------------------------------------------

    languages = [
        "arabic",
        "bengali",
        "english",
        "finnish",
        "indonesian",
        "japanese",
        "korean",
        "russian",
        "swahili",
        "telugu",
        "thai",
    ]

    # Human-readable dataset names -> ISO 639-1 codes
    #
    # These are dataset-specific names, so this is a small normalization
    # layer rather than a giant ISO-code dictionary.
    language_codes = {
        "arabic": "ar",
        "bengali": "bn",
        "english": "en",
        "finnish": "fi",
        "indonesian": "id",
        "japanese": "ja",
        "korean": "ko",
        "russian": "ru",
        "swahili": "sw",
        "telugu": "te",
        "thai": "th",
    }

    # ------------------------------------------------------------------
    # Optional language selection
    # ------------------------------------------------------------------

    if args.languages:

        requested = set(args.languages)

        unknown = requested - set(languages)

        if unknown:
            raise ValueError(
                "Unknown TyDi QA language(s):\n"
                + "\n".join(sorted(unknown))
                + "\n\nAvailable languages:\n"
                + "\n".join(languages)
            )

        languages = [
            language
            for language in languages
            if language in requested
        ]

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    for i, language in enumerate(
        languages,
        start=1,
    ):

        iso_code = iso639_3(
            language_codes[language]
        )

        print(
            f"[{i}/{len(languages)}] "
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

            # HF "validation" becomes our "dev".
            split_names = {
                "train": "train",
                "validation": "dev",
            }

            for hf_split, output_name in (
                split_names.items()
            ):

                if hf_split not in dataset:
                    print(
                        f"  WARNING: "
                        f"no {hf_split} split"
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

