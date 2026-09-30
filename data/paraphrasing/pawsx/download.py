from pathlib import Path

from datasets import load_dataset
from langcodes import Language


DATASET = "google-research-datasets/paws-x"
OUTPUT_DIR = Path("pawsx_tsv")

# PAWS-X language codes -> ISO-639-3
LANGUAGES = {
    "en": "eng",
    "de": "deu",
    "es": "spa",
    "fr": "fra",
    "zh": "zho",
    "ja": "jpn",
    "ko": "kor",
}


def iso3(language):
    """Convert an ISO-639-1 code to ISO-639-3."""
    return Language.get(language).to_alpha3()


def clean(text):
    return (
        str(text)
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


for lang in LANGUAGES:
    lang3 = iso3(lang)

    print(f"Loading {lang} -> {lang3}...")

    # PAWS-X has one configuration per language.
    dataset = load_dataset(
        DATASET,
        name=lang,
    )

    output_dir = OUTPUT_DIR / lang3
    output_dir.mkdir(parents=True, exist_ok=True)

    for split_name, split in dataset.items():

        # Keep the standard train/dev/test naming.
        if split_name == "validation":
            split_name = "dev"

        output_file = output_dir / f"{split_name}.tsv"

        with output_file.open("w", encoding="utf-8") as f:
            f.write("id\tsource\ttarget\tlabel\n")

            for row in split:
                f.write(
                    f"{clean(row['id'])}\t"
                    f"{clean(row['sentence1'])}\t"
                    f"{clean(row['sentence2'])}\t"
                    f"{row['label']}\n"
                )

        print(
            f"  ✓ {output_file} "
            f"({len(split):,} examples)"
        )

print("\nDone.")

