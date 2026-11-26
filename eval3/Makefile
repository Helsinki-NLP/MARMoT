.DEFAULT_GOAL := help

STATIC_GOALS := help venvs list status continue-all continue-all-force test-sif find-sif reset-plan-all score-all \
		plot-docmt list-sacre-all sacre-tsv-all list-tsv-all coverage-partition infer-score-all \
		compare help list-groups models-ready squeue bleu chrf eval3-migrate-all stale-hypotheses \
		submit-inf-worker submit-inf-worker-dev-g eval3-scheduler-dirs test-eval3-worker \
		view-inventory view-scores view-raw view-pivot view-compare inspect-all-models \
		view-heatmap view-cactus view-distance view-requirements view-check view-all \
		evaluation-archive-list evaluation-archive-all evaluation-archive \
		evaluation-archive-dir evaluation-restore inspect-training-status inspect-training-status-tsv \
		inspect-ready-mismatch models-ready-preview inspect-not-ready inspect-evaluate-now inspect-training-review
STATIC_ONLY := $(if $(filter-out $(STATIC_GOALS),$(MAKECMDGOALS)),,yes)

SELFDIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
.RECIPEPREFIX := >
.SHELLFLAGS := -c
SHELL := /bin/bash

# -----------------------------------------------------------------------------
# Model Selection
# -----------------------------------------------------------------------------

include $(SELFDIR)/include/mk-model.mk  # model names and paths
export $(addprefix MODEL_,$(MODEL_ALIASES))
STATUS_MODELS := $(foreach a,$(MODEL_ALIASES),--model "$(a)=$(MODEL_$(a))")

include $(SELFDIR)/include/mk-targs.mk  # parse commandline args
MODELDIR_CLEAN := $(patsubst %/,%,$(MODELDIR))
MODEL := $(MODELDIR_CLEAN)/

.PHONY: list-eval-files migrate-eval-dry-run migrate-eval
include $(SELFDIR)/include/mk-paths.mk  # parse commandline args

# -----------------------------------------------------------------------------
# Mammoth and Eval Configuration
# -----------------------------------------------------------------------------

# project_462001059
JOBPROJECT     := project_462001509
DISKPROJECT    := project_462001087

TESTINGDIR     := /scratch/$(DISKPROJECT)/shared/testing-shared
DATADIR        := $(TESTINGDIR)/data

MAMMOTH_XT_64   := /scratch/$(JOBPROJECT)/shared/mammoth-shared/mammoth-64
MAMMOTH_XT_DEF  := /scratch/$(JOBPROJECT)/shared/mammoth-shared/mammoth-dev
MAMMOTH_PYTORCH := /scratch/$(JOBPROJECT)/shared/mammoth-shared/mammoth_pytorch

# MAMMOTH_TYPE
# ├── pytorch
# │   └── MAMMOTH_PYTORCH/mammoth => MAMMOTH_PYTHONPATH
# └── xtransformers
#     └── MAMMOTH_XT_DEF/mammoth => MAMMOTH_PYTHONPATH

ifeq ($(MAMMOTH_TYPE),xtransformers)
  MAMMOTH_ROOT       := $(MAMMOTH_XT_DEF)
  MAMMOTH_PYTHONPATH := $(MAMMOTH_XT_DEF)/mammoth
endif
ifeq ($(MAMMOTH_TYPE),pytorch)
  MAMMOTH_ROOT       := $(MAMMOTH_PYTORCH)
  MAMMOTH_PYTHONPATH := $(MAMMOTH_PYTORCH)/mammoth
endif

VENV           := /scratch/$(JOBPROJECT)/shared/mammoth-shared/.venv
INF_ACTIVATE   := $(VENV)/bin/activate

SACRE_VENV     := $(TESTINGDIR)/venvs/sacre
SACRE_ACTIVATE := $(SACRE_VENV)/bin/activate
SACREPYTHON    := $(SACRE_VENV)/bin/python

