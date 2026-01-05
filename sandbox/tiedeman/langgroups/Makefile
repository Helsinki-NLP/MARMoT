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

OELLM_LANGS := 	$(sort deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos isl kat \
		mkd sqi srp_Cyrl)

## task list (English centric in both directions

TASKS := $(foreach l,${OELLM_LANGS},$l-eng eng-$l)

## task encoder and decoder definitions with 3 steps:
## - 3 language-specific layers (meta-languages in encoders)
## - 3 language-group specific layers (immediate parent lang-group)
## - 3 completely shared layers

OELLM_META_LANGS  := $(shell iso639 -m ${OELLM_LANGS} 2>/dev/null)
OELLM_LANG_GROUPS := $(shell langgroup -p ${OELLM_META_LANGS} 2>/dev/null)
OELLM_LANG_NRS    := $(shell seq $(words ${OELLM_LANGS}))

TASK_ENCODERS := $(foreach l,${OELLM_LANG_NRS},"$(word $l,${OELLM_META_LANGS})","$(word $l,${OELLM_LANG_GROUPS})","all" "eng","gmw","all")
TASK_DECODERS := $(foreach l,${OELLM_LANG_NRS},"all","gmw","eng" "all","$(word $l,${OELLM_LANG_GROUPS})","$(word $l,${OELLM_LANGS})")


## GPU assignments: simply distribute one task per GPU

TASK_GPUS := $(shell \
	n=0; g=0; \
	for t in ${TASKS}; do \
	  echo "$$n:$$g"; \
	  ((g++)); \
	  if [ $$g -gt 7 ]; then \
	    ((n++)); \
	    g=0; \
	  fi; \
	done )


MODEL_NAME      := eucore
ENCODER_LAYERS  := 3,3,3
DECODER_LAYERS  := 3,3,3


## include common configuration and make targets

include ${MAKEFILE_DIR}/env.mk
include ${MAKEFILE_DIR}/config.mk
include ${MAKEFILE_DIR}/train.mk
include ${MAKEFILE_DIR}/eval.mk
include ${MAKEFILE_DIR}/slurm.mk


.PHONY: %.exp2
%.exp2:
	${MAKE} -s \
		MODEL_NAME=eucore2 \
		LEARNING_RATE=0.0005 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)

.PHONY: %.exp3
%.exp3:
	${MAKE} -s \
		MODEL_NAME=eucore3 \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)

.PHONY: %.exp4
%.exp4:
	${MAKE} -s \
		MODEL_NAME=shared \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=9 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
		DEFAULT_ENCODER="shared" \
		DEFAULT_DECODER="shared" \
	$(basename $@)

.PHONY: %.exp5
%.exp5:
	${MAKE} -s \
		MODEL_NAME=separate \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=9 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
	$(basename $@)
