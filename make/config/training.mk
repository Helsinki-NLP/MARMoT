#--------------------------------------------------------------
# training parameters
#--------------------------------------------------------------

## task distribution: sampled proportional to the given weight
## - default: uniform sampling (all tasks get weight 1.0)
## - if USE_DATASIZE_AS_TASK_WEIGHT=1: sample proportional to TRAINDATA_SIZE
## - task-specific weights can also be specified in TASK_WEIGHTS
## - multiply by TASK_WEIGHT_FACTORS
## - temperature-based sampling using SAMPLING_TEMP or TASK_WEIGHT_TEMPS

TASK_DISTRIBUTION ?= weighted_sampling

ifeq (${USE_DATASIZE_AS_TASK_WEIGHT},1)
  ifneq (${TRAINDATA_SIZE},)
    SAMPLING_WEIGHT ?= ${TRAINDATA_SIZE}
  endif
endif

SAMPLING_WEIGHT  ?= 1
SAMPLING_FACTOR  ?= 1
SAMPLING_TEMP    ?= 1

TASK_WEIGHT_BASE   := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS)) $(SAMPLING_WEIGHT))
TASK_WEIGHT_FACTOR := $(firstword $(word ${TASK_NR},$(TASK_WEIGHT_FACTORS)) $(SAMPLING_FACTOR))
TASK_WEIGHT_TEMP   := $(firstword $(word ${TASK_NR},$(TASK_WEIGHT_TEMPS)) $(SAMPLING_TEMP))

## temperature-based scaling of weights: w_t = w^(1/T)
## for bc we need to transform this to   w_t = e(1/T*l(w))

ifneq ($(TASK_WEIGHT_FACTOR),1)
  ifneq ($(TASK_WEIGHT_TEMP),1)
    TASK_WEIGHT := $(shell echo 'e(1/${TASK_WEIGHT_TEMP}*l(${TASK_WEIGHT_BASE}*${TASK_WEIGHT_FACTOR}))' | bc -l)
  else
    TASK_WEIGHT := $(shell echo '${TASK_WEIGHT_BASE}*${TASK_WEIGHT_FACTOR}' | bc)
  endif
else
  ifneq ($(TASK_WEIGHT_TEMP),1)
    TASK_WEIGHT := $(shell echo 'e(1/${TASK_WEIGHT_TEMP}*l(${TASK_WEIGHT_BASE}))' | bc -l)
  else
    TASK_WEIGHT := ${TASK_WEIGHT_BASE}
  endif
endif





# type of unit for batch size
# batch size per GPU

BATCH_TYPE   ?= tokens
# BATCH_SIZE ?= 32768
# BATCH_SIZE ?= 16384
BATCH_SIZE   ?= 8192


## sequence length restrictions (min and max)

MIN_SRCSEQ_LENGTH ?= 1
MIN_TRGSEQ_LENGTH ?= 1
MAX_SEQ_LENGTH    ?= 1024
MAX_SRCSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}
MAX_TRGSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}


# validation batch size
# max sequence length for validation examples
# time-out for validation tasks (5 min)
# time-out for decoding one batch during validation (1 min)

VALID_BATCH          ?= 16
VALID_MAX_LENGTH     ?= ${MAX_SEQ_LENGTH}
VALID_TIMEOUT        ?= 300
VALID_DECODE_TIMEOUT ?= 60


# gradient accumulation (number of batches)
# batch look-ahead to sort training examples by length
# queue size in data loader

GRADIENT_ACCUM       ?= 20
LOOK_AHEAD           ?= 80
QUEUE_SIZE           ?= 120


# validation frequency (in steps)
# validation metrics
# checkpoint saving frequency (in steps)
# nr of checkpoints to keep
# progress reporting frequency (steps)
# activate tensorboard logging

VALID_FREQ       ?= 2500
VALID_METRICS    ?= bleu,chrf
SAVE_FREQ        ?= 2500
KEEP_CHECKPOINTS ?= 1
REPORT_FREQ      ?= 500
REPORT_TFLOPS    ?= true
TENSORBOARD      ?= true
TENSORBOARD_DIR  ?= ${EXPERIMENT_DIR}/tb_logs
# TENSORBOARD_DIR  ?= ${MODEL_DIR}/tb_logs


# optimizer and learning parameters

OPTIMIZER        ?= adamw
RESET_OPTIMIZER  ?= none
LEARNING_RATE    ?= 0.0003
# LEARNING_RATE    ?= 0.0001
# LEARNING_RATE    ?= 0.0005
# LEARNING_RATE    ?= 0.0008
ADAM_BETA1       ?= 0.9
ADAM_BETA2       ?= 0.95
# ADAM_BETA2       ?= 0.9
# ADAM_BETA2       ?= 0.999
# ADAMW_FUSED      ?= true
WEIGHT_DECAY     ?= 0.01
MAX_GRAD_NORM    ?= 1.0
LABEL_SMOOTHING  ?= 0.1
WARMUP_STEPS     ?= 1000
# WARMUP_STEPS     ?= 10000
DECAY_METHOD     ?= linear_warmup
LR_DECAY         ?= 0.5
DECAY_START      ?= 10000
# DECAY_START      ?= ${WARMUP_STEPS}
# AVERAGE_DECAY    ?= 0.0005
AVERAGE_DECAY    ?= 0
RANDOM_SEED      ?= 42


# number of training steps to run
# early stopping: number of validation steps without improving

TRAINING_STEPS   ?= 250000
EARLY_STOPPING   ?= 5

