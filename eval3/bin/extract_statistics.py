#!/usr/bin/env python3
"""Extract compact per-sentence/batch inference measurements from Mammoth logs.

Input files may be plain-text ``.err`` logs or gzip-compressed ``.err.gz`` logs.
For each input log, one TSV is written to ``--runs-dir``. The first row contains
column names and the first column is the 1-based sentence number.

The TSV intentionally excludes run-constant model/configuration metadata. It
keeps the task identifier plus quantities that vary by sentence or batch.

Timing semantics
----------------
Mammoth translates sentences in batches. The log does not contain an
independent runtime measurement for each sentence. Therefore the script stores:

* ``batch_wall_s``: first source-token log -> last target-output log
* ``batch_decode_s``: last source-token log -> first generated-sequence log
* ``batch_s_per_sentence``: batch_wall_s / batch_size

The batch-level measurements are repeated for every sentence in that batch.
``batch_s_per_sentence`` is an amortized batch cost, not measured sentence
latency.

python3 extract_statistics.py --runs-dir "$MODELDIR/evaluation/runs" \
    "$MODELDIR"/evaluation/logs/job*.err
python3 extract_statistics.py --runs-dir "$MODELDIR/evaluation/runs" \
    "$MODELDIR"/evaluation/logs/job*.err.gz

"""

from __future__ import annotations

import argparse
import ast
import csv
import gzip
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, TextIO

TS_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\b")
SEQ_RE = re.compile(r"Sequence\s+(\d+)\s+token IDs:\s*(.*)$")
TASK_RE = re.compile(r"TaskSpecs\(.*?corpus_id='([^']+)'")
INT_RE = re.compile(r"-?\d+")


def parse_ts(line: str) -> Optional[datetime]:
    m = TS_RE.match(line)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")


def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return path.open("rt", encoding="utf-8", errors="replace")


def parse_python_list(after_marker: str):
    try:
        return ast.literal_eval(after_marker.strip())
    except (ValueError, SyntaxError):
        return None


def count_sequence_ids(block: str) -> tuple[int, Optional[int]]:
    """Return (number of token ids, final token id) from a tensor block."""
    start = block.find("tensor([")
    if start < 0:
        return 0, None
    start += len("tensor([")

    end = block.find("], device=", start)
    if end < 0:
        end = block.find("]", start)
    if end < 0:
        return 0, None

    ids = [int(x) for x in INT_RE.findall(block[start:end])]
    return len(ids), (ids[-1] if ids else None)


@dataclass
class SrcRec:
    ts: Optional[datetime]
    total: int
    nonpad: int
    pad: int


@dataclass
class SeqRec:
    ts: Optional[datetime]
    index: int
    raw_tokens: int
    final_id: Optional[int]


@dataclass
class TgtRec:
    ts: Optional[datetime]
    chars: int
    words: int


@dataclass
class Batch:
    src: list[SrcRec] = field(default_factory=list)
    seq: list[SeqRec] = field(default_factory=list)
    tgt: list[TgtRec] = field(default_factory=list)


def finalize_batch(batch: Batch, batches: list[Batch], path: Path) -> Batch:
    if not (batch.src or batch.seq or batch.tgt):
        return Batch()

    if not (len(batch.src) == len(batch.seq) == len(batch.tgt)):
        raise ValueError(
            f"{path}: incomplete/misaligned batch: "
            f"src={len(batch.src)} seq={len(batch.seq)} tgt={len(batch.tgt)}"
        )

    batches.append(batch)
    return Batch()


