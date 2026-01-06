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
## experiment 2: multi-node
##
##   the job fails with some strange error message about
##   'ValueError: ProcessGroupNCCL is only supported with GPUs, no GPUs found!'
##
##   however, manually starting the job with the same slurm script
##   and sbatch from command-line seems to work --> WHY?
##-----------------------------------------------------------

EXP2_GPUS := 0:0 1:0

.PHONY: %.exp2
%.exp2:
	${MAKE} MODEL_NAME=exp2 TASK_GPUS="${EXP2_GPUS}" $(basename $@)
