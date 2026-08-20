# models for OpenEuroLLM languages
#
# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)
# - monolingual text-prediction tasks from MultiSynth
#

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

## data directories

TRAINDATA := multisynt/train/len1024
DEVDATA   := flores200/dev

# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt


## denoising tasks (use same as MT training data)

DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_WEIGHTS    := $(foreach l,${DENOISE_TASK_IDS},1)


## English-centric translation tasks

DOCMT_TASK_IDS     := $(foreach l,$(filter-out eng,${LANGUAGES}),mt_$l-eng mt_eng-$l)
DOCMT_TRANSFORMS   := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_WEIGHTS      := $(foreach l,${DOCMT_TASK_IDS},10)


## task definitions put together

TASK_IDS            := ${DOCMT_TASK_IDS} ${DENOISE_TASK_IDS} 
TASK_TRANSFORMS     := ${DOCMT_TRANSFORMS} ${DENOISE_TRANSFORMS}
TASK_WEIGHT_FACTORS := ${DOCMT_WEIGHTS} ${DENOISE_WEIGHTS}


DECODER_LAYERS  := 2
MODEL_DIMENSION := 256


NR_OF_NODES                 := 9
USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})


## test zero-shot translation


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASK_IDS="mt_por-swe mt_swe-fin"
