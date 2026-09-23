# -----------------------------------------------------------------------------
# mk-confs.mk — Common setup for the eval2 workflow
# -----------------------------------------------------------------------------
# Included by the top-level Makefile. Provides Python environment setup.
#
# Main targets
# ------------
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
#   SACRE_VENV, PLOT_VENV, VIEW_VENV and their *_ACTIVATE paths
#   LANG2VEC_REPO, DISKPROJECT, JOBPROJECT
#
# This fragment currently defines SIF and LANG2VEC_READY itself.
# Recipes require Bash, the module command, and the cray-python module.
# Container operations use /usr/bin/singularity; test targets require Slurm.
# Environment installation requires access to package sources.
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
#   SACRE_VENV          SacreBLEU environment.
#   PLOT_VENV           Matplotlib environment.
#   VIEW_VENV           PyYAML, NetworkX, NumPy, SciPy, and lang2vec.
#   LANG2VEC_REPO       Local lang2vec source checkout.
#   LANG2VEC_READY      Successful lang2vec installation marker.
#
# Notes
# -----
# Start basic setup outside Slurm. Container test targets request allocations
# themselves.
# -----------------------------------------------------------------------------

.PHONY: venvs lang2vec test-sif find-sif


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
> srun --partition=dev-g --account=$(JOBPROJECT) --time=00:00:05 \
>  --nodes=1 --ntasks=1 --cpus-per-task=1 --gpus-per-node=1 \
>  --pty bash -lc "set -euxo pipefail; /usr/bin/singularity inspect '$(SIF)'; /usr/bin/singularity exec '$(SIF)' python --version"

find-sif:
> srun --partition=dev-g --account=$(JOBPROJECT) --time=00:00:05 \
>  --nodes=1 --ntasks=1 --cpus-per-task=1 --gpus-per-node=1 \
>  --pty bash -lc 'set -euo pipefail; find -L /appl/local/laifs/containers -maxdepth 3 -type f \( -name "*multitorch*.sif" -o -name "*torch*.sif" \) -print'

