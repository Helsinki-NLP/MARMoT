# RFC: Evaluation production and score-query views for MARMoT eval3

Status: **query implementation and LUMI integration notes** (updated 2026-10-24). The query targets do not run inference. Examples below reflect the subsequently integrated `include/mk-views.mk` interface; earlier package-installation instructions are retained for historical reference.

## Decision: separate expensive production from cheap exploration

Jörg's request has two distinct use cases:

1. **Produce selected evaluations**: plan inference for a selected set of tasks and submit/run only that subset. This is a workflow change in eval3's existing inference planner and scheduler; it must be implemented against the real eval3 rules.
2. **Query completed evaluations**: filter the existing `sacre.tsv` by tasks, models, benchmarks, languages and metric; output tables or figures without scheduling any inference. **Implemented here.**

Never overload the existing `evaluation` target to mean both things. Keep existing default behavior unchanged. Proposed future target names are `evaluation-plan-selected` and `evaluation-run-selected`, with a separately validated `TASKS` filter applied to the task manifest *after planning* but *before scheduling*. For zero-shot tasks, allow an explicit finite selection. Ensure the selected-task run cannot overwrite, delete, or mark unselected results complete. This is a design specification, **not** an implemented eval3 patch.

## Query contract

All view targets are **read-only** and independent of eval3 inference rules. Default `MODELS`, `TASKS`, `TESTSETS`, `SRC`, `TGT` are empty, meaning *all available*. `METRIC=BLEU` by default. `KIND=all` includes `mt`, `zero`, `sentmt`, `docmt` and other task kinds; set `KIND=mt` or `KIND=zero` to restrict. Filters are space- or comma-separated glob patterns (`*`, `?`); task names must match the **actual TSV spelling** (for example `mt_eng-fin`). No SQL shell quoting is needed beyond `TASKS="..."`.

**A missing result stays missing.** The views never infer that unobserved evaluations have score zero. A repeated header row in a concatenated TSV is ignored; duplicate `(modelname,taskname,testset,testset_src,testset_tgt,metric)` result keys cause an error rather than silent averaging. For mixed metric tables, explicitly select one metric or group by metric.

### View catalogue

| Make target | Program | Output | Semantics |
|---|---|---|---|
| `view-inventory` | `view-inventory.py` | TSV stdout | Model x task kind x benchmark x metric counts; inventory before analysis |
| `view-raw` | `view-scores.py` | TSV stdout | Exact filtered result rows, no aggregation |
| `view-scores` | `view-scores.py` | TSV stdout | Grouped mean scores; `GROUP_BY` controls dimensions |
| `view-pivot` | `view-pivot.py` | TSV stdout | Matrix of source x target (or other row/column keys) |
| `view-compare` | `view-compare.py` | TSV stdout | Matched A-minus-B model differences, by metric |
| `view-heatmap` | `view-heatmap.py` | `VIEW_OUT/heatmap.png` | Single-model source x target matrix |
| `view-cactus` | `view-cactus.py` | `VIEW_OUT/cactus.png` | Percentage of exactly common cases above each score threshold |
| `view-distance` | `view-distance.py` | `VIEW_OUT/distance.png` and `.tsv` | Classical MDS of models on exact common cases |

The tabular views can write to a file via `--output file.tsv`; the integrated Make fragment also exposes `VIEW_OUTPUT=file.tsv`. See the current LUMI usage section for the stdout convention.

### Ready-to-use Make examples

```bash
# Discover which scores are present
make SACRE_TSV=/scratch/.../sacre.tsv view-inventory | head -30

# Only two completed MT directions, across all models and testsets
make SACRE_TSV=/scratch/.../sacre.tsv TASKS="mt_eng-fin mt_fin-eng" view-raw

# The same two tasks: model-by-task summary
make SACRE_TSV=/scratch/.../sacre.tsv TASKS="mt_eng-fin mt_fin-eng" GROUP_BY=modelname,taskname,metric view-scores

# All zero-shot evaluations on a particular benchmark
make SACRE_TSV=/scratch/.../sacre.tsv KIND=zero TESTSETS=flores200 GROUP_BY=modelname,metric view-scores

# A single model, source-target matrix (SQL-style pivot)
make SACRE_TSV=/scratch/.../sacre.tsv MODELS=base-4p+d-Lenc-Ldec-640k view-pivot

# A single model, PNG heatmap
make SACRE_TSV=/scratch/.../sacre.tsv MODELS=base-4p+d-Lenc-Ldec-640k view-heatmap

# Exact matched model comparison; positive = first model better
make SACRE_TSV=/scratch/.../sacre.tsv \
  COMPARE_A=base-4p+d-Lenc-Ldec-640k \
  COMPARE_B=base-4p+d-Genc-Ldec-640k view-compare

# Cactus and distance maps on a selected model family
make SACRE_TSV=/scratch/.../sacre.tsv 'MODELS=base-4p+d-*-Ldec-640k' view-cactus
make SACRE_TSV=/scratch/.../sacre.tsv 'MODELS=base-4p+d-*-Ldec-640k' view-distance
```

