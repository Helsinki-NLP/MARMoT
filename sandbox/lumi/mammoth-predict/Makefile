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
## (leave out Bosnian to fit all tasks on 18 compute nodes)

DENOISE_TASK_IDS   := $(foreach l,$(filter-out bos,${LANGUAGES}),denoise_$l-$l)
DENOISE_TRAINDATA  := $(foreach l,${DENOISE_TASK_IDS},${TRANSLATE_TRAIN})
DENOISE_DEVDATA    := $(foreach l,${DENOISE_TASK_IDS},${TRANSLATE_DEV})
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)


## text-prediction tasks
## (leave out Bosnian to fit all tasks on 18 compute nodes)

PREDICT_TASK_IDS   := $(foreach l,$(filter-out bos,${LANGUAGES}),predict_$l-$l)
PREDICT_TRAINDATA  := $(foreach l,${PREDICT_TASK_IDS},${PREDICT_TRAIN})
PREDICT_DEVDATA    := $(foreach l,${PREDICT_TASK_IDS},${PREDICT_DEV})


## English-centric translation tasks

DOCMT_TASK_IDS     := $(foreach l,$(filter-out eng,${LANGUAGES}),mt_$l-eng mt_eng-$l)
DOCMT_TRAINDATA    := $(foreach l,${DOCMT_TASK_IDS},${TRANSLATE_TRAIN})
DOCMT_DEVDATA      := $(foreach l,${DOCMT_TASK_IDS},${TRANSLATE_DEV})


## task definitions put together

TASK_IDS           := ${DENOISE_TASK_IDS} ${PREDICT_TASK_IDS} ${DOCMT_TASK_IDS}
TASK_TRAINDATA     := ${DENOISE_TRAINDATA} ${PREDICT_TRAINDATA} ${DOCMT_TRAINDATA}
TASK_DEVDATA       := ${DENOISE_DEVDATA} ${PREDICT_DEVDATA} ${DOCMT_DEVDATA}
TASK_TRANSFORMS    := ${DENOISE_TRANSFORMS}


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt


# ## additional model parameters

# ENCODER_LAYERS   := 12
# DECODER_LAYERS   := 12
# XTRF_HEADS       := 12


# ## reduce batch size for the bigger 12x12 model

# # BATCH_SIZE       := 8192
# BATCH_SIZE       := 16384



include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

