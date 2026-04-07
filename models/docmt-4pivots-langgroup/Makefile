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


## all task IDs and langgroup-based encoder definitions
## - English-centric translation tasks in both directions
## - task encoders: use the language groups defined in the TASKS

include ../../make/utilities.mk
langgroup = $(call lookup,$1,$(LANGS),$(LANG_GROUPS))


## 4 pivot languages + 4 extra language pairs to distribute uiformely across 35 nodes (280 tasks)

PIVOT_LANGS    := deu eng fra spa
TASKS          := $(sort $(foreach p,${PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGS}),$l-$p $p-$l)) fin-swe swe-fin fin-ukr ukr-fin)
TASK_LANGPAIRS := $(foreach l,$(TASKS),$(call langgroup,$(firstword $(subst -, ,$l)))-$(lastword $(subst -, ,$l)))
TASK_ENCODERS  := $(foreach l,$(TASKS),"$(firstword $(subst -, ,$l))")
TASK_IDS       := $(patsubst %,mt_%,${TASKS})


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
## use 65K lang-group vocabularies on encoder side

VOCAB          := tatoeba_hplt_multisynt
VOCAB_SRC_SIZE := 65472



## include this at the end to set all variables and
## to include all makefile targets for marmot experiments

include ../../make/marmot.mk


info:
	@echo $(words ${TASK_IDS})
