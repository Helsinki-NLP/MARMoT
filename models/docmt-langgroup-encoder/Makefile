#
# document-level MT model over OpenEuroLLM languages
#  - english centric MultiSynth data
#  - language-group-specific encoders
#  - language-specific decoders


MODEL_NAME := mammoth-docmt

LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

LANG_GROUPS := 	zls zls roa zlw gmq gmw grk gmw \
		urj euq urj roa cel roa zls urj \
		gmq roa ccs bat bat zls sem gmw \
		gmq gmq zlw roa roa zlw zls roa \
		mul zls gmq trk zle


## data directories and vocabularies

TRAINDATA := multisynt/train/len1024
DEVDATA   := flores200/dev
TESTDATA  := flores200/devtest
VOCAB     := tatoeba_hplt_multisynt

## all task IDs and langgroup-based encoder definitions
## - English-centric translation tasks in both directions
## - task encoders: use the language groups defined in the TASKS

include ../../make/utilities.mk
langgroup = $(call lookup,$1,$(LANGS),$(LANG_GROUPS))

TASK_LANGPAIRS := $(foreach l,$(filter-out eng,${LANGS}),$l-eng eng-$l)
TASK_IDS       := $(patsubst %,mt_%,${TASK_LANGPAIRS})
TASKS          := $(foreach l,$(TASK_LANGPAIRS),$(call langgroup,$(firstword $(subst -, ,$l)))-$(lastword $(subst -, ,$l)))
TASK_ENCODERS  := $(foreach l,$(TASKS),"$(firstword $(subst -, ,$l))")


## final model parameters

ENCODER_LAYERS    := 6
DECODER_LAYERS    := 6
XTRF_HEADS        := 8
MAX_SEQ_LENGTH    := 1024
KEEP_CHECKPOINTS  := 1
VOCAB_SRC_SIZE    := 65472
VOCAB_TRG_SIZE    := 32000


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments

include ../../make/marmot.mk