VIEW_VENV      := $(TESTINGDIR)/venvs/view
VIEW_ACTIVATE  := $(VIEW_VENV)/bin/activate
VIEW_PYTHON    := $(VIEW_VENV)/bin/python
LANG2VEC_REPO  := $(TESTINGDIR)/pkgs/lang2vec

PLOT_ACTIVATE  := $(TESTINGDIR)/venvs/plot/bin/activate
PLOT_PYTHON    := $(TESTINGDIR)/venvs/plot/bin/python
PLOT_VENV      := $(TESTINGDIR)/venvs/plot


INF_TEMPLATE := $(SELFDIR)/template/slurm_inf.templ
CNT_TEMPLATE := $(SELFDIR)/template/slurm_cnt.templ
MET_TEMPLATE := $(SELFDIR)/template/slurm_met.templ

INSPECT_MODEL_FILES := $(SELFDIR)/bin/inspect-model-files.py

EVAL3_SCHEDULER ?= /scratch/$(JOBPROJECT)/members/tiedeman/MARMoT/models/eval3scheduler
EVAL3_QUEUE     := $(EVAL3_SCHEDULER)/queue
EVAL3_CLAIMS    := $(EVAL3_SCHEDULER)/claims
EVAL3_LOGS      := $(EVAL3_SCHEDULER)/logs

# -----------------------------------------------------------------------------
# Top-level workflow
# -----------------------------------------------------------------------------

