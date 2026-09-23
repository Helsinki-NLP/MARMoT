# -----------------------------------------------------------------------------
# mk-basic.mk — Common setup for the eval2 workflow
# -----------------------------------------------------------------------------
# Included by the top-level Makefile. Provides model inspection, Mammoth
# selection, and evaluation-directory creation.
#
# Main targets
# ------------
# mk-basic
#   Builds BAS_DONE, prints planning-log paths, and checks that the caller
#   is outside Slurm. Prerequisites run before this Slurm check.
#
# inspect-model-summary
#   Creates and displays MODEL_SUMMARY by inspecting checkpoint files inside
#   the configured Singularity container.
#
# which-mammoth
#   Creates and displays MAMMOTH_SELECTED. Selects MAMMOTH_XT_64 when the model
#   summary contains the legacy head-dimension warning; otherwise selects
#   MAMMOTH_XT_DEF.
#
# Inputs and assumptions
# ----------------------
# The including Makefile supplies:
#   MODELDIR, TESTINGDIR, DATADIR, TRAINCONFIG
#   EVAL_DIRS, BAS_DONE, PLAN_LOG, PLAN_ERR
#   MODEL_SUMMARY, MAMMOTH_SELECTED
#   INSPECT_MODEL_FILES, MAMMOTH_XT_DEF, MAMMOTH_XT_64
#   MAMMOTH_ROOT, MAMMOTH_PYTHONPATH
#
# Recipes require Bash, the module command, and the cray-python module.
# Checkpoints must be trusted: inspection uses --unsafe loading.
#
# Reads
# -----
#   Training-configuration path and model checkpoints under MODELDIR.
#   The checkpoint inspector and configured container.
#   MODEL_SUMMARY when selecting the Mammoth implementation.
#
# Writes / effects
# ----------------
#   MODEL_SUMMARY       Inferred checkpoint architecture.
#   MAMMOTH_SELECTED    Selected Mammoth source path.
#   BAS_DONE            Basic-setup completion marker.
#   EVAL_DIRS           Evaluation directories, created as needed.
#
# Notes
# -----
# Paths are supplied by mk-paths.mk. This fragment does not change the working
# directory or independently detect the old/new evaluation layout.
# Existing activation files and completion markers control rebuilding.
# Setup checks are target-driven; existing file targets may skip their recipes.
# -----------------------------------------------------------------------------

.PHONY: mk-basic inspect-model-summary which-mammoth
.PHONY: clean-mammoth clean-basic

inspect-model-summary: $(MODEL_SUMMARY)
> @echo "mk-basic.mk: 🛠️ Short model-file summary for $(MODELDIR):"; \
> cat $(MODEL_SUMMARY) | egrep -v '_wrapper_'; \
> ls  $(MODEL_SUMMARY)

which-mammoth: $(MAMMOTH_SELECTED)
> @echo -n "Selected model: "
> @cat $(MAMMOTH_SELECTED)

# MAMMOTH_TYPE
# ├── pytorch
# │   └── MAMMOTH_PYTORCH/mammoth => $(MAMMOTH_SELECTED)
# └── xtransformers
#     ├── legacy trained_head_dim=64 warning
#     │   └── MAMMOTH_XT_64/mammoth => $(MAMMOTH_SELECTED)
#     └── otherwise
#         └── MAMMOTH_XT_DEF/mammoth => $(MAMMOTH_SELECTED)
#
$(MAMMOTH_SELECTED): $(MODEL_SUMMARY) | $(EVAL_DIRS_TO_CREATE)
> @set -euo pipefail; \
> echo "mk-basic.mk:    Reading $(MODEL_SUMMARY)"; \
> case "$(MAMMOTH_TYPE)" in \
>   pytorch) \
>     selected="$(MAMMOTH_PYTORCH)/mammoth"; \
>     variant="PyTorch backend"; \
>     ;; \
>   xtransformers) \
>     if grep -Fq \
>          'use older Mammoth compatible with trained_head_dim=64' \
>          "$(MODEL_SUMMARY)"; then \
>       selected="$(MAMMOTH_XT_64)/mammoth"; \
>       variant="x-transformers, legacy hard-coded head_dim=64"; \
>     else \
>       selected="$(MAMMOTH_XT_DEF)/mammoth"; \
>       variant="x-transformers, computed head_dim"; \
>     fi; \
>     ;; \
>   *) \
>     echo "mk-basic.mk: ❌ Unknown Mammoth type: $(MAMMOTH_TYPE)" >&2; \
>     exit 1; \
>     ;; \
> esac; \
> echo "mk-basic.mk:    Selected $$variant"; \
> printf '%s\n' "$$selected" > "$@"; \
> echo "mk-basic.mk: ✅ Written file $@"

# This is needed if the mammoth binaries have been moved
clean-mammoth:
> rm -f "$(MAMMOTH_SELECTED)"

