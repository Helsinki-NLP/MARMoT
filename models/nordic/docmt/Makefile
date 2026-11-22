
# model architecture

MODEL_ARCHITECTURE := transformer-big
ENCODER            := "{langgroup}","all"
ENCODER_LAYERS     := 2,4

# tasks

TASKS     := eng-fin fin-eng dan-eng eng-dan swe-eng eng-swe nob-eng eng-nob
TASK_IDS  := $(addprefix mt_,${TASKS})
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB          := sent_doc
VOCAB_SIZE     := 32704


BATCH_SIZE     := 16384
GRADIENT_ACCUM := 10
LOOK_AHEAD     := 10
VALID_FREQ     := 2500
SAVE_FREQ      := 2500
REPORT_FREQ    := 500

SLURM_MAX_GPU_TIME := 1-00:00:00


include ../../../make/marmot.mk


info:
	@echo "number of tasks: $(words ${TASK_IDS})"


## test zero-shot translation

.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) \
		SLURM_GPU_PARTITION=dev-g \
		EVAL_TASKS_WALLTIME=15:00 \
		TASKS="swe-fin fin-swe"
