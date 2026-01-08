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


HPC_PROJECT    ?= project_2001194
PROJECT_SPACE  ?= /scratch/${HPC_PROJECT}
PROJECT_DIR    ?= ${PROJECT_SPACE}/MARMoT
MAMMOTH_DIR    ?= ${PROJECT_DIR}/mammoth


## data directories

DATA_DIR      ?= ${PROJECT_DIR}/data
TRAINDATA_DIR ?= ${DATA_DIR}/tatoeba/train
DEVDATA_DIR   ?= ${DATA_DIR}/tatoeba/dev5K
# TESTDATA_DIR  ?= ${DATA_DIR}/tatoeba/test
TESTDATA_DIR  ?= ${DATA_DIR}/flores200/devtest
TESTDATA_NAME ?= flores200-devtest
VOCAB_DIR     ?= ${PROJECT_DIR}/tokenizer/tatoeba



MAMMOTH_ENV          ?= ${MAMMOTH_DIR}/.venv
MAMMOTH_ENV_PYTHON   ?= ${MAMMOTH_ENV}/bin/python
MAMMOTH_ENV_ACTIVATE ?= source ${MAMMOTH_ENV}/bin/activate