.PHONY: list status help
list: 
> @$(foreach a,$(MODEL_ALIASES),printf "  %-10s -> %s\n" "$(a)" "$(MODEL_$(a))";)
> @echo Remember to mount the project directories in slurm_*.templ files when using containers
status:
> @module load cray-python; python3 "$(SELFDIR)/bin/status.py" $(STATUS_MODELS)
help:
> @printf '%s\n' \
>   'Usage (run from eval3; * = usual command):' \
>   '  * make help' \
>   '  * make list' \
>   '  make <MODEL> <target>                                  alias first' \
>   '  make MODELDIR=/path/to/mammoth <target>                known backend root required' \
>   '  See README.md, CHEATSHEET.md, SURVIVAL-GUIDE.md and DEVELOPMENT-NOTES.md.' \
>   'Setup and registration:' \
>   '  make venvs                                             shared Python environments' \
>   '  make test-sif / find-sif                               container test / discovery (separate targets)' \
>   '  * make models-ready                                    replace ready list, not submit jobs' \
>   'Optional training and snapshot diagnostics (slow, read-only):' \
>   '  * make inspect-training-status                         training and snapshot audit' \
>   '  make inspect-training-status-tsv                       machine-readable audit' \
>   '  make inspect-not-ready                                 excluded models' \
>   '  * make inspect-evaluate-now                            new or potentially stale evaluations' \
>   '  make inspect-training-review                           uncertain training/archive state' \
>   '  * make inspect-ready-mismatch                          compare recommendations with models.ready' \
>   '  make models-ready-preview                              preview replacement list' \
>   '  make stale-hypotheses                                  older loose-file timestamp check' \
>   '  make inspect-all-models                                optional summaries for ready models' \
>   '  make <MODEL> inspect-model-summary                     optional checkpoint inspection' \
>   '  make <MODEL> which-mammoth                             select/show backend' \
>   '  make <MODEL> mk-basic                                  prepare model-local directories' \
>   '  make <MODEL> clean-mammoth / clean-basic               reset backend / also summary' \
>   'Planning and normal per-model execution:' \
>   '  make <MODEL> mk-tasks                                  propose tasks; requires accepted list' \
>   '  * make <MODEL> mk-tasks-force                          accept proposed tasks' \
>   '  * make <MODEL> mk-calls                                plan with accepted tasks' \
>   '  make <MODEL> mk-calls-force                            accept suggestions and plan' \
>   '  make <MODEL> mk-slurm                                  prepare batch scripts' \
>   '  make <MODEL> infer                                     submit inference only (mk-infer alias)' \
>   '  * make <MODEL> infer-score                             submit inference + continuation' \
>   '  * make <MODEL> mk-infer-score-force                    accept suggestions + infer-score' \
>   '  make <MODEL> mk-infer-force                            accept suggestions + inference only' \
>   '  * make <MODEL> continue-eval                           replan residual work and submit next phase' \
>   '  make <MODEL> continue-eval-force                       also accept suggestions' \
>   '  make <MODEL> score                                     scoring + continuation (mk-score alias)' \
>   '  make <MODEL> score-only                                scoring without continuation' \
>   '  make <MODEL> score-if-needed                           plan and submit missing scores' \
>   '  make <MODEL> mk-score-force                            legacy force wrapper; prefer explicit planning' \
>   '  make <MODEL> mk-comet                                  placeholder; not implemented' \
>   '  make <MODEL> dev-g-smoke                               small inference probe' \
>   '  make <MODEL> dev-g-smoke-force                         accept suggestions + probe' \
>   '  make <MODEL> dev-g-smoke-submit                        internal probe submission' \
>   '  * make infer-score-all                                 submit across registered models; review list first' \
>   '  make continue-all [CONTINUE_MODELS=...]                continue selected models (default all)' \
>   '  make continue-all-force                                also accept suggestions' \
>   '  * make score-all                                       score missing results across registered models' \
>   'Monitoring and repair (stop affected jobs before changing plans):' \
>   '  * make status                                          current plan, loose outputs and job flags' \
>   '  * make squeue                                          your Slurm jobs' \
>   '  make <MODEL> list-eval-files                           inspect artifact layout' \
>   '  make <MODEL> status-infer / status-score               may plan and clean stale flags' \
>   '  make <MODEL> reset-plan                                remove derived plans, preserve outputs' \
>   '  make reset-plan-all                                    reset and replan registered models' \
>   '  make <MODEL> reset-replan                              experimental wrapper; see survival guide' \
>   '  make <MODEL> clean-calls / clean                       remove calls / also YAMLs' \
>   '  make <MODEL> clean-slurm                               remove generated Slurm scripts' \
>   '  make <MODEL> clean-inf-lock / clean-cnt-lock / clean-met-lock  check/clear job flags' \
>   'Results and analysis:' \
>   '  make list-sacre-all                                    list loose score files' \
>   '  * make sacre-tsv-all                                   per-model reports/sacre.tsv' \
>   '  * make list-tsv-all                                    check per-model TSVs' \
>   '  make view-inventory / view-scores / view-raw / view-pivot / view-all' \
>   '  make view-compare COMPARE_A=... COMPARE_B=...' \
>   '  make view-heatmap / view-cactus / view-distance' \
>   '  make view-requirements / view-check                    coverage / strict coverage' \
>   '  make coverage-partition PARTITION_MODELS=...' \
>   '  make compare [COMPARE_GROUP=...]                       older comparison interface' \
>   '  make compare list-groups                               available groups' \
>   '  make compare help                                      comparison options (also prints this help)' \
>   '  make bleu TASKS=... / chrf TASKS=...                   HPO score tables' \
>   '  Legacy: <MODEL> mt-bleu, mt-chrf, mt-bleu-chrf, sentmt-bleu, docmt-bleu;' \
>   '          plot-docmt, plot-sentmt (old paths/dependencies; not routine).' \
>   'Archiving and migration (quiescent models only):' \
>   '  make evaluation-archive-list' \
>   '  * make evaluation-archive MODEL=alias DRY_RUN=1' \
>   '  make evaluation-archive MODEL=alias                    keep originals by default' \
>   '  make evaluation-archive-all DRY_RUN=1                  preview all under HPO_ROOT' \
>   '  make evaluation-archive-dir EVAL_DIR=...               explicit directory under HPO_ROOT' \
>   '  make evaluation-restore MODEL=alias                    restore absent directories' \
>   '  DELETE_ORIGINALS=1 opts into deletion after verification; see survival guide.' \
>   '  make <MODEL> migrate-eval-dry-run                      legacy directory move preview' \
>   '  make <MODEL> migrate-eval                              execute directory migration' \
>   '  make <MODEL> mk-eval3-yaml                             combined inference.yaml' \
>   '  make <MODEL> eval3-migrate-dry                         print artifact rename script' \
>   '  make eval3-migrate-all MIGRATE_MODELS=...              executes renames, NOT a dry run' \
>   'Shared inference queue (experimental bridge toward eval4):' \
>   '  make eval3-scheduler-dirs                              queue/claims/logs, same-device check' \
>   '  make <MODEL> mk-inf-tasks                              durable one-hypothesis tasks' \
>   '  make <MODEL> require-inf-tasks                         verify task set' \
>   '  make <MODEL> mk-queue                                  enqueue (queue-infer alias)' \
>   '  make submit-inf-worker                                 shared worker, not normal eval3 submission' \
>   '  make submit-inf-worker-dev-g EVAL3_SCHEDULER=...       isolated smoke scheduler' \
>   '  make test-eval3-worker                                 worker tests'

