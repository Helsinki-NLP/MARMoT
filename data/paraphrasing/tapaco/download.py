from collections import defaultdict
from pathlib import Path

from datasets import load_dataset
from langcodes import Language


DATASET = "community-datasets/tapaco"
OUTPUT_DIR = Path("tapaco_tsv")


def iso3(language):
    """Convert TaPaCo's ISO-639-1 language code to ISO-639-3."""
    try:
        lang3 = Language.get(language).to_alpha3()
    except:
        lang3 = language
    return lang3


def clean(text):
    return " ".join(
        str(text)
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\n", " ")
        .split()
    )


print("Downloading TaPaCo...")
dataset = load_dataset(DATASET, split="train")

print(f"Loaded {len(dataset):,} sentences.")


# ---------------------------------------------------------------------
# Group sentences by:
#
#   language
#       └── paraphrase_set_id
#               ├── sentence 1
#               ├── sentence 2
#               └── ...
#
# TaPaCo defines all sentences within one paraphrase_set_id as
# paraphrases of one another.
# ---------------------------------------------------------------------

groups = defaultdict(lambda: defaultdict(list))

for row in dataset:
    language = row["language"]
    set_id = str(row["paraphrase_set_id"])
    sentence = clean(row["paraphrase"])

    if not sentence:
        continue

    groups[language][set_id].append(sentence)


# ---------------------------------------------------------------------
# Write one TSV per language.
#
# We generate both directions:
#
#   A -> B
#   B -> A
#
# for every pair in a paraphrase set.
# ---------------------------------------------------------------------

for language in sorted(groups):
    lang3 = iso3(language)

    output_dir = OUTPUT_DIR / lang3
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "train.tsv"

    pair_count = 0
    set_count = 0

    with output_file.open("w", encoding="utf-8") as f:
        f.write("set_id\tsource\ttarget\n")

        for set_id, sentences in groups[language].items():

            # Remove duplicate sentences while preserving order.
            sentences = list(dict.fromkeys(sentences))

            # A set needs at least two distinct sentences to form
            # a paraphrase pair.
            if len(sentences) < 2:
                continue

            set_count += 1

            # Generate all ordered pairs.
            for i, source in enumerate(sentences):
                for j, target in enumerate(sentences):

                    if i == j:
                        continue

                    f.write(
                        f"{set_id}\t"
                        f"{source}\t"
                        f"{target}\n"
                    )

                    pair_count += 1

    print(
        f"{language:>5} -> {lang3:>3} | "
        f"{set_count:,} sets | "
        f"{pair_count:,} pairs | "
        f"{output_file}"
    )

print("\nDone.")

