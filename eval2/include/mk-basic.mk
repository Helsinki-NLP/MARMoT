# -----------------------------------------------------------------------------
# mk-basic.mk — Common setup for the eval2 workflow
# -----------------------------------------------------------------------------
# Included by the top-level Makefile. Provides model inspection, Mammoth
# selection, evaluation-directory creation, and Python environment setup.
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
#   Creates and displays MAMMOTH_SELECTED. Selects MAMMOTH64 when the model
#   summary contains the legacy head-dimension warning; otherwise selects
#   MAMMOTHDEF.
#
# venvs
#   Prepares the scoring, plotting, and planning environments, including
#   lang2vec installation and validation.
#
# lang2vec
#   Installs the local lang2vec checkout into VIEW_VENV, checks its distance
#   API, and records success in LANG2VEC_READY.
#
# clean-mammoth / clean-basic
#   Remove the Mammoth selection, or both the selection and model summary,
#   so they are regenerated when next required.
#
# test-sif / find-sif
#   Request a short Slurm GPU allocation to test the configured container
#   or list candidate containers.
#
# Inputs and assumptions
# ----------------------
# The including Makefile supplies:
#   MODELDIR, TESTINGDIR, DATADIR, TRAINCONFIG
#   EVAL_DIRS, BAS_DONE, PLAN_LOG, PLAN_ERR
#   MODEL_SUMMARY, MAMMOTH_SELECTED
#   INSPECT_MODEL_FILES, MAMMOTHDEF, MAMMOTH64
#   SACRE_VENV, PLOT_VENV, VIEW_VENV and their *_ACTIVATE paths
#   LANG2VEC_REPO, DISKPROJECT, JOBPROJECT
#
# This fragment currently defines SIF and LANG2VEC_READY itself.
# Recipes require Bash, the module command, and the cray-python module.
# Container operations use /usr/bin/singularity; test targets require Slurm.
# Environment installation requires access to package sources.
# Checkpoints must be trusted: inspection uses --unsafe loading.
#
# Reads
# -----
#   Training-configuration path and model checkpoints under MODELDIR.
#   The checkpoint inspector and configured container.
#   MODEL_SUMMARY when selecting the Mammoth implementation.
#   The lang2vec checkout, cloned if its setup.py is missing.
#
# Writes / effects
# ----------------
#   MODEL_SUMMARY       Inferred checkpoint architecture.
#   MAMMOTH_SELECTED    Selected Mammoth source path.
#   BAS_DONE            Basic-setup completion marker.
#   EVAL_DIRS           Evaluation directories, created as needed.
#   SACRE_VENV          SacreBLEU environment.
#   PLOT_VENV           Matplotlib environment.
#   VIEW_VENV           PyYAML, NetworkX, NumPy, SciPy, and lang2vec.
#   LANG2VEC_REPO       Local lang2vec source checkout.
#   LANG2VEC_READY      Successful lang2vec installation marker.
#
# Notes
# -----
# Paths are supplied by mk-paths.mk. This fragment does not change the working
# directory or independently detect the old/new evaluation layout.
# Existing activation files and completion markers control rebuilding.
# Setup checks are target-driven; existing file targets may skip their recipes.
# Start basic setup outside Slurm. Container test targets request allocations
# themselves.
# -----------------------------------------------------------------------------

.PHONY: mk-basic inspect-model-summary which-mammoth
.PHONY: clean-mammoth clean-basic
.PHONY: venvs lang2vec test-sif find-sif

inspect-model-summary: $(MODEL_SUMMARY)
> @echo "mk-basic.mk: 🛠️ Short model-file summary for $(MODELDIR):"; \
> cat $(MODEL_SUMMARY)

which-mammoth: $(MAMMOTH_SELECTED)
> @echo -n "Selected model: "
> @cat $(MAMMOTH_SELECTED)

$(MAMMOTH_SELECTED): $(MODEL_SUMMARY) | $(EVAL_DIRS)
> @set -euo pipefail; \
> echo "mk-basic.mk:    Reading $(MODEL_SUMMARY)"; \
> if grep -Fq 'use older Mammoth compatible with trained_head_dim=64' "$(MODEL_SUMMARY)"; then \
>   echo "mk-basic.mk:    The model has a hard-coded head_dim"; \
>   printf '%s\n' "$(MAMMOTH64)" > "$@"; \
> else \
>   echo "mk-basic.mk:    The model uses a computed head_dim"; \
>   printf '%s\n' "$(MAMMOTHDEF)" > "$@"; \
> fi; \
> echo "mk-basic.mk: ✅ Written file $@"

# This is needed if the mammoth binaries have been moved
clean-mammoth:
> rm -f "$(MAMMOTH_SELECTED)"

clean-basic:
> rm -f "$(MAMMOTH_SELECTED)" "$(MODEL_SUMMARY)"
> @echo "mk-basic.mk: ✨ Cleaning done."

# The folloing sends the names of the model files to the inspector and
# then stores the outputs to a model-summary.yaml file.
$(MODEL_SUMMARY): | $(EVAL_DIRS)
> @set -euo pipefail; \
> trap 'rm -f "$@"' ERR; \
> [[ -f "$(INSPECT_MODEL_FILES)" ]] || { echo "mk-basic.mk: ❌ Missing $(INSPECT_MODEL_FILES)" >&2; exit 1; }; \
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
>   --env PYTHONPATH="$(MAMMOTHDEF):$${PYTHONPATH:-}" \
>   "$(SIF)" \
>   python3 "$(INSPECT_MODEL_FILES)" --unsafe --depth 2 --top-mods 8 --model-summary --yaml-like "$${keep[@]}" \
>   > "$@"

