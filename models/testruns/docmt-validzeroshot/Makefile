
TASK_IDS            := zeroshotmt_eng-swe denoise_fin-fin denoise_eng-eng denoise_swe-swe mt_fin-eng mt_eng-fin mt_fin-swe mt_swe-fin mt_swe-eng
TASK_TRANSFORMS     := filtertoolong denoising,filtertoolong denoising,filtertoolong denoising,filtertoolong 
TASK_GPUS           := "0:7"
TASK_WEIGHTS        := 0

## taining data directory
TRAINDATA := multisynt/train/len1024

# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


BATCH_SIZE := 32768
GRADIENT_ACCUM := 10


# 1 day only
SLURM_MAX_GPU_TIME := 12:00:00


include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"


