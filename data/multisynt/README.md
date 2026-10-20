# MultiSynth doc-level MT data (Nemotron-CC English, run 1)

Builds document-level MT training data from the *MultiSynth* collection: English text sampled from Nemotron-CC (english run 1, `maxidl` distribution) and machine-translated to the OpenEuroLLM languages. This is the canonical example of the doc-level pipelines in this repo (see also [`multisynt_run2`](../multisynt_run2) and [`transweb-edu`](../transweb-edu)).

The translated corpus is fetched from `https://object.pouta.csc.fi/OELLM-synthetic/maxidl/nemotron-cc-english-run1/translated/` (JSONL + plain-text versions per shard), converted to document bitexts with [`tools/multisynt_to_docbitext.py`](../../tools/multisynt_to_docbitext.py), split into `train`/`dev`/`test`, and also converted into next-sentence-prediction ("textpredict") data.

**Shards** 00–49 are used: shards 00–48 → `train`, shard 49 → `dev` (last 2000 documents) and `test` (first 2000 documents).

## Usage

```bash
make all              # MT + text-prediction data for the default target language (fin)
make all-mt           # MT training/dev/test data only
make all-textpredict  # text prediction data only

make all-oellm-mt       # submit one SLURM job per OELLM language (MT data)
make all-oellm-predict  # submit SLURM jobs for the text-prediction data (all languages)
make all-4096           # same pipeline with LENGTH=4096 (via SLURM, 32 CPUs, 64GB)

make convert          # convert a single shard (FILEID=00 by default)
make fetch            # fetch the raw JSONL/txt files for one shard
make count-lines      # print line counts of the generated train files
make count-broken     # print line counts for the known problem languages
```

## Output

```text
train/len1024/nemotron-cc-english-run1-train-00-48.fin.gz        # MT train
train/len1024/nemotron-cc-english-run1-train-00-48.eng.gz
dev/len1024/nemotron-cc-english-run1-train-49-tail2000.fin.gz    # MT dev
test/len1024/nemotron-cc-english-run1-train-49-head2000.fin.gz   # MT test
textpredict/train/...1.gz  textpredict/train/...2.gz             # adjacent-sentence pairs
```

(`.1.gz` = sentence, `.2.gz` = next sentence; `END_OF_DOCUMENT` markers are stripped.)

## Variables & SLURM

| variable | default | description |
|---|---|---|
| `DATASET` | `OELLM-synthetic/maxidl/nemotron-cc-english-run1` | corpus on `object.pouta.csc.fi` |
| `FILEBASE` | `nemotron-cc-english-run1-train-` | file name prefix per shard |
| `SRC`, `TRG` | `eng`, `fin` | source/target language (target overridden per OELLM language) |
| `LENGTH` | `1024` | maximum document length used by the converter (`-l` option) |
| `FILEID` | `00` | shard id used by `convert`/`fetch` |
| `HPC_PROJECT` | `project_465001864` | SLURM account |

`OELLM_LANGS` lists the 36 target languages (deu, fin, nob, nno, spa, mlt, ukr, gle, glg, cat, ces, swe, tur, bul, lav, lit, slk, nld, dan, ell, est, fra, hrv, hun, ita, pol, por, ron, slv, eus, bos, isl, kat, mkd, sqi, srp_Cyrl). Jobs are submitted with `make <target>.slurmjob` (see the [top-level data README](../README.md) for the SLURM conventions).

## Known caveat

For some languages (e.g. `bos`, `deu`, `ukr`) `zcat` over many files can silently produce partial data; the makefiles note this and suggest concatenating individual files in a loop instead (`BROKEN_LANGS` is `bos deu hrv kat lav mkd pol slv srp_Cyrl ukr`).