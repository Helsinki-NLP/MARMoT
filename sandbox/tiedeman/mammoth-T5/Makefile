
# MODEL_NAME := textpredict
# TASK_IDS   := predict_eng-eng

MODEL_NAME := swedish
TASK_IDS   := predict_swe-swe

TRAINDATA_BASENAME := *
DEVDATA_BASENAME   := *
TASK_TRAINDATA     := multisynt/textpredict/swe/train/len1024
TASK_DEVDATA       := multisynt/textpredict/swe/dev/len1024
MAX_SEQ_LENGTH     := 1024

SKIP_SAME_LANGUAGE_EVAL_TASKS := 0

include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt


ENG_PREDICT_TRAIN := multisynt/textpredict/eng/train/len1024
FIN_PREDICT_TRAIN := multisynt/textpredict/fin/train/len1024
SWE_PREDICT_TRAIN := multisynt/textpredict/swe/train/len1024

ENG_PREDICT_DEV := multisynt/textpredict/eng/dev/len1024
FIN_PREDICT_DEV := multisynt/textpredict/fin/dev/len1024
SWE_PREDICT_DEV := multisynt/textpredict/swe/dev/len1024


.PHONY: %.eng
%.eng:
	@${MAKE} -s MODEL_NAME=english \
		TASK_IDS=predict_eng-eng \
		TASK_TRAINDATA=${ENG_PREDICT_TRAIN} \
		TASK_DEVDATA=${ENG_PREDICT_DEV} \
	$(basename $@)



.PHONY: %.finland-predict
%.finland-predict:
	@${MAKE} -s MODEL_NAME=finland-predict \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe" \
		TASK_TRAINDATA="${ENG_PREDICT_TRAIN} ${FIN_PREDICT_TRAIN} ${SWE_PREDICT_TRAIN}" \
		TASK_DEVDATA="${ENG_PREDICT_DEV} ${FIN_PREDICT_DEV} ${SWE_PREDICT_DEV}" \
	$(basename $@)


.PHONY: %.finland-predict-trans
%.finland-predict-trans:
	@${MAKE} -s MODEL_NAME=finland-predict-trans \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_eng-swe mt_swe-eng" \
		TRAINDATA=multisynt/train/len1024 \
		TASK_TRAINDATA="${ENG_PREDICT_TRAIN} ${FIN_PREDICT_TRAIN} ${SWE_PREDICT_TRAIN}" \
		TASK_DEVDATA="${ENG_PREDICT_DEV} ${FIN_PREDICT_DEV} ${SWE_PREDICT_DEV}" \
	$(basename $@)


