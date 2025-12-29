
HPC_PROJECT   := project_462000964
SANDBOX_HOME  := /scratch/${HPC_PROJECT}/members/tiedeman/MARMoT
SANDBOX_DIR   := ${SANDBOX_HOME}/sandbox/tiedeman/mammoth
MAKEFILE_DIR  := ${SANDBOX_HOME}/make


include ${MAKEFILE_DIR}/env.mk
include ${MAKEFILE_DIR}/config.mk
include ${MAKEFILE_DIR}/train.mk
include ${MAKEFILE_DIR}/eval.mk
include ${MAKEFILE_DIR}/slurm.mk


##-----------------------------------------------------------
## experiment 1:
##
## run like 'make train.exp1'
##-----------------------------------------------------------

.PHONY: %.exp1
%.exp1:
	${MAKE} MODEL_NAME=exp1 \
		TASKS="fin-eng eng-fin" \
		TASK_GPUS="0:0 0:1" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		DEFAULT_ENCODER="shared" \
	$(basename $@)
