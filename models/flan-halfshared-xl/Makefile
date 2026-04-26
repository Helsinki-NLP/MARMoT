

INSTRUCT_LANGPAIRS := ces-eng deu-eng eng-eng fin-eng fra-eng ron-eng
TASK_IDS           := $(patsubst %,instruct_%,${INSTRUCT_LANGPAIRS})

## data directories

TRAINDATA := instruct/train
DEVDATA   := instruct/dev


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt


## very big model architecture

MODEL_ARCHITECTURE := transformer-xl

## set the encoder to be shared among all langages

ENCODER         := "{lang}","all"
ENCODER_LAYERS  := 6,6


PRETRAINED_MODEL := $(shell realpath ../docmt-4pivots-denoise-halfsharedenc-xl)


include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

