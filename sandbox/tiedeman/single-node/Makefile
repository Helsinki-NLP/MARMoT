#-*-makefile-*-


## set experiment parameters (if different from defaults)

MODEL_NAME      := fin-eng
TASKS           := fin-eng eng-fin
TASK_GPUS       := 0:0     0:1
ENCODER_LAYERS  := 9
DECODER_LAYERS  := 3
DEFAULT_ENCODER := "shared"


## include common configuration and make targets
## and set environment (if different from standard)

HPC_PROJECT := project_462000964
MAMMOTH_DIR := /scratch/${HPC_PROJECT}/shared/mammoth

include ../../../make/marmot.mk



##-----------------------------------------------------------
## experiment 2: additional languages and denoising
##-----------------------------------------------------------

EXP2_TASKS           := eng-eng fin-fin fin-eng swe-eng deu-eng eng-fin eng-swe eng-deu fin-swe swe-fin
EXP2_TASK_GPUS       := 0:7     0:7     0:0     0:1     0:2     0:3     0:4     0:5     0:6     0:7
EXP2_TASK_WEIGHTS    := 0.1     0.1
EXP2_TASK_TRANSFORMS := denoising,filtertoolong denoising,filtertoolong

.PHONY: %.exp2
%.exp2:
	${MAKE} MODEL_NAME=deu-eng-fin-swe \
		TASKS="${EXP2_TASKS}" \
		TASK_GPUS="${EXP2_TASK_GPUS}" \
		TASK_WEIGHTS="${EXP2_TASK_WEIGHTS}" \
		TASK_TRANSFORMS="${EXP2_TASK_TRANSFORMS}" \
	$(basename $@)
