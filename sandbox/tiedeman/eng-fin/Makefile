#-*-makefile-*-


## set experiment parameters (if different from defaults)

MODEL_NAME      := eng-fin
TASKS           := eng-fin
ENCODER_LAYERS  := 6
DECODER_LAYERS  := 6


## include common configuration and make targets
## and set environment (if different from standard)

include ../../../make/marmot.mk




.PHONY: %.bt
%.bt:
	@${MAKE} -s MODEL_NAME=eng-fin-bt \
		TASKS="eng-fin eng-fin" \
		TASK_IDS="wiki_eng-fin tc_eng-fin" \
		TASK_TRAINDATA_SRCS=/scratch/project_2001194/MARMoT/data/synthetic/Wiki/fin-eng.eng.gz \
		TASK_TRAINDATA_TRGS=/scratch/project_2001194/MARMoT/data/synthetic/Wiki/fin-eng.fin.gz \
	$(basename $@)


tt:
	echo ${GPU_RANKS}
