# MARMoT Data Pipelines

This directory contains the data preparation makefiles and scripts that fetch raw corpora and convert them into the formats used by the [experiment makefiles](../make/README.md) and the [tokenizer training makefiles](../tokenizer/README.md). Each sub-directory is a dataset (or a family of related datasets) with its own `README.md`.

## Data format conventions

Almost everything is stored as gzip-compressed text files (`*.gz`), one segment per line, source and target streams as separate files. Language IDs are the three-letter ISO 639-3 codes used throughout the repo (e.g. `deu`, `eng`, `fin`, `fra`).

**Parallel (bitext) data** – `<src>-<trg>.<src>.gz` and `<src>-<trg>.<trg>.gz`, lines aligned:

```text
data/tatoeba/train/deu-eng.deu.gz      data/tatoeba/train/deu-eng.eng.gz
data/opus/OpenSubtitles/deu-eng.deu.gz data/opus/OpenSubtitles/deu-eng.eng.gz
```

**Splits** – data is split into `train/`, `dev/` and `test/` directories:
* `tatoeba/` provides `dev5K/` (dev sets capped at 5000 lines) which is the default dev data for the experiments ([`make/config/data.mk`](../make/config/data.mk) picks `flores200/dev` when available, otherwise `tatoeba/dev5K`).
* The doc-level MT pipelines (`multisynt`, `multisynt_run2`, `transweb-edu`) produce `train/`, `dev/` (`49-tail2000`) and `test/` (`49-head2000`) splits under `len<length>/` sub-directories.

**Same-language pairs** – used for denoising and next-sentence-prediction tasks, named with `1`/`2` suffixes instead of language IDs:

```text
train/summarization.eng1.gz  train/summarization.eng2.gz   # adjacent sentences
ylenews/train/ylenews.fin1.gz ylenews/train/ylenews.fin2.gz
```

**Doc-level (document bitext) data** – the synthetic MT corpora (`multisynt*`, `transweb-edu*`) store documents as consecutive lines with `END_OF_DOCUMENT` markers between documents, one side per file:

```text
multisynt/train/len1024/nemotron-cc-english-run1-train-00-48.fin.gz
```

**Text prediction data** – `textpredict/` directories contain adjacent-sentence pairs (`*1.gz` = sentence, `*2.gz` = next sentence), built from the doc-level corpora and used for causal-language-modelling style tasks. See `make/` task docs and the [`textpredict`](textpredict/README.md) pipeline.

## Common toolchain

| tool | where | used for |
|---|---|---|
| `wget` / `git clone` | everywhere | downloading data |
| `gzip`/`zcat`, `pigz` | everywhere | (de)compressing streams |
| `tail`/`head`/`cut`/`paste`/`tr` | everywhere | slicing and reshaping text streams |
| `terashuf` | `sentmt`, `instruct` | shuffling large corpora on disk |
| `iso639` | `opus`, `synthetic`, `OpenSubtitles2024-multiset`, `wmt`, `wmt24pp`, ... | converting ISO 639-2/-3 codes and language names |
| `langgroup` | `instruct`, tokenizer | resolving language-group memberships (e.g. `ine`, `zls`) |
| `opus_get` | `opus` | retrieving corpora from OPUS |
| `python3` scripts in [`tools/`](../tools) | various | format conversions (`multisynt_to_docbitext.py`, `jsonl_to_textpredict.py`, `wmt24_to_tsv.py`, `wmt24_to_predict.py`, ...) |

## SLURM jobs

Most makefiles `include ../../tools/slurMake/slurm.mk`, which defines the pattern rules `%.slurm` (generate a SLURM script) and `%.slurmjob` (generate **and submit** it). Any target can be run as a SLURM job by appending `.slurmjob`:

```bash
make all-oellm-mt.slurmjob     # run make all-oellm-mt inside a SLURM allocation
```

The generated script is placed next to the target (`<target>.slurm`, renamed to `<target>.slurm.done` when it finishes) and uses these variables (see [`tools/slurMake/slurm.mk`](../tools/slurMake/slurm.mk) for defaults):

* `HPC_PROJECT` – the project/account to charge (e.g. `project_462000964`)
* `SLURM_CPUS`, `SLURM_MEM`, `SLURM_TIME`, `SLURM_PARTITION` – job resources
* `SLURM_MAX_NR_JOBS` – the makefile polls `squeue` and waits while you have more jobs queued than this (default 200)

