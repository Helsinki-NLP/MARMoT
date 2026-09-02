# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)

include ../../../make/env.mk

DEFAULT_ENCODER := "all"

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr




## translation tasks, pivoted by selected languages

DOCMT_PIVOT_LANGS := eng fra
DOCMT_TASK_IDS    := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),mt_$l-$p mt_$p-$l)))
DOCMT_TRANSFORMS  := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_GPUS        := $(call rotating_gpu_assignment,0,9,$(words ${DOCMT_TASK_IDS}))


## denoising tasks (use same as MT training data)

DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_GPUS       := $(call rotating_gpu_assignment,9,1,$(words ${DENOISE_TASK_IDS}))


## task definitions put together

TASK_IDS            := ${DOCMT_TASK_IDS} ${DENOISE_TASK_IDS} 
TASK_TRANSFORMS     := ${DOCMT_TRANSFORMS} ${DENOISE_TRANSFORMS}
TASK_GPUS           := ${DOCMT_GPUS} ${DENOISE_GPUS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


# from memory-profiler
# BATCH_SIZE ?= 46538

# harmonize with other comparable runs with transformer-base
BATCH_SIZE := 32768

# 1 day only
SLURM_MAX_GPU_TIME := 12:00:00



include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"


## test zero-shot translation


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) \
		SLURM_GPU_PARTITION=dev-g \
		EVAL_TASKS_WALLTIME=15:00 \
		TASKS="por-swe ces-ukr" \
		TASK_IDS="mt_por-swe mt_ces-ukr"
