

MODEL_ARCHITECTURE := transformer-xl

## tasks: fin-swe and fin-eng in both directions

MT_TASKS := fin-eng eng-fin fin-swe swe-fin
MT_GPUS  := 0:0 0:1 0:2 0:3


## sentence-level translation data

SENTMT_TASK_IDS  := $(addprefix sentmt_,${MT_TASKS})
SENTMT_TRAINDATA := $(patsubst %,sentmt,${MT_TASKS})


## synthetic document-level translation data

DOCMT_TASK_IDS  := $(addprefix docmt1_,${MT_TASKS})
DOCMT_TRAINDATA := $(patsubst %,multisynt/train/len1024,${MT_TASKS})


DENOISE_TASKS := denoise_fin-fin denoise_eng-eng denoise_swe-swe
DENOISE_DATA  := multisynt/train/len1024 multisynt/train/len1024 multisynt/train/len1024
# DENOISE_DATA  := sentmt sentmt sentmt
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASKS},denoising,filtertoolong)
DENOISE_WEIGHT_FACTORS := 0.05 0.05 0.05
DENOISE_GPUS  := 0:0 0:1 0:3



##----------------------------------------------------------
## task definitions put together
## - skip evaluating docmt and wiki-bt tasks (will be the same as sentmt)
## - only wiki tasks require different train file names
## - GPU assignments (put the same language pair on the same GPU)
##----------------------------------------------------------


TASK_IDS       := ${DENOISE_TASKS} ${DOCMT_TASK_IDS} ${SENTMT_TASK_IDS} 
TASK_TRAINDATA := ${DENOISE_DATA} ${DOCMT_TRAINDATA} ${SENTMT_TRAINDATA}
TASK_TRANSFORMS := ${DENOISE_TRANSFORMS}
TASK_WEIGHT_FACTORS := ${DENOISE_WEIGHT_FACTORS}
TASK_GPUS      := ${DENOISE_GPUS} ${MT_GPUS} ${MT_GPUS}



## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt



BATCH_SIZE := 16384

USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../../make/marmot.mk


info:
	@echo $(words ${TASK_IDS})

