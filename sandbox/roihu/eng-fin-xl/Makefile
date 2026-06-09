

MODEL_ARCHITECTURE := transformer-xl
PRETRAINED_MODEL   := ../finnish-xl/mammoth


TASK_IDS     := sentmt_eng-fin \
		docmt1_eng-fin \
		docmt2_eng-fin \
		docmt3_eng-fin \
		docmt4_eng-fin 
TASK_TRAINDATA := sentmt multisynt/train/len1024 \
		multisynt_run2/train/len1024 \
		transweb-edu/train/len1024 \
		transweb-edu_50-99/train/len1024 \
		transweb-edu_100-471/train/len1024 
TASK_GPUS    := 0:0 0:0 0:0 0:0 0:0



VOCAB := tatoeba_hplt_multisynt



BATCH_SIZE := 16384

USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../../make/marmot.mk


info:
	@echo $(words ${TASK_IDS})

