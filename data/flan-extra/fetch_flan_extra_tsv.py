"""
Robust downloader for selected Tier-1 and Tier-2 NLP datasets.

Output structure:

    extra_tsv/
        wikilarge/
            eng/
                train.tsv
                dev.tsv
                test.tsv

        wiki_split/
            eng/
                train.tsv
                dev.tsv
                test.tsv

        tydiqa/
            ara/
                train.tsv
                dev.tsv
                test.tsv
            ...

        mkqa/
            eng/
                train.tsv
            deu/
                train.tsv
            ...

        xor_tydiqa/
            fin/
                train.tsv
                dev.tsv
                test.tsv
            ...

        ...

This version deliberately avoids relying on legacy Hugging Face dataset
scripts whenever possible.

Install:

    pip install -U datasets huggingface_hub langcodes pandas requests

No machine-translation datasets are included.
"""

from pathlib import Path
import gzip
import json
import re
import tempfile

import langcodes
import pandas as pd
import requests

from datasets import load_dataset
from huggingface_hub import hf_hub_download


OUTPUT_DIR = Path("extra_tsv")


# =====================================================================
# Utilities
# =====================================================================

def clean_text(value):
    """Convert a value into a TSV-safe string."""

    if value is None:
        return ""

    if isinstance(value, (list, tuple)):
        value = " || ".join(clean_text(x) for x in value)

    elif isinstance(value, dict):
        value = json.dumps(
            value,
            ensure_ascii=False,
        )

    else:
        value = str(value)

    value = value.replace("\t", " ")
    value = value.replace("\r", " ")
    value = value.replace("\n", " ")

    return re.sub(r"\s+", " ", value).strip()


def iso3(language):
    """
    Convert an ISO-639-1 / BCP-47 language identifier to ISO-639-3.

    Examples:

        en -> eng
        de -> deu
        fi -> fin
        zh_cn -> zho

    Script/region suffixes are ignored for the ISO-639-3 directory.
    """

    language = str(language).strip()

    language = language.replace("_", "-")

    aliases = {
        "english": "en",
        "german": "de",
        "french": "fr",
        "spanish": "es",
        "italian": "it",
        "portuguese": "pt",
        "russian": "ru",
        "arabic": "ar",
        "bengali": "bn",
        "finnish": "fi",
        "indonesian": "id",
        "japanese": "ja",
        "korean": "ko",
        "swahili": "sw",
        "telugu": "te",
        "thai": "th",
        "danish": "da",
        "dutch": "nl",
        "polish": "pl",
        "turkish": "tr",
        "vietnamese": "vi",
        "hebrew": "he",
        "hungarian": "hu",
        "norwegian": "no",
        "swedish": "sv",
        "khmer": "km",
    }

    base = language.split("-")[0].lower()

    base = aliases.get(
        base,
        base,
    )

    return langcodes.Language.get(base).to_alpha3()


def split_name(name):
    """Convert HF split names to the train/dev/test convention."""

    name = str(name).lower()

    if name in {
        "validation",
        "valid",
        "dev",
        "development",
    }:
        return "dev"

    if name == "train":
        return "train"

    if name == "test":
        return "test"

    return name


def write_tsv(
    dataset_name,
    language,
    split,
    rows,
    columns,
):
    """Write rows to dataset/language/split.tsv."""

    language = iso3(language)
    split = split_name(split)

    output_dir = (
        OUTPUT_DIR
        / dataset_name
        / language
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"{split}.tsv"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "\t".join(columns)
            + "\n"
        )

        for row in rows:

            values = [
                clean_text(
                    row.get(
                        column,
                        "",
                    )
                )
                for column in columns
            ]

            f.write(
                "\t".join(values)
                + "\n"
            )

    print(
        f"    {len(rows):,} rows -> "
        f"{output_path}"
    )


def load_hf_parquet(
    repo_id,
    subset=None,
):
    """
    Load a dataset using its already-converted Parquet files.

    This avoids legacy dataset loading scripts.
    """

    kwargs = {}

    if subset is not None:
        kwargs["name"] = subset

    return load_dataset(
        repo_id,
        **kwargs,
    )


# =====================================================================
# WikiLarge
# =====================================================================

def download_wikilarge():

    print("\n" + "=" * 70)
    print("WikiLarge")
    print("=" * 70)

    repo = "eilamc14/wikilarge-clean"

    dataset = load_dataset(repo)

    for split, data in dataset.items():

        rows = []

        for example in data:

            rows.append({
                "source": example.get(
                    "source",
                    "",
                ),
                "target": example.get(
                    "target",
                    "",
                ),
            })

        write_tsv(
            "wikilarge",
            "en",
            split,
            rows,
            [
                "source",
                "target",
            ],
        )


# =====================================================================
# WikiSplit
# =====================================================================

def download_wikisplit():

    print("\n" + "=" * 70)
    print("WikiSplit")
    print("=" * 70)

    # WikiSplit is distributed through GEM.
    #
    # Try the current GEM release first. If the local datasets version
    # cannot load it, download the repository data directly.

    try:

        dataset = load_dataset(
            "GEM/wiki_split"
        )

        for split, data in dataset.items():

            rows = []

            for example in data:

                source = (
                    example.get("source")
                    or example.get("text")
                    or example.get("original")
                    or ""
                )

                target = (
                    example.get("target")
                    or example.get("split")
                    or example.get("simple")
                    or ""
                )

                rows.append({
                    "source": source,
                    "target": target,
                })

            write_tsv(
                "wiki_split",
                "en",
                split,
                rows,
                [
                    "source",
                    "target",
                ],
            )

        return

    except Exception as exc:

        print(
            "    HF loader unavailable:"
        )
        print(
            f"    {exc}"
        )

        print(
            "    WikiSplit was not downloaded automatically."
        )
        print(
            "    Please use the original WikiSplit release."
        )


# =====================================================================
# TyDi QA
# =====================================================================

def extract_tydi_answer(example):

    annotations = example.get(
        "annotations",
        [],
    )

    if not annotations:
        return ""

    annotation = annotations[0]

    # Yes/no questions.
    yes_no = annotation.get(
        "yes_no_answer",
        [],
    )

    if yes_no:

        value = yes_no[0]

        if value != "NONE":
            return str(value).lower()

    # Minimal answer span.
    starts = annotation.get(
        "minimal_answers_start_byte",
        [],
    )

    ends = annotation.get(
        "minimal_answers_end_byte",
        [],
    )

    if not starts or not ends:
        return ""

    document = example.get(
        "document_plaintext",
        "",
    )

    start = starts[0]
    end = ends[0]

    if start < 0 or end < 0:
        return ""

    raw = document.encode(
        "utf-8"
    )

    try:

        return raw[start:end].decode(
            "utf-8",
            errors="ignore",
        )

    except Exception:

        return ""


def download_tydiqa():

    print("\n" + "=" * 70)
    print("TyDi QA")
    print("=" * 70)

    # The original HF loader is a legacy dataset script.
    #
    # Use the SEACrowd Parquet-compatible mirror when possible.
    #
    # This gives us the TyDi QA examples without depending on the old
    # Google-research HF loading script.

    repo = "SEACrowd/tydiqa"

    try:

        dataset = load_dataset(
            repo,
            trust_remote_code=True,
        )

    except Exception as exc:

        print(
            "    SEACrowd loader unavailable:"
        )
        print(
            f"    {exc}"
        )

        print(
            "    Skipping TyDi QA automatically."
        )
        print(
            "    Your existing TyDi QA GoldP dataset is unaffected."
        )

        return

    for split, data in dataset.items():

        columns = set(
            data.column_names
        )

        print(
            f"    Split {split}: "
            f"{len(data):,} rows"
        )

        # SEACrowd has a normalized schema. Try the common fields.

        language_col = next(
            (
                x
                for x in [
                    "language",
                    "lang",
                ]
                if x in columns
            ),
            None,
        )

        context_col = next(
            (
                x
                for x in [
                    "context",
                    "document_plaintext",
                ]
                if x in columns
            ),
            None,
        )

        question_col = next(
            (
                x
                for x in [
                    "question",
                    "question_text",
                ]
                if x in columns
            ),
            None,
        )

        answer_col = next(
            (
                x
                for x in [
                    "answer",
                    "answers",
                ]
                if x in columns
            ),
            None,
        )

        if language_col is None:
            print(
                "    Could not identify language field."
            )
            continue

        grouped = {}

        for example in data:

            language = example[
                language_col
            ]

            if isinstance(
                language,
                list,
            ):
                language = language[0]

            row = {
                "context": (
                    example.get(
                        context_col,
                        "",
                    )
                    if context_col
                    else ""
                ),
                "question": (
                    example.get(
                        question_col,
                        "",
                    )
                    if question_col
                    else ""
                ),
                "answer": (
                    example.get(
                        answer_col,
                        "",
                    )
                    if answer_col
                    else ""
                ),
            }

            grouped.setdefault(
                language,
                [],
            ).append(row)

        for language, rows in grouped.items():

            write_tsv(
                "tydiqa",
                language,
                split,
                rows,
                [
                    "context",
                    "question",
                    "answer",
                ],
            )


