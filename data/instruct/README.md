# FLAN instruction-tuning data

Prepares the per-language FLAN instruction-tuning data (from the `../FLAN_perlang_*_mt_*` directories outside this folder) into the standard training/dev split format used by the experiment makefiles.

For every language found in `../FLAN_perlang_*_mt_*/<lang>/data.*`:

* the **first 200 lines** of each input file become the dev set (`dev/<lang>.data.<suffix>.gz`),
* the **remaining lines** (from line 201 on) become the training set (`train/<lang>.data.<suffix>.gz`),
* a `.stats` file (uncompressed `wc` output) is written next to each split.

## Usage

```bash
make all             # train + dev data for all FLAN languages
make train           # training data only
make dev             # dev data only
make info            # print the list of training targets

make merge-langgroups          # merge per-language data into language-group sets
make shuffle-langgroup-data    # shuffle the merged group data (terashuf)
make shuffle-langgroup-data-job  # ... as a SLURM job (16 CPUs, 96GB)
make langgroup-stats           # wc stats for the merged group files
```

### Language groups

`merge-langgroups` merges the per-language files into `langgroups/train/` and `langgroups/dev/` where all source languages of a pair belong to the same language group (`LANG_GROUPS`: `bat ccs cel euq gmq gmw gem grk ine mul roa sem sla trk urj zle zls zlw`), using the `langgroup` tool to resolve group membership. `shuffle-langgroup-data` then shuffles the pairs with `terashuf` into `langgroups/train-shuffled/`.

## Requirements

* the FLAN per-language data directories (`../FLAN_perlang_*_mt_*/<lang>/data.*`) must exist,
* `pigz`, `terashuf` and the `langgroup` tool must be on `PATH`.

The targets at the bottom of the makefile (`all-original`, `subsets` for zeroshot/fewshot data from `../FLAN_proc`) are **legacy** and no longer used.