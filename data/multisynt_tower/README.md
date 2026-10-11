# Tower-72B translations of Nemotron-CC (multisynt_tower)

Extracts aligned document bitexts from the **Nemotron-CC-Tower+** machine-translation catalogue (the `tower72b` model translations of the English Nemotron-CC corpus), stored on LUMI at `/appl/local/openeurollm/training/catalogue/...` (see `MULTISYNT_PARALLEL`). The target-language translations live in `.../parallel/tower72b/<lang>/.../*.jsonl.zst` shards; the English originals are read from `.../parallel/eng_Latn`. For each shard, [`multisynt2bitext.py`](multisynt2bitext.py) aligns the English original paragraphs with the translations and writes the two sides (`*.eng.gz` / `*.txt.gz`) under `${TOWER_MODEL}/${TRG}/`.

For each shard, [`multisynt2bitext.py`](multisynt2bitext.py) aligns the English original paragraphs with the translations and writes the two sides (`*.eng.gz` / `*.txt.gz`) under `${TOWER_MODEL}/${TRG}/`. Afterwards the per-shard files are merged into a single multilingual parallel corpus per language:

```text
parallel/tower72b/nemotron-cc.eng.gz
parallel/tower72b/nemotron-cc.<trg>.gz
```

## Usage

```bash
make all-jobs      # extract + convert all shards for all languages (SLURM jobs)
make merge         # merge the per-shard bitexts (after all jobs finished)
make finnish | german | spanish | italian | swedish   # shorthand for one language
make bitexts       # extract for the default language (fin_Latn) and merge
make counts        # wc counts of the parallel files
make eng-fin       # build a bilingual pair: bilingual/tower72b/nemotron-cc.eng-fin.fin.gz
make fin-swe       # ... and the reverse direction helper
```

* `TOWER_MODEL = tower72b`, `TOWER_LANGS = deu_Latn fin_Latn ita_Latn spa_Latn swe_Latn`, `TRGLANG` selects one (default `fin_Latn`).
* Per-shard jobs use 2 CPUs / 8GB / 48h; merge jobs 4 CPUs / 8GB / 12h.
* `HPC_PROJECT` defaults to `project_462001087` (LUMI-specific — the catalogue path is only available there).
* The merged English file drops `END_OF_DOCUMENT` markers and empty lines; the bilingual targets additionally filter out empty lines on either side.