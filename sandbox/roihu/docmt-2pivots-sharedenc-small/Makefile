
include ../../../make/env.mk

LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## English-centric translation tasks
## assign them to GPUs rotating over all GPUs on each node using 35 nodes (node 0-34)

# DOCMT_PIVOT_LANGS := deu eng fra spa
# DOCMT_EXTRA_TASKS := fin-swe swe-fin fin-ukr ukr-fin
DOCMT_PIVOT_LANGS := eng fin
DOCMT_PIVOT_TASKS := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),$l-$p $p-$l)))
DOCMT_EXTRA_TASKS := fin-swe swe-fin


TASKS := ${DOCMT_PIVOT_TASKS} ${DOCMT_EXTRA_TASKS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


## small transformer architecture

MODEL_ARCHITECTURE := transformer-small
DEFAULT_ENCODER    := "all"


NR_OF_NODES := 12
BATCH_SIZE  := 32768



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
