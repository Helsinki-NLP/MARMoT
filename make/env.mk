#-*-makefile-*-

SHELL  := /bin/bash
PWD    := $(abspath $(shell pwd))
WHOAMI := $(shell whoami)


HPC_PROJECT    ?= project_462000964
PROJECT_SPACE  ?= /scratch/${HPC_PROJECT}
PROJECT_DIR    ?= ${PROJECT_SPACE}/MARMoT
MAMMOTH_DIR    ?= ${PROJECT_DIR}/shared/mammoth
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