# =====================================================================
# MKQA
# =====================================================================

MKQA_URL = (
    "https://github.com/apple/ml-mkqa/"
    "raw/main/dataset/mkqa.jsonl.gz"
)


def download_mkqa():

    print("\n" + "=" * 70)
    print("MKQA")
    print("=" * 70)

    print(
        "    Downloading original MKQA JSONL..."
    )

    response = requests.get(
        MKQA_URL,
        timeout=120,
    )

    response.raise_for_status()

    with tempfile.NamedTemporaryFile(
        suffix=".jsonl.gz",
        delete=False,
    ) as tmp:

        tmp.write(
            response.content
        )

        temp_path = Path(
            tmp.name
        )

    grouped = {}

    try:

        with gzip.open(
            temp_path,
            "rt",
            encoding="utf-8",
        ) as f:

            for line in f:

                if not line.strip():
                    continue

                example = json.loads(
                    line
                )

                queries = example.get(
                    "queries",
                    {},
                )

                answers = example.get(
                    "answers",
                    {},
                )

                for language, query in queries.items():

                    answer_items = answers.get(
                        language,
                        [],
                    )

                    answer_strings = []

                    for answer in answer_items:

                        if not isinstance(
                            answer,
                            dict,
                        ):
                            answer_strings.append(
                                str(answer)
                            )
                            continue

                        text = answer.get(
                            "text"
                        )

                        if text:
                            answer_strings.append(
                                text
                            )

                        aliases = answer.get(
                            "aliases",
                            [],
                        )

                        if not text and aliases:
                            answer_strings.extend(
                                aliases
                            )

                        entity = answer.get(
                            "entity"
                        )

                        if (
                            not text
                            and not aliases
                            and entity
                        ):
                            answer_strings.append(
                                entity
                            )

                    # Remove duplicates.
                    seen = set()
                    unique_answers = []

                    for answer in answer_strings:

                        if answer not in seen:
                            seen.add(answer)
                            unique_answers.append(
                                answer
                            )

                    grouped.setdefault(
                        language,
                        [],
                    ).append({
                        "question": query,
                        "answer": " || ".join(
                            unique_answers
                        ),
                    })

    finally:

        temp_path.unlink(
            missing_ok=True
        )

    # MKQA has a single train/evaluation set.
    for language, rows in grouped.items():

        write_tsv(
            "mkqa",
            language,
            "train",
            rows,
            [
                "question",
                "answer",
            ],
        )


# =====================================================================
# XOR-TyDi QA
# =====================================================================

def download_xor_tydiqa():

    print("\n" + "=" * 70)
    print("XOR-TyDi QA")
    print("=" * 70)

    # The current HF repository has two configurations:
    #
    #   xor-retrieve
    #   xor-full
    #
    # We use the Parquet-converted files when available.

    repo = "akariasai/xor_tydi_qa"

    for config in [
        "xor-retrieve",
        "xor-full",
    ]:

        print(
            f"\n    Configuration: {config}"
        )

        try:

            dataset = load_dataset(
                repo,
                name=config,
            )

        except Exception as exc:

            print(
                "    Could not load configuration:"
            )
            print(
                f"    {exc}"
            )
            continue

        for split, data in dataset.items():

            grouped = {}

            for example in data:

                language = (
                    example.get("lang")
                    or example.get(
                        "language",
                        "en",
                    )
                )

                answer = example.get(
                    "answers",
                    "",
                )

                if isinstance(
                    answer,
                    list,
                ):
                    answer = " || ".join(
                        str(x)
                        for x in answer
                    )

                grouped.setdefault(
                    language,
                    [],
                ).append({
                    "question": example.get(
                        "question",
                        "",
                    ),
                    "answer": answer,
                })

            for language, rows in grouped.items():

                dataset_dir = (
                    "xor_tydiqa_"
                    + config.replace(
                        "-",
                        "_",
                    )
                )

                write_tsv(
                    dataset_dir,
                    language,
                    split,
                    rows,
                    [
                        "question",
                        "answer",
                    ],
                )


# =====================================================================
# PubMedQA
# =====================================================================

def download_pubmedqa():

    print("\n" + "=" * 70)
    print("PubMedQA")
    print("=" * 70)

    repo = "qiaojin/PubMedQA"

    # We want the expert-labeled data rather than the artificial or
    # unlabeled subsets.

    try:

        dataset = load_dataset(
            repo,
            name="pqa_labeled",
        )

    except Exception as exc:

        print(
            "    Could not load PubMedQA through datasets:"
        )
        print(
            f"    {exc}"
        )

        print(
            "    Trying the Parquet files directly..."
        )

        try:

            dataset = load_dataset(
                "parquet",
                data_files={
                    "train": (
                        "https://huggingface.co/datasets/"
                        "qiaojin/PubMedQA/resolve/main/"
                        "pqa_labeled/train-00000-of-00001.parquet"
                    )
                },
            )

        except Exception as exc2:

            print(
                "    Direct Parquet loading failed:"
            )
            print(
                f"    {exc2}"
            )
            return

    for split, data in dataset.items():

        rows = []

        for example in data:

            context = example.get(
                "context",
                {},
            )

            if isinstance(
                context,
                dict,
            ):

                context = " ".join(
                    str(x)
                    for x in context.get(
                        "contexts",
                        [],
                    )
                )

            answer = example.get(
                "long_answer",
                "",
            )

            decision = example.get(
                "final_decision",
                "",
            )

            rows.append({
                "context": context,
                "question": example.get(
                    "question",
                    "",
                ),
                "answer": answer,
                "decision": decision,
            })

        write_tsv(
            "pubmedqa",
            "en",
            split,
            rows,
            [
                "context",
                "question",
                "answer",
                "decision",
            ],
        )


# =====================================================================
# E2E NLG
# =====================================================================

def download_e2e():

    print("\n" + "=" * 70)
    print("E2E NLG")
    print("=" * 70)

    repo = "GEM/e2e_nlg"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Standard loader failed:"
        )
        print(
            f"    {exc}"
        )

        print(
            "    Trying the Parquet representation."
        )

        try:

            dataset = load_dataset(
                "parquet",
                data_files={
                    "train": (
                        "https://huggingface.co/datasets/"
                        "GEM/e2e_nlg/resolve/main/"
                        "e2e_nlg/train-00000-of-00001.parquet"
                    )
                },
            )

        except Exception as exc2:

            print(
                "    Parquet loading failed:"
            )
            print(
                f"    {exc2}"
            )
            return

    for split, data in dataset.items():

        rows = []

        for example in data:

            source = (
                example.get(
                    "meaning_representation",
                    example.get(
                        "mr",
                        "",
                    ),
                )
            )

            target = (
                example.get(
                    "target",
                    example.get(
                        "ref",
                        "",
                    ),
                )
            )

            rows.append({
                "source": source,
                "target": target,
            })

        write_tsv(
            "e2e_nlg",
            "en",
            split,
            rows,
            [
                "source",
                "target",
            ],
        )


# =====================================================================
# WebNLG
# =====================================================================

def download_webnlg():

    print("\n" + "=" * 70)
    print("WebNLG")
    print("=" * 70)

    repo = "GEM/web_nlg"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Standard loader failed:"
        )
        print(
            f"    {exc}"
        )
        return

    for split, data in dataset.items():

        rows = []

        for example in data:

            inputs = example.get(
                "input",
                [],
            )

            if isinstance(
                inputs,
                list,
            ):

                source = " || ".join(
                    str(x)
                    for x in inputs
                )

            else:

                source = str(inputs)

            target = example.get(
                "target",
                "",
            )

            rows.append({
                "source": source,
                "target": target,
            })

        write_tsv(
            "web_nlg",
            "en",
            split,
            rows,
            [
                "source",
                "target",
            ],
        )


# =====================================================================
# SciTLDR
# =====================================================================

def download_scitldr():

    print("\n" + "=" * 70)
    print("SciTLDR")
    print("=" * 70)

    repo = "allenai/scitldr"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Could not load SciTLDR:"
        )
        print(
            f"    {exc}"
        )
        return

    for split, data in dataset.items():

        rows = []

        for example in data:

            source = example.get(
                "source",
                [],
            )

            target = example.get(
                "target",
                [],
            )

            if not isinstance(
                source,
                list,
            ):
                source = [source]

            if not isinstance(
                target,
                list,
            ):
                target = [target]

            source_text = " ".join(
                str(x)
                for x in source
            )

            for summary in target:

                rows.append({
                    "source": source_text,
                    "target": summary,
                })

        write_tsv(
            "scitldr",
            "en",
            split,
            rows,
            [
                "source",
                "target",
            ],
        )


