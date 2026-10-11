# tools: conversion helpers and a small SLURM framework

This directory holds the small, self-contained pieces of code that the
[`data/`](../data/README.md) preparation pipelines and some experiments call.
There is no package here, just individual scripts plus a tiny makefile framework
for generating and submitting SLURM jobs.

> The [`make/`](../make) directory contains a *different*, more capable SLURM
> framework for running MAMMOTH experiments (`make/marmot.mk` includes
> `make/slurm.mk`). `tools/slurMake/` is the lightweight one that the
> `data/` makefiles include directly.

## Python conversion scripts

| Script | Purpose | Used by |
| --- | --- | --- |
| [`jsonl_to_textpredict.py`](jsonl_to_textpredict.py) | Build next-sentence-prediction data from a gzipped JSONL corpus: reads the `text` field of each document, optionally splits it into sentences and re-merges them into segments, and writes the `(previous segment, current segment)` pairs to a source/target pair of `.gz` files. | [`data/textpredict`](../data/textpredict/README.md) |
| [`multisynt_to_docbitext.py`](multisynt_to_docbitext.py) | Merge per-language machine-translated plain-text files back into a document-level bitext. Aligns the translated text with the segmentation of the original JSONL document and emits tab-separated `source<TAB>target`. | [`data/multisynt`](../data/multisynt/README.md), `transweb-edu*`, `multisynt_run2` |
| [`wmt24_to_tsv.py`](wmt24_to_tsv.py) | Filter: read WMT JSONL on stdin and print `source<TAB>target`, with embedded newlines escaped. | [`data/testsets/wmt24pp`](../data/testsets/wmt24pp/README.md) |
| [`wmt24_to_predict.py`](wmt24_to_predict.py) | Build adjacent-sentence pairs from one JSON field of a JSONL file using the Loomchild sentence segmenter. | [`data/testsets/wmt24pp`](../data/testsets/wmt24pp/README.md) |

The three JSONL-based scripts share the same idea: a document is segmented into
sentences, and adjacent sentences are emitted as `input<TAB>output` pairs.
They rely on the `loomchild.segmenter` Python package (the `LoomchildSegmenter`
class) for sentence segmentation.

### Options

`jsonl_to_textpredict.py`

| Option | Meaning | Default |
| --- | --- | --- |
| `-i`, `--input-file` | gzipped input JSONL | a FineWeb-Edu shard |
| `-l`, `--lang` | document language (passed to the segmenter) | `en` |
| `-m`, `--max-line-length` | maximum segment length in characters | `256` |
| `-M`, `--max-sentence-length` | maximum length before a sentence is further split | `1024` |
| `-s`, `--segment-into-sentences` | split the document into sentences first | off |
| `-S`, `--source-file` | output file for the inputs | `source.txt.gz` |
| `-T`, `--target-file` | output file for the outputs | `target.txt.gz` |

`multisynt_to_docbitext.py`

| Option | Meaning | Default |
| --- | --- | --- |
| `-j`, `--jsonl-file` | original translated JSONL | – |
| `-s`, `--source-language-file` | plain-text translation of the source language | – |
| `-t`, `--target-language-file` | plain-text translation of the target language | – |
| `-m`, `--minimum-length` | minimum segment length | `0` |
| `-l`, `--length` | target segment length | `256` |

`wmt24_to_predict.py`

| Option | Meaning | Default |
| --- | --- | --- |
| `-i`, `--input-file` | input JSONL (not gzipped) | – |
| `-l`, `--lang` | language passed to the segmenter | `en` |
| `-f`, `--field` | JSON field to segment (`source` or `target`) | `source` |

## Shell helpers

| Script | Purpose |
| --- | --- |
| [`lumi_gpu_usage.sh`](lumi_gpu_usage.sh) | Loop that prints `rocm-smi -u` GPU utilisation every 10 seconds. Used on LUMI as the `MONITOR_GPU_USAGE` command (see `make/env/lumi.mk`) to log GPU usage during a job. |

## `slurMake/`: a minimal SLURM job framework

`slurMake` turns a makefile into a SLURM workflow using two pattern rules. It is
independent of `make/` and is meant to be included by a data pipeline makefile:

```make
include ../../tools/slurMake/slurm.mk
```

The convention is that a normal target `foo` can be run on the cluster by
building the derived target `foo.slurmjob`:

```make
all: mydata.slurmjob
```

Building `foo.slurmjob` first generates a SLURM script `foo.slurm` (from the
resource variables below), then submits it with `sbatch`. A `foo.slurm` target
generates the script without submitting it.

| File | Contents |
| --- | --- |
| `slurm.mk` | Node/GPU/CPU/resource variables and the `%.slurm` / `%.slurmjob` pattern rules. |
| `env.mk` | Detects the host from `HOSTNAME` (`puhti`, `mahti`, else `lumi`) and includes `env/<host>.mk`; sets `HPC_PROJECT`, `MAX_MEM_PER_GPU`, `MAX_CPUS_PER_GPU`. |
| `env/lumi.mk` | LUMI-specific partitions, time limits, GPU GRES, and GPU energy/usage monitoring. |

Useful variables (all with `?=` defaults, so a makefile or the command line can
override them): `NR_OF_NODES`, `GPUS_PER_NODE`, `SLURM_CPUS`, `SLURM_MEM`,
`SLURM_TIME`, `SLURM_PARTITION`, `SLURM_GRES`, `HPC_PROJECT`, `EMAIL`, and
`SLURM_PARALLEL_JOBS` (the `-j` value passed to `make` inside the job). GPU
selection is automatic: if `SLURM_GPUS` is non-zero the GPU partition/GRES/limit
are used, otherwise the CPU ones.