def parse_log(path: Path, eos_id: Optional[int]) -> tuple[list[dict], str, dict]:
    task = ""
    batches: list[Batch] = []
    batch = Batch()
    in_generated_part = False

    # A Sequence tensor may span several physical log lines.
    seq_ts: Optional[datetime] = None
    seq_index: Optional[int] = None
    seq_parts: list[str] = []

    def finish_seq() -> None:
        nonlocal seq_ts, seq_index, seq_parts, in_generated_part
        if seq_index is None:
            return

        block = " ".join(seq_parts)
        n, final_id = count_sequence_ids(block)
        batch.seq.append(SeqRec(seq_ts, seq_index, n, final_id))

        seq_ts = None
        seq_index = None
        seq_parts = []
        in_generated_part = True

    with open_text(path) as fh:
        for line in fh:
            if seq_index is not None:
                seq_parts.append(line.rstrip("\n"))
                if "], device=" in line or ")]" in line:
                    finish_seq()
                continue

            ts = parse_ts(line)

            if not task and "TaskSpecs(" in line:
                m = TASK_RE.search(line)
                if m:
                    task = m.group(1)

            # A new source group after generated output starts a new batch.
            if "src tokens:" in line:
                if in_generated_part:
                    batch = finalize_batch(batch, batches, path)
                    in_generated_part = False

                raw = line.split("src tokens:", 1)[1]
                toks = parse_python_list(raw)
                if toks is None:
                    raise ValueError(f"{path}: cannot parse source token list")

                total = len(toks)
                pad = sum(1 for tok in toks if tok == "<pad>")
                batch.src.append(SrcRec(ts, total, total - pad, pad))
                continue

            sm = SEQ_RE.search(line)
            if sm:
                seq_ts = ts
                seq_index = int(sm.group(1))
                seq_parts = [sm.group(2)]
                if "], device=" in sm.group(2) or ")]" in sm.group(2):
                    finish_seq()
                continue

            if "tgt output tokens:" in line:
                raw = line.split("tgt output tokens:", 1)[1]
                obj = parse_python_list(raw)

                if isinstance(obj, list):
                    text = " ".join(str(x) for x in obj)
                elif obj is None:
                    text = raw.strip()
                else:
                    text = str(obj)

                batch.tgt.append(TgtRec(ts, len(text), len(text.split())))
                in_generated_part = True

    finish_seq()
    finalize_batch(batch, batches, path)

    rows: list[dict] = []
    sentence = 0
    total_src = 0
    total_tgt = 0
    first_sentence_ts: Optional[datetime] = None
    last_sentence_ts: Optional[datetime] = None

    for batch_id, b in enumerate(batches, 1):
        n = len(b.src)
        if not n:
            continue

        src_first = b.src[0].ts
        src_last = b.src[-1].ts
        seq_first = b.seq[0].ts
        tgt_last = b.tgt[-1].ts

        batch_wall_s = (
            (tgt_last - src_first).total_seconds()
            if src_first is not None and tgt_last is not None
            else None
        )
        batch_decode_s = (
            (seq_first - src_last).total_seconds()
            if src_last is not None and seq_first is not None
            else None
        )
        batch_s_per_sentence = (
            batch_wall_s / n if batch_wall_s is not None else None
        )

        batch_src_tokens = sum(x.nonpad for x in b.src)

        def target_tokens(seq: SeqRec) -> int:
            count = seq.raw_tokens
            if eos_id is not None and seq.final_id == eos_id and count:
                count -= 1
            return count

        batch_tgt_tokens = sum(target_tokens(x) for x in b.seq)
        batch_max_src_tokens = max(x.nonpad for x in b.src)
        batch_max_tgt_tokens = max(target_tokens(x) for x in b.seq)

        for i, (src, seq, tgt) in enumerate(zip(b.src, b.seq, b.tgt)):
            sentence += 1
            tgt_tokens = target_tokens(seq)

            total_src += src.nonpad
            total_tgt += tgt_tokens

            if first_sentence_ts is None:
                first_sentence_ts = src.ts
            if tgt.ts is not None:
                last_sentence_ts = tgt.ts

            rows.append(
                {
                    "sentence": sentence,
                    "task": task,
                    "batch": batch_id,
                    "batch_pos": i + 1,
                    "batch_size": n,
                    "src_tokens": src.nonpad,
                    "src_pad_tokens": src.pad,
                    "tgt_tokens": tgt_tokens,
                    "tgt_words": tgt.words,
                    "tgt_chars": tgt.chars,
                    "batch_src_tokens": batch_src_tokens,
                    "batch_tgt_tokens": batch_tgt_tokens,
                    "batch_max_src_tokens": batch_max_src_tokens,
                    "batch_max_tgt_tokens": batch_max_tgt_tokens,
                    "batch_wall_s": batch_wall_s,
                    "batch_decode_s": batch_decode_s,
                    "batch_s_per_sentence": batch_s_per_sentence,
                }
            )

    file_wall_s = (
        (last_sentence_ts - first_sentence_ts).total_seconds()
        if first_sentence_ts is not None and last_sentence_ts is not None
        else None
    )

    summary = {
        "sentences": sentence,
        "batches": len(batches),
        "src_tokens": total_src,
        "tgt_tokens": total_tgt,
        "file_wall_s": file_wall_s,
    }
    return rows, task, summary


FIELDS = [
    "sentence",
    "task",
    "batch",
    "batch_pos",
    "batch_size",
    "src_tokens",
    "src_pad_tokens",
    "tgt_tokens",
    "tgt_words",
    "tgt_chars",
    "batch_src_tokens",
    "batch_tgt_tokens",
    "batch_max_src_tokens",
    "batch_max_tgt_tokens",
    "batch_wall_s",
    "batch_decode_s",
    "batch_s_per_sentence",
]


def fmt_value(value):
    if isinstance(value, float):
        return f"{value:.6f}"
    if value is None:
        return ""
    return value


def output_name(path: Path) -> str:
    name = path.name
    if name.endswith(".gz"):
        name = name[:-3]
    if name.endswith(".err"):
        name = name[:-4]
    return name + ".tsv"


def write_tsv(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt_value(row.get(key)) for key in FIELDS})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "logs",
        nargs="+",
        type=Path,
        help="Mammoth .err or .err.gz inference logs",
    )
    ap.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("runs"),
        help="output directory (default: runs)",
    )
    ap.add_argument(
        "--eos-id",
        type=int,
        default=0,
        help="terminal EOS id to exclude from tgt_tokens; default: 0",
    )
    args = ap.parse_args()

    args.runs_dir.mkdir(parents=True, exist_ok=True)

    rc = 0
    for log in args.logs:
        try:
            rows, task, summary = parse_log(log, args.eos_id)
            out = args.runs_dir / output_name(log)
            write_tsv(out, rows)

            print(f"wrote {out}", file=sys.stderr)
            print(
                "  "
                f"task={task or '?'} "
                f"sentences={summary['sentences']} "
                f"batches={summary['batches']} "
                f"src_tokens={summary['src_tokens']} "
                f"tgt_tokens={summary['tgt_tokens']} "
                + (
                    f"wall_s={summary['file_wall_s']:.3f}"
                    if summary["file_wall_s"] is not None
                    else "wall_s=?"
                ),
                file=sys.stderr,
            )
        except Exception as exc:
            print(f"ERROR: {log}: {exc}", file=sys.stderr)
            rc = 1

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