clean-basic:
> rm -f "$(MAMMOTH_SELECTED)" "$(MODEL_SUMMARY)"
> @echo "mk-basic.mk: ✨ Cleaning done."

# The folloing sends the names of the model files to the inspector and
# then stores the outputs to a model-summary.yaml file.
$(MODEL_SUMMARY): | $(EVAL_DIRS_TO_CREATE)
> @set -euo pipefail; \
> trap 'rm -f "$@"' ERR; \
> [[ -f "$(INSPECT_MODEL_FILES)" ]] || { echo "mk-basic.mk: ❌ Missing $(INSPECT_MODEL_FILES)" >&2; exit 1; }; \
> [[ "$(MAMMOTH_TYPE)" != unknown ]] || { \
>   echo "mk-basic.mk: ❌ Cannot infer Mammoth type for $(MODELDIR_CLEAN)" >&2; \
>   exit 1; \
> }; \
> echo "mk-basic.mk:    Mammoth type: $(MAMMOTH_TYPE)"; \
> shopt -s nullglob; \
> files=( "$(MODELDIR)"/*.pt ); \
> keep=(); \
> for f in "$${files[@]}"; do \
>   b="$$(basename "$$f")"; \
>   case "$$b" in \
>     *_optim.pt) ;; \
>     *) keep+=( "$$f" );; \
>   esac; \
> done; \
> if [ "$${#keep[@]}" -eq 0 ]; then \
>   echo "mk-basic.mk: ℹ️ No inspectable .pt model files found in $(MODELDIR)"; \
>   exit 1; \
> fi; \
> module load cray-python; \
> /usr/bin/singularity exec \
>   -B "/scratch/$(DISKPROJECT):/scratch/$(DISKPROJECT):rw" \
>   -B "$(SELFDIR):$(SELFDIR):ro" \
>   -B "$(MODELDIR):$(MODELDIR):rw" \
>   -B "$(MAMMOTH_ROOT):$(MAMMOTH_ROOT):ro" \
>   --env PYTHONPATH="$(MAMMOTH_PYTHONPATH):$${PYTHONPATH:-}" \
>   "$(SIF)" \
>   python3 "$(INSPECT_MODEL_FILES)" --unsafe --depth 2 --top-mods 8 \
>           --model-summary --backend "$(MAMMOTH_TYPE)" --yaml-like "$${keep[@]}" \
>   > "$@"

$(MODELDIR) $(TESTINGDIR) $(DATADIR) $(TRAINCONFIG): 
> @set -euo pipefail; \
> [[ -d "$(MODELDIR)"    ]] || { echo "mk-basic.mk: ❌ Missing directory: $(MODELDIR)" >&2; exit 1; }; \
> [[ -d "$(TESTINGDIR)"  ]] || { echo "mk-basic.mk: ❌ Missing directory: $(TESTINGDIR)" >&2; exit 1; }; \
> [[ -d "$(DATADIR)"     ]] || { echo "mk-basic.mk: ❌ Missing directory: $(DATADIR)" >&2; exit 1; }; \
> [[ -s "$(TRAINCONFIG)" ]] || { echo "mk-basic.mk: ❌ Missing training config: $(TRAINCONFIG)" >&2; exit 1; }; \
> echo "mk-basic.mk: ✅ Directories and the config file found"

$(BAS_DONE): $(MODELDIR) $(TESTINGDIR) $(DATADIR) $(TRAINCONFIG) $(MAMMOTH_SELECTED) $(SACRE_ACTIVATE) | $(EVAL_DIRS_TO_CREATE)
> @set -euo pipefail; \
> MAMMOTHSEL="$$(cat "$(MAMMOTH_SELECTED)")"; \
> echo "mk-basic.mk:    Using: $$MAMMOTHSEL"; \
> echo "mk-basic.mk:    Ensured sacrebleu virtual environment"; \
> echo "mk-basic.mk:    Ensured the existence of local {tasks,configs,hypotheses,flags,logs,scores} directories"; \
> echo "mk-pairs.mk: ✨ I am happy with the basics."; \
> touch "$@"

mk-basic: $(BAS_DONE) 
> @echo "mk-basic.mk:    MODELDIR: $(MODELDIR)"; \
> echo  "mk-basic.mk:    PLAN_LOG: $(PLAN_LOG)"; \
> echo  "mk-basic.mk:    PLAN_ERR: $(PLAN_ERR)"; \
> [[ -z "$${SLURM_JOBID:-}" ]] || { echo "mk-basic.mk: Run make outside SLURM first" >&2; exit 1; }
> @echo "mk-basic.mk: ✅ Running outside SLURM"; \
> echo "mk-basic.mk: ✨ I am happy with the preparations (dirs, venvs, version)."; \
> echo

$(EVAL_DIRS_TO_CREATE):
> @mkdir -p "$@"

