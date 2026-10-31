## doc-level MT trained on MultiSynt data
## Encoder: 3 layers shared across language groups + 3 layers completely shared
## Decoder: 6 language-specific layers


include ../../../make/env.mk


## model architecture

MODEL_ARCHITECTURE := transformer-base
ENCODER            := "{langgroup}","all"
ENCODER_LAYERS     := 3,3


LANGUAGES := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## pivot-centric translation tasks
## retating GPU assignments

DOCMT_PIVOT_LANGS := eng spa
DOCMT_TASKS       := $(sort $(foreach p,${DOCMT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),$l-$p $p-$l)))
DOCMT_TASK_IDS    := $(addprefix mt_,${DOCMT_TASKS})
DOCMT_TRANSFORMS  := $(foreach l,${DOCMT_TASK_IDS},filtertoolong)
DOCMT_GPUS        := $(call rotating_gpu_assignment,0,9,$(words ${DOCMT_TASK_IDS}))




## zeroshot translation tasks: select language pairs around some pivot languages
## exclude trained language pairs --> it's still too many

# ZEROSHOT_PIVOT_LANGS := fin por
# ZEROSHOT_TASKS       := $(filter-out ${DOCMT_TASKS},$(sort $(foreach p,${ZEROSHOT_PIVOT_LANGS},$(foreach l,$(filter-out $p,${LANGUAGES}),$l-$p $p-$l))))


## language pairs from https://docs.google.com/spreadsheets/d/1K_gIAzUC5apVEhmpMKFlxCFFlFZgLjprqk4JE2Uq2MM/edit?usp=sharing

ZEROSHOT_TASKS := deu-tur deu-ukr fra-nld swe-fin ces-slk bos-hrv bos-srp_Cyrl hrv-srp_Cyrl slv-bos bul-tur deu-ron glg-por eus-fra dan-nob \
		  tur-deu ukr-deu nld-fra fin-swe slk-ces hrv-bos srp_Cyrl-bos srp_Cyrl-hrv bos-slv tur-bul ron-deu por-glg fra-eus nob-dan
ZEROSHOT_TASK_IDS    := $(addprefix zero_,${ZEROSHOT_TASKS})
ZEROSHOT_TRANSFORMS  := $(foreach l,${ZEROSHOT_TASK_IDS},filtertoolong)
ZEROSHOT_WEIGHTS     := $(foreach l,${ZEROSHOT_TASK_IDS},0)
ZEROSHOT_GPUS        := $(call rotating_gpu_assignment,0,9,$(words ${ZEROSHOT_TASK_IDS}))


## task definitions put together

TASK_IDS            := ${ZEROSHOT_TASK_IDS} ${DOCMT_TASK_IDS}
TASK_TRANSFORMS     := ${ZEROSHOT_TRANSFORMS} ${DOCMT_TRANSFORMS}
TASK_GPUS           := ${ZEROSHOT_GPUS} ${DOCMT_GPUS}
TASK_WEIGHTS        := ${ZEROSHOT_WEIGHTS}


## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


# BATCH_SIZE       := 32768
# GRADIENT_ACCUM   := 10
# LOOK_AHEAD       := 10
BATCH_SIZE       := 20480
GRADIENT_ACCUM   := 16
LOOK_AHEAD       := 16
KEEP_CHECKPOINTS := 10


VALID_FREQ  := 2500
SAVE_FREQ   := 2500
REPORT_FREQ := 500


# SLURM_MAX_GPU_TIME := 2-00:00:00


include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"

info-mt:
	@echo "number of tasks: $(words ${DOCMT_TASK_IDS})"

info-zero:
	@echo "number of tasks: $(words ${ZEROSHOT_TASK_IDS})"
	@echo ${ZEROSHOT_TASK_IDS}


## test zero-shot translation


.PHONY: %.zero-shot
%.zero-shot:
	@${MAKE} -s $(basename $@) \
		SLURM_GPU_PARTITION=dev-g \
		EVAL_TASKS_WALLTIME=15:00 \
		TASKS="por-swe ces-ukr" \
		TASK_IDS="mt_por-swe mt_ces-ukr"
