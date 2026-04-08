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
TASKS := $(sort $(foreach p,deu eng fra spa,$(foreach l,$(filter-out $p,${LANGS}),$l-$p $p-$l)))


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


## restrict number of GPU nodes
NR_OF_NODES := 8


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk


