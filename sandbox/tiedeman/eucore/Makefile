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


## set experiment parameters (if different from defaults)

LANGS := $(sort deu spa fra ita por ces pol swe fin ron hun ell)

## task list (English centric in both directions

TASKS := $(foreach l,${LANGS},$l-eng eng-$l)

## task encoder and decoder definitions with 3 steps:
## - 3 language-specific layers (meta-languages in encoders)
## - 3 language-group specific layers (immediate parent lang-group)
## - 3 completely shared layers

META_LANGS  := $(shell iso639 -m ${LANGS} 2>/dev/null)
LANG_GROUPS := $(shell langgroup -p ${META_LANGS} 2>/dev/null)
LANG_NRS    := $(shell seq $(words ${LANGS}))

TASK_ENCODERS := $(foreach l,${LANG_NRS},"$(word $l,${META_LANGS})","$(word $l,${LANG_GROUPS})","all" "eng","gmw","all")
TASK_DECODERS := $(foreach l,${LANG_NRS},"all","gmw","eng" "all","$(word $l,${LANG_GROUPS})","$(word $l,${LANGS})")


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
## and set environment (if different from standard)

HPC_PROJECT := project_462000964
MAMMOTH_DIR := /scratch/${HPC_PROJECT}/shared/mammoth

include ../../../make/marmot.mk


#-----------------------------------------------------
# other experiments with slightly different settings
#-----------------------------------------------------


.PHONY: %.exp2
%.exp2:
	@${MAKE} -s \
		MODEL_NAME=eucore2 \
		LEARNING_RATE=0.0005 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)


.PHONY: %.exp3
%.exp3:
	@${MAKE} -s \
		MODEL_NAME=eucore3 \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)

.PHONY: %.exp4
%.exp4:
	@${MAKE} -s \
		MODEL_NAME=shared \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=9 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
		DEFAULT_ENCODER="shared" \
		DEFAULT_DECODER="shared" \
		ADD_LANGUAGE_TOKEN=true \
	$(basename $@)

.PHONY: %.exp4b
%.exp4b:
	@${MAKE} -s \
		MODEL_NAME=shared-no-prefix \
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
	@${MAKE} -s \
		MODEL_NAME=separate \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=9 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
	$(basename $@)