# A bare model alias only selects its backend.  Full checkpoint inspection is
# available explicitly through `make <MODEL> inspect-model-summary`.
.PHONY: $(MODEL_ALIASES)
$(MODEL_ALIASES):
> @if [ "$(words $(MAKECMDGOALS))" -eq 1 ]; then \
>   $(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODEL_$@)" which-mammoth; \
> fi

.PHONY: venvs lang2vec test-sif find-sif
include $(SELFDIR)/include/mk-confs.mk # venvs, (non)slurm detection, python, sif

.PHONY: mk-basic inspect-model-summary which-mammoth clean-mammoth clean-basic
include $(SELFDIR)/include/mk-basic.mk # model inspection, mammoth ver, dirs

include $(SELFDIR)/include/mk-eval3.mk

.PHONY: mk-tasks
include $(SELFDIR)/include/mk-tasks.mk # determine the desired language tasks

.PHONY: calls clean-calls mk-calls mk-calls-force 
include $(SELFDIR)/include/mk-calls.mk # calls.*.out and yaml files

# Fine-grained shared inference queue: one durable *.inf task per hypothesis.
include $(SELFDIR)/include/mk-queue.mk

.PHONY: mk-slurm slurm clean-slurm
.PHONY: clean-inf-lock clean-cnt-lock clean-met-lock
include $(SELFDIR)/include/mk-slurm.mk # slurm scripts and sbatch lines

.PHONY: status-infer infer infer-score
.PHONY: mk-infer mk-infer-force mk-infer-score mk-infer-score-force
include $(SELFDIR)/include/mk-infer.mk # run inference calls

.PHONY: status-score score mk-score mk-score-force mk-comet
include $(SELFDIR)/include/mk-score.mk # run scoring calls

.PHONY: continue-eval continue-eval-force continue-all continue-all-force
include $(SELFDIR)/include/mk-contr.mk # loop runs until done

.PHONY: list-sacre-all sacre-tsv-all list-tsv-all
include $(SELFDIR)/include/mk-saved.mk # saved scores

# Read-only views and completeness audits.
include $(SELFDIR)/include/mk-views.mk

##################################
# VISUALIZATION AND QUERY TARGETS
##################################

# It would be good if evaluation can be done also for selected tasks
# only. Automation is good but it would also be good if we can do
# something like make TASKS="mt_eng-fin mt_fin-eng" evaluation to only
# run evaluation over different benchmarks for the selected
# tasks. Some kind of flexibility is good  to have.  That could maybe
# also apply to analysis and visualization. Would be quite nice if one
# could make a selection of tasks to print score overviews and
# visualizations. Sometimes it can be good to zoom in into specific
# tasks instead of having the whole overview of the entire system with
# all tasks.
.PHONY: mt-bleu mt-chrf mt-bleu-chrf
mt-bleu:
> module load cray-python; python "$(SELFDIR)/bin/summarize_sacre.py" --metric BLEU --kind mt $(MODELDIR)/inf_scores/
sentmt-bleu:
> module load cray-python; python "$(SELFDIR)/bin/summarize_sacre.py" --metric BLEU --kind sentmt $(MODELDIR)/inf_scores/
docmt-bleu:
> module load cray-python; python "$(SELFDIR)/bin/summarize_sacre.py" --metric BLEU --kind docmt $(MODELDIR)/inf_scores/
mt-chrf:
> @module load cray-python; python "$(SELFDIR)/bin/summarize_sacre.py" --metric chrF2 --kind mt $(MODELDIR)/inf_scores/
mt-bleu-chrf:
> @module load cray-python; python "$(SELFDIR)/bin/summarize_sacre.py" --kind mt $(MODELDIR)/inf_scores/

plot-docmt:
> $(PLOT_PYTHON) compare.py \
>  --mk-models include/mk-model.mk \
>  --kind mt \
>  --dataset bqtpar \
>  --models docmt4denhalfbase docmt4denhalfsmall docmt4denhalfxl docmt10denhalf \
>  --delta docmt10denhalf docmt4denhalfxl \
>  --outdir cmp_docmt
> cat cmp_docmt/dominance_pretty.txt
> cat cmp_docmt/dominance_percent.txt
> cat cmp_docmt/condorcet.txt

plot-sentmt:
> $(PLOT_PYTHON) compare.py   --mk-models include/mk-model.mk   --kind sentmt   \
>   --dataset bqtpar   --models sentmtdenoise sentmthalfsmall sentmthalfxl  \
>   --delta sentmthalfsmall sentmthalfxl   --outdir cmp_sentmt

PARTITION_MODELS ?= $(MODEL_ALIASES)
PARTITION_VIEW   ?= summary
PARTITION_METRIC ?= BLEU
PARTITION_DATASET ?=

.PHONY: coverage-partition
coverage-partition:
> @set -eu; \
> args=""; \
> for a in $(PARTITION_MODELS); do \
>   eval "model_dir=\$${MODEL_$$a}"; \
>   if [ -d "$$model_dir/evaluation" ]; then \
>     tsv_file="$$model_dir/evaluation/reports/sacre.tsv"; \
>   else \
>     tsv_file="$$model_dir/eval3/sacre.tsv"; \
>   fi; \
>   if [ ! -f "$$tsv_file" ]; then \
>     echo "ERROR: missing sacre.tsv for $$a: $$tsv_file" >&2; \
>     exit 1; \
>   fi; \
>   args="$$args --input $$a=$$tsv_file"; \
> done; \
> dataset_arg=""; \
> if [ -n "$(PARTITION_DATASET)" ]; then \
>   dataset_arg="--dataset $(PARTITION_DATASET)"; \
> fi; \
> module load cray-python; python3 "$(SELFDIR)/bin/partition_coverage.py" \
>   $$args \
>   --metric "$(PARTITION_METRIC)" \
>   $$dataset_arg \
>   --view "$(PARTITION_VIEW)"

# make compare COMPARE_GROUP=G06
# make compare COMPARE_MODELS="docmt4denhalfbase docmt4denhalfxl docmt4"
COMPARE_GROUP   ?=
COMPARE_METRIC  ?= BLEU
COMPARE_DATASET ?= bqtpar
COMPARE_MODE    ?= all

.PHONY: compare help list-groups

