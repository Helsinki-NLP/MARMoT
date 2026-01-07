#-*-makefile-*-

SHELL  := /bin/bash
PWD    := $(shell pwd | xargs realpath)
WHOAMI := $(shell whoami)


## host specific configuration:
## - try to find some know hosts in HOSTNAME
## - LUMI is included as default

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

ifeq ($(findstring puhti,${HOSTNAME}),puhti)
  include ${MAKEFILE_DIR}env/puhti.mk
else ifeq ($(findstring mahti,${HOSTNAME}),mahti)
  include ${MAKEFILE_DIR}env/mahti.mk
else
  include ${MAKEFILE_DIR}env/lumi.mk
endif


HPC_PROJECT    ?= project_2001194
PROJECT_SPACE  ?= /scratch/${HPC_PROJECT}
PROJECT_DIR    ?= ${PROJECT_SPACE}/MARMoT
MAMMOTH_DIR    ?= ${PROJECT_DIR}/mammoth
MAKEFILE_DIR   ?= ${PROJECT_DIR}/make
EXPERIMENT_DIR ?= ${PWD}

MODEL_NAME     ?= mammoth
MODEL_DIR      ?= ${EXPERIMENT_DIR}/${MODEL_NAME}
MODEL_PATH     ?= ${MODEL_DIR}/model
MODEL_META     ?= ${MODEL_PATH}_checkpoint_metadata.json
EVAL_DIR       ?= ${MODEL_DIR}/eval


## data directories

DATA_DIR      ?= ${PROJECT_DIR}/data
TRAINDATA_DIR ?= ${DATA_DIR}/tatoeba/train
DEVDATA_DIR   ?= ${DATA_DIR}/tatoeba/dev5K
# TESTDATA_DIR  ?= ${DATA_DIR}/tatoeba/test
TESTDATA_DIR  ?= ${DATA_DIR}/flores200/devtest
TESTDATA_NAME ?= flores200-devtest
VOCAB_DIR     ?= ${PROJECT_DIR}/tokenizer/tatoeba



PYTORCH_CONTAINER ?= /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif
