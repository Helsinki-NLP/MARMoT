
LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## task definitions (leave out Georgian)


## English-centric translation tasks

TASK_IDS     := $(foreach l,$(filter-out eng,${LANGUAGES}),sentmt_$l-eng sentmt_eng-$l)
TRAINDATA    := $(foreach l,${MT_TASK_IDS},sentmt)
# TASK_GPUS    := $(call rotating_gpu_assignment,0,9,$(words ${MT_TASK_IDS}))

## data directories

TRAINDATA := sentmt


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt

## very big model architecture

MODEL_ARCHITECTURE := transformer-xl

## set the encoder to be shared among all langages

ENCODER         := "{lang}","all"
ENCODER_LAYERS  := 6,6

NR_OF_NODES                 := 1
USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


PRETRAINED_MODEL := $(shell realpath ../docmt-4pivots-denoise-halfsharedenc-xl/mammoth)/
RESET_OPTIMIZER  := keep_states

include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

