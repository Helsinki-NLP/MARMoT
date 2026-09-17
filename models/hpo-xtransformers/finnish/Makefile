
include ../../make/env.mk

## tasks: fin-swe and fin-eng in both directions

MT_TASKS := fin-eng eng-fin fin-swe swe-fin
MT_GPUS  := 0:0 0:1 0:2 0:3


## sentence-level translation data

SENTMT_TASK_IDS  := $(addprefix sentmt_,${MT_TASKS})
SENTMT_TRAINDATA := $(patsubst %,sentmt,${MT_TASKS})


## synthetic document-level translation data

DOCMT1_TASK_IDS  := $(addprefix docmt1_,${MT_TASKS})
DOCMT1_TRAINDATA := $(patsubst %,multisynt/train/len1024,${MT_TASKS})

DOCMT2_TASK_IDS  := $(addprefix docmt2_,${MT_TASKS})
DOCMT2_TRAINDATA := $(patsubst %,multisynt_run2/train/len1024,${MT_TASKS})

DOCMT3_TASK_IDS  := $(addprefix docmt3_,${MT_TASKS})
DOCMT3_TRAINDATA := $(patsubst %,transweb-edu/train/len1024,${MT_TASKS})

DOCMT4_TASK_IDS  := docmt4_fin-eng docmt4_eng-fin
DOCMT4_TRAINDATA := transweb-edu_50-99/train/len1024 transweb-edu_50-99/train/len1024
DOCMT4_GPUS      := 0:0 0:1

DOCMT5_TASK_IDS  := docmt5_fin-eng docmt5_eng-fin
DOCMT5_TRAINDATA := transweb-edu_100-471/train/len1024 transweb-edu_100-471/train/len1024
DOCMT5_GPUS      := 0:0 0:1

## list all document-level tasks

DOCMT_TASK_IDS  := ${DOCMT1_TASK_IDS} ${DOCMT2_TASK_IDS} ${DOCMT3_TASK_IDS} ${DOCMT4_TASK_IDS} ${DOCMT5_TASK_IDS}
DOCMT_TRAINDATA := ${DOCMT1_TRAINDATA} ${DOCMT2_TRAINDATA} ${DOCMT3_TRAINDATA} ${DOCMT4_TRAINDATA} ${DOCMT5_TRAINDATA}
DOCMT_GPUS      := ${MT_GPUS} ${MT_GPUS} ${MT_GPUS} ${DOCMT4_GPUS} ${DOCMT5_GPUS}



## wiki backtranslation data
## - file basenames are different from all others: use reverse language direction

WIKI_TASK_IDS    := wiki_fin-eng wiki_eng-fin wiki_fin-swe wiki_swe-fin
WIKI_TRAINDATA   := synthetic/Wikipedia synthetic/Wiki synthetic/Wiki synthetic/Wiki
WIKI_BASENAMES   := *eng-fin* *fin-eng* *swe-fin* *fin-swe*




##----------------------------------------------------------
## task definitions put together
## - skip evaluating docmt and wiki-bt tasks (will be the same as sentmt)
## - only wiki tasks require different train file names
## - GPU assignments (put the same language pair on the same GPU)
##----------------------------------------------------------

TASK_IDS       := ${WIKI_TASK_IDS} ${DOCMT_TASK_IDS} ${SENTMT_TASK_IDS} 
TASK_TRAINDATA := ${WIKI_TRAINDATA} ${DOCMT_TRAINDATA} ${SENTMT_TRAINDATA}
TASK_DEVDATA   := $(patsubst %,skip,${WIKI_TASK_IDS} ${DOCMT_TASK_IDS})
TASK_GPUS      := ${MT_GPUS} ${DOCMT_GPUS} ${MT_GPUS}

TASK_TRAINDATA_BASENAMES := ${WIKI_BASENAMES}






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

