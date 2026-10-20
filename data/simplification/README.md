# Text simplification data

Simplification corpora (standard → simplified text). The top-level makefile combines the two YleNews sub-datasets; per-dataset converters live in the sub-directories.

## Top-level makefile

Combines the sentence- and paragraph-level YleNews data into one training corpus:

```bash
make all
# -> ylenews/train/ylenews.fin1.gz  ylenews/train/ylenews.fin2.gz
```

(`fin1` = standard Finnish, `fin2` = *selkokieli* / easy Finnish; the input streams are concatenated from `ylenews-sent/train` and `ylenews-par/train`.)

## Sub-datasets

| sub-dataset | source | how | output |
|---|---|---|---|
| **YleNews (paragraphs)** | YLE news 2014–2018 aligned easy-Finnish paragraphs | `make -C ylenews-par ylenews-par` | `ylenews-par/train/ylenews-fi-2014-2018-selko-par.fin{1,2}.gz` |
| **YleNews (sentences)** | YLE news 2014–2020 sentence-aligned data | `make -C ylenews-sent all` | `ylenews-sent/train|test/ylenews-fi-2014-2020-selko-par-sent.fin{1,2}.gz` |
| **MultiSim** | [huggingface.co/datasets/MichaelR207/MultiSim](https://huggingface.co/datasets/MichaelR207/MultiSim) | `make -C MultiSim all` | `MultiSim/{train,dev,test}/multisim.<lang>{1,2}.gz` (8 languages) |
| **RuAdapt** | [github.com/Digital-Pushkin-Lab/RuAdapt](https://github.com/Digital-Pushkin-Lab/RuAdapt) | `make -C RuAdapt RuAdapt` | clones the repository (no conversion) |

### MultiSim

Downloads via `fetch_tsv.py` and converts for Brazilian Portuguese (`por_BR`), English, French, German, Italian, Japanese, Russian and Slovene (see the makefile for the `LANGNAME`/`LANGID` mapping).

### YleNews details

The CSV sources are converted with `csv2tsv.py` (sentence-level uses `test_csv2tsv.py` and a golden-alignments test set); lines with leading/trailing whitespace are filtered out. The sentence-level repo previously used WikiLarge (see the note in `MultiSim/README.md`).