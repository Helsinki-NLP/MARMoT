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

# OELLM_LANGS := 	$(sort deu fin nob nno spa mlt ukr \
# 		gle glg cat ces swe tur bul \
# 		lav lit slk nld dan ell est fra \
# 		hrv hun ita pol por ron \
# 		slv eus bos isl kat \
# 		mkd sqi srp_Cyrl)


OELLM_LANGS := 	$(sort deu spa fra ita por ces pol swe fin ron hun ell)

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

QUEUE_SIZE := 2
LOOK_AHEAD := 2
GRADIENT_ACCUM := 10

## include common configuration and make targets

include ${MAKEFILE_DIR}/env.mk
include ${MAKEFILE_DIR}/config.mk
include ${MAKEFILE_DIR}/train.mk
include ${MAKEFILE_DIR}/eval.mk
include ${MAKEFILE_DIR}/slurm.mk

