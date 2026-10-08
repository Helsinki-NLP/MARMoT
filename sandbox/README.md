# sandbox: experiment playground

`sandbox` is a scratch area for testing models, tools and pipelines. Unlike
[`models/`](../models/README.md), it is **not** a curated, reproducible registry:
the directories are working copies for developing and debugging experiments,
and many are unfinished or superseded. Expect duplicates, stale configurations
and half-finished helper targets.

## Layout

The directories are grouped by compute system and, within each, by the person
who worked there:

| Directory | Contents |
| --- | --- |
| [`lumi/`](lumi/) | Experiments on CSC LUMI, mostly document-level (`docmt`) models and English–Finnish (`eng-fin`/`fin-eng`) runs, including early tower and shared-encoder variants. |
| [`roihu/`](roihu/) | Experiments on CSC Roihu, mostly `xl` models and Finnish-centric multitask/denoising/prediction runs. |
| [`tiedeman/`](tiedeman/) | Personal working area: multilingual and European-language models (`eucore`, `european`), OpenEuroLLM runs, FLAN, and assorted evaluation outputs. |

Each leaf directory contains a `Makefile` — and often some committed score
tables (`valid-*.tsv`, `eval-scores.*.tsv`) from past runs. There is no
top-level makefile that builds everything here.

## Relationship to `make/` and `models/`

Like the model directories, a sandbox `Makefile` defines a small experiment and
ends with an include of the shared framework, e.g.:

```make
include ../../make/marmot.mk
```

so it supports the same `make train`, `make eval`, reporting and `make stop`
targets documented in [`make/`](../make/README.md). The difference is intent:
sandbox experiments are for exploration, while the ones worth keeping are
promoted into [`models/`](../models/README.md) and get their statistics
collected and plotted.

## Note

The relative include path depends on the depth of the directory; adjust it to
the number of levels between the sandbox experiment and the repository root.
When you create a new experiment, it is usually easier to start from an existing
sandbox or `models/` Makefile and edit the task definitions.