$(MODELDIR) $(TESTINGDIR) $(DATADIR) $(TRAINCONFIG): 
> @set -euo pipefail; \
> [[ -d "$(MODELDIR)"    ]] || { echo "mk-basic.mk: ❌ Missing directory: $(MODELDIR)" >&2; exit 1; }; \
> [[ -d "$(TESTINGDIR)"  ]] || { echo "mk-basic.mk: ❌ Missing directory: $(TESTINGDIR)" >&2; exit 1; }; \
> [[ -d "$(DATADIR)"     ]] || { echo "mk-basic.mk: ❌ Missing directory: $(DATADIR)" >&2; exit 1; }; \
> [[ -s "$(TRAINCONFIG)" ]] || { echo "mk-basic.mk: ❌ Missing training config: $(TRAINCONFIG)" >&2; exit 1; }; \
> echo "mk-basic.mk: ✅ Directories and the config file found"

$(BAS_DONE): $(MODELDIR) $(TESTINGDIR) $(DATADIR) $(TRAINCONFIG) $(MAMMOTH_SELECTED) $(SACRE_ACTIVATE) | $(EVAL_DIRS)
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

$(EVAL_DIRS):
> @mkdir -p "$@"

$(SACRE_ACTIVATE):
> @set -euo pipefail; \
> trap 'rm -f "$@"' ERR; \
> echo "mk-basic.mk:    Building sacrebleu virtual environment..."; \
> module load cray-python; \
> python3 -m venv "$(SACRE_VENV)"; \
> source "$(SACRE_ACTIVATE)"; \
> python -m pip install --upgrade pip; \
> python -m pip install sacrebleu; \
> echo "Built scoring venv $(SACRE_VENV)"

$(PLOT_ACTIVATE):
> @set -euo pipefail; \
> trap 'rm -f "$@"' ERR; \
> echo "mk-basic.mk:    Building plotting virtual environment..."; \
> module load cray-python; \
> python3 -m venv "$(PLOT_VENV)"; \
> source "$(PLOT_ACTIVATE)"; \
> python -m pip install --upgrade pip; \
> python -m pip install matplotlib; \
> echo "Built plotting venv $(PLOT_VENV)"

# Basic planning environment.
$(VIEW_ACTIVATE):
> @set -euo pipefail; \
> trap 'rm -f "$@"' ERR; \
> echo "mk-basic.mk:    Building viewing virtual environment..."; \
> module load cray-python; \
> python3 -m venv "$(VIEW_VENV)"; \
> source "$(VIEW_ACTIVATE)"; \
> python -m pip install --upgrade pip; \
> python -m pip install pyyaml networkx numpy scipy; \
> echo "Built planning venv $(VIEW_VENV)"

# Source checkout, independent of the virtual environment.
$(LANG2VEC_REPO)/setup.py:
> @mkdir -p "$(dir $(LANG2VEC_REPO))"
> git clone https://github.com/antonisa/lang2vec.git "$(LANG2VEC_REPO)"

LANG2VEC_READY := $(VIEW_VENV)/.lang2vec-installed
$(LANG2VEC_READY): $(VIEW_ACTIVATE) $(LANG2VEC_REPO)/setup.py
> @set -euo pipefail; \
> module load cray-python; \
> "$(VIEW_VENV)/bin/python" -m pip install \
>   --upgrade --force-reinstall --no-deps "$(LANG2VEC_REPO)"; \
> (cd "$(VIEW_VENV)" && "$(VIEW_VENV)/bin/python" -c \
>   'import lang2vec.lang2vec as l2v; print("lang2vec:", l2v.__file__); print(l2v.distance("syntactic", ["eng", "deu"]))'); \
> touch "$@"

lang2vec: $(LANG2VEC_READY)

# Install and validate lang2vec separately.
.PHONY: venvs lang2vec
venvs: $(PLOT_ACTIVATE) $(SACRE_ACTIVATE) lang2vec

# SIF := /appl/local/laifs/containers/lumi-multitorch-u24r64f21m43t29-20260225_144743/lumi-multitorch-full-u24r64f21m43t29-20260225_144743.sif
SIF := /appl/local/laifs/containers/lumi-multitorch-u24r70f21m50t210-20260513_121430/lumi-multitorch-full-u24r70f21m50t210-20260513_121430.sif

test-sif:
> srun --partition=dev-g --account=$(JOBPROJECT) --time=00:10:00 \
>  --nodes=1 --ntasks=1 --cpus-per-task=1 --gpus-per-node=1 \
>  --pty bash -lc "set -euxo pipefail; /usr/bin/singularity inspect '$(SIF)'; /usr/bin/singularity exec '$(SIF)' python --version"

find-sif:
> srun --partition=dev-g --account=$(JOBPROJECT) --time=00:05:00 \
>  --nodes=1 --ntasks=1 --cpus-per-task=1 --gpus-per-node=1 \
>  --pty bash -lc 'set -euo pipefail; find -L /appl/local/laifs/containers -maxdepth 3 -type f \( -name "*multitorch*.sif" -o -name "*torch*.sif" \) -print'