# =====================================================================
# QASPER
# =====================================================================

def download_qasper():

    print("\n" + "=" * 70)
    print("QASPER")
    print("=" * 70)

    repo = "allenai/qasper"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Could not load QASPER:"
        )
        print(
            f"    {exc}"
        )
        return

    for split, data in dataset.items():

        rows = []

        for example in data:

            # Flatten paper sections.
            full_text = example.get(
                "full_text",
                {},
            )

            sections = []

            if isinstance(
                full_text,
                dict,
            ):

                paragraphs = full_text.get(
                    "paragraphs",
                    [],
                )

                for section in paragraphs:

                    if isinstance(
                        section,
                        list,
                    ):

                        sections.extend(
                            str(x)
                            for x in section
                        )

                    else:

                        sections.append(
                            str(section)
                        )

            context = "\n".join(
                sections
            )

            qas = example.get(
                "qas",
                {},
            )

            questions = qas.get(
                "question",
                [],
            )

            answers = qas.get(
                "answers",
                [],
            )

            for i, question in enumerate(
                questions
            ):

                answer = ""

                if i < len(answers):

                    annotation = answers[i]

                    if isinstance(
                        annotation,
                        dict,
                    ):

                        answer_list = (
                            annotation.get(
                                "answer",
                                [],
                            )
                        )

                        if answer_list:

                            first = answer_list[0]

                            if isinstance(
                                first,
                                dict,
                            ):

                                answer = (
                                    first.get(
                                        "free_form_answer",
                                        "",
                                    )
                                )

                                if not answer:

                                    yes_no = (
                                        first.get(
                                            "yes_no"
                                        )
                                    )

                                    if yes_no is not None:
                                        answer = str(
                                            yes_no
                                        )

                rows.append({
                    "context": context,
                    "question": question,
                    "answer": answer,
                })

        write_tsv(
            "qasper",
            "en",
            split,
            rows,
            [
                "context",
                "question",
                "answer",
            ],
        )


# =====================================================================
# CommonGen
# =====================================================================

def download_commongen():

    print("\n" + "=" * 70)
    print("CommonGen")
    print("=" * 70)

    repo = "allenai/common_gen"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Could not load CommonGen:"
        )
        print(
            f"    {exc}"
        )
        return

    for split, data in dataset.items():

        rows = []

        for example in data:

            concepts = example.get(
                "concepts",
                [],
            )

            if isinstance(
                concepts,
                list,
            ):

                source = " ".join(
                    str(x)
                    for x in concepts
                )

            else:

                source = str(concepts)

            rows.append({
                "source": source,
                "target": example.get(
                    "target",
                    "",
                ),
            })

        write_tsv(
            "commongen",
            "en",
            split,
            rows,
            [
                "source",
                "target",
            ],
        )


# =====================================================================
# DuoRC
# =====================================================================

def download_duorc():

    print("\n" + "=" * 70)
    print("DuoRC")
    print("=" * 70)

    repo = "ibm-research/duorc"

    try:

        dataset = load_dataset(
            repo
        )

    except Exception as exc:

        print(
            "    Could not load DuoRC:"
        )
        print(
            f"    {exc}"
        )
        return

    for split, data in dataset.items():

        rows = []

        for example in data:

            answers = example.get(
                "answers",
                [],
            )

            if isinstance(
                answers,
                list,
            ):

                answer = " || ".join(
                    str(x)
                    for x in answers
                )

            else:

                answer = str(answers)

            rows.append({
                "context": example.get(
                    "plot",
                    "",
                ),
                "question": example.get(
                    "question",
                    "",
                ),
                "answer": answer,
            })

        write_tsv(
            "duorc",
            "en",
            split,
            rows,
            [
                "context",
                "question",
                "answer",
            ],
        )


# =====================================================================
# HotpotQA
# =====================================================================

def flatten_hotpot_context(
    context
):
    """Convert HotpotQA's nested context to plain text."""

    if not context:
        return ""

    if not isinstance(
        context,
        dict,
    ):
        return str(context)

    titles = context.get(
        "title",
        [],
    )

    sentences = context.get(
        "sentences",
        [],
    )

    blocks = []

    for i, title in enumerate(
        titles
    ):

        if i >= len(sentences):
            continue

        sentence_list = sentences[i]

        if isinstance(
            sentence_list,
            list,
        ):

            text = " ".join(
                str(x)
                for x in sentence_list
            )

        else:

            text = str(
                sentence_list
            )

        blocks.append(
            f"{title}: {text}"
        )

    return "\n".join(
        blocks
    )


