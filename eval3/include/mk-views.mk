# =============================================================================
# mk-views.mk — Read-only evaluation queries and visualizations
# =============================================================================
#
# Included by the top-level eval3 Makefile.
#
# Requires:
#   SELFDIR, VIEW_PYTHON, SACRE_TSV
#   .RECIPEPREFIX := >
#
# All view targets read existing evaluation results.
# They never schedule inference or scoring.
#
# Examples:
#   make view-inventory
#   make view-scores TASKS="mt_eng-fin mt_fin-eng"
#   make view-scores TASKS="mt_eng-fin" VIEW_OUTPUT=scores.tsv
#   make view-scores VIEW_METRIC=chrF2 VIEW_KIND=zero
#   make view-compare COMPARE_A=model1 COMPARE_B=model2
#   make view-check TASKS="mt_eng-fin" TESTSETS="flores200 bouquet"
#
# =============================================================================

# -----------------------------------------------------------------------------
# Paths and defaults
# -----------------------------------------------------------------------------

VIEW_DIR         ?= $(SELFDIR)
VIEW_PYTHON      ?= python3
SACRE_TSV        ?= $(SELFDIR)/sacre.tsv

VIEW_MODELS      ?= $(MODELS)
VIEW_TASKS       ?=
VIEW_TESTSETS    ?= $(TESTSETS)
VIEW_SRC         ?=
VIEW_TGT         ?=

VIEW_METRIC      ?= BLEU
VIEW_KIND        ?= all
VIEW_AGGREGATION ?= direction
VIEW_GROUP_BY    ?= modelname,metric
VIEW_OUTPUT      ?=
VIEW_SORT        ?= score
VIEW_OUT         ?= view-output

ROWS             ?= testset_src
COLUMNS          ?= testset_tgt

COMPARE_A        ?=
COMPARE_B        ?=

VIEW_EXPECTED    ?=

# Explicit command-line TASKS takes precedence over VIEW_TASKS.
# Ignore TASKS inherited from eval3's inference planner.
ifeq ($(origin TASKS),command line)
  VIEW_SELECTED_TASKS := $(TASKS)
else
  VIEW_SELECTED_TASKS = $(VIEW_TASKS)
endif

# -----------------------------------------------------------------------------
# Shared Python arguments
# -----------------------------------------------------------------------------

VIEW_ARGS = \
  --input "$(SACRE_TSV)" \
  --models "$(VIEW_MODELS)" \
  --tasks "$(VIEW_SELECTED_TASKS)" \
  --testsets "$(VIEW_TESTSETS)" \
  --src "$(VIEW_SRC)" \
  --tgt "$(VIEW_TGT)" \
  --metric "$(or $(VIEW_METRIC),BLEU)" \
  --kind "$(or $(VIEW_KIND),all)" \
  --aggregation "$(or $(VIEW_AGGREGATION),direction)"

VIEW_OUTPUT_ARG = \
  $(if $(strip $(VIEW_OUTPUT)),--output "$(VIEW_OUTPUT)",)

# -----------------------------------------------------------------------------
# Target declarations
# -----------------------------------------------------------------------------

.PHONY: \
  view-inventory \
  view-scores \
  view-raw \
  view-pivot \
  view-compare \
  view-heatmap \
  view-cactus \
  view-distance \
  view-requirements \
  view-check \
  view-all

# -----------------------------------------------------------------------------
# Inventory: available models, tasks, benchmarks and metrics
# -----------------------------------------------------------------------------

view-inventory:
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-inventory.py" \
>   $(VIEW_ARGS) \
>   $(VIEW_OUTPUT_ARG)

# -----------------------------------------------------------------------------
# Scores: aggregated score tables
# -----------------------------------------------------------------------------

view-scores:
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-scores.py" \
>   $(VIEW_ARGS) \
>   --group-by "$(or $(VIEW_GROUP_BY),modelname,metric)" \
>   --sort "$(VIEW_SORT)" $(VIEW_OUTPUT_ARG)

# -----------------------------------------------------------------------------
# Raw scores: individual model/task/benchmark observations
# -----------------------------------------------------------------------------

view-raw:
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-scores.py" \
>   $(VIEW_ARGS) \
>   --group-by raw \
>   $(VIEW_OUTPUT_ARG)

# -----------------------------------------------------------------------------
# Pivot: SQL-style cross-tabulation
# -----------------------------------------------------------------------------

view-pivot:
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-pivot.py" \
>   $(VIEW_ARGS) \
>   --rows "$(or $(ROWS),testset_src)" \
>   --columns "$(or $(COLUMNS),testset_tgt)" \
>   $(VIEW_OUTPUT_ARG)

# -----------------------------------------------------------------------------
# Compare: matched differences between two models
# -----------------------------------------------------------------------------

view-compare:
> @test -n "$(COMPARE_A)" -a -n "$(COMPARE_B)" || { \
>   echo "ERROR: Set COMPARE_A and COMPARE_B" >&2; \
>   exit 2; \
> }
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-compare.py" \
>   $(VIEW_ARGS) \
>   --a "$(COMPARE_A)" \
>   --b "$(COMPARE_B)" \
>   --summary \
>   $(VIEW_OUTPUT_ARG)

# -----------------------------------------------------------------------------
# Visualizations
# -----------------------------------------------------------------------------

view-heatmap view-cactus view-distance:
> @mkdir -p "$(VIEW_OUT)"
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/$@.py" \
>   $(VIEW_ARGS) \
>   --output "$(VIEW_OUT)/$(patsubst view-%,%,$@).png" \
>   $(if $(filter view-distance,$@),--coordinates "$(VIEW_OUT)/distance.tsv",)

# -----------------------------------------------------------------------------
# Requirements: compare requested evaluations against completed scores
# -----------------------------------------------------------------------------

view-requirements view-check:
> @$(VIEW_PYTHON) "$(VIEW_DIR)/bin/view-requirements.py" \
>   --input "$(SACRE_TSV)" \
>   --models "$(VIEW_MODELS)" \
>   --tasks "$(VIEW_SELECTED_TASKS)" \
>   --testsets "$(VIEW_TESTSETS)" \
>   --metric "$(or $(VIEW_METRIC),BLEU)" \
>   $(if $(strip $(VIEW_EXPECTED)),--expected "$(VIEW_EXPECTED)",) \
>   $(if $(filter view-check,$@),--strict,)

# -----------------------------------------------------------------------------
# Combined overview
# -----------------------------------------------------------------------------

view-all: view-inventory view-scores