compare:
> @set -eu; \
> case "$(word 2,$(MAKECMDGOALS))" in \
>   help) \
>     module load cray-python; python3 "$(SELFDIR)/bin/compare_scores.py" --help \
>     ;; \
>   list-groups) \
>     module load cray-python; python3 "$(SELFDIR)/bin/compare_scores.py" --list-groups \
>       --mode "$(COMPARE_MODE)" \
>       --mk-models "$(SELFDIR)/include/mk-model.mk" ;\
>     ;; \
>   "") \
>     group_arg=""; \
>     if [ -n "$(COMPARE_GROUP)" ]; then \
>       group_arg="--group $(COMPARE_GROUP)"; \
>     fi; \
>     module load cray-python; python3 "$(SELFDIR)/bin/compare_scores.py" \
>       --mk-models "$(SELFDIR)/include/mk-model.mk" \
>       $$group_arg \
>       --metric "$(COMPARE_METRIC)" \
>       --mode "$(COMPARE_MODE)" \
>       --dataset "$(COMPARE_DATASET)"; \
>     ;; \
>   *) \
>     echo "ERROR: unknown compare command: $(word 2,$(MAKECMDGOALS))" >&2; \
>     exit 1; \
>     ;; \
> esac

.PHONY: squeue
squeue:
> @squeue -u $$USER -o "%.4Q %.18i %.9P %.47j %.8T %.10M %.9l %.6D %R"

list-groups:
> @:

# -----------------------------------------------------------------------------
# HPO score tables
# -----------------------------------------------------------------------------

HPO_SCORE_TABLES := $(SELFDIR)/bin/hpo_score_tables.py
HPO_DATASET ?= flo
HPO_DEBUG ?=

.PHONY: bleu chrf

bleu:
> @test -n "$(strip $(TASKS))" || { \
>   echo 'Usage: make TASKS="mt_eng-fin [mt_fin-eng ...]" [HPO_DATASET=flo] bleu'; \
>   exit 2; \
> }
> @$(SACREPYTHON) "$(HPO_SCORE_TABLES)" \
>   --hpo-root "$(PMODELS)" \
>   --metric BLEU \
>   --dataset "$(HPO_DATASET)" \
>   $(foreach t,$(TASKS),--task "$(t)") \
>   $(if $(HPO_DEBUG),--debug,)

chrf:
> @test -n "$(strip $(TASKS))" || { \
>   echo 'Usage: make TASKS="mt_eng-fin [mt_fin-eng ...]" [HPO_DATASET=flo] chrf'; \
>   exit 2; \
> }
> @$(SACREPYTHON) "$(HPO_SCORE_TABLES)" \
>   --hpo-root "$(PMODELS)" \
>   --metric chrF2 \
>   --dataset "$(HPO_DATASET)" \
>   $(foreach t,$(TASKS),--task "$(t)") \
>   $(if $(HPO_DEBUG),--debug,)

.PHONY: infer-score-all
infer-score-all:
> @failed=""; \
> for model in $(MODEL_ALIASES); do \
>   echo >&2; \
>   echo "============================================================" >&2; \
>   echo "infer-score: $$model" >&2; \
>   echo "============================================================" >&2; \
>   if ! $(MAKE) --no-print-directory "$$model" infer-score; then \
>     echo "infer-score: $$model FAILED or already running; continuing" >&2; \
>     failed="$$failed $$model"; \
>   fi; \
> done; \
> if [ -n "$$failed" ]; then \
>   echo >&2; \
>   echo "infer-score: models returning non-zero:" >&2; \
>   for model in $$failed; do echo "  $$model" >&2; done; \
> fi

.PHONY: inspect-all-models

inspect-all-models:
> @set -eu; \
> test -n "$(strip $(READY_MODEL_ALIASES))" || { \
>     echo "ERROR: No models registered"; exit 1; \
> }; \
> inspected=0; skipped=0; \
> for entry in $(foreach a,$(sort $(READY_MODEL_ALIASES)),$(a)=$(MODEL_$(a))); do \
>     model=$${entry%%=*}; \
>     dir=$${entry#*=}; \
>     if [ -z "$$dir" ]; then \
>         echo "SKIP: $$model (no resolved checkpoint directory)"; \
>         skipped=$$((skipped + 1)); \
>         continue; \
>     fi; \
>     echo "===== Inspecting $$model ====="; \
>     $(MAKE) MODELDIR="$$dir" inspect-model-summary; \
>     inspected=$$((inspected + 1)); \
> done; \
> echo "Completed: $$inspected inspected, $$skipped skipped"









# ============================================================
# MARMoT: Safe archiving of HPO evaluation directories
# ============================================================

.RECIPEPREFIX := >
SHELL := /bin/bash

HPO_ROOT ?= /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo

DRY_RUN ?= 0
DELETE_ORIGINALS ?= 0

.PHONY: evaluation-archive-list evaluation-archive-all
.PHONY: evaluation-archive evaluation-archive-dir
.PHONY: evaluation-restore

# ------------------------------------------------------------
# List evaluation directories for all HPO models
# ------------------------------------------------------------

evaluation-archive-list:
> @set -euo pipefail; \
> root="$$(realpath -e -- "$(HPO_ROOT)")"; \
> find "$$root" -mindepth 3 -maxdepth 3 \
>   -type d -path '*/mammoth/evaluation' -print | sort

# ------------------------------------------------------------
# Archive all HPO models
# ------------------------------------------------------------

evaluation-archive-all:
> @set -euo pipefail; \
> root="$$(realpath -e -- "$(HPO_ROOT)")"; \
> find "$$root" -mindepth 3 -maxdepth 3 \
>   -type d -path '*/mammoth/evaluation' -print0 | \
> while IFS= read -r -d '' d; do \
>   $(MAKE) --no-print-directory evaluation-archive-dir \
>     EVAL_DIR="$$d" \
>     DRY_RUN="$(DRY_RUN)" \
>     DELETE_ORIGINALS="$(DELETE_ORIGINALS)"; \
> done

# ------------------------------------------------------------
# Archive one HPO model
# Usage: make evaluation-archive MODEL=model_name
# ------------------------------------------------------------

evaluation-archive:
> @set -euo pipefail; \
> model="$(MODEL)"; \
> [[ -n "$$model" && "$$model" != */* && "$$model" != "." && "$$model" != ".." ]] || { \
>   echo "ERROR: invalid MODEL"; exit 1; \
> }; \
> $(MAKE) --no-print-directory evaluation-archive-dir \
>   EVAL_DIR="$(HPO_ROOT)/$$model/mammoth/evaluation" \
>   DRY_RUN="$(DRY_RUN)" \
>   DELETE_ORIGINALS="$(DELETE_ORIGINALS)"

# ------------------------------------------------------------
# Archive one evaluation directory
# ------------------------------------------------------------

evaluation-archive-dir:
> @set -euo pipefail; \
> root="$$(realpath -e -- "$(HPO_ROOT)")"; \
> eval_input="$(EVAL_DIR)"; \
> [[ -n "$$eval_input" && -d "$$eval_input" && ! -L "$$eval_input" ]] || { \
>   echo "ERROR: invalid evaluation directory"; exit 1; \
> }; \
> eval_dir="$$(realpath -e -- "$$eval_input")"; \
> relative="$${eval_dir#"$$root/"}"; \
> [[ "$$eval_dir" == "$$root/"* && "$$relative" =~ ^[^/]+/mammoth/evaluation$$ ]] || { \
>   echo "ERROR: unexpected evaluation path: $$eval_dir"; exit 1; \
> }; \
> [[ "$(DRY_RUN)" == 0 || "$(DRY_RUN)" == 1 ]] || exit 1; \
> [[ "$(DELETE_ORIGINALS)" == 0 || "$(DELETE_ORIGINALS)" == 1 ]] || exit 1; \
> echo "=== $$eval_dir ==="; \
> for name in scores tasks hypotheses configs; do \
>   case "$$name" in \
>     scores|tasks|hypotheses|configs) ;; \
>     *) echo "ERROR: forbidden directory"; exit 1 ;; \
>   esac; \
>   dir="$$eval_dir/$$name"; \
>   archive="$$eval_dir/$$name.tar.gz"; \
>   tmp="$$archive.tmp"; \
>   if [[ ! -e "$$dir" && ! -L "$$dir" ]]; then \
>     echo "SKIP: $$name (source absent)"; \
>     continue; \
>   fi; \
>   if [[ ! -d "$$dir" || -L "$$dir" ]]; then \
>     echo "ERROR: invalid source directory: $$dir"; exit 1; \
>   fi; \
>   if [[ -L "$$archive" || -L "$$tmp" ]]; then \
>     echo "ERROR: archive path is a symlink"; exit 1; \
>   fi; \
>   if [[ "$(DRY_RUN)" == 1 ]]; then \
>     echo "DRY RUN: $$dir -> $$archive"; \
>     continue; \
>   fi; \
>   if [[ -e "$$tmp" ]]; then \
>     echo "ERROR: temporary archive already exists: $$tmp"; exit 1; \
>   fi; \
>   if [[ ! -e "$$archive" ]]; then \
>     echo "ARCHIVING: $$name"; \
>     (umask 077; set -C; tar -C "$$eval_dir" -czf "$$tmp" "$$name"); \
>     gzip -t -- "$$tmp"; \
>     tar -C "$$eval_dir" -dzf "$$tmp"; \
>     mv -n -- "$$tmp" "$$archive"; \
>     [[ -f "$$archive" && ! -e "$$tmp" ]] || { \
>       echo "ERROR: archive installation failed"; exit 1; \
>     }; \
>   fi; \
>   echo "VERIFYING: $$name"; \
>   gzip -t -- "$$archive"; \
>   tar -C "$$eval_dir" -dzf "$$archive"; \
>   if [[ "$(DELETE_ORIGINALS)" == 1 ]]; then \
>     [[ -d "$$dir" && ! -L "$$dir" ]] || exit 1; \
>     echo "DELETING VERIFIED SOURCE: $$name"; \
>     case "$$name" in \
>       scores) \
>         rm -r --one-file-system -- "$$eval_dir/scores" ;; \
>       tasks) \
>         rm -r --one-file-system -- "$$eval_dir/tasks" ;; \
>       hypotheses) \
>         rm -r --one-file-system -- "$$eval_dir/hypotheses" ;; \
>       configs) \
>         rm -r --one-file-system -- "$$eval_dir/configs" ;; \
>       *) \
>         echo "ERROR: forbidden deletion target"; exit 1 ;; \
>     esac; \
>     echo "DONE: $$archive"; \
>   else \
>     echo "KEPT ORIGINAL: $$dir"; \
>   fi; \
> done

# ------------------------------------------------------------
# Restore one HPO model
# Usage: make evaluation-restore MODEL=model_name
# ------------------------------------------------------------

evaluation-restore:
> @set -euo pipefail; \
> model="$(MODEL)"; \
> [[ -n "$$model" && "$$model" != */* && "$$model" != "." && "$$model" != ".." ]] || { \
>   echo "ERROR: invalid MODEL"; exit 1; \
> }; \
> d="$(HPO_ROOT)/$$model/mammoth/evaluation"; \
> [[ -d "$$d" && ! -L "$$d" ]] || exit 1; \
> for name in scores tasks hypotheses configs; do \
>   archive="$$d/$$name.tar.gz"; \
>   if [[ ! -f "$$archive" || -L "$$archive" ]]; then \
>     continue; \
>   fi; \
>   if [[ -e "$$d/$$name" || -L "$$d/$$name" ]]; then \
>     echo "SKIP: $$name already exists"; \
>     continue; \
>   fi; \
>   echo "RESTORING: $$name"; \
>   tar -C "$$d" -xzf "$$archive"; \
> done
