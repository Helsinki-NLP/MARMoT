# MARMoT Tokenizer Makefiles

This directory contains makefiles for training the HuggingFace (HF) tokenizers used by the [MARMoT experiment makefiles](../make/README.md). All tokenizers are sentencepiece-style HF tokenizers trained with MAMMOTH's training script `examples/hf_tokenizers/train.py` (part of the MAMMOTH installation, see `TRAIN_HF_TOKENIZER` below) on (a subset of) the parallel training data described below.

Two tokenizer sets are provided:

* [`tatoeba/`](tatoeba/Makefile) – one tokenizer per language, trained **only on Tatoeba** translation-challenge data.
* [`tatoeba_hplt_multisynt/`](tatoeba_hplt_multisynt/Makefile) – one tokenizer per language, trained on a **combination of Tatoeba, MultiSynth and HPLT** data, plus tokenizers trained on **language groups** (e.g. `ine` = Indo-European, `mul` = multilingual).

## Output layout

For every language, a tokenizer is created at

```
<tokenizer-set>/<language>/<vocab_size>/tokenizer.json
```

e.g. `tatoeba/eng/32000/tokenizer.json` or `tatoeba_hplt_multisynt/deu/16000/tokenizer.json`.

This exactly matches the layout expected by the experiment makefiles ([`config/vocab.mk`](../make/config/vocab.mk)): `${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json`. Just set the experiment variables accordingly:

```make
VOCAB     := tatoeba                 # name of the tokenizer set directory
VOCAB_DIR := /path/to/tokenizer      # the directory containing <set>/<lang>/<size>/tokenizer.json
# VOCAB_SIZE := 32000                 # must match the trained vocabulary size
```

## Prerequisites

* **Training data**: the tokenizer makefiles read `.gz` bitext files from the data directories produced by the `data/` pipelines:
  * Tatoeba data: `data/tatoeba/train` (default `DATADIR`)
  * MultiSynth data: `data/multisynt/train/len1024` (`MULTISYNT_DATADIR`)
  * HPLT data: `data/opus/HPLT` (`HPLT_DATADIR`)
* **MAMMOTH installation**: the tokenizer training script is called as `python3 ${MAMMOTH_HOME}/examples/hf_tokenizers/train.py`. The default `MAMMOTH_HOME` differs per makefile (`../../mammoth` in `tatoeba/`, a LUMI scratch path in `tatoeba_hplt_multisynt/`) – override it if needed.
* **External tools**: `iso639` and `langgroup`, used only for the language-group tokenizers in `tatoeba_hplt_multisynt/`.
* **SLURM**: the `*-jobs` / `*.submit` targets submit CPU jobs and are tuned for **LUMI** (partition `small`); adapt `HPC_PROJECT`, `HPC_MEM` and the sbatch options otherwise.

## Common configuration

| variable | default (`tatoeba`) | default (`tatoeba_hplt_multisynt`) | description |
|---|---|---|---|
| `VOCAB_SIZE` | `32000` | `16000` | vocabulary size of the tokenizers |
| `LANGUAGE` | first language in `LANGUAGES` | same | the language to build a tokenizer for |
| `LANGUAGES` | auto-detected | auto-detected | all languages found in the Tatoeba data directory |
| `MAX_LINES` | `100000000` | `100000000` | maximum number of lines used from **Tatoeba** data |
| `MAX_LINES_HPLT` | – | `20000000` | maximum number of lines used from **HPLT** data |
| `MAX_LINES_SYNT` | – | `20000000` | maximum number of lines used from **MultiSynth** data |
| `DATASET` | `tatoeba` | `tatoeba` | name of the Tatoeba data set |
| `DATADIR` | `../../data/${DATASET}/train` | `../../data/${DATASET}/train` | Tatoeba data directory |
| `MULTISYNT_DATADIR` | – | `../../data/multisynt/train/len1024` | MultiSynth data directory |
| `HPLT_DATADIR` | – | `../../data/opus/HPLT` | HPLT data directory |
| `MAMMOTH_HOME` | `../../mammoth` | LUMI scratch path | path to the MAMMOTH installation |
| `TRAIN_HF_TOKENIZER` | `python3 ${MAMMOTH_HOME}/examples/hf_tokenizers/train.py` | same | command that trains the tokenizer |
| `HPC_PROJECT` | `project_2001194` | `project_462001509` | SLURM account for the `*.submit` jobs |
| `SLURM_MAX_NR_JOBS` | `200` | `200` | wait while the user has this many queued jobs |

`LANGUAGES` is derived automatically from the Tatoeba data directory by listing the files `*-*.*.gz` and extracting the two language IDs of each language pair (which are alphabetically sorted in the Tatoeba naming, e.g. `deu-eng.deu.gz` / `deu-eng.eng.gz`).

## Targets

| target | purpose |
|---|---|
| `make all` | train tokenizers for **all detected languages** (runs locally, one after the other) |
| `make all-jobs` | submit **one SLURM job per language** (`all` on the cluster) |
| `make tokenizer` | train the tokenizer for a single language (set `LANGUAGE=eng`) |
| `make tokenizer-job` | submit a SLURM job for a single language |
| `make oellm` / `make oellm-jobs` | train/submit tokenizers for the **OpenEuroLLM** languages |
| `make tatoeba` / `make tatoeba-jobs` / `make tatoeba-job` | train/submit tokenizers for the Tatoeba language list (only in `tatoeba_hplt_multisynt/`) |
| `make langgroup-tokenizer(s)` / `langgroup-tokenizer-jobs` | train/submit **language-group** tokenizers (only in `tatoeba_hplt_multisynt/`) |
| `make oellm-langgroup-job` / `oellm-langgroup-jobs` | language-group tokenizers for the OpenEuroLLM languages with pre-set line budgets and `VOCAB_SIZE=65472` |
| `make ine-mul-job` | the two large groups `ine` (Indo-European) and `mul` (multilingual) with reduced line budgets |
| `make langgroup-info` | print the detected language groups (only in `tatoeba_hplt_multisynt/`) |

### How a tokenizer is trained

For a single language, the makefile

1. creates the output directory `<language>/<vocab_size>/`,
2. concatenates the (gzipped) bitext files of that language, restricted to the newest `MAX_LINES*` lines:
   * `tatoeba/`: `zcat ${DATADIR}/*.<lang>.gz | head -${MAX_LINES}`
   * `tatoeba_hplt_multisynt/`: the three data sources are appended with their own line budgets (`MAX_LINES`, `MAX_LINES_HPLT`, `MAX_LINES_SYNT`)
3. trains the tokenizer: `python3 ${MAMMOTH_HOME}/examples/hf_tokenizers/train.py --input_file traindata.txt --vocab_size ${VOCAB_SIZE} --output_dir <language>/<vocab_size>/`,
4. removes the temporary `traindata.txt`.

Language-group tokenizers work the same way but iterate over all member languages of the group (resolved with the `langgroup` tool) and append their data; the concatenated file is built in the group's output directory.

### SLURM submission

The pattern rule `%.submit` generates a SLURM script for the corresponding tokenizer target and submits it with `sbatch`:

* account `-A ${HPC_PROJECT}`, job name `tokenizer`,
* partition `small`, 1 node, 8 CPUs, `--mem=48G` (`tatoeba/`) or `256G` (`tatoeba_hplt_multisynt/`), time limit 1 day,
* logs in the tokenizer output directory as `train.%j.log` and `train.%j.err` (standard output and errors of the job),
* the script removes itself when it finishes,
* submission is **skipped if the tokenizer file already exists** (no re-training), and the makefile **waits** while your user has more than `SLURM_MAX_NR_JOBS` jobs queued.

## Example workflow

Train the English and German tokenizers for `tatoeba` on a single machine:

```bash
cd tokenizer/tatoeba
make LANGUAGE=eng tokenizer
make LANGUAGE=deu tokenizer
```

Train tokenizers for all OpenEuroLLM languages on the cluster (LUMI):

```bash
cd tokenizer/tatoeba
make oellm-jobs
```

Train the combined Tatoeba + MultiSynth + HPLT tokenizers (e.g. with a 32k vocabulary) and the shared language-group tokenizers:

```bash
cd tokenizer/tatoeba_hplt_multisynt

# per-language tokenizers for all OELLM languages, 32k vocab
make VOCAB_SIZE=32000 oellm-jobs

# language-group tokenizers (e.g. ine, mul, zls, ...) with a ~65k vocab
make oellm-langgroup-jobs
```

After training, use the tokenizers in your experiments (see the [vocabulary configuration](../make/doc/config.md) and the [environment documentation](../make/doc/env.md)).

## Notes

* The set-directory name is the value of `VOCAB` in the experiment makefiles: `tatoeba` is the default, and experiments in `models/hpo` use `tatoeba_hplt_multisynt`.
* To train with a different vocabulary size than the default, override `VOCAB_SIZE` (e.g. `make VOCAB_SIZE=32000 all`). Unused size alternatives can be found as comments at the top of `tatoeba_hplt_multisynt/Makefile`.
* `MAX_LINE_LENGTH` (2048) is defined but currently unused (it would filter out over-long lines during data concatenation).