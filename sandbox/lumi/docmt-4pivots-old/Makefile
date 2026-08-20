#
# document-level MT model over OpenEuroLLM languages
#  - german/english/french/spanish-centric MultiSynth data
#  - language-specific encoders
#  - language-specific decoders


MODEL_NAME := mammoth-docmt

LANGS := bos bul cat ces dan deu ell eng \
	est eus fin fra gle glg hrv hun \
	isl ita kat lav lit mkd mlt nld \
	nno nob pol por ron slk slv spa \
	sqi srp_Cyrl swe tur ukr


## all English-centric translation tasks in both directions

PIVOT_LANGS    := deu eng fra spa
TASKS          := $(sort $(foreach p,${PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGS}),$l-$p $p-$l)) fin-swe swe-fin fin-ukr ukr-fin)
TASK_IDS       := $(patsubst %,mt_%,${TASKS})


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk



info:
	@echo $(words ${TASK_IDS})


## test zero-shot translation


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASKS="por-swe swe-fin"
