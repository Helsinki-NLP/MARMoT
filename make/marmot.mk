#-*-makefile-*-

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

include ${MAKEFILE_DIR}env.mk
include ${MAKEFILE_DIR}config.mk
include ${MAKEFILE_DIR}train.mk
include ${MAKEFILE_DIR}eval.mk
include ${MAKEFILE_DIR}slurm.mk