## Directory index

| directory | what it provides | make targets |
|---|---|---|
| [tatoeba](tatoeba/README.md) | Tatoeba Translation Challenge bitexts (train/dev/test, macro-language pairs, dev5K) | `make oellm`, `oellm-eng`, `oellm-pivot`, `all`, `dev5K` |
| [opus](opus/README.md) | OPUS corpora via `opus_get` (OpenSubtitles, HPLT, ...) | `make opensubs`, `hplt`, `hplt2`, `all` |
| [OpenSubtitles2024-multiset](OpenSubtitles2024-multiset/README.md) | per-language files from the OpenSubtitles2024 multilingual movie linksets | `make all` |
| [flores200](flores200/README.md) | FLORES-200 dev/test sets (default test data) | `make devtest` |
| [synthetic](synthetic/README.md) | OPUS synthetic corpora for any language pair | `make all`, `fin-eng`, `eng-fin` |
| [sentmt](sentmt/README.md) | shuffled sentence-level MT data for all OELLM pairs | `make all` |
| [multisynt](multisynt/README.md) | Nemotron-CC English→OELLM doc-level MT data (run 1) | `make all`, `all-oellm-mt` |
| [multisynt_run2](multisynt_run2/README.md) | Nemotron-CC English→OELLM doc-level MT data (run 2, 500 shards) | same as multisynt |
| [multisynt_tower](multisynt_tower/README.md) | Tower-72B translations of Nemotron-CC (bilingual corpora) | `make all-jobs`, `merge`, `bilingual`, ... |
| [transweb-edu](transweb-edu/README.md) | FineWeb-edu (350BT) English→OELLM doc-level MT data, shards 00000–00049 | `make all`, `all-oellm-mt` |
| [transweb-edu_50-99](transweb-edu_50-99/README.md) | FineWeb-edu (350BT) doc-level MT data, shards 00050–00099 | same |
| [transweb-edu_100-471](transweb-edu_100-471/README.md) | FineWeb-edu (350BT) doc-level MT data, shards 00100–00471 (training only) | `make all-mt` |
| [textpredict](textpredict/README.md) | next-sentence-prediction data from translated JSONL shards | `make all` |
| [testsets](testsets/README.md) | NTREX-128, WMT24 devsets, WMT24++ test and prediction data | `make -C testsets/ntrex all`, ... |
| [definition_modelling](definition_modelling/README.md) | 3D-EX and CoDWoE definition-modelling data | `make 3d-ex-data`, `make -C CoDWoE all` |
| [instruct](instruct/README.md) | FLAN instruction-tuning data, split into train/dev and language-group sets | `make all`, `merge-langgroups` |
| [paraphrasing](paraphrasing/README.md) | Opusparcus, ParaBank2, ParaNMT, PAWS-X, TaPaCo paraphrase data | `make all` per sub-dataset |
| [simplification](simplification/README.md) | YleNews easy-Finnish, MultiSim, RuAdapt simplification data | `make all`, per sub-dataset targets |
| [summarization](summarization/README.md) | Samsum, WikiLingua, XLSum, CrossSum; combined multilingual corpus | `make all`, per sub-dataset targets |
| [question_answering](question_answering/README.md) | Mintaka, MultiNativeQA, TyDiQA QA data | `python3 download_*.py` |
| [parsing](parsing/README.md) | MTOP multilingual task-oriented parsing data | `python3 download_mtop.py` |
| [flan-extra](flan-extra/README.md) | extra FLAN (Tier-1/Tier-2) task datasets as TSVs | `python3 fetch_flan_extra_tsv*.py` |

## How the data is used

* **Experiments** – [`make/config/data.mk`](../make/config/data.mk) resolves training/dev/test data under `${DATA_DIR}` (default `${PROJECT_DIR}/data`) from the dataset names above, e.g. `TRAINDATA := tatoeba/train`, `TESTDATA := flores200/devtest`. See the [data configuration docs](../make/doc/data.md).
* **Tokenizers** – the [tokenizer makefiles](../tokenizer/README.md) train subword tokenizers on `tatoeba/train`, `multisynt/train/len1024` and `opus/HPLT` data.
* **datasets consumed elsewhere** – `instruct` reads FLAN per-language data from `../FLAN_perlang_*_mt_*` directories (outside this folder), and `sentmt` combines `../opus` and `../tatoeba` files.