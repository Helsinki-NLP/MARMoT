
## model architecture

MODEL_ARCHITECTURE := transformer-big
ENCODER            := "{langgroup}","all"
ENCODER_LAYERS     := 2,4
NR_OF_NODES        := 1


NORDIC_TASKS    := eng-fin fin-eng dan-eng eng-dan swe-eng eng-swe nob-eng eng-nob
MT_TASK_IDS := $(addprefix mt_,${NORDIC_TASKS})
BT_TASK_IDS := $(addprefix bt_,${NORDIC_TASKS})

MT_TASK_TRAINDATA := $(foreach t,${MT_TASK_IDS},tatoeba/train)
BT_TASK_TRAINDATA := $(foreach t,${MT_TASK_IDS},synthetic/wiki-bt)

MT_TASK_WEIGHTS   := $(foreach t,${MT_TASK_IDS},10)
BT_TASK_WEIGHTS   := $(foreach t,${MT_TASK_IDS},1)
BT_TASK_DEVDATA   := $(foreach t,${MT_TASK_IDS},skip)


# put it all together

TASK_IDS       := ${BT_TASK_IDS} ${MT_TASK_IDS}
TASK_TRAINDATA := ${BT_TASK_TRAINDATA} ${MT_TASK_TRAINDATA}
TASK_WEIGHTS   := ${BT_TASK_WEIGHTS} ${MT_TASK_WEIGHTS}
TASK_DEVDATA   := ${BT_TASK_DEVDATA}


# vocabularies / tokenizers
VOCAB      := sent_doc
VOCAB_SIZE := 32704


BATCH_SIZE       := 16384
GRADIENT_ACCUM   := 20
LOOK_AHEAD       := 20

VALID_FREQ  := 2500
SAVE_FREQ   := 2500
REPORT_FREQ := 500


SLURM_MAX_GPU_TIME := 1-00:00:00


include ../../../make/marmot.mk


info:
	@echo "number of tasks: $(words ${TASK_IDS})"
	@echo $(words ${TASK_GPU_ASSIGNMENTS})
	@echo $(words $(sort ${TASK_GPU_ASSIGNMENTS}))



## test zero-shot translation

.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) \
		SLURM_GPU_PARTITION=dev-g \
		EVAL_TASKS_WALLTIME=15:00 \
		TASKS="swe-fin fin-swe"
