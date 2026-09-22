
MODEL_ARCHITECTURE := transformer-base

ENCODER            := "{lang}","{task}"
ENCODER_LAYERS     := 3,3


DOCMT_TASKS       := deu-eng eng-deu fra-eng eng-fra ita-eng eng-ita slv-eng eng-slv
DOCMT_TASK_IDS    := $(addprefix mt_,${DOCMT_TASKS})
DOCMT_TRAINDATA   := $(patsubst %,multisynt/train/len1024,${DOCMT_TASKS})

SIMPL_TASKS       := deu-deu eng-eng ita-ita fra-fra slv-slv
SIMPL_TASK_IDS    := $(addprefix simpl_,${SIMPL_TASKS})
SIMPL_TRAINDATA   := $(patsubst %,MultiSim/train,${SIMPL_TASKS})
SIMPL_DEVDATA     := $(patsubst %,MultiSim/dev,${SIMPL_TASKS})
SIMPL_TESTDATA    := $(patsubst %,MultiSim/test,${SIMPL_TASKS})



TASK_IDS          := ${SIMPL_TASK_IDS} ${DOCMT_TASK_IDS}
TASK_TRAINDATA    := ${SIMPL_TRAINDATA} ${DOCMT_TRAINDATA}
TASK_DEVDATA      := ${SIMPL_DEVDATA}
TASK_TESTDATA     := ${SIMPL_TESTDATA}



# vocabularies / tokenizers
VOCAB := tatoeba_hplt_multisynt


BATCH_SIZE       := 32768
GRADIENT_ACCUM   := 10
LOOK_AHEAD       := 10


VALID_FREQ  := 2500
SAVE_FREQ   := 2500
REPORT_FREQ := 500


SLURM_MAX_GPU_TIME := 12:00:00


include ../../../make/marmot.mk



info:
	@echo "number of tasks: $(words ${TASK_IDS})"
