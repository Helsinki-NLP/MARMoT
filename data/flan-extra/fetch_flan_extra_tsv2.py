from pathlib import Path
from urllib.request import urlopen, Request
import json
import ast

from datasets import load_dataset
from langcodes import Language


OUT_ROOT = Path("extra_tsv")


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def clean_text(x):
    if x is None:
        return ""

    if isinstance(x, str):
        return " ".join(x.replace("\t", " ").replace("\n", " ").split())

    return " ".join(str(x).replace("\t", " ").replace("\n", " ").split())


def iso3(lang):
    """Convert an ISO-639-1/BCP-47 language code to ISO-639-3."""
    try:
        return Language.get(lang).to_alpha3()
    except Exception:
        return lang


def write_tsv(rows, path, columns):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        f.write("\t".join(columns) + "\n")

        for row in rows:
            values = [clean_text(row.get(col, "")) for col in columns]
            f.write("\t".join(values) + "\n")


def answer_text(value):
    """
    Normalize answer fields that may be:
      - a string
      - a list of strings
      - a dict containing 'text'
      - a dict/list serialized as a string
    """
    if value is None:
        return ""

    if isinstance(value, str):
        value = value.strip()

        # Try to decode serialized Python/JSON structures.
        if value.startswith("[") or value.startswith("{"):
            try:
                value = json.loads(value)
            except Exception:
                try:
                    value = ast.literal_eval(value)
                except Exception:
                    return clean_text(value)

        if isinstance(value, str):
            return clean_text(value)

    if isinstance(value, dict):
        if "text" in value:
            return answer_text(value["text"])
        if "answer" in value:
            return answer_text(value["answer"])

    if isinstance(value, (list, tuple)):
        for item in value:
            text = answer_text(item)
            if text:
                return text

    return clean_text(value)


# ---------------------------------------------------------------------
# XOR-TyDi QA
#
# The HF repository contains Parquet files under:
#   xor-retrieve/{train,validation,test}/
#   xor-full/{train,validation,test}/
#
# We load these directly instead of invoking the legacy dataset script.
# ---------------------------------------------------------------------

def load_xor_config(config):
    splits = {}

    for split in ["train", "validation", "test"]:
        url = (
            "https://huggingface.co/datasets/"
            f"akariasai/xor_tydi_qa/resolve/main/"
            f"{config}/{split}/0000.parquet"
        )

        splits[split] = load_dataset(
            "parquet",
            data_files={split: url},
        )[split]

    return splits



def download_jsonl(url):
    """
    Download and parse a JSONL file directly.

    We intentionally bypass Hugging Face's legacy dataset loader because
    XOR-TyDi QA's current HF repository uses the old Python loading script.
    """
    print(f"    Downloading: {url}")

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    with urlopen(request) as response:
        data = response.read().decode("utf-8")

    return [
        json.loads(line)
        for line in data.splitlines()
        if line.strip()
    ]


def process_xor_tydi():
    print("\n=== XOR-TyDi QA ===")

    # These are the actual source URLs used by the official
    # Hugging Face dataset loading script.
    configs = {
        "xor-retrieve": {
            "train": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_train_retrieve_eng_span.jsonl"
            ),
            "dev": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_dev_retrieve_eng_span_v1_1.jsonl"
            ),
            "test": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_test_retrieve_eng_span_q_only_v1_1.jsonl"
            ),
        },

        "xor-full": {
            "train": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_train_full.jsonl"
            ),
            "dev": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_dev_full_v1_1.jsonl"
            ),
            "test": (
                "https://nlp.cs.washington.edu/xorqa/"
                "XORQA_site/data/"
                "xor_test_full_q_only_v1_1.jsonl"
            ),
        },
    }

    for config, split_urls in configs.items():
        print(f"\nLoading {config}...")

        for split, url in split_urls.items():
            try:
                data = download_jsonl(url)
            except Exception as e:
                print(f"  FAILED {split}: {e}")
                continue

            # Group examples by question language.
            by_language = {}

            for row in data:
                lang = row.get("lang", "").strip()

                if not lang:
                    continue

                by_language.setdefault(lang, []).append(row)

            for lang, rows in sorted(by_language.items()):
                lang3 = iso3(lang)

                # Keep the two XOR tasks separate.
                if config == "xor-retrieve":
                    dataset_dir = "xor_tydi_qa_retrieve"
                else:
                    dataset_dir = "xor_tydi_qa"

                out_dir = (
                    OUT_ROOT
                    / dataset_dir
                    / lang3
                )

                out_file = (
                    out_dir
                    / f"{split}.tsv"
                )

                output_rows = []

                for row in rows:
                    question = row.get("question", "")

                    answers = row.get("answers", "")

                    # The official HF loader converts the answer list
                    # into one space-separated string.
                    if isinstance(answers, list):
                        answer = " ".join(
                            str(x) for x in answers
                        )
                    else:
                        answer = str(answers)

                    # Test files contain questions only.
                    # The official loader represents their answer as
                    # "None", so preserve that behavior.
                    if split == "test":
                        answer = "None"

                    output_rows.append({
                        "question": question,
                        "answer": answer,
                    })

                write_tsv(
                    output_rows,
                    out_file,
                    ["question", "answer"],
                )

                print(
                    f"  ✓ {config}/{split}/{lang} -> "
                    f"{out_file} "
                    f"({len(output_rows):,})"
                )

    print("\nXOR-TyDi QA complete.")

