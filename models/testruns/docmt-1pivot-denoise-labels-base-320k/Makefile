# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)

include ../../../make/env.mk


ADD_LANGUAGE_TOKEN := true

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr



## English-centric translation tasks
## assign them to GPUs rotating over all GPUs on each node using 18 nodes (node 0-17)

DOCMT_PIVOT_LANGS := eng
DOCMT_TASK_IDS    := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),mt_$l-$p mt_$p-$l)))
DOCMT_TRANSFORMS  := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_GPUS        := $(call rotating_gpu_assignment,0,5,$(words ${DOCMT_TASK_IDS}))


## denoising tasks (use same as MT training data)
## assign them all to one GPU-node (node 18) rotating over the GPUs on that node

DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_GPUS       := $(call rotating_gpu_assignment,5,1,$(words ${DENOISE_TASK_IDS}))


ZEROSHOT_TASKS     := fin-swe swe-fin pol-ukr ukr-pol slk-ces ces-slk fin-est est-fin fin-ukr ukr-fin tur-swe swe-fin
ZEROSHOT_TASK_IDS  := $(foreach l,${ZEROSHOT_TASKS},zero_$l)
ZEROSHOT_TRANSFORMS := $(foreach l,${ZEROSHOT_TASK_IDS},filtertoolong)
ZEROSHOT_WEIGHTS   := $(foreach l,${ZEROSHOT_TASK_IDS},0)
ZEROSHOT_GPUS      := $(call rotating_gpu_assignment,0,5,$(words ${ZEROSHOT_TASK_IDS}))



## task definitions put together

TASK_IDS            := ${ZEROSHOT_TASK_IDS} ${DOCMT_TASK_IDS} ${DENOISE_TASK_IDS} 
TASK_TRANSFORMS     := ${ZEROSHOT_TRANSFORMS} ${DOCMT_TRANSFORMS} ${DENOISE_TRANSFORMS}
TASK_GPUS           := ${ZEROSHOT_GPUS} ${DOCMT_GPUS} ${DENOISE_GPUS}
TASK_WEIGHTS        := ${ZEROSHOT_WEIGHTS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


BATCH_SIZE := 32768
GRADIENT_ACCUM := 10
KEEP_CHECKPOINTS := 10

# 1 day only
SLURM_MAX_GPU_TIME := 24:00:00


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
