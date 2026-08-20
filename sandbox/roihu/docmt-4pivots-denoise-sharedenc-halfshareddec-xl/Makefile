# - English-centric doc-level MT tasks from MultiSynt
# - monolingual denoising tasks (using MultiSynth)

include ../../../make/env.mk

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## English-centric translation tasks
## assign them to GPUs rotating over all GPUs on each node using 35 nodes (node 0-34)

DOCMT_PIVOT_LANGS := deu eng fra spa
DOCMT_EXTRA_TASKS := mt_fin-swe mt_swe-fin mt_fin-ukr mt_ukr-fin
DOCMT_TASK_IDS    := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),mt_$l-$p mt_$p-$l)) ${DOCMT_EXTRA_TASKS})
DOCMT_TRANSFORMS  := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_GPUS        := $(call rotating_gpu_assignment,0,35,$(words ${DOCMT_TASK_IDS}))


## denoising tasks (use same as MT training data)
## assign them all to one GPU-node (node 35) rotating over the GPUs on that node

DENOISE_TASK_IDS   := $(foreach l,${LANGUAGES},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_GPUS       := $(call rotating_gpu_assignment,35,4,$(words ${DENOISE_TASK_IDS}))


## task definitions put together

TASK_IDS            := ${DOCMT_TASK_IDS} ${DENOISE_TASK_IDS} 
TASK_TRANSFORMS     := ${DOCMT_TRANSFORMS} ${DENOISE_TRANSFORMS}
TASK_GPUS           := ${DOCMT_GPUS} ${DENOISE_GPUS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


## very big model architecture

MODEL_ARCHITECTURE := transformer-xl
ENCODER            := "all"
DECODER            := "all","{lang}"
DECODER_LAYERS     := 6,6


BATCH_SIZE := 16384



include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"


## test zero-shot translation

ZERO_SHOT_TASKS := 	spa-cat cat-spa spa-eus eus-spa spa-glg glg-spa pol-ukr ukr-pol \
			deu-tur tur-deu deu-ukr ukr-deu fra-nld nld-fra \
			ces-slk slk-ces bos-hrv hrv-bos bos-srp_Cyrl srp_Cyrl-bos bos-slv slv-bos \
			hrv-srp_Cyrl srp_Cyrl-hrv sqi-mkd mkd-sqi bul-tur tur-bul \
			spa-ron ron-spa glg-por por-glg eus-fra fra-eus dan-nob nob-dan \
			hun-ukr ukr-hun ces-ukr ukr-ces ukr-slk slk-ukr swe-ukr ukr-swe


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) TASKS="${ZERO_SHOT_TASKS}"
