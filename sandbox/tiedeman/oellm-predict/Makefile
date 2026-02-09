#-*-makefile-*-
##-----------------------------------------------------------
## testing multi-node job
##
##   the job fails with some strange error message about
##   'ValueError: ProcessGroupNCCL is only supported with GPUs, no GPUs found!'
##
##   however, manually starting the job with the same slurm script
##   and sbatch from command-line seems to work --> WHY?
##-----------------------------------------------------------

MODEL_NAME := oellm-predict

# 37 OpenEuroLLM languages
# --> right now it's problematic to have a number of tasks that
#     does not distribute well over nodes with one task per GPU
# --> need to remove 4 languages, let's leave out nno,mkd,bos,kat

OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## trying to make all kinds of language and language pairs subsets to meet our requirements
##
## 36_LANGS ............ 36 OELLM languages (leaving out bos)
## 32_LANGS ............ 32 OELLM languages (leaving out bos kat mkd nno srp_Cyrl)
##
## 36_LANGS_NOEN ....... 36 OELLM languages (leaving out eng)
## 32_LANGS_NOEN ....... 32 OELLM languages (leaving out eng bos kat mkd nno)

36_LANGS_NOEN := $(filter-out eng,${OELLM_LANGS})
32_LANGS_NOEN := $(filter-out eng bos kat mkd nno,${OELLM_LANGS})

36_LANGS := $(filter-out bos,${OELLM_LANGS})
32_LANGS := $(filter-out bos kat mkd nno srp_Cyrl,${OELLM_LANGS})


NR_LANGS ?= 32

ifeq (${NR_LANGS},36)
  LANGS         ?= ${36_LANGS}
  LANGS_NOEN    ?= ${36_LANGS_NOEN}
else
  LANGS         ?= ${32_LANGS}
  LANGS_NOEN    ?= ${32_LANGS_NOEN}
endif

META_LANGS      ?= $(shell iso639 -m ${LANGS} 2>/dev/null)
META_LANGS_NOEN ?= $(shell iso639 -m ${LANGS_NOEN} 2>/dev/null)


## old ....
#
# LANGS := bul cat ces dan deu ell est eus \
#	fin fra gle glg hrv hun isl ita \
#	lav lit mlt nld nob pol por ron \
#	slk slv spa sqi srp_Cyrl swe tur ukr
#
# META_LANGS  := $(shell iso639 -m ${LANGS} 2>/dev/null)
#
## end of old ....


TRANSLATE_TRAIN := multisynt/train/len1024
TRANSLATE_DEV   := flores200/dev
PREDICT_TRAIN   := multisynt/textpredict/train/len1024
PREDICT_DEV     := multisynt/textpredict/dev/len1024

TRAINDATA_BASENAME := *
DEVDATA_BASENAME   := *
TRAINDATA          := ${PREDICT_TRAIN}
DEVDATA            := ${PREDICT_DEV}
MAX_SEQ_LENGTH     := 1024
KEEP_CHECKPOINTS   := 1

SKIP_SAME_LANGUAGE_VALID_TASKS := 0


## tasks for predicting the next sentences
## task encoders are shared across macro-languages!

TASK_IDS      := $(foreach l,${LANGS},predict_$l-$l)
TASK_ENCODERS := $(foreach l,${META_LANGS},"$l")

include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt

PARTSHARED_TASK_ENCODERS  := $(foreach l,${META_LANGS},"$l","all")
PARTSHARED_TASK_DECODERS  := $(foreach l,${META_LANGS},"all","$l")


.PHONY: %.partially-shared
%.partially-shared:
	@${MAKE} -s MODEL_NAME=oellm-predict-partially-shared \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		TASK_ENCODERS='${PARTSHARED_TASK_ENCODERS}' \
		TASK_DECODERS='${PARTSHARED_TASK_DECODERS}' \
	$(basename $@)



CROSS_TASK_IDS      := $(foreach l,${LANGS_NOEN},predict_$l-eng)
CROSS_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l")

.PHONY: %.crosspredict
%.crosspredict:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict \
		TASK_IDS="${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${TASK_ENCODERS}' \
	$(basename $@)



## add translation tasks

MT_XXEN_TASK_IDS  := $(foreach l,${LANGS_NOEN},mt_$l-eng)
MT_ENXX_TASK_IDS  := $(foreach l,${LANGS_NOEN},mt_eng-$l)
MT_TASK_ENCODERS  := $(foreach l,${META_LANGS_NOEN},"$l")

MT_TRAINDATA := $(foreach l,${LANGS_NOEN},${TRANSLATE_TRAIN})
MT_DEVDATA   := $(foreach l,${LANGS_NOEN},${TRANSLATE_DEV})

.PHONY: %.predict-translate
%.predict-translate:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MT_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)


.PHONY: %.crosspredict-translate
%.crosspredict-translate:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict-translate \
		TASK_IDS="${MT_TASK_IDS} ${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${MT_TASK_ENCODERS} ${TASK_ENCODERS} ${CROSS_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)



## translate in both directions

.PHONY: %.predict-translate2
%.predict-translate2:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate2 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MT_TASK_ENCODERS} ${MT_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)



## add denoising tasks
##
## NOTE: here we can use all OELLM languages as we have enough tasks
##       to distribute evenly on compute nodes with 8 GPUs each


.PHONY: %.predict-denoise-translate2
%.predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

DENOISE_TASK_IDS   := $(foreach l,${LANGS},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${LANGS},filtertoolong,denoising)

.PHONY: %.predict-denoise-translate2-${NR_LANGS}
%.predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-predict-denoise-translate2 \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${MT_TASK_ENCODERS} ${MT_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
	$(basename $@)