# ---------------------------------------------------------------------
# WebNLG
#
# WebNLG currently uses a legacy loader. Explicit configs are required
# because the repository contains multiple language/config variants.
#
# We use the high-level Hugging Face loader here rather than trying to
# interpret the raw nested WebNLG JSON ourselves.
# ---------------------------------------------------------------------

def process_webnlg():
    print("\n=== WebNLG ===")

    # WebNLG v3 contains English and Russian.
    configs = {
        "en": "eng",
        "ru": "rus",
    }

    for config, lang3 in configs.items():
        print(f"Loading WebNLG config={config}...")

        try:
            ds = load_dataset(
                "GEM/web_nlg",
                name=config,
                trust_remote_code=True,
            )
        except Exception as e:
            print(f"  FAILED config={config}: {e}")
            continue

        for split_name, split_ds in ds.items():
            # GEM uses train/validation/test.
            out_split = (
                "dev" if split_name in {"validation", "dev"} else split_name
            )

            rows = []

            for row in split_ds:
                # Current GEM representation:
                #   input = list of triples
                #   target = lexicalized text
                #
                # Older/alternate representations can expose an "entry"
                # field, so handle both.

                target = row.get("target", "")

                if not target:
                    continue

                source = row.get("input", "")

                if isinstance(source, list):
                    triples = []

                    for triple in source:
                        if isinstance(triple, dict):
                            s = triple.get("subject", "")
                            p = triple.get("property", "")
                            o = triple.get("object", "")
                            triples.append(
                                f"{s} | {p} | {o}"
                            )
                        else:
                            triples.append(str(triple))

                    source = " ; ".join(triples)

                rows.append({
                    "source": source,
                    "target": target,
                })

            out_dir = OUT_ROOT / "webnlg_tsv" / lang3
            out_file = out_dir / f"{out_split}.tsv"

            write_tsv(
                rows,
                out_file,
                ["source", "target"],
            )

            print(
                f"  ✓ {config}/{split_name} -> "
                f"{out_file} ({len(rows):,})"
            )


# ---------------------------------------------------------------------
# DuoRC
#
# The repository now has two explicit configs:
#   ParaphraseRC
#   SelfRC
#
# It is Parquet-backed, so load the config explicitly.
# ---------------------------------------------------------------------

def process_duorc():
    print("\n=== DuoRC ===")

    configs = [
        "ParaphraseRC",
        "SelfRC",
    ]

    for config in configs:
        print(f"Loading DuoRC config={config}...")

        try:
            ds = load_dataset(
                "ibm-research/duorc",
                name=config,
            )
        except Exception as e:
            print(f"  FAILED config={config}: {e}")
            continue

        # Keep the two DuoRC tasks separate.
        config_dir = config.lower()

        for split_name, split_ds in ds.items():
            out_split = (
                "dev" if split_name in {"validation", "dev"} else split_name
            )

            rows = []

            for row in split_ds:
                # DuoRC fields:
                # plot, title, question, answers, no_answer
                #
                # For seq2seq QA, use:
                #   plot + question -> answer

                plot = row.get("plot", "")
                question = row.get("question", "")
                answers = answer_text(row.get("answers", ""))

                # Skip explicit no-answer examples.
                if row.get("no_answer", False):
                    continue

                if not question or not answers:
                    continue

                rows.append({
                    "context": plot,
                    "question": question,
                    "answer": answers,
                })

            out_dir = OUT_ROOT / "duorc_tsv" / config_dir
            out_file = out_dir / f"{out_split}.tsv"

            write_tsv(
                rows,
                out_file,
                ["context", "question", "answer"],
            )

            print(
                f"  ✓ {config}/{split_name} -> "
                f"{out_file} ({len(rows):,})"
            )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

if __name__ == "__main__":
    process_xor_tydi()
    process_webnlg()
    process_duorc()

    print("\nDone.")

