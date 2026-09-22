
MODEL_ARCHITECTURE := transformer-base

ENCODER            := "{lang}","{task}"
ENCODER_LAYERS     := 3,3


DOCMT_TASKS        := deu-eng eng-deu fra-eng eng-fra ita-eng eng-ita slv-eng eng-slv
DOCMT_TASK_IDS     := $(addprefix mt_,${DOCMT_TASKS})
DOCMT_TRAINDATA    := $(patsubst %,multisynt/train/len1024,${DOCMT_TASKS})

SIMPL_TASKS        := deu-deu eng-eng ita-ita fra-fra slv-slv
SIMPL_TASK_IDS     := $(addprefix simpl_,${SIMPL_TASKS})
SIMPL_TRAINDATA    := $(patsubst %,MultiSim/train,${SIMPL_TASKS})
SIMPL_DEVDATA      := $(patsubst %,MultiSim/dev,${SIMPL_TASKS})
SIMPL_TESTDATA     := $(patsubst %,MultiSim/test,${SIMPL_TASKS})

DEF_TASKS          := eng-eng fra-fra
DEF_TASK_IDS       := $(addprefix def_,${DEF_TASKS})
DEF_TRAINDATA      := $(patsubst %,definition_modelling/CoDWoE/train,${DEF_TASKS})
DEF_DEVDATA        := $(patsubst %,definition_modelling/CoDWoE/dev,${DEF_TASKS})

SUM_TASKS          := eng-eng fra-fra deu-deu
SUM_TASK_IDS       := $(addprefix sum_,${SUM_TASKS})
SUM_TRAINDATA      := $(patsubst %,summarization/train,${SUM_TASKS})
SUM_DEVDATA        := $(patsubst %,summarization/dev,${SUM_TASKS})
SUM_TESTDATA       := $(patsubst %,summarization/test,${SUM_TASKS})

DENOISE_TASKS      := eng-eng fra-fra deu-deu
DENOISE_TASK_IDS   := $(addprefix denoise_,${DENOISE_TASKS})
DENOISE_TRANSFORMS := $(foreach l,${DENOISE_TASK_IDS},denoising,filtertoolong)
DENOISE_TRAINDATA  := $(patsubst %,multisynt/train/len1024,${DENOISE_TASKS})
DENOISE_DEVDATA    := $(patsubst %,flores200/dev,${DENOISE_TASKS})
DENOISE_TESTDATA   := $(patsubst %,flores200/devtest,${DENOISE_TASKS})


TASK_IDS           := ${DENOISE_TASK_IDS} ${SIMPL_TASK_IDS} ${SUM_TASK_IDS} ${DEF_TASK_IDS} ${DOCMT_TASK_IDS}
TASK_TRAINDATA     := ${DENOISE_TRAINDATA} ${SIMPL_TRAINDATA} ${SUM_TRAINDATA} ${DEF_TRAINDATA} ${DOCMT_TRAINDATA}
TASK_DEVDATA       := ${DENOISE_DEVDATA} ${SIMPL_DEVDATA} ${SUM_DEVDATA} ${DEF_DEVDATA}
TASK_TESTDATA      := ${DENOISE_TESTDATA} ${SIMPL_TESTDATA} ${SUM_TESTDATA}
TASK_TRANSFORMS    := ${DENOISE_TRANSFORMS}


# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


BATCH_SIZE       := 16384
GRADIENT_ACCUM   := 20
LOOK_AHEAD       := 20


VALID_FREQ  := 1000
SAVE_FREQ   := 1000
REPORT_FREQ := 250


SLURM_MAX_GPU_TIME := 12:00:00


include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"
