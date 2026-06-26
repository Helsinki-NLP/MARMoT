# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)

include ../../../make/env.mk

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## English-centric translation tasks
## assign them to GPUs rotating over all GPUs on each node using 32 nodes (node 0-31)

export DOCMT_PIVOT_LANGS := ces deu eng fin fra spa hrv swe tur ukr
export DOCMT_TASK_IDS    := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),mt_$l-$p mt_$p-$l)))
export DOCMT_TRANSFORMS  := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
export DOCMT_GPUS        := $(call rotating_gpu_assignment,0,31,$(words ${DOCMT_TASK_IDS}))


## denoising tasks (use same as MT training data)

export DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
export DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
export DENOISE_GPUS       := $(call rotating_gpu_assignment,31,1,$(words ${DENOISE_TASK_IDS}))


## task definitions put together

export TASK_IDS            := ${DOCMT_TASK_IDS} ${DENOISE_TASK_IDS} 
export TASK_TRANSFORMS     := ${DOCMT_TRANSFORMS} ${DENOISE_TRANSFORMS}
export TASK_GPUS           := ${DOCMT_GPUS} ${DENOISE_GPUS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt



# MODEL_ARCHITECTURE := transformer-base
# ENCODER            := "all"

ENCODER         := "{lang}","all"
ENCODER_LAYERS  := 2,4

BATCH_SIZE      := 32768
GRADIENT_ACCUM  := 50
LOOK_AHEAD      := 100
QUEUE_SIZE      := 200


include ../../../make/marmot.mk


info:
	@echo "number of tasks: $(words ${TASK_IDS})"

print-tasks:
	@echo "${DOCMT_GPUS}"


## test zero-shot translation


ZERO_SHOT_TASKS := 	bos-srp_Cyrl srp_Cyrl-bos bos-slv slv-bos \
			sqi-mkd mkd-sqi glg-por por-glg dan-nob nob-dan


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASKS="${ZERO_SHOT_TASKS}"
