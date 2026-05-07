#-*-makefile-*-


## set experiment parameters (if different from defaults)

MODEL_NAME      := mammoth
TASK_IDS        := doc_eng-fin wiki_eng-fin tc_eng-fin
ENCODER_LAYERS  := 6
DECODER_LAYERS  := 6
MAX_SEQ_LENGTH  := 1024


MAMMOTH_VERSION := dev


## include common configuration and make targets
## and set environment (if different from standard)

include ../../make/marmot.mk


DOC_TRAIN_SRC := ${DATA_DIR}/multisynt/train/len1024/nemotron-cc-english-run1-train-00-48.eng.gz
DOC_TRAIN_TRG := ${DATA_DIR}/multisynt/train/len1024/nemotron-cc-english-run1-train-00-48.fin.gz

BT_TRAIN_SRC  := ${DATA_DIR}/synthetic/Wiki/fin-eng.eng.gz
BT_TRAIN_TRG  := ${DATA_DIR}/synthetic/Wiki/fin-eng.fin.gz

TASK_TRAINDATA_SRCS := ${DOC_TRAIN_SRC} ${BT_TRAIN_SRC}
TASK_TRAINDATA_TRGS := ${DOC_TRAIN_TRG} ${BT_TRAIN_TRG}

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt



.PHONY: %.doc
%.doc:
	@${MAKE} -s MODEL_NAME=eng-fin-doc \
		MAX_SEQ_LENGTH=1024 \
		VOCAB_DIR=${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt \
		TASK_IDS="doc_eng-fin wiki_eng-fin tc_eng-fin" \
		TASK_TRAINDATA_SRCS="${DOC_TRAIN_SRC} ${BT_TRAIN_SRC}" \
		TASK_TRAINDATA_TRGS="${DOC_TRAIN_TRG} ${BT_TRAIN_TRG}" \
	$(basename $@)
