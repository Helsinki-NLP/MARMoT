
include ../../make/env.mk

## tasks: fin-swe and fin-eng in both directions

MT_TASKS := fin-eng eng-fin fin-swe swe-fin
MT_GPUS  := 0:0 0:1 0:2 0:3


## sentence-level translation data

SENTMT_TASK_IDS  := $(addprefix sentmt_,${MT_TASKS})
SENTMT_TRAINDATA := $(patsubst %,sentmt,${MT_TASKS})


## synthetic document-level translation data

DOCMT_TASK_IDS  := $(addprefix docmt1_,${MT_TASKS})
DOCMT_TRAINDATA := $(patsubst %,multisynt/train/len1024,${MT_TASKS})



##----------------------------------------------------------
## task definitions put together
## - skip evaluating docmt and wiki-bt tasks (will be the same as sentmt)
## - only wiki tasks require different train file names
## - GPU assignments (put the same language pair on the same GPU)
##----------------------------------------------------------


TASK_IDS       := ${DOCMT_TASK_IDS} ${SENTMT_TASK_IDS} 
TASK_TRAINDATA := ${DOCMT_TRAINDATA} ${SENTMT_TRAINDATA}
TASK_GPUS      := ${MT_GPUS} ${MT_GPUS}



## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


BATCH_SIZE := 32768


USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk


info:
	@echo $(words ${TASK_IDS})


ZERO_SHOT_TASKS := eng-swe swe-eng

.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASKS="${ZERO_SHOT_TASKS}"
