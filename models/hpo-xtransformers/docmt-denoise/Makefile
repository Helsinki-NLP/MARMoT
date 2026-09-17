# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)

include ../../make/env.mk

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## English-centric translation tasks
## assign them to GPUs rotating over all GPUs on each node using 9 nodes (node 0-8)

DOCMT_TASK_IDS     := $(foreach l,$(filter-out eng,${LANGUAGES}),mt_$l-eng mt_eng-$l)
DOCMT_TRANSFORMS   := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_GPUS         := $(call rotating_gpu_assignment,0,9,$(words ${DOCMT_TASK_IDS}))


## denoising tasks (use same as MT training data)
## assign them all to one GPU-node (node 10) rotating over the GPUs on that node

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


include ../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"


## test zero-shot translation

.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASK_IDS="mt_por-swe mt_swe-fin"
