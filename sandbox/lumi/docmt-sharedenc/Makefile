#
# document-level MT model over OpenEuroLLM languages
#  - english centric MultiSynth data
#  - language-specific encoders
#  - language-specific decoders


MODEL_NAME := mammoth

LANGS := bos bul cat ces dan deu ell eng \
	est eus fin fra gle glg hrv hun \
	isl ita kat lav lit mkd mlt nld \
	nno nob pol por ron slk slv spa \
	sqi srp_Cyrl swe tur ukr


## all English-centric translation tasks in both directions
TASKS := $(foreach l,$(filter-out eng,${LANGS}),$l-eng eng-$l)


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


## set the encoder to be shared among all langages
DEFAULT_ENCODER := "all"


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk



## test zero-shot translation


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASKS="deu-fra swe-fin"
