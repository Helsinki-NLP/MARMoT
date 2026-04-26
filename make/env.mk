#-*-makefile-*-

SHELL  := /bin/bash
PWD    := $(shell pwd | xargs realpath)
WHOAMI := $(shell whoami)



## job/node-specific log directories for SLURM jobs

SLURM_NODE_LOGDIR ?= ${PWD}/log/job$${SLURM_JOBID}/node$${SLURM_PROCID}


## host specific configuration:
## - try to find some know hosts in HOSTNAME
## - LUMI is used as default

ifndef HPC_HOST
  ifeq ($(findstring puhti,${HOSTNAME}),puhti)
    HPC_HOST := puhti
  else ifeq ($(findstring mahti,${HOSTNAME}),mahti)
    HPC_HOST := mahti
  else
    HPC_HOST := lumi
  endif
endif


## include host-specific configuration

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include ${MAKEFILE_DIR}env/${HPC_HOST}.mk


## some default values (in case those variables are not set yet)

HPC_PROJECT      ?= project_2001194
PROJECT_SPACE    ?= /scratch/${HPC_PROJECT}
PROJECT_DIR      ?= ${PROJECT_SPACE}/MARMoT
MAX_MEM_PER_GPU  ?= 32
MAX_CPUS_PER_GPU ?= 10


## in case we need some commands for setting up and cleaning up GPU environments

PREPARE_GPU_ENV   ?= echo "all ready to run"
CLEANUP_GPU_ENV   ?= echo "ready for shutting down"
MONITOR_GPU_USAGE ?= echo "Monitoring GPU Usage is not implemented"


## mammoth environment

MAMMOTH_DIR          ?= ${PROJECT_DIR}/mammoth
MAMMOTH_ENV          ?= ${MAMMOTH_DIR}/.venv
MAMMOTH_ENV_PYTHON   ?= ${MAMMOTH_ENV}/bin/python
MAMMOTH_ENV_ACTIVATE ?= source ${MAMMOTH_ENV}/bin/activate



## look for some tools

THREADS  ?= 4
SORT     := sort -T ${TMPDIR} --parallel=${THREADS}
SHUFFLE  := ${shell which terashuf 2>/dev/null || echo "${SORT} --random-sort"}
GZIP     := ${shell which pigz     2>/dev/null || echo gzip}
ZCAT     := ${GZIP} -cd


include ${MAKEFILE_DIR}utilities.mk
