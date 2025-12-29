#-*-makefile-*-

PWD    := $(shell pwd)
WHOAMI := $(shell whoami)


HPC_PROJECT   ?= project_462000964
PROJECT_SPACE ?= /scratch/${HPC_PROJECT}
PROJECT_DIR   ?= ${PROJECT_SPACE}/MARMoT
MAMMOTH_DIR   ?= ${PROJECT_SPACE}/shared/mammoth
SANDBOX_DIR   ?= ${PWD}/sandbox/${WHOAMI}


MODEL_NAME    ?= mammoth
WORK_DIR      ?= ${SANDBOX_DIR}/${MODEL_NAME}
MODEL_DIR     ?= ${WORK_DIR}
MODEL_PATH    ?= ${MODEL_DIR}/model
MODEL_META    ?= ${MODEL_PATH}_checkpoint_metadata.json



## data directories

DATA_DIR      ?= ${PROJECT_DIR}/data
TRAINDATA_DIR ?= ${DATA_DIR}/tatoeba/train
DEVDATA_DIR   ?= ${DATA_DIR}/tatoeba/dev5K
# TESTDATA_DIR  ?= ${DATA_DIR}/tatoeba/test
TESTDATA_DIR  ?= ${DATA_DIR}/flores200/devtest
VOCAB_DIR     ?= ${PROJECT_DIR}/tokenizer/tatoeba