def download_hotpotqa():

    print("\n" + "=" * 70)
    print("HotpotQA")
    print("=" * 70)

    repo = "hotpotqa/hotpot_qa"

    # Use the fullwiki configuration because it provides train,
    # validation and test.
    #
    # The HF repository currently exposes this configuration directly.

    try:

        dataset = load_dataset(
            repo,
            name="fullwiki",
        )

    except Exception as exc:

        print(
            "    Could not load HotpotQA fullwiki:"
        )
        print(
            f"    {exc}"
        )

        print(
            "    Trying the distractor configuration."
        )

        try:

            dataset = load_dataset(
                repo,
                name="distractor",
            )

        except Exception as exc2:

            print(
                "    Could not load distractor either:"
            )
            print(
                f"    {exc2}"
            )

            return

    for split, data in dataset.items():

        rows = []

        for example in data:

            rows.append({
                "context": flatten_hotpot_context(
                    example.get(
                        "context",
                        {},
                    )
                ),
                "question": example.get(
                    "question",
                    "",
                ),
                "answer": example.get(
                    "answer",
                    "",
                ),
            })

        write_tsv(
            "hotpotqa",
            "en",
            split,
            rows,
            [
                "context",
                "question",
                "answer",
            ],
        )


# =====================================================================
# Manual-resource report
# =====================================================================

MANUAL_DATASETS = {
    "D-Wikipedia": (
        "Document-level Wikipedia simplification. "
        "Use the original release."
    ),
    "SWiPE": (
        "Document-level simplification with "
        "fine-grained edit information."
    ),
    "Newsela": (
        "Professionally rewritten educational/news text; "
        "distribution/access should be handled from the original source."
    ),
    "QATS": (
        "Quality-aware text simplification benchmark."
    ),
    "WikiSmall": (
        "Small Wikipedia simplification benchmark."
    ),
    "PWKP": (
        "Classic Wikipedia simplification corpus."
    ),
    "C&K": (
        "Coster & Kauchak Wikipedia simplification corpora."
    ),
    "Dsim": (
        "Danish news simplification."
    ),
    "DoQA": (
        "Domain-specific question answering."
    ),
}


def write_manual_report():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        OUTPUT_DIR
        / "MANUAL_DATASETS.txt"
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "Datasets requiring separate acquisition\n"
        )
        f.write(
            "=" * 60
            + "\n\n"
        )

        for name, description in (
            MANUAL_DATASETS.items()
        ):

            f.write(
                f"{name}\n"
            )

            f.write(
                f"  {description}\n\n"
            )

    print(
        f"\nManual-resource report: {path}"
    )


# =====================================================================
# Main
# =====================================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Datasets that are straightforward with current HF releases.
    # ---------------------------------------------------------------

    functions = [
        ("WikiLarge", download_wikilarge),
        ("WikiSplit", download_wikisplit),
        ("TyDi QA", download_tydiqa),
        ("MKQA", download_mkqa),
        ("XOR-TyDi QA", download_xor_tydiqa),
        ("PubMedQA", download_pubmedqa),
        ("E2E NLG", download_e2e),
        ("WebNLG", download_webnlg),
        ("SciTLDR", download_scitldr),
        ("QASPER", download_qasper),
        ("CommonGen", download_commongen),
        ("DuoRC", download_duorc),
        ("HotpotQA", download_hotpotqa),
    ]

    successful = []
    failed = []

    for name, function in functions:

        try:

            function()

            successful.append(name)

        except Exception as exc:

            print(
                "\n"
                + "!" * 70
            )

            print(
                f"{name} FAILED"
            )

            print(
                str(exc)
            )

            print(
                "!" * 70
            )

            failed.append(name)

    write_manual_report()

    print(
        "\n"
        + "=" * 70
    )

    print(
        "Finished."
    )

    print(
        "=" * 70
    )

    print(
        "\nSuccessful:"
    )

    for name in successful:

        print(
            f"  ✓ {name}"
        )

    if failed:

        print(
            "\nFailed:"
        )

        for name in failed:

            print(
                f"  ✗ {name}"
            )

    print(
        "\nOutput:"
    )

    print(
        OUTPUT_DIR.resolve()
    )


if __name__ == "__main__":
    main()

