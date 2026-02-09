#-*-makefile-*-


## set experiment parameters (if different from defaults)

MODEL_NAME      := eng-fin
TASK_IDS        := task_eng-fin
ENCODER_LAYERS  := 6
DECODER_LAYERS  := 6


MAMMOTH_VERSION := dev


## include common configuration and make targets
## and set environment (if different from standard)

include ../../../make/marmot.mk





DOC_TRAIN_SRC := ${DATA_DIR}/multisynt/train/len1024/nemotron-cc-english-run1-train-00-48.eng.gz
DOC_TRAIN_TRG := ${DATA_DIR}/multisynt/train/len1024/nemotron-cc-english-run1-train-00-48.fin.gz

BT_TRAIN_SRC  := ${DATA_DIR}/synthetic/Wiki/fin-eng.eng.gz
BT_TRAIN_TRG  := ${DATA_DIR}/synthetic/Wiki/fin-eng.fin.gz


.PHONY: %.doc
%.doc:
	@${MAKE} -s MODEL_NAME=eng-fin-doc \
		MAX_SEQ_LENGTH=1024 \
		VOCAB_DIR=${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt \
		TASK_IDS="doc_eng-fin wiki_eng-fin tc_eng-fin" \
		TASK_TRAINDATA_SRCS="${DOC_TRAIN_SRC} ${BT_TRAIN_SRC}" \
		TASK_TRAINDATA_TRGS="${DOC_TRAIN_TRG} ${BT_TRAIN_TRG}" \
	$(basename $@)

.PHONY: %.doconly
%.doconly:
	@${MAKE} -s MODEL_NAME=eng-fin-doconly \
		MAX_SEQ_LENGTH=1024 \
		VOCAB_DIR=${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt \
		TASK_IDS="doc_eng-fin" \
		TASK_TRAINDATA_SRCS="${DOC_TRAIN_SRC}" \
		TASK_TRAINDATA_TRGS="${DOC_TRAIN_TRG}" \
	$(basename $@)


.PHONY: %.bt
%.bt:
	@${MAKE} -s MODEL_NAME=eng-fin-bt \
		TASKS="eng-fin eng-fin" \
		TASK_IDS="wiki_eng-fin tc_eng-fin" \
		TASK_TRAINDATA_SRCS="${BT_TRAIN_SRC}" \
		TASK_TRAINDATA_TRGS="${BT_TRAIN_TRG}" \
	$(basename $@)



.PHONY: %.onlybt
%.onlybt:
	@${MAKE} -s MODEL_NAME=eng-fin-onlybt TRAINDATA_DIR=${DATA_DIR}/synthetic/Wiki $(basename $@)

