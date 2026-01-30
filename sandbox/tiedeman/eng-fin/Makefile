#-*-makefile-*-


## set experiment parameters (if different from defaults)

MODEL_NAME      := eng-fin
TASKS           := eng-fin
ENCODER_LAYERS  := 6
DECODER_LAYERS  := 6


MAMMOTH_VERSION := dev


## include common configuration and make targets
## and set environment (if different from standard)

include ../../../make/marmot.mk




.PHONY: %.bt
%.bt:
	@${MAKE} -s MODEL_NAME=eng-fin-bt \
		TASKS="eng-fin eng-fin" \
		TASK_IDS="wiki_eng-fin tc_eng-fin" \
		TASK_TRAINDATA_SRCS=${DATA_DIR}/synthetic/Wiki/fin-eng.eng.gz \
		TASK_TRAINDATA_TRGS=${DATA_DIR}/synthetic/Wiki/fin-eng.fin.gz \
	$(basename $@)



.PHONY: %.onlybt
%.onlybt:
	@${MAKE} -s MODEL_NAME=eng-fin-onlybt TRAINDATA_DIR=${DATA_DIR}/synthetic/Wiki $(basename $@)

