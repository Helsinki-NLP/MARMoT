
LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## task definitions (leave out Georgian)

TASK_IDS := $(foreach l,$(filter-out kat,${LANGUAGES}),predict_$l-$l)


## data directories

TRAINDATA := multisynt/textpredict/train/len1024
DEVDATA   := multisynt/textpredict/dev/len1024


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt

## very big model architecture

MODEL_ARCHITECTURE := transformer-xl

## set the encoder to be shared among all langages

ENCODER         := "{lang}","all"
ENCODER_LAYERS  := 6,6


PRETRAINED_MODEL := $(shell realpath ../docmt-4pivots-denoise-halfsharedenc-xl/mammoth/)


include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

