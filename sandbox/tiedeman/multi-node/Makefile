#-*-makefile-*-
##-----------------------------------------------------------
## testing multi-node job
##
##   the job fails with some strange error message about
##   'ValueError: ProcessGroupNCCL is only supported with GPUs, no GPUs found!'
##
##   however, manually starting the job with the same slurm script
##   and sbatch from command-line seems to work --> WHY?
##-----------------------------------------------------------

## set environment (if different from standard)

SHELL         := /bin/bash
HPC_PROJECT   := project_462000964
MAMMOTH_DIR   := /scratch/${HPC_PROJECT}/shared/mammoth
MAKEFILE_DIR  := $(shell realpath ../../..)/make


## set experiment parameters (if different from defaults)

MODEL_NAME      := fin-eng
TASKS           := fin-eng eng-fin
TASK_GPUS       := 0:0     1:0
ENCODER_LAYERS  := 9
DECODER_LAYERS  := 3
DEFAULT_ENCODER := "shared"


## include common configuration and make targets

include ${MAKEFILE_DIR}/env.mk
include ${MAKEFILE_DIR}/config.mk
include ${MAKEFILE_DIR}/train.mk
include ${MAKEFILE_DIR}/eval.mk
include ${MAKEFILE_DIR}/slurm.mk

