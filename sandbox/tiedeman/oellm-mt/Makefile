
#
# big model for OpenEuroLLM languages
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
# model:
# - 3-component encoder? 4+4+4
# - language-specific decoder? 12 layers
# - warmup: 10000 steps
# - decay starting at 10000 steps
#

OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

OELLM_LANGS_NOEN := $(filter-out eng,${OELLM_LANGS})



## MultiSynth document-level MT training data (English-centric)

DOCMT_LANGPAIRS := $(foreach l,${OELLM_LANGS_NOEN},$l-eng eng-$l)


## OPUS sentence-level MT training data (with more that 10 million training exampels)

ifndef SENTMT_LANGPAIRS

  reverse = $(lastword $(subst -, ,$(1)))-$(firstword $(subst -, ,$(1)))
  LUMI_DATAHOME := /scratch/project_462000964/MARMoT/data
  # SENTMT_LANGPAIRS := $(sort $(basename $(basename $(notdir $(wildcard ${LUMI_DATAHOME}/sentmt/*.gz))
  SENTMT_LANGPAIRS_FWD := $(sort $(basename $(strip $(notdir $(shell grep -E '^[0-9]{8}' ${LUMI_DATAHOME}/sentmt/*.stats | cut -f1 -d:)))))
  SENTMT_LANGPAIRS_REV := $(foreach l,${SENTMT_LANGPAIRS_FWD},$(call reverse,$l))
  SENTMT_LANGPAIRS_ALL := $(sort ${SENTMT_LANGPAIRS_FWD} ${SENTMT_LANGPAIRS_REV})

  ALL_OELLM_LANGPAIRS := $(foreach s,${OELLM_LANGS},$(foreach t,${OELLM_LANGS},$s-$t))
  SENTMT_LANGPAIRS := $(filter-out eng-eng por-por,$(filter ${SENTMT_LANGPAIRS_ALL},${ALL_OELLM_LANGPAIRS}))

endif



## data directories

TRANSLATE_TRAIN_DOC  := multisynt/train/len1024
TRANSLATE_TRAIN_SENT := sentmt
TRANSLATE_DEV        := flores200/dev
PREDICT_TRAIN        := multisynt/textpredict/train/len1024
PREDICT_DEV          := multisynt/textpredict/dev/len1024
INSTRUCT_TRAIN       := instruct/train
INSTRUCT_DEV         := instruct/dev


## translation tasks

DOCMT_TASKS      := $(patsubst %,docmt_%,${DOCMT_LANGPAIRS})
SENTMT_TASKS     := $(patsubst %,sentmt_%,${SENTMT_LANGPAIRS})
DOCMT_TRAINDATA  := $(foreach l,${DOCMT_TASKS},${TRANSLATE_TRAIN_DOC})
SENTMT_TRAINDATA := $(foreach l,${SENTMT_TASKS},${TRANSLATE_TRAIN_SENT})

MT_TASKS         := ${DOCMT_TASKS} ${SENTMT_TASKS}
MT_TRAINDATA     := ${DOCMT_TRAINDATA} ${SENTMT_TRAINDATA}
MT_DEVDATA       := $(foreach l,${MT_TASKS},${TRANSLATE_DEV})
# MT_TASK_PREFIXES := $(foreach l,${MT_TASKS},<<translate>>)


## text-prediction tasks

# PREDICT_LANGS          := $(filter-out bos,${OELLM_LANGS})
PREDICT_LANGS          := ${OELLM_LANGS}
PREDICT_TASKS          := $(foreach l,${PREDICT_LANGS},predict_$l-$l)
PREDICT_TRAINDATA      := $(foreach l,${PREDICT_TASKS},${PREDICT_TRAIN})
PREDICT_DEVDATA        := $(foreach l,${PREDICT_TASKS},${PREDICT_DEV})
# PREDICT_TASK_PREFIXES  := $(foreach l,${PREDICT_TASKS},<<continue>>)


## instruction tasks
##
## language pairs with > 10M taining examples
## (egrep '^ *[0-9]{8}' train/*.stats | grep -v total)

INSTRUCT_LANGPAIRS     := ces-eng deu-eng eng-eng fra-eng
INSTRUCT_TASKS         := $(patsubst %,zsinstruct_%,${INSTRUCT_LANGPAIRS})
INSTRUCT_TRAINDATA     := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_TRAIN})
INSTRUCT_DEVDATA       := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_DEV})
# INSTRUCT_TASK_PREFIXES := $(foreach l,${INSTRUCT_TASKS},<<reply>>)


## denoising tasks (MultiSynth data)

DENOISE_TASKS          := $(foreach l,${OELLM_LANGS},denoise_$l-$l)
DENOISE_TRAINDATA      := $(foreach l,${DENOISE_TASKS},${TRANSLATE_TRAIN_DOC})
DENOISE_DEVDATA        := $(foreach l,${DENOISE_TASKS},skip)
DENOISE_TRANSFORMS     := $(foreach l,${DENOISE_TASKS},denoising,filtertoolong)
# DENOISE_TRANSFORMS     := $(foreach l,${DENOISE_TASKS},denoising,prefix,filtertoolong)
# DENOISE_TASK_PREFIXES  := $(foreach l,${DENOISE_TASKS},<<denoise>>)


## all task IDs and data directories

# TASK_IDS         := ${DENOISE_TASKS} ${PREDICT_TASKS} ${MT_TASKS} ${INSTRUCT_TASKS}
# TASK_TRAINDATA   := ${DENOISE_TRAINDATA} ${PREDICT_TRAINDATA} ${MT_TRAINDATA} ${INSTRUCT_TRAINDATA}
# TASK_DEVDATA     := ${DENOISE_DEVDATA} ${PREDICT_DEVDATA} ${MT_DEVDATA} ${INSTRUCT_DEVDATA}
# TASK_TRANSFORMS  := ${DENOISE_TRANSFORMS}

TASK_IDS         := ${MT_TASKS}
TASK_TRAINDATA   := ${MT_TRAINDATA}
TASK_DEVDATA     := ${MT_DEVDATA}



## task encoder definitions
## NOTE: requires `langgroups` tool!
##
## helper function that create 3-component encoders:
## - 2-levels of intermediate language groups if they exist
## - final component: shared among all languages


## ENC_LANG = encoder languages
## ENC_COMP = encoder components (note: placeholder "SRC")

ENC_LANG  := $(shell echo "${TASK_IDS}" | tr ' ' "\n" | sed 's/^[^_]*_//' | cut -f1 -d-)
META_LANG := $(shell iso639 -m ${ENC_LANG} 2>/dev/null)
ENC_COMP  := $(shell langgroup -P ${META_LANG} 2>/dev/null | \
		tr ' ' "\n" | sed 's/:mul//' | cut -f1,2 -d: | \
		sed 's/^/SRC:/' | rev | cut -f1,2 -d: | rev | \
		sed 's/$$/:all/' | sed 's/:/","/g;s/^/"/;s/$$/"/;')

## need to replace the placeholder "SRC" with the current encoder (meta) language

TASK_ENC_NR   := $(shell seq $(words ${ENC_COMP}))
TASK_ENCODERS := $(foreach e,$(TASK_ENC_NR),$(subst "SRC","$(word $e,${META_LANG})",$(word $e,${ENC_COMP})))



## OLD: take parent and grand-parent language group per meta-language
## ISSUE: some languages have no intermediate language groups

# META_SRCLANGS        := $(shell iso639 -m ${SRCLANGS} 2>/dev/null)
# SRCLANG_PARENTS      := $(shell langgroup -p ${META_SRCLANGS} 2>/dev/null)
# SRCLANG_GRANDPARENTS := $(shell langgroup -p ${SRCLANG_PARENTS} 2>/dev/null)

# TASK_ENCODERS := $(foreach l,$(shell seq $(words ${TASK_IDS})),"$(word $l,${SRCLANG_PARENTS})","$(word $l,${SRCLANG_GRANDPARENTS})","all")



## task decoders require tas-specific prefix token (and not language prefix)
## --> set default prefix to empty string!

ADD_LANGUAGE_TOKEN := false
# ADD_LANGUAGE_TOKEN := true
# DEFAULT_SRCPREFIX  :=
# DEFAULT_TRGPREFIX  :=



## final model parameters

MODEL_NAME := mammoth-t5

ENCODER_LAYERS := 4,4,4
DECODER_LAYERS := 12


DEVDATA_BASENAME               := *
MAX_SEQ_LENGTH                 := 1024
KEEP_CHECKPOINTS               := 1
SKIP_SAME_LANGUAGE_VALID_TASKS := 0


include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt


info:
	@echo $(words ${TASK_IDS})



.PHONY: %.mammoth-t5-base
%.mammoth-t5-base:
	@${MAKE} -s MODEL_NAME=mammoth-t5-base \
		ENCODER_LAYERS=2,2,2 \
		DECODER_LAYERS=6 \
	$(basename $@)

.PHONY: %.mammoth-t5-basetest
%.mammoth-t5-basetest:
	@${MAKE} -s MODEL_NAME=mammoth-t5-basetest \
		ENCODER_LAYERS=2,2,2 \
		DECODER_LAYERS=6 \
	$(basename $@)


.PHONY: %.mammoth-t5-smalldec
%.mammoth-t5-smalldec:
	@${MAKE} -s MODEL_NAME=mammoth-t5-smalldec \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)


.PHONY: %.mammoth-t5-small
%.mammoth-t5-small:
	@${MAKE} -s MODEL_NAME=mammoth-t5-small \
		ENCODER_LAYERS=2,2,2 \
		DECODER_LAYERS=3 \
	$(basename $@)
