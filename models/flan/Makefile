
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


## OPUS sentence-level MT training data (with more that 10 million training exampels)

SENTMT_LANGPAIRS := bos-bul bos-ces bos-dan bos-deu bos-ell bos-eng bos-fin bos-fra bos-hrv bos-hun bos-ita bos-nld bos-pol bos-por bos-ron bos-spa bos-swe bos-tur bul-bos bul-ces bul-dan bul-deu bul-ell bul-eng bul-est bul-fin bul-fra bul-hrv bul-hun bul-ita bul-nld bul-pol bul-por bul-ron bul-slv bul-spa bul-swe bul-tur bul-ukr cat-eng cat-fra cat-ita cat-por cat-spa ces-bos ces-bul ces-dan ces-deu ces-ell ces-eng ces-est ces-fin ces-fra ces-hrv ces-hun ces-ita ces-nld ces-pol ces-por ces-ron ces-slv ces-spa ces-swe ces-tur ces-ukr dan-bos dan-bul dan-ces dan-deu dan-ell dan-eng dan-est dan-fin dan-fra dan-hrv dan-hun dan-ita dan-nld dan-pol dan-por dan-ron dan-slv dan-spa dan-swe dan-tur deu-bos deu-bul deu-ces deu-dan deu-ell deu-eng deu-est deu-fin deu-fra deu-hrv deu-hun deu-isl deu-ita deu-lav deu-lit deu-nld deu-pol deu-por deu-ron deu-slv deu-spa deu-swe deu-tur deu-ukr ell-bos ell-bul ell-ces ell-dan ell-deu ell-eng ell-est ell-fin ell-fra ell-hrv ell-hun ell-ita ell-nld ell-pol ell-por ell-ron ell-slk ell-slv ell-spa ell-swe ell-tur eng-bos eng-bul eng-cat eng-ces eng-dan eng-deu eng-ell eng-est eng-eus eng-fin eng-fra eng-gle eng-glg eng-hrv eng-hun eng-isl eng-ita eng-kat eng-lav eng-lit eng-mkd eng-mlt eng-nld eng-nob eng-pol eng-por eng-ron eng-slk eng-slv eng-spa eng-sqi eng-srp_Cyrl eng-swe eng-tur eng-ukr est-bul est-ces est-dan est-deu est-ell est-eng est-fin est-fra est-hrv est-hun est-ita est-nld est-pol est-por est-ron est-slv est-spa est-swe est-tur eus-eng eus-spa fin-bos fin-bul fin-ces fin-dan fin-deu fin-ell fin-eng fin-est fin-fra fin-hrv fin-hun fin-ita fin-nld fin-pol fin-por fin-ron fin-slv fin-spa fin-swe fin-tur fra-bos fra-bul fra-cat fra-ces fra-dan fra-deu fra-ell fra-eng fra-est fra-fin fra-hrv fra-hun fra-ita fra-nld fra-pol fra-por fra-ron fra-slv fra-spa fra-swe fra-tur fra-ukr gle-eng glg-eng glg-por glg-spa hrv-bos hrv-bul hrv-ces hrv-dan hrv-deu hrv-ell hrv-eng hrv-est hrv-fin hrv-fra hrv-hun hrv-ita hrv-nld hrv-pol hrv-por hrv-ron hrv-slv hrv-spa hrv-swe hrv-tur hrv-ukr hun-bos hun-bul hun-ces hun-dan hun-deu hun-ell hun-eng hun-est hun-fin hun-fra hun-hrv hun-ita hun-nld hun-pol hun-por hun-ron hun-slk hun-slv hun-spa hun-swe hun-tur hun-ukr isl-deu isl-eng ita-bos ita-bul ita-cat ita-ces ita-dan ita-deu ita-ell ita-eng ita-est ita-fin ita-fra ita-hrv ita-hun ita-lit ita-nld ita-pol ita-por ita-ron ita-slv ita-spa ita-swe ita-tur ita-ukr kat-eng lav-deu lav-eng lit-deu lit-eng lit-ita lit-pol lit-spa lit-tur mkd-eng mlt-eng nld-bos nld-bul nld-ces nld-dan nld-deu nld-ell nld-eng nld-est nld-fin nld-fra nld-hrv nld-hun nld-ita nld-pol nld-por nld-ron nld-slv nld-spa nld-swe nld-tur nld-ukr nob-eng pol-bos pol-bul pol-ces pol-dan pol-deu pol-ell pol-eng pol-est pol-fin pol-fra pol-hrv pol-hun pol-ita pol-lit pol-nld pol-por pol-ron pol-slk pol-slv pol-spa pol-swe pol-tur pol-ukr por-bos por-bul por-cat por-ces por-dan por-deu por-ell por-eng por-est por-fin por-fra por-glg por-hrv por-hun por-ita por-nld por-pol por-ron por-slv por-spa por-swe por-tur por-ukr ron-bos ron-bul ron-ces ron-dan ron-deu ron-ell ron-eng ron-est ron-fin ron-fra ron-hrv ron-hun ron-ita ron-nld ron-pol ron-por ron-slk ron-slv ron-spa ron-swe ron-tur slk-ell slk-eng slk-hun slk-pol slk-ron slk-spa slk-tur slv-bul slv-ces slv-dan slv-deu slv-ell slv-eng slv-est slv-fin slv-fra slv-hrv slv-hun slv-ita slv-nld slv-pol slv-por slv-ron slv-spa slv-swe slv-tur slv-ukr spa-bos spa-bul spa-cat spa-ces spa-dan spa-deu spa-ell spa-eng spa-est spa-eus spa-fin spa-fra spa-glg spa-hrv spa-hun spa-ita spa-lit spa-nld spa-pol spa-por spa-ron spa-slk spa-slv spa-swe spa-tur spa-ukr sqi-eng srp_Cyrl-eng swe-bos swe-bul swe-ces swe-dan swe-deu swe-ell swe-eng swe-est swe-fin swe-fra swe-hrv swe-hun swe-ita swe-nld swe-pol swe-por swe-ron swe-slv swe-spa swe-tur tur-bos tur-bul tur-ces tur-dan tur-deu tur-ell tur-eng tur-est tur-fin tur-fra tur-hrv tur-hun tur-ita tur-lit tur-nld tur-pol tur-por tur-ron tur-slk tur-slv tur-spa tur-swe tur-ukr ukr-bul ukr-ces ukr-deu ukr-eng ukr-fra ukr-hrv ukr-hun ukr-ita ukr-nld ukr-pol ukr-por ukr-slv ukr-spa ukr-tur

