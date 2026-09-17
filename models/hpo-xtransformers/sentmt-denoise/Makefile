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

MT_TASK_IDS     := $(foreach l,$(filter-out eng,${LANGUAGES}),mt_$l-eng mt_eng-$l)
MT_TRAINDATA    := $(foreach l,${MT_TASK_IDS},sentmt)
MT_TRANSFORMS   := $(foreach l,${MT_TASK_IDS},filtertoolong)
MT_GPUS         := $(call rotating_gpu_assignment,0,9,$(words ${MT_TASK_IDS}))


## denoising tasks (use same as MT training data)
## assign them all to one GPU-node (node 10) rotating over the GPUs on that node

DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
DENOISE_TRAINDATA  := $(foreach l,${DENOISE_TASK_IDS},multisynt/train/len1024)
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_GPUS       := $(call rotating_gpu_assignment,9,1,$(words ${DENOISE_TASK_IDS}))


## task definitions put together

TASK_IDS            := ${MT_TASK_IDS} ${DENOISE_TASK_IDS}
TASK_TRAINDATA      := ${MT_TRAINDATA} ${DENOISE_TRAINDATA}
TASK_TRANSFORMS     := ${MT_TRANSFORMS} ${DENOISE_TRANSFORMS}
TASK_GPUS           := ${MT_GPUS} ${DENOISE_GPUS}



# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


include ../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"


## test zero-shot translation

.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASK_IDS="mt_por-swe mt_swe-fin"
