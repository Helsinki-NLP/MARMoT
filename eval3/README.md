# MARMoT eval3 — operator handover

Eval3 is a valuable, substantially automated evaluation system built through a major development effort. It turns heterogeneous multilingual Mammoth checkpoints into comparable benchmark results, handles task and vocabulary sharing, prepares inference and scoring jobs, resumes unfinished work and provides reusable evaluation artifacts and analysis tools. It has supported large model collections without requiring operators to manually construct hundreds of translation commands. Its artifact and YAML conventions are a particularly useful foundation for future development.

The system has accumulated complexity because model formats, storage layouts, evaluation requirements and scheduling strategies evolved during development, often before simple, agreed environment, artifact and scheduler specifications were available. The existing RFCs now provide a foundation for consolidating these decisions. Eval3 is usable today; it is not a fully portable, self-configuring or universally tested service.

## Start here

- This guide: normal workflow, from installation to archived results.
- [CHEATSHEET.md](CHEATSHEET.md): commands for everyday use.
- [SURVIVAL-GUIDE.md](SURVIVAL-GUIDE.md): exceptions, recovery and migration.
- [DEVELOPMENT-NOTES.md](DEVELOPMENT-NOTES.md): limitations, priorities and eval4 handover.
- `make help`: command index; an asterisk identifies recommended frequent commands, not a literal part of the command.

Existing `RFC-EVAL-ARTIFACTS.md`, `RFC-EVAL-YAML.md`, `RFC_EVAL-VIEW.md` and the existing component Markdown files remain unchanged. Read the RFCs for intended contracts; this guide describes the supplied implementation and calls out deviations. The repository snapshot is from November 2026. Commands below are examples for LUMI, not a claim that they have been executed in a live cluster during this documentation review.

## 0. Obtain and configure the system

Obtain the MARMoT repository URL and branch from the maintainer (not recorded in this archive). Replace the placeholder before executing:

```sh
# Clone the repository (replace the URL placeholder first).
git clone <MARMoT-repository-URL>
# Enter the eval3 working directory.
cd MARMoT/eval3
# Display the command index and frequently used targets.
make help
```

Use a login node, Bash, GNU Make (recipes use `>`), Slurm, Singularity and a modern Python (`module load cray-python`; planner annotations require Python 3.10+). Ensure access to the model checkpoints, benchmark data, Mammoth source and shared environments. Coordinate changes to shared environments with their owners.

Configuration checklist:

| Location | Settings to verify |
|---|---|
| `Makefile` | `JOBPROJECT` (Slurm account, currently project_462001509), `DISKPROJECT` (currently project_462001087), `TESTINGDIR`, `DATADIR`, Mammoth backend paths, `VENV`, scoring/view/plot environments |
| `include/mk-model.mk` | `PMODELS`, `NMODELS` (PyTorch collections), `XMODELS` (x-transformers), manual aliases, ready-file path |
| `include/mk-confs.mk` | `SIF` container, Python environments and lang2vec setup |
| `template/slurm_*.templ`, `bin/eval3_worker.slurm` | account, partitions, time limits, bind mounts, executable paths |
| `Makefile` archive section | `HPO_ROOT` (defaults to the hpo collection only) |

Current `TESTINGDIR` is `/scratch/$(DISKPROJECT)/shared/testing-shared`; `DATADIR` is its `data` child. `make venvs` builds missing scoring, plotting and viewing environments and installs lang2vec; the Mammoth inference environment is separately provisioned. `make find-sif` and `make test-sif` help diagnose the container (the latter requests resources). Do not assume a new account has permission to modify shared installations.

### Benchmark data

Follow `downloaders/README.md` for environment setup and Hugging Face authentication, including accepting FLORES+ terms. The actual downloader scripts write relative `data/...` paths, so run them from `TESTINGDIR`, not its `data` child. For example, after setting real paths:

```sh
# Set the absolute path to the eval3 checkout.
EVAL3=/absolute/path/to/MARMoT/eval3
# Set the shared benchmark workspace path.
TESTINGDIR=/absolute/path/to/testing-shared
# Load the modern Python environment on LUMI.
module load cray-python
# Run downloaders from the workspace containing data/.
cd "$TESTINGDIR"
# Activate the prepared downloader environment.
source /path/to/downloader/venv/bin/activate
# Download FLORES+ benchmark data.
python "$EVAL3/downloaders/dl-flores-all.py"
# Download BOUQuET benchmark data.
python "$EVAL3/downloaders/dl-bouquet-all.py"
# Download parallel BOUQuET benchmark data.
python "$EVAL3/downloaders/dl-bouquet-all-par.py"
# Download WMT24++ benchmark data.
python "$EVAL3/downloaders/dl-wmt-all.py"
# Return to the eval3 working directory.
cd "$EVAL3"
```

Expected planner inputs are `data/flores_plus/devtest/<language>.txt`, `data/bouquet/test/<language>.txt`, `data/bouquet_par/test/<language>.txt`, and `data/wmt24pp/train/en-<locale>/{source.en.txt,reference.target.txt}`. Check nonempty files, line alignment, locale variants and benchmark revisions. WMT non-English pairs are constructed using the target-side files of English-centric configurations; confirm alignment rather than assuming it. Existing data should not be silently replaced. Adding datasets has not been exercised recently (approximately half a year, according to the handover context).

## 1. Register models and check snapshots

A model alias resolves to the checkpoint directory, normally `<collection>/<alias>/mammoth`, not the parent architecture directory. PyTorch aliases are read from `models.ready`, then resolved under `NMODELS` before `PMODELS`; aliases without `model_best*` are omitted. Manual aliases are a separate mechanism. Registration does not submit jobs.

For routine registration, run only:

```sh
# Inspect model readiness and replace models.ready with eligible aliases.
make models-ready
```

This is sufficient to refresh the ready-model inventory. The diagnostic commands below are optional alternatives for investigating specific questions, not additional workflow steps. Each independently repeats the relatively expensive inspection of model directories, training logs, Slurm state and hypothesis timestamps (including supported archives). Do not run all of them in sequence merely to register models.

| Optional command (read-only) | Purpose |
|---|---|
| `make inspect-training-status` | Full diagnostic report, including training state, checkpoint and hypothesis times, readiness and recommended action. |
| `make inspect-training-status-tsv` | Same underlying report in machine-readable TSV format; useful for saving and filtering a single inspection result. |
| `make inspect-ready-mismatch` | Show discrepancies between the readiness recommendations and the existing `models.ready` list. |
| `make inspect-evaluate-now` | Show models recommended for evaluation or reevaluation; not a general test-coverage or scoring-completeness check. |
| `make models-ready-preview` | Print the proposed ready-model inventory without replacing `models.ready`. |
| `make inspect-not-ready` | Show models with a NO readiness recommendation, including active training and missing best checkpoints. |
| `make inspect-training-review` | Show cases requiring manual review, including unknown training termination or archive-reading problems. |

For several diagnostic questions, save one report instead of repeating the inspection:

```sh
# Run one read-only inspection and save its TSV report locally (overwrites this report file).
make --no-print-directory -s inspect-training-status-tsv > training-status.tsv
```

This is a point-in-time report, not a live inventory or an input cache for `models-ready`. Refresh it when model or job state changes. None of the optional diagnostic commands updates `models.ready`, deletes hypotheses or submits jobs. Readiness is distinct from evaluation freshness and completeness: a ready model may still need inference, reevaluation or scoring. Use `make status` for ordinary evaluation progress.

The training inspector reads training logs, queries Slurm and compares training end, best-checkpoint modification time and hypothesis timestamps. Its default safety margin is 3600 seconds. It includes `hypotheses.tar*` members in the timing audit. A stopped training job with a usable best checkpoint can be eligible even if it ended by timeout or cancellation. Review scientific suitability separately. Unknown training termination is a review case, not automatic acceptance. `models-ready` replaces the list atomically with YES recommendations and refuses an empty replacement; an existing ready file is required by the inspector. Back up a curated list before refreshing it. See the survival guide for exclusions and stale outputs.

Model summaries are optional for normal PyTorch evaluation:

```sh
# Generate a missing checkpoint summary for one model (trusted checkpoints only).
make MODEL_ALIAS inspect-model-summary
# Generate missing checkpoint summaries across the registered collection.
make inspect-all-models
```

These inspect trusted checkpoint files (unsafe loading is used) and generate `evaluation/model-summary.yaml` if absent. Legacy x-transformers backend selection can still require a summary to distinguish the head-dimension-64 variant. PyTorch backend selection is based on collection path. Use `make MODEL_ALIAS which-mammoth` to check it.

## 2. Establish the baseline

```sh
# List registered model aliases and their resolved paths.
make list
# Show evaluation coverage, remaining work and job states.
make status
# Show your current Slurm jobs and continuations.
make squeue
```

`list` shows registered aliases and paths. `status` reports accepted tasks, planned tests, matching loose hypotheses and scores, remaining inference/scoring and job states. A zero or small test count is not proof that evaluation is complete. Inspect the plan and expected coverage. `squeue` shows your Slurm jobs, including continuations. `make MODEL_ALIAS list-eval-files` helps locate individual artifacts.

## 3. Understand the evaluation selection

Task selection and benchmark selection are distinct. `inf_tasks.py` proposes task IDs from the training configuration; the accepted list is `evaluation/inf_tasks.txt`. The planner expands the selected translation tasks into dataset/language cases, skipping same-language objectives. Its default proxy is a hard-coded whitelist `EVAL3_PROXY_PAIRS` in `bin/plan_eval3_inference.py`, keyed by original task ID and benchmark name. Missing dataset files are skipped; localized variants may expand or collapse. For the recent 170-task model family, the observed usual proxy result is 131 tests (31 MT, 100 zero-shot), not a universal invariant. Unrestricted plans have been observed with 632 tests. One to six tests for an otherwise comparable model is an anomaly.

`EVAL3_PROXY_FILTER=0 make MODEL_ALIAS mk-calls` disables the proxy for that invocation, but Make may reuse an existing plan. Reset and replan explicitly if changing the policy; do not mix policies during an active evaluation or assume continuations retain an ad hoc environment setting. Record the policy and plan used. A shared `eval.yaml` has been discussed on Slack (as reported by the maintainer); no implemented or agreed schema is supplied here. It is a future design, not a configuration file the current planner reads.

## 4. Plan and run

Use an actual alias from `make list` in place of `MODEL_ALIAS`. Start with one model. Do not use force targets blindly if someone curated the accepted task list.

```sh
# Accept the proposed task list, replacing any existing accepted selection.
make MODEL_ALIAS mk-tasks-force
# Prepare inference YAMLs, evaluation plans and command lists as needed.
make MODEL_ALIAS mk-calls
# Show evaluation coverage, remaining work and job states.
make status
# Submit the model-specific inference/scoring workflow to Slurm.
make MODEL_ALIAS infer-score
```

The first command accepts proposed tasks. Without force, inspect `evaluation/inf_tasks.txt.input` and explicitly prepare the accepted list. Planning generates per-task YAMLs, `plan.out`, `calls.out`, `calls.sacre.out`, `calls.comet.out` and durable `.inf` files. Inspect `evaluation/testing.out` (or `testing.err` on failure) and the test counts before submission. `infer-score` submits model-specific inference and an after-any continuation; it is not a synchronous scoring command. Inference-only is `infer` / `mk-infer`. `mk-infer-score-force` combines acceptance and submission for a fresh model.

For a reviewed collection with accepted tasks, `make infer-score-all` attempts inference submission for every registered alias; it is not restricted to the inspector's EVALUATE_NOW recommendations. Prefer explicit per-model submissions when only a few models need work. `make continue-all CONTINUE_MODELS="alias1 alias2"` limits continuation to named models; its default is all registered aliases. Check logs for per-model failures even if a bulk command returns successfully.

The shared inference queue (`mk-queue`, `submit-inf-worker`) is a separate experimental bridge toward eval4, not the ordinary per-model workflow. Do not mix the two on the same outputs.

## 5. Follow up

```sh
# Show evaluation coverage, remaining work and job states.
make status
# Show your current Slurm jobs and continuations.
make squeue
```

The continuation replans unfinished inference and scoring. It can submit another inference job or SacreBLEU job, with a separate 10-minute continuation on `small`. The GPU phase normally uses `small-g`. If the pipeline stops, inspect logs, flags and actual jobs before using `make MODEL_ALIAS continue-eval`. For missing scores only, `make MODEL_ALIAS score-if-needed` or `make score-all` can be useful after checking plans. Existing hypotheses are accepted by the planner when their line count matches the source; score files over 500 bytes are treated as already scored. These are pragmatic checks, not content or checkpoint provenance verification. COMET is currently a placeholder and the continuation has an unfinished visualization branch; judge completion by the expected inference and BLEU/chrF artifacts, not a final continuation message alone.

## 6. Convert results to TSV and inspect

```sh
# Load the modern Python environment on LUMI.
module load cray-python
# Convert available SacreBLEU results to per-model TSV summaries.
make sacre-tsv-all
# List the available per-model TSV summaries.
make list-tsv-all
```

The batch converter reads loose `.sacre` files and produces `evaluation/reports/sacre.tsv` per model (legacy fallback: `eval3/sacre.tsv`). It retains a valid existing TSV when loose scores are absent, but may delete invalid or failed summaries. Preserve a verified copy before conversion or archiving. The older `TSVDIR` variable in `mk-paths.mk` points to `evaluation/tsv`; the batch converter uses `reports` instead. Do not confuse these locations.

The view commands consume a combined long-form TSV; `sacre-tsv-all` does not assemble it. The supplied checkout has a `sacre.tsv` symlink to a shared table; verify it or explicitly pass `SACRE_TSV=/path/to/combined.tsv`. To combine compatible per-model TSVs manually, check identical headers, use one header followed by all data rows, verify unique artifact/metric keys and write to a new file (never blindly redirect into the shared symlink). Example queries:

```sh
# Inspect model and evaluation coverage in the combined TSV.
make view-inventory SACRE_TSV=/path/to/combined.tsv
# View zero-shot scores from the combined TSV.
make view-scores SACRE_TSV=/path/to/combined.tsv VIEW_KIND=zero
# Compare the scores of two named models.
make view-compare SACRE_TSV=/path/to/combined.tsv COMPARE_A=alias1 COMPARE_B=alias2
# Generate a score heatmap for the named model.
make view-heatmap SACRE_TSV=/path/to/combined.tsv VIEW_MODELS=alias1
```

See `RFC_EVAL-VIEW.md` and the actual `VIEW_*` settings in `include/mk-views.mk`. Coverage checks and visualizations are useful exploratory tools, not automated scientific comparisons.

## 7. Pack and archive completed evaluations

Generate and verify TSVs first; stop all producers and continuations for the model. Archive commands default to the hpo root, not every collection. Start with one model:

```sh
# List evaluation archive candidates under the configured HPO root.
make evaluation-archive-list
# Preview archiving one model without packing or deleting files.
make evaluation-archive MODEL=MODEL_ALIAS DRY_RUN=1
# Pack and verify one model’s evaluation files; retain originals by default.
make evaluation-archive MODEL=MODEL_ALIAS
```

The last command packs `scores`, `tasks`, `hypotheses`, `configs` separately as `.tar.gz` and verifies them against the originals. It keeps originals by default. After checking the archive and retaining a backup, `DELETE_ORIGINALS=1` explicitly permits deletion of those verified source directories. `reports`, logs, flags and checkpoints are not packed by this target. Archiving is not a complete backup of the model. See the survival guide before deletion, bulk archiving or restoration.

`make status` now reads an archived `plan.out` when the live plan is missing and consults hypothesis and score archives when planned files are missing. Live and archived names are combined without double-counting, so archiving and deleting verified originals should no longer reduce reported coverage. Status does not extract files or verify artifact freshness or validity. Inference, scoring and TSV conversion still require loose files; restore the relevant directories before resuming evaluation or recomputing results.