ifndef SENTMT_LANGPAIRS

  LUMI_DATAHOME := /scratch/project_462000964/MARMoT/data
  SENTMT_LANGPAIRS_FWD := $(sort $(basename $(strip $(notdir $(shell grep -E '^[0-9]{8}' ${LUMI_DATAHOME}/sentmt/*.stats | cut -f1 -d:)))))
  SENTMT_LANGPAIRS_REV := $(foreach l,${SENTMT_LANGPAIRS_FWD},$(call reverse,$l))
  SENTMT_LANGPAIRS_ALL := $(sort ${SENTMT_LANGPAIRS_FWD} ${SENTMT_LANGPAIRS_REV})

  ALL_OELLM_LANGPAIRS := $(foreach s,${OELLM_LANGS},$(foreach t,${OELLM_LANGS},$s-$t))
  SENTMT_LANGPAIRS := $(filter-out eng-eng por-por,$(filter ${SENTMT_LANGPAIRS_ALL},${ALL_OELLM_LANGPAIRS}))

endif



## data directories

TRANSLATE_TRAIN_DOC  ?= multisynt/train/len1024
TRANSLATE_TRAIN_SENT ?= sentmt
TRANSLATE_DEV        ?= flores200/dev
PREDICT_TRAIN        ?= multisynt/textpredict/train/len1024
PREDICT_DEV          ?= multisynt/textpredict/dev/len1024
INSTRUCT_TRAIN       ?= instruct/langgroups/train
INSTRUCT_DEV         ?= instruct/langgroups/dev


## translation tasks

DOCMT_TASKS          := $(patsubst %,docmt_%,${DOCMT_LANGPAIRS})
DOCMT_TRAINDATA      := $(foreach l,${DOCMT_TASKS},${TRANSLATE_TRAIN_DOC})
DOCMT_DEVDATA        := $(foreach l,${DOCMT_TASKS},${TRANSLATE_DEV})
DOCMT_TRANSFORMS     := $(foreach l,${DOCMT_TASKS},filtertoolong)
DOCMT_PREFIXES       := $(foreach l,${DOCMT_TASKS},<<translate>>)

SENTMT_TASKS         := $(patsubst %,sentmt_%,${SENTMT_LANGPAIRS})
SENTMT_TRAINDATA     := $(foreach l,${SENTMT_TASKS},${TRANSLATE_TRAIN_SENT})
SENTMT_DEVDATA       := $(foreach l,${SENTMT_TASKS},${TRANSLATE_DEV})
SENTMT_TRANSFORMS    := $(foreach l,${SENTMT_TASKS},filtertoolong)
SENTMT_PREFIXES      := $(foreach l,${SENTMT_TASKS},<<translate>>)

MT_TASKS         := ${DOCMT_TASKS} ${SENTMT_TASKS}
MT_TRAINDATA     := ${DOCMT_TRAINDATA} ${SENTMT_TRAINDATA}
MT_DEVDATA       := ${DOCMT_DEVDATA} ${SENTMT_DEVDATA}
MT_TRANSFORMS    := ${DOCMT_TRANSFORMS} ${SENTMT_TRANSFORMS}
MT_PREFIXES      := ${DOCMT_PREFIXES} ${SENTMT_PREFIXES}




## text-prediction tasks

PREDICT_TASKS          := $(foreach l,${OELLM_LANGS},predict_$l-$l)
PREDICT_TRAINDATA      := $(foreach l,${PREDICT_TASKS},${PREDICT_TRAIN})
PREDICT_DEVDATA        := $(foreach l,${PREDICT_TASKS},${PREDICT_DEV})
PREDICT_TRANSFORMS     := $(foreach l,${PREDICT_TASKS},filtertoolong)
PREDICT_PREFIXES       := $(foreach l,${PREDICT_TASKS},<<continue>>)





## instruction tasks
##
## language pairs with > 10M taining examples
## (egrep '^ *[0-9]{8}' train/*.stats or similar queries)

INSTRUCT_LANGPAIRS     := gmw-ces gmw-deu gmw-eng gmw-fra roa-eng zlw-eng
INSTRUCT_TASKS         := $(patsubst %,instruct_%,${INSTRUCT_LANGPAIRS})
INSTRUCT_TRAINDATA     := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_TRAIN})
INSTRUCT_DEVDATA       := $(foreach l,${INSTRUCT_TASKS},${INSTRUCT_DEV})
INSTRUCT_TRANSFORMS    := $(foreach l,${INSTRUCT_TASKS},filtertoolong)
# INSTRUCT_PREFIXES      := $(foreach l,${INSTRUCT_TASKS},<<reply>>)




## denoising tasks (MultiSynth data)

DENOISE_TASKS          := $(foreach l,${OELLM_LANGS},denoise_$l-$l)
DENOISE_TRAINDATA      := $(foreach l,${DENOISE_TASKS},${TRANSLATE_TRAIN_DOC})
DENOISE_DEVDATA        := $(foreach l,${DENOISE_TASKS},${TRANSLATE_DEV})
DENOISE_TRANSFORMS     := $(foreach l,${DENOISE_TASKS},denoising,filtertoolong)
DENOISE_PREFIXES       := $(foreach l,${DENOISE_TASKS},<<denoise>>)




## define the training curriculum:
##
## - trainig steps when to start a certain task type
## - weight factors for each category (will be multiplied with data size)
##   (increasing factors as the curriculum moves on so that earlier tasks fade out)

DENOISE_TRAINSTEPS  := $(foreach l,${DENOISE_TASKS},0)
SENTMT_TRAINSTEPS   := $(foreach l,${SENTMT_TASKS},25000)
DOCMT_TRAINSTEPS    := $(foreach l,${DOCMT_TASKS},50000)
PREDICT_TRAINSTEPS  := $(foreach l,${PREDICT_TASKS},75000)
INSTRUCT_TRAINSTEPS := $(foreach l,${INSTRUCT_TASKS},100000)

DENOISE_WEIGHTS     := $(foreach l,${DENOISE_TASKS},1)
SENTMT_WEIGHTS      := $(foreach l,${SENTMT_TASKS},2)
DOCMT_WEIGHTS       := $(foreach l,${DOCMT_TASKS},4)
PREDICT_WEIGHTS     := $(foreach l,${PREDICT_TASKS},8)
INSTRUCT_WEIGHTS    := $(foreach l,${INSTRUCT_TASKS},16)


TRAINING_STEPS      := 500000
WARMUP_STEPS        := 50000



## task definitions put together

LANG_GROUPS_EXTENDED := ${LANG_GROUPS} gem ine mul sla
LANGS_WITH_FALLBACK  := $(OELLM_LANGS) ${LANG_GROUPS_EXTENDED}

# langgroup = $(call lookup,$1,$(OELLM_LANGS),$(LANG_GROUPS))
langgroup = $(call lookup_with_fallback,$1,$(LANGS_WITH_FALLBACK),$(LANG_GROUPS_EXTENDED))

MODEL_NAME          := mammoth-flan
TASK_IDS            := ${DENOISE_TASKS} ${SENTMT_TASKS} ${DOCMT_TASKS} ${PREDICT_TASKS} ${INSTRUCT_TASKS}
TASK_TRAINDATA      := ${DENOISE_TRAINDATA} ${SENTMT_TRAINDATA} ${DOCMT_TRAINDATA} ${PREDICT_TRAINDATA} ${INSTRUCT_TRAINDATA}
TASK_DEVDATA        := ${DENOISE_DEVDATA} ${SENTMT_DEVDATA} ${DOCMT_DEVDATA} ${PREDICT_DEVDATA} ${INSTRUCT_DEVDATA}
TASK_TRAINSTEPS     := ${DENOISE_TRAINSTEPS} ${SENTMT_TRAINSTEPS} ${DOCMT_TRAINSTEPS} ${PREDICT_TRAINSTEPS} ${INSTRUCT_TRAINSTEPS}
TASK_WEIGHT_FACTORS := ${DENOISE_WEIGHTS} ${SENTMT_WEIGHTS} ${DOCMT_WEIGHTS} ${PREDICT_WEIGHTS} ${INSTRUCT_WEIGHTS}
TASK_SRCPREFIXES    := ${DENOISE_PREFIXES} ${SENTMT_PREFIXES} ${DOCMT_PREFIXES} ${PREDICT_PREFIXES}
TASK_TRANSFORMS     := ${DENOISE_TRANSFORMS}
TASKS               := $(shell echo "${TASK_IDS}" | tr ' ' "\n" | sed 's/^[^_]*_//')
TASK_LANGPAIRS      := $(foreach l,$(TASKS),$(call langgroup,$(firstword $(subst -, ,$l)))-$(lastword $(subst -, ,$l)))
TASK_ENCODERS       := $(foreach l,$(TASK_LANGPAIRS),"$(firstword $(subst -, ,$l))")






## task decoders require task-specific prefix token (and not language prefix)
## --> set default prefix to empty string!

ifneq (${TASK_SRCPREFIXES}${TASK_TRGPREFIXES},)
  ADD_LANGUAGE_TOKEN := true
  DEFAULT_SRCPREFIX  :=
  DEFAULT_TRGPREFIX  :=
else
  ADD_LANGUAGE_TOKEN := false
endif



# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt

VOCAB_SRC_SIZE := 65472
VOCAB_TRG_SIZE := 32000



## additional model parameters

ENCODER_LAYERS   := 12
DECODER_LAYERS   := 12
XTRF_HEADS       := 12

USE_DATASIZE_AS_TASK_WEIGHT := 1

MAX_SEQ_LENGTH   := 1024
KEEP_CHECKPOINTS := 1


## distribute all tasks over 4 nodes
## (this will be super crowded)

NR_OF_NODES := 4



include ../../make/marmot.mk


info:
	@echo $(words ${TASK_IDS})