The example `mt_eng-fin` directions may not exist in every local score file. If none are present, the command fails clearly with `No results match...`; it never triggers inference.

### Direct CLI examples (outside Make)

```bash
python3 tools/eval3_views/bin/view-scores.py --input sacre.tsv \
  --tasks 'mt_eng-fin mt_fin-eng' --group-by modelname,taskname,metric \
  --output selected.tsv
python3 tools/eval3_views/bin/view-compare.py --input sacre.tsv \
  --a base-4p+d-Lenc-Ldec-640k --b base-4p+d-Genc-Ldec-640k \
  --summary --output comparison.tsv
python3 tools/eval3_views/bin/view-heatmap.py --input sacre.tsv \
  --models base-4p+d-Lenc-Ldec-640k --output heatmap.png
```

## Current LUMI usage: score tables, grouping, sorting and output

The integrated eval3 installation uses `include/mk-views.mk`, `bin/view-scores.py`, and `bin/viewlib.py`, with the Python executable supplied by `VIEW_PYTHON`. The examples in this section use the **current `VIEW_*` Make variables**; older examples above using unprefixed `GROUP_BY`, `KIND`, `MODELS`, or `TESTSETS` describe the original package interface and should not be copied unchanged into the integrated Makefile.

Set the consolidated score file once in your shell, or pass `SACRE_TSV=...` to each command:

```bash
export SACRE_TSV=/scratch/project_462001509/members/tiedeman/MARMoT/models/sacre.tsv
```

**Overall ranking** (one mean per model and metric):

```bash
make view-scores TASKS="mt_eng-fin mt_fin-eng" \
  VIEW_GROUP_BY="modelname,metric" VIEW_SORT="score"
```

**Component scores by direction** (one row per model and task):

```bash
make view-scores TASKS="mt_eng-fin mt_fin-eng" \
  VIEW_GROUP_BY="modelname,taskname,metric" \
  VIEW_SORT="modelname,taskname,metric"
```

**Detailed scores including benchmark/testset**, sorted by model, task, testset and metric:

```bash
make view-scores TASKS="mt_eng-fin mt_fin-eng" \
  VIEW_GROUP_BY="modelname,taskname,testset,metric" \
  VIEW_SORT="modelname,taskname,testset,metric"
```

The grouped detailed view averages any observations remaining within each group. To see individual observations with their `testset_src` and `testset_tgt` identifiers, use:

```bash
make view-raw TASKS="mt_eng-fin mt_fin-eng"
```

**Metrics:** The current default is `VIEW_METRIC=BLEU`. For chrF use the exact metric spelling `chrF2`:

```bash
make view-scores TASKS="mt_eng-fin mt_fin-eng" \
  VIEW_METRIC=chrF2 \
  VIEW_GROUP_BY="modelname,taskname,testset,metric" \
  VIEW_SORT="modelname,taskname,testset,metric"
```

Run BLEU and chrF2 separately unless the installed `viewlib.read()` has been extended and tested to accept multiple metric patterns.

**Sorting:** The original `view-scores.py` accepts only one `--sort` column (default `score`, descending). Comma-separated `VIEW_SORT` as used above requires the **multi-column sort patch** discussed during integration: parse comma-separated column names, verify each is present in the grouped result, and pass them to `DataFrame.sort_values()` with `ascending=False` for `score` and `True` for other columns. `include/mk-views.mk` must forward `--sort "$(VIEW_SORT)"`. Without that patch, group by all four columns but sort by a single column, or apply the patch first.

**Output:** With `VIEW_OUTPUT` unset, or set to `-`, print a human-readable, aligned table to the console. With a filename, write machine-readable TSV:

```bash
make view-scores TASKS="mt_eng-fin mt_fin-eng" \
  VIEW_GROUP_BY="modelname,taskname,testset,metric" \
  VIEW_SORT="modelname,taskname,testset,metric" \
  VIEW_OUTPUT=scores.tsv

column -t -s $'\t' scores.tsv | less -S
```

The integrated `emit()` function in `bin/viewlib.py` **must** treat `output is None` **or** `output == "-"` as stdout; otherwise a file literally named `-` is created and the console appears silent. For console tables, left-align text columns (especially `modelname`) and right-align numeric columns; format floating scores to three decimals. TSV exports should retain headers and tab separators.

**Aggregation and the `directions` column:** `VIEW_AGGREGATION=direction` first averages selected benchmark scores within each source-target direction, then averages directions. `VIEW_AGGREGATION=case` weights each observed benchmark case equally. `directions` counts distinct ordered source-target pairs in the group; for a single `taskname` it is normally 1, and for two distinct selected directions it can be 2. It does not count benchmarks or establish completeness. Missing observations are not zeros.

**Diagnostic commands:**

```bash
make -n view-scores TASKS="mt_eng-fin mt_fin-eng" VIEW_OUTPUT=
make --trace view-scores TASKS="mt_eng-fin mt_fin-eng" VIEW_OUTPUT=
grep -n -A 18 '^def emit' bin/viewlib.py
```

Note that `TASKS` is also used internally by the inference planner. In the integrated Make fragment, only use command-line `TASKS` for a view when `$(origin TASKS)` is `command line`; otherwise use `VIEW_TASKS`. This prevents an internal `.../evaluation/inf_tasks.txt` path from being misinterpreted as a query filter.

## Statistical definitions and reproducibility

The raw unit is a `(modelname, taskname, testset, testset_src, testset_tgt, metric)` observation. For `view-compare`, exact matching requires identical `taskname`, `testset`, `testset_src`, `testset_tgt`, and `metric`. If a task's name differs across models, it is **not** matched; no heuristic normalization is attempted.

`AGGREGATION=direction` (default) first averages scores over available testsets for each source-target direction, then macroaverages directions within each requested grouping. `AGGREGATION=case` averages all selected testset cases directly. The latter gives extra weight to directions evaluated on more benchmarks. **Neither option creates statistical confidence intervals.** The previous research analyses used bootstrap by direction and multiplicity corrections; those inferential routines are intentionally not conflated with these everyday querying tools.

`view-cactus` uses the intersection of evaluation keys across **all selected models** and computes the percentage meeting each score threshold. If adding a model shrinks the common cohort, the plotted curves change even for existing models; record the common-case count. `view-distance` uses the same complete-case policy, RMS score distance, and classical metric MDS; `--center` subtracts each model's mean score and exposes profile differences. MDS projections are descriptive; interpret within-map distances only.

## SQL / database workflows

The canonical file is TSV and is suitable for import into SQLite, DuckDB, or MariaDB/MySQL. The views themselves do not require a database. For interactive SQL on LUMI, DuckDB or SQLite are simpler than operating a persistent MySQL service on HPC. Example SQLite import (requires the `sqlite3` CLI):

```bash
sqlite3 scores.sqlite <<'SQL'
.mode tabs
.import --skip 1 sacre.tsv scores
.headers on
SELECT modelname, AVG(CAST(score AS REAL)) AS mean_bleu
FROM scores WHERE metric='BLEU' AND taskname IN ('mt_eng-fin','mt_fin-eng')
GROUP BY modelname ORDER BY mean_bleu DESC;
SQL
```

**Important:** SQLite import from arbitrary concatenated TSVs should be preceded by the Python validation / cleanup stage if repeated headers or collisions are present. Do not assume SQL AVG handles missing cases or fair model comparison. The view scripts are the reproducible reference implementation.

## Planned extensions (not yet implemented)

- `view-significance.py`: paired direction bootstrap, confidence intervals, BH adjustment, controlled cohort manifest.
- `view-penalty.py`: per-direction Lenc-minus-shared penalties, distributions and cactus curves.
- `view-clusters.py`: feature-standardized direction clustering and stability diagnostics.
- `view-exposure.py`: task-sharing components parsed from train YAMLs, not merely composite group labels.
- `view-dashboard.py`: local static HTML explorer with linked filters and download buttons.
- Selected inference: integrate a filter at the *planned-task manifest* boundary, not at a later aggregation stage. Need actual eval3 Makefiles/planner code before implementation.

## Test and deployment checklist

Run `python3 -m unittest discover -s tools/eval3_views/tests -v`. Test against the real score file; validate empty filters, missing tasks, duplicated keys, and exact pairwise matching. Verify the Make include does not change default targets or existing `evaluation` semantics. Run `make -n view-scores` to inspect the expanded command. For LUMI, generate PNGs in a writable results directory and avoid GUI backends.

## Design principle

**Plan broadly when appropriate; evaluate selectively when cost demands; query freely after results exist.** Do not couple score queries to scheduling, and do not make exploratory visualization change training or inference state.


## Integration with the supplied October 2026 eval3 Makefile

The top-level Makefile sets `.RECIPEPREFIX := >`, `SELFDIR`, `STATIC_GOALS`, and `VIEW_PYTHON`. Therefore use **`include/mk-views-eval3.mk`** (not the generic `mk-views.mk`), whose recipes use `>` and which does not overwrite the existing `VIEW_PYTHON`. Add the included `Makefile.patch` manually or apply it with `git apply Makefile.patch` from the repository root after placing this package at `tools/eval3_views/`. The patch adds the view targets to `STATIC_GOALS` to prevent model-selection side effects in `mk-targs.mk`. No changes are made to the existing `bleu`, `chrf`, `compare`, `coverage-partition`, or inference targets.

The supplied Makefile has model-local paths under `<model>/evaluation/reports/sacre.tsv` or `<model>/eval3/sacre.tsv` and a distinct cross-model `sacre-tsv-all` workflow. The query tools require **one consolidated TSV** for cross-model queries. Set `SACRE_TSV` to that file. Do not assume `sacre-tsv-all` necessarily creates the consolidated file: inspect `include/mk-saved.mk` before wiring it as a dependency. For single-model queries, point `SACRE_TSV` to the model's actual local file and optionally select `MODELS`.

### Checking requirements without scheduling

`view-requirements.py` audits completed result keys. It has two modes:

* **Authoritative manifest**: `VIEW_EXPECTED=expected.tsv`, with columns `modelname`, `taskname`, `testset`, `metric`, optionally `testset_src`, `testset_tgt`. Each manifest row is a requirement; status is `complete` or `missing`. This is the recommended mode. Generate the manifest from the eval3 planned inference/scoring tasks when planner details are available.
* **Explicit rectangular request**: exact `MODELS`, `TASKS`, `TESTSETS`, `METRIC` values produce their Cartesian product and test whether each result exists. This is useful for quick focused checks but **may overstate requirements** if some model/task/benchmark combinations were never planned.

If scope is not fully known (wildcards, missing model list, no testsets), output `observed_only` rows and a warning. Do not claim completeness from observed rows. `view-check` exits 3 when missing or unresolved; `view-requirements` exits 0 but reports missing rows for inspection. This is deliberate: a score file alone cannot reveal all *expected* evaluations.

```bash
make SACRE_TSV=/path/to/sacre.tsv \
  MODELS=base-4p+d-Lenc-Ldec-640k \
  TASKS='mt_eng-fin mt_fin-eng' TESTSETS='flores200 bouquet' \
  view-requirements

make SACRE_TSV=/path/to/sacre.tsv \
  VIEW_EXPECTED=/path/to/expected.tsv view-check
```

### Deferred queries: design contract (not implemented)

When a requirement audit identifies missing rows, it may eventually emit a **query request** consisting of an immutable query specification, an expected-result manifest, and an output destination. The future scheduler can queue missing inference/scoring tasks, then a dependent query job can run once all required result keys are present. The dependency must use durable task IDs, support idempotent retries, and distinguish `not planned`, `queued`, `running`, `scored`, `failed`, and `unknown`. `sacre.tsv` only certifies observed scores; it cannot distinguish those other states. This package does not submit tasks or queue deferred queries.

### Future implementation prerequisites

To produce an authoritative manifest automatically, inspect `include/mk-eval3.mk`, `include/mk-queue.mk`, `include/mk-saved.mk`, and the Python planner used by `mk-inf-tasks`. Those files were not supplied; the integration deliberately does not infer their internal APIs.

