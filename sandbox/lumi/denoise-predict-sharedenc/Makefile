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

TRANSLATE_TRAIN    := multisynt/train/len1024
TRANSLATE_DEV      := flores200/dev
PREDICT_TRAIN      := multisynt/textpredict/train/len1024
PREDICT_DEV        := multisynt/textpredict/dev/len1024



## denoising tasks (use same as MT training data)
## (leave out Bosnian to fit all tasks on 9 compute nodes)

DENOISE_TASK_IDS   := $(foreach l,$(filter-out bos,${LANGUAGES}),denoise_$l-$l)
DENOISE_TRAINDATA  := $(foreach l,${DENOISE_TASK_IDS},${TRANSLATE_TRAIN})
DENOISE_DEVDATA    := $(foreach l,${DENOISE_TASK_IDS},${TRANSLATE_DEV})
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_WEIGHTS    := $(foreach l,${DENOISE_TASK_IDS},1)


## text-prediction tasks
## (leave out Bosnian to fit all tasks on 9 compute nodes)

PREDICT_TASK_IDS   := $(foreach l,$(filter-out bos,${LANGUAGES}),predict_$l-$l)
PREDICT_TRAINDATA  := $(foreach l,${PREDICT_TASK_IDS},${PREDICT_TRAIN})
PREDICT_DEVDATA    := $(foreach l,${PREDICT_TASK_IDS},${PREDICT_DEV})
PREDICT_WEIGHTS    := $(foreach l,${PREDICT_TASK_IDS},10)



## task definitions put together

TASK_IDS            := ${DENOISE_TASK_IDS} ${PREDICT_TASK_IDS}
TASK_TRAINDATA      := ${DENOISE_TRAINDATA} ${PREDICT_TRAINDATA}
TASK_DEVDATA        := ${DENOISE_DEVDATA} ${PREDICT_DEVDATA}
TASK_TRANSFORMS     := ${DENOISE_TRANSFORMS}
TASK_WEIGHT_FACTORS := ${DENOISE_WEIGHTS} ${PREDICT_WEIGHTS}


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt


## set the encoder to be shared among all langages

DEFAULT_ENCODER := "all"


NR_OF_NODES                 := 9
USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

