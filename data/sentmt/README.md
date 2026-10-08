# Sentence-level MT data (combined & shuffled)

Combines all sentence-level parallel data from [`opus`](../opus) and [`tatoeba`](../tatoeba) into one shuffled bitext per OpenEuroLLM language pair.

For every pair it concatenates all source-side files (`../tatoeba/train/<pair>.<s>.gz` + `../opus/*/<pair>.<s>.gz`, sorted), all target-side files, pastes them, shuffles the aligned lines with `terashuf` and writes back

```text
<langpair>.<src>.gz
<langpair>.<trg>.gz
<langpair>.stats    # line+word counts (uncompressed)
```

## Usage

```bash
make all      # build stats files for all OELLM pairs found in the source data
make info     # print the number of language pairs
make rev      # process pairs in reverse order (useful when resuming)
```

## Requirements & notes

* needs `../opus` and `../tatoeba` data to exist first,
* needs the `terashuf` and `pigz` command-line tools,
* `TMPDIR` is set to the current directory for `terashuf` (run locally or via SLURM — the makefile includes `../../tools/slurMake/slurm.mk`, so `make all.slurmjob` works).