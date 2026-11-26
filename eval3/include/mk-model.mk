# Registration and model resolution are separate from evaluation scheduling.
# The ready inventory is read at Make startup; a subsequent invocation sees
# changes to that inventory. Alias resolution prefers the architecture root.

# -----------------------------------------------------------------------------
# Model aliases
# -----------------------------------------------------------------------------
# Shared base directory for model aliases.
XMODELS := /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-xtransformers
PMODELS := /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo
NMODELS := /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-architecture

# PyTorch models accepted for evaluation.  This is only registration:
# no model is submitted merely by appearing in this file.
READY_MODELS_FILE ?= $(SELFDIR)/models.ready
READY_MODEL_ALIASES := $(strip $(shell \
  test -f "$(READY_MODELS_FILE)" && sed '/^[[:space:]]*$$/d' "$(READY_MODELS_FILE)"))

#Resolve each ready model to its actual checkpoint directory.
# Prefer hpo-architecture if the alias exists in both locations.
$(foreach a,$(READY_MODEL_ALIASES),\
  $(eval MODEL_$(a) := $(firstword \
    $(foreach base,$(NMODELS) $(PMODELS),\
      $(if $(wildcard $(base)/$(a)/mammoth/model_best*),\
        $(base)/$(a)/mammoth)))))

# Keep only ready aliases whose checkpoint directories were resolved.
# This also protects against a stale models.ready file.
READY_MODEL_ALIASES := $(strip \
  $(foreach a,$(READY_MODEL_ALIASES),\
    $(if $(strip $(MODEL_$(a))),$(a))))

.PHONY: models-ready
models-ready:
> @set -euo pipefail; \
> tmp="$$(mktemp "$(READY_MODELS_FILE).tmp.XXXXXX")"; \
> trap 'rm -f -- "$$tmp"' EXIT; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
>   | awk -F '\t' 'NR>1 && $$2=="YES" {print $$1}' \
>   | sort -u > "$$tmp"; \
> if [ ! -s "$$tmp" ]; then \
>   echo "ERROR: No ready models found; refusing to replace $(READY_MODELS_FILE)" >&2; \
>   exit 1; \
> fi; \
> mv -- "$$tmp" "$(READY_MODELS_FILE)"; \
> echo "mk-model.mk: Updated $(READY_MODELS_FILE): $$(wc -l < "$(READY_MODELS_FILE)") models"

.PHONY: models-ready-preview
models-ready-preview:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
>   | awk -F '\t' 'NR>1 && $$2=="YES" {print $$1}' \
>   | sort -u


# Add model aliases here.
MODEL_big-2p-GAenc-Ldec-320k := $(PMODELS)/big-2p-GAenc-Ldec-320k/mammoth

MODEL_docmt4denhalfbig    := $(XMODELS)/docmt-4pivots-denoise-halfsharedenc-big/mammoth
MODEL_docmt4denhalfbase   := $(XMODELS)/docmt-4pivots-denoise-halfsharedenc-base/mammoth
MODEL_docmt4denhalfsmall  := $(XMODELS)/docmt-4pivots-denoise-halfsharedenc-small/mammoth
MODEL_docmt4denhalfxl     := $(XMODELS)/docmt-4pivots-denoise-halfsharedenc-xl/mammoth
MODEL_docmt10denhalf      := $(XMODELS)/docmt-10pivots-denoise-halfsharedenc/mammoth
MODEL_docmt4              := $(XMODELS)/docmt-4pivots/mammoth
MODEL_finnish             := $(XMODELS)/finnish/mammoth
MODEL_finnish_denoise_xl  := $(XMODELS)/finnish-denoise-xl/mammoth
MODEL_denoise             := $(XMODELS)/docmt-denoise/mammoth
MODEL_d_fincentric        := $(XMODELS)/docmt-denoise-fincentric/mammoth
MODEL_d_halfsharedenc     := $(XMODELS)/docmt-denoise-halfsharedenc/mammoth
MODEL_d_sharedenc         := $(XMODELS)/docmt-denoise-sharedenc/mammoth
MODEL_LGAenc              := $(XMODELS)/docmt-denoise-LGAenc/mammoth
MODEL_LGAenc_fincentric   := $(XMODELS)/docmt-denoise-LGAenc-fincentric/mammoth
MODEL_sentmtdenoise       := $(XMODELS)/sentmt-denoise/mammoth
MODEL_sentmthalfsmall     := $(XMODELS)/sentmt-halfsharedenc-small/mammoth
MODEL_sentmthalfxl        := $(XMODELS)/sentmt-halfsharedenc-xl/mammoth
EX_MANUAL_MODEL_ALIASES := docmt4denhalfbase docmt4denhalfsmall docmt4denhalfxl \
  docmt10denhalf docmt4 finnish finnish_denoise_xl denoise d_fincentric \
  d_halfsharedenc d_sharedenc LGAenc LGAenc_fincentric sentmtdenoise sentmthalfsmall \
  sentmthalfxl big-2p-GAenc-Ldec-320k

MODEL_ALIASES := $(sort $(MANUAL_MODEL_ALIASES) $(READY_MODEL_ALIASES))

# Explicit list only: never submit all registered models accidentally.
CONTINUE_MODELS ?= $(MODEL_ALIASES)

# Naming conventions for tasks:
# * sentmt: sentence-level MT with OPUS data (Tatoeba TC, HPLT, OpenSubtitles2024)
# * docmt: document-level MT with synthetic data (max length 1024 characters)
# * 4pivots: English/Spanish/German/French-centric MT training data (default otherwise is English-centric)
# * denoise: monolingual denoising tasks (using doc-level synthetic data, English is original)
#
# Naming conventions for parameter sharing:
# * sharedenc: fully shared encoder (but still language-specific vocabs/embeddings)
# * halfsharedenc: half of the encoder is shared across all languages, the other is language-specific
# * LGAenc: encoders with three components: language-specific + shared across language group + fully-shared
# * default is to have completely language-specific encoders and decoders
#
# Naming conventions for model sizes:
# * tiny: transformer-tiny (student) model with 2 decoder layers and model dimension = 256
# * small: transformer-small (student) model with 2 decoder layers and model dimension = 512
# * base (default): transformer-base model (6x6) and model dimension = 512
# * big: transformer-big model (6x6) with 16 attention heads and double model dimensions (1024)
# * xl: 12x12 transformer model with 16 attention heads and double model dimensions (1024)
#
# Models
# Training on English/Spanish/German/French-centric machine translatino tasks
# * docmt-4pivots
# * docmt-4pivots-denoise-halfsharedenc-small
# * docmt-4pivots-denoise-halfsharedenc-base
# * docmt-4pivots-denoise-halfsharedenc-xl
# Training on English-centric machine translation tasks + monolingual denoising:
# * sentmt-denoise
# * docmt-denoise
# * docmt-denoise-sharedenc
# * docmt-denoise-halfsharedenc
# * docmt-denoise-LGAenc
# Other models:
# * predict-halfshared-xl:
#   - initialized with MT model with 4 pivot languages in training data
# * flan-halfshared-xl:
#   - initialized with MT model with 4 pivot languages in training data

# Models to migrate. Override from the command line if desired:
#   make eval3-migrate-all MIGRATE_MODELS="model1 model2 model3"
MIGRATE_MODELS ?= $(MODEL_ALIASES)

.PHONY: eval3-migrate-all
eval3-migrate-all:
> @set -euo pipefail; \
> for model in $(MIGRATE_MODELS); do \
>   echo >&2; \
>   echo "============================================================" >&2; \
>   echo "eval3: migrating $$model" >&2; \
>   echo "============================================================" >&2; \
>   $(MAKE) --no-print-directory "$$model" eval3-migrate-dry | bash; \
> done

.PHONY: stale-hypotheses
stale-hypotheses:
> @set -euo pipefail; \
> printf '%-40s  %-12s  %-19s  %-19s\n' \
>   "MODEL" "STATUS" "NEWEST MODEL" "OLDEST HYPOTHESIS"; \
> printf '%-40s  %-12s  %-19s  %-19s\n' \
>   "----------------------------------------" \
>   "------------" "-------------------" "-------------------"; \
> for item in $(foreach a,$(MODEL_ALIASES),'$(a)|$(MODEL_$(a))'); do \
>   a="$${item%%|*}"; \
>   model="$${item#*|}"; \
>   newest=0; \
>   for f in "$$model"/model_best*; do \
>     [ -f "$$f" ] || continue; \
>     t="$$(stat -c %Y "$$f")"; \
>     if (( t > newest )); then \
>       newest="$$t"; \
>     fi; \
>   done; \
>   oldest=0; \
>   for f in "$$model"/evaluation/hypotheses/*.hyp; do \
>     [ -f "$$f" ] || continue; \
>     t="$$(stat -c %Y "$$f")"; \
>     if (( oldest == 0 || t < oldest )); then \
>       oldest="$$t"; \
>     fi; \
>   done; \
>   if (( newest == 0 )); then \
>     status="NO MODEL"; \
>     newest_s="-"; \
>   else \
>     newest_s="$$(date -d "@$$newest" '+%Y-%m-%d %H:%M:%S')"; \
>     if (( oldest == 0 )); then \
>       status="NO HYP"; \
>     elif (( newest > oldest )); then \
>       status="STALE"; \
>     else \
>       status="OK"; \
>     fi; \
>   fi; \
>   if (( oldest == 0 )); then \
>     oldest_s="-"; \
>   else \
>     oldest_s="$$(date -d "@$$oldest" '+%Y-%m-%d %H:%M:%S')"; \
>   fi; \
>   printf '%-40s  %-12s  %-19s  %-19s\n' \
>     "$$a" "$$status" "$$newest_s" "$$oldest_s"; \
> done


TRAINING_STATUS_MARGIN ?= 3600
TRAINING_STATUS_ROOTS ?= $(PMODELS) $(NMODELS)

.PHONY: inspect-training-status \
        inspect-training-status-tsv \
        inspect-not-ready \
        inspect-evaluate-now \
        inspect-training-review \
        inspect-ready-mismatch

inspect-training-status-tsv:
> @module load cray-python && \
> LC_ALL=C python3 bin/inspect_training_status.py \
>   --roots $(TRAINING_STATUS_ROOTS) \
>   --margin "$(TRAINING_STATUS_MARGIN)" \
>   --ready-file "$(READY_MODELS_FILE)"

inspect-training-status:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
> | column -t -s "$$(printf '\t')"

inspect-not-ready:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
> | awk -F '\t' 'NR==1 || $$2=="NO"' \
> | cut -f1-6,15 \
> | column -t -s "$$(printf '\t')"

inspect-evaluate-now:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
> | awk -F '\t' 'NR==1 || $$5=="EVALUATE_NOW" || $$5=="REEVALUATE_NOW"' \
> | cut -f1-6,13-15 \
> | column -t -s "$$(printf '\t')"

inspect-training-review:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
> | awk -F '\t' 'NR==1 || $$2=="REVIEW" || $$5 ~ /^REVIEW_/' \
> | cut -f1-6,15 \
> | column -t -s "$$(printf '\t')"

inspect-ready-mismatch:
> @set -euo pipefail; \
> $(MAKE) --no-print-directory -s inspect-training-status-tsv \
> | awk -F '\t' 'NR==1 || $$4!="OK"' \
> | cut -f1-6,15 \
> | column -t -s "$$(printf '\t')"
