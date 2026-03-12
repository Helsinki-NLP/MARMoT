
MODEL_NAME := noprefix

TRANSLATE_TRAIN    := multisynt/train/len1024
TRANSLATE_DEV      := flores200/dev
PREDICT_TRAIN      := multisynt/textpredict/train/len1024
PREDICT_DEV        := multisynt/textpredict/dev/len1024

TASK_IDS           := denoise_eng-eng mt_fin-eng predict_eng-eng predict_fin-eng
TASK_TRAINDATA     := ${TRANSLATE_TRAIN} ${TRANSLATE_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}
TASK_DEVDATA       := ${TRANSLATE_DEV} ${TRANSLATE_DEV} ${PREDICT_DEV} ${PREDICT_DEV}
TASK_TRANSFORMS    := denoising,filtertoolong

TRAINDATA_BASENAME := *
DEVDATA_BASENAME   := *
MAX_SEQ_LENGTH     := 1024
KEEP_CHECKPOINTS   := 1
TRAINING_STEPS     := 20000

ADD_LANGUAGE_TOKEN := false
DEFAULT_SRCPREFIX  :=
DEFAULT_TRGPREFIX  :=

SKIP_SAME_LANGUAGE_VALID_TASKS := 0

include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt

.PHONY: %.fineng
%.fineng:
	@${MAKE} -s MODEL_NAME=fineng \
		TASK_IDS=mt_fin-eng \
		TASK_TRAINDATA=${TRANSLATE_TRAIN} \
		TASK_DEVDATA=${TRANSLATE_DEV} \
		TASK_TRANSFORMS= \
	$(basename $@)

.PHONY: %.srcprefix
%.srcprefix:
	@${MAKE} -s MODEL_NAME=srcprefix \
		ADD_LANGUAGE_TOKEN=true \
		TASK_SRCPREFIXES="<<denoise>> <<translate>> <<continue>> <<continue>>" \
	$(basename $@)

.PHONY: %.trgprefix
%.trgprefix:
	@${MAKE} -s MODEL_NAME=trgprefix \
		ADD_LANGUAGE_TOKEN=true \
		TASK_TRGPREFIXES="<<denoise>> <<translate>> <<continue>> <<continue>>" \
	$(basename $@)

.PHONY: %.prefix
%.prefix:
	@${MAKE} -s MODEL_NAME=prefix \
		ADD_LANGUAGE_TOKEN=true \
		TASK_SRCPREFIXES="<<denoise>> <<translate>> <<continue>> <<continue>>" \
		TASK_TRGPREFIXES="<<denoise>> <<translate>> <<continue>> <<continue>>" \
	$(basename $@)



.PHONY: %.trgprefix2
%.trgprefix2:
	@${MAKE} -s MODEL_NAME=trgprefix2 \
		ADD_LANGUAGE_TOKEN=true \
		DECAY_START=10000 \
		TASK_TRGPREFIXES="<<denoise>> <<translate>> <<continue>> <<continue>>" \
	$(basename $@)


.PHONY: %.fineng1
%.fineng1:
	@${MAKE} -s MODEL_NAME=fineng1 \
		TASK_IDS=mt_fin-eng \
		TASK_TRAINDATA=${TRANSLATE_TRAIN} \
		TASK_DEVDATA=${TRANSLATE_DEV} \
		TASK_TRANSFORMS= \
	$(basename $@)

.PHONY: %.fineng2
%.fineng2:
	@${MAKE} -s MODEL_NAME=fineng1 \
		TASK_IDS=mt_fin-eng \
		TASK_TRAINDATA=${TRANSLATE_TRAIN} \
		TASK_DEVDATA=${TRANSLATE_DEV} \
		TASK_TRANSFORMS= \
		DECAY_START=10000 \
	$(basename $@)
