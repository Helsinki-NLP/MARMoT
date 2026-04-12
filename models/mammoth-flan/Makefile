
#
# models for OpenEuroLLM languages
#
# - doc-level MT tasks:
#   - English-centric translation tasks from MultiSynth
# - sentence-level MT tasks: shuffled combination of the following resources for language pairs with > 10M training examples
#   - TatoebaChallenge training data
#   - OpenSubtitle 2024 parallel data for MT tasks
#   - HPLT parallel data for MT tasks
# - monolingual denoising tasks (using MultiSynth)
# - monolingual text-prediction tasks from MultiSynth
# - English-centric parallel text prediction tasks from MultiSynth
# - instruction data from FLAN collection
#

include ../../make/utilities.mk

OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

LANG_GROUPS  := zls zls roa zlw gmq gmw grk gmw \
		urj euq urj roa cel roa zls urj \
		gmq roa ccs bat bat zls sem gmw \
		gmq gmq zlw roa roa zlw zls roa \
		mul zls gmq trk zle

OELLM_LANGS_NOEN := $(filter-out eng,${OELLM_LANGS})


## MultiSynth document-level MT training data (English-centric)

DOCMT_LANGPAIRS := $(foreach l,${OELLM_LANGS_NOEN},$l-eng eng-$l)




## data directories

TRANSLATE_TRAIN_DOC  ?= multisynt/train/len1024
TRANSLATE_TRAIN_SENT ?= sentmt
TRANSLATE_DEV        ?= flores200/dev
PREDICT_TRAIN        ?= multisynt/textpredict/train/len1024
PREDICT_DEV          ?= multisynt/textpredict/dev/len1024
INSTRUCT_TRAIN       ?= instruct/langgroups/train
INSTRUCT_DEV         ?= instruct/langgroups/dev



## denoising tasks (MultiSynth data)

DENOISE_TASKS          := $(foreach l,${OELLM_LANGS},denoise_$l-$l)
DENOISE_TRAINDATA      := $(foreach l,${DENOISE_TASKS},${TRANSLATE_TRAIN_DOC})
DENOISE_DEVDATA        := $(foreach l,${DENOISE_TASKS},${TRANSLATE_DEV})
DENOISE_TRANSFORMS     := $(foreach l,${DENOISE_TASKS},denoising,filtertoolong)


## text-prediction tasks

PREDICT_TASKS          := $(foreach l,${OELLM_LANGS},predict_$l-$l)
PREDICT_TRAINDATA      := $(foreach l,${PREDICT_TASKS},${PREDICT_TRAIN})
PREDICT_DEVDATA        := $(foreach l,${PREDICT_TASKS},${PREDICT_DEV})
PREDICT_TRANSFORMS     := $(foreach l,${PREDICT_TASKS},filtertoolong)


## translation tasks

DOCMT_TASKS          := $(patsubst %,docmt_%,${DOCMT_LANGPAIRS})
DOCMT_TRAINDATA      := $(foreach l,${DOCMT_TASKS},${TRANSLATE_TRAIN_DOC})
DOCMT_DEVDATA        := $(foreach l,${DOCMT_TASKS},${TRANSLATE_DEV})
DOCMT_TRANSFORMS     := $(foreach l,${DOCMT_TASKS},filtertoolong)


## instruction tasks
##
## language pairs with > 10M taining examples
## (egrep '^ *[0-9]{8}' train/*.stats or similar queries)

INSTRUCT_LANGPAIRS     := gmw-ces gmw-deu gmw-eng gmw-fra roa-eng zlw-eng
INSTRUCT_TASKS         := $(patsubst %,instruct_%,${INSTRUCT_LANGPAIRS})
INSTRUCT_TRAINDATA     := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_TRAIN})
INSTRUCT_DEVDATA       := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_DEV})
INSTRUCT_TRANSFORMS    := $(foreach l,${INSTRUCT_TASKS},filtertoolong)





## define the training curriculum:
##
## - trainig steps when to start a certain task type
## - weight factors for each category (will be multiplied with data size)
##   (increasing factors as the curriculum moves on so that earlier tasks fade out)

DENOISE_TRAINSTEPS  := $(foreach l,${DENOISE_TASKS},0)
PREDICT_TRAINSTEPS  := $(foreach l,${PREDICT_TASKS},25000)
DOCMT_TRAINSTEPS    := $(foreach l,${DOCMT_TASKS},75000)
INSTRUCT_TRAINSTEPS := $(foreach l,${INSTRUCT_TASKS},150000)

DENOISE_WEIGHTS     := $(foreach l,${DENOISE_TASKS},1)
PREDICT_WEIGHTS     := $(foreach l,${PREDICT_TASKS},4)
DOCMT_WEIGHTS       := $(foreach l,${DOCMT_TASKS},16)
INSTRUCT_WEIGHTS    := $(foreach l,${INSTRUCT_TASKS},64)


BATCH_SIZE          := 8192
TRAINING_STEPS      := 250000
WARMUP_STEPS        := 5000



## task definitions put together

LANG_GROUPS_EXTENDED := ${LANG_GROUPS} gem ine mul sla
LANGS_WITH_FALLBACK  := $(OELLM_LANGS) ${LANG_GROUPS_EXTENDED}

# langgroup = $(call lookup,$1,$(OELLM_LANGS),$(LANG_GROUPS))
langgroup = $(call lookup_with_fallback,$1,$(LANGS_WITH_FALLBACK),$(LANG_GROUPS_EXTENDED))

MODEL_NAME          := mammoth
TASK_IDS            := ${DENOISE_TASKS} ${PREDICT_TASKS} ${DOCMT_TASKS} ${INSTRUCT_TASKS}
TASK_TRAINDATA      := ${DENOISE_TRAINDATA} ${PREDICT_TRAINDATA} ${DOCMT_TRAINDATA} ${INSTRUCT_TRAINDATA}
TASK_DEVDATA        := ${DENOISE_DEVDATA} ${PREDICT_DEVDATA} ${DOCMT_DEVDATA} ${INSTRUCT_DEVDATA}
TASK_TRAINSTEPS     := ${DENOISE_TRAINSTEPS} ${PREDICT_TRAINSTEPS} ${DOCMT_TRAINSTEPS} ${INSTRUCT_TRAINSTEPS}
TASK_WEIGHT_FACTORS := ${DENOISE_WEIGHTS} ${PREDICT_WEIGHTS} ${DOCMT_WEIGHTS} ${INSTRUCT_WEIGHTS}
TASK_TRANSFORMS     := ${DENOISE_TRANSFORMS}
TASKS               := $(shell echo "${TASK_IDS}" | tr ' ' "\n" | sed 's/^[^_]*_//')
TASK_LANGPAIRS      := $(foreach l,$(TASKS),$(call langgroup,$(firstword $(subst -, ,$l)))-$(lastword $(subst -, ,$l)))
TASK_ENCODERS       := $(foreach l,$(TASK_LANGPAIRS),"$(firstword $(subst -, ,$l))")





# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt

VOCAB_SRC_SIZE := 65472
VOCAB_TRG_SIZE := 32000



## additional model parameters

ENCODER_LAYERS   := 12
DECODER_LAYERS   := 12
XTRF_HEADS       := 12

USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


MAX_SEQ_LENGTH   := 1024
KEEP_CHECKPOINTS := 1


## distribute all tasks over 4 nodes

NR_OF_NODES := 4


include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

