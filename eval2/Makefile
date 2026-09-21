.DEFAULT_GOAL := help

STATIC_GOALS := help venvs list status continue-all continue-all-force test-sif find-sif \
                plot-docmt list-sacre-all sacre-tsv-all list-tsv-all coverage-partition \
                compare help list-groups 

SELFDIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
.RECIPEPREFIX := >
.SHELLFLAGS := -lc
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

include $(SELFDIR)/include/mk-paths.mk  # parse commandline args

# -----------------------------------------------------------------------------
# Mammoth and Eval Configuration
# -----------------------------------------------------------------------------

JOBPROJECT     := project_462001059
DISKPROJECT    := project_462001087

MAMMOTHDEF     := /scratch/$(DISKPROJECT)/shared/mammoth-shared/mammoth-dev/mammoth
MAMMOTH64      := /scratch/$(DISKPROJECT)/shared/mammoth-shared/mammoth-64/mammoth
TESTINGDIR     := /scratch/$(DISKPROJECT)/shared/testing-shared
# /scratch/project_462001087/shared/testing-shared

DATADIR        := $(TESTINGDIR)/data

VENV           := /scratch/$(DISKPROJECT)/shared/mammoth-shared/.venv
INF_ACTIVATE   := $(VENV)/bin/activate

SACRE_VENV     := $(TESTINGDIR)/venvs/sacre
SACRE_ACTIVATE := $(SACRE_VENV)/bin/activate
SACREPYTHON    := $(SACRE_VENV)/bin/python

VIEW_VENV      := $(TESTINGDIR)/venvs/view
VIEW_ACTIVATE  := $(VIEW_VENV)/bin/activate
VIEWPYTHON     := $(VIEW_VENV)/bin/python
LANG2VEC_REPO  := $(TESTINGDIR)/pkgs/lang2vec

PLOT_ACTIVATE  := $(TESTINGDIR)/venvs/plot/bin/activate
PLOT_PYTHON    := $(TESTINGDIR)/venvs/plot/bin/python
PLOT_VENV      := $(TESTINGDIR)/venvs/plot


INF_TEMPLATE := $(SELFDIR)/template/slurm_inf.templ
CNT_TEMPLATE := $(SELFDIR)/template/slurm_cnt.templ
MET_TEMPLATE := $(SELFDIR)/template/slurm_met.templ

INSPECT_MODEL_FILES := $(SELFDIR)/bin/inspect-model-files.py

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
> @printf "\n\
Usage:\n\
  make help\n\
  make <MODEL> <target>                 # generic form for known models (include/mk-model.mk)\n\
  make MODELDIR=/path/to/model <target> # generic form for unknon models\n\
  make list                             # shows the list of declared MODELs\n\
Setup:\n\
  make mk-basic                         # ensures subdirs + mammoth + sacre + testing.yaml (?!!)\n\
  make <MODEL> inspect-model-summary    # shows information on the model files \n\
  make <MODEL> which-mammoth            # shows the path of selected mammoth installation\n\
  make <MODEL> clean-mammoth            # resets the model's mammoth installation path for the model\n\
  make <MODEL> clean-basic              # resets the mammoth path and the model information\n\
Planning:\n\
  make <MODEL> mk-pairs                 # construct suggestions for language pairs\n\
  make <MODEL> mk-pairs-force           # construct and accept suggestions for language pairs\n\
  make <MODEL> mk-calls                 # mk-pairs + plan the inference and/or scoring calls\n\
  make <MODEL> mk-calls-force           # accept the suggested language pairs + mk-calls\n\
Inference & Scoring:\n\
  make <MODEL> mk-infer                 # run planned inferences\n\
  make <MODEL> mk-infer-force           # accept the suggested language pairs + mk-inder\n\
  make <MODEL> mk-infer-score           # run scorings\n\
  make <MODEL> mk-infer-score-force     # accept the suggested language pairs + mk-score\n\
  make <MODEL> mk-infer-score           # mk-infer + mk-score\n\
  make <MODEL> mk-infer-score-force     # accept the suggested language pairs + mk-infer-score\n\
  make <MODEL> mk-continue-eval         # replan the residual runs and continue them\n\
  make <MODEL> mk-continue-eval-force   # accept the suggested language pairs + mk-continue-eval\n\
General goals:\n\
  make mk-continue-all                  # for all models, mk-continue-eval\n\
  make mk-continue-all-force            # for all models, mk-continue-eval-force\n\
  make status                           # shows the scoring status of declared models\n\
"

# This is used to inpect the model properties - helps to choose the correct MAMMOTH version
.PHONY: $(MODEL_ALIASES)
$(MODEL_ALIASES):
> @if [ "$(words $(MAKECMDGOALS))" -eq 1 ]; then \
>   $(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODEL_$@)" inspect-model-summary; \
> fi

.PHONY: mk-basic inspect-model-summary which-mammoth
.PHONY: clean-mammoth clean-basic venvs lang2vec
.PHONY: test-sif find-sif
include $(SELFDIR)/include/mk-basic.mk # venvs, model inspection, mammoth ver, dirs, (non)slurm detection

.PHONY: mk-pairs mk-pairs-force
include $(SELFDIR)/include/mk-pairs.mk # determine the desired language pairs

.PHONY: calls clean-calls mk-calls mk-calls-force 
include $(SELFDIR)/include/mk-calls.mk # calls.*.out and yaml files

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

##################################
# VISUALIZATION AND QUERY TARGETS
##################################

.PHONY: mt-bleu mt-chrf mt-bleu-chrf

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

list-groups:
> @:

