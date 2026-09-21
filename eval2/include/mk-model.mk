# -----------------------------------------------------------------------------
# Model aliases
# -----------------------------------------------------------------------------
# Shared base directory for model aliases.
XMODELS := /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-xtransformers

# Add model aliases here.
#MODEL_docmt4densmall      := $(XMODELS)/docmt-4pivots-denoise-small/mammoth
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
MODEL_ALIASES := docmt4denhalfbase docmt4denhalfsmall docmt4denhalfxl \
  docmt10denhalf docmt4 finnish finnish_denoise_xl denoise d_fincentric \
  d_halfsharedenc d_sharedenc LGAenc LGAenc_fincentric sentmtdenoise sentmthalfsmall \
  sentmthalfxl

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
