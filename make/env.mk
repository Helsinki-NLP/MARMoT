#-*-makefile-*-

SHELL  := /bin/bash
PWD    := $(shell pwd | xargs realpath)
WHOAMI := $(shell whoami)


EXPERIMENT_DIR ?= ${PWD}
MODEL_NAME     ?= mammoth
MODEL_DIR      ?= ${EXPERIMENT_DIR}/${MODEL_NAME}
MODEL_PATH     ?= ${MODEL_DIR}/model
MODEL_META     ?= ${MODEL_PATH}_checkpoint_metadata.json
EVAL_DIR       ?= ${MODEL_DIR}/eval


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


## mammoth environment

MAMMOTH_DIR          ?= ${PROJECT_DIR}/mammoth
MAMMOTH_ENV          ?= ${MAMMOTH_DIR}/.venv
MAMMOTH_ENV_PYTHON   ?= ${MAMMOTH_ENV}/bin/python
MAMMOTH_ENV_ACTIVATE ?= source ${MAMMOTH_ENV}/bin/activate


## data directories (assuming that we have data prepared in the project dir)
## - default training data from the Tatoeba translation challenge
## - default dev and test data from Flores200 if the exists (Tatoeba otherwise)

DATA_DIR        ?= ${PROJECT_DIR}/data
TRAINDATA       ?= tatoeba/train
TRAINDATA_NAME  ?= tatoeba-test-v2023-09-26

ifneq ($(wildcard ${DATA_DIR}/flores200/dev),)
  DEVDATA       ?= flores200/dev
  DEVDATA_NAME  ?= flores200-dev
else
  DEVDATA       ?= tatoeba/dev5K
  DEVDATA_NAME  ?= tatoeba-test-v2023-09-26
endif

ifneq ($(wildcard ${DATA_DIR}/flores200/devtest),)
  TESTDATA      ?= flores200/devtest
  TESTDATA_NAME ?= flores200-devtest
else
  TESTDATA      ?= tatoeba/test
  TESTDATA_NAME ?= tatoeba-test-v2023-09-26
endif


## tokenizer directory

VOCAB     ?= tatoeba
VOCAB_DIR ?= ${PROJECT_DIR}/tokenizer/${VOCAB}


## look for some tools

THREADS  ?= 4
SORT     := sort -T ${TMPDIR} --parallel=${THREADS}
SHUFFLE  := ${shell which terashuf 2>/dev/null || echo "${SORT} --random-sort"}
GZIP     := ${shell which pigz     2>/dev/null || echo gzip}
ZCAT     := ${GZIP} -cd
