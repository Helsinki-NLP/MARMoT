#-*-makefile-*-

#--------------------------------------------------------------------------
# task definitions:
#
# - TASKS: source - target language pairs
# - TASK_GPUS: GPU assignment for each task (node:gpu)
# - TASK_WEIGHTS: task weight for sampling training examples
# - TASK_TRANSFORMS: transformations done for each task
# - TASK_ENCODERS: encoder-spec for each task
# - TASK_DECODERS: decoder-spec for each task
# - ZERO_SHOT_TASKS: zero-shot tasks that can be tested at inference time
#
# TASK_GPUS, TASK_WEIGHTS and TASK_TRANSFORMS may only cover the first n tasks;
# all other tasks will obtain default weights and transforms:
#
#    DEFAULT_GPU        := 0:0
#    DEFAULT_WEIGHT     := 1.0
#    DEFAULT_TRANSFORM  := filtertoolong
#
# TASK_ENCODERS and TASK_DECODERS will be set to default values (see below)
# if not specified for the corresponding task; default values are:
#
#    DEFAULT_ENCODER    := "${SRCLANG}"
#    DEFAULT_DECODER    := "${TRGLANG}"
#
#--------------------------------------------------------------------------
# Example task definition:
#
# TASKS           ?= eng-eng fin-fin fin-eng eng-fin 
# TASK_GPUS       ?= 0:0     0:1     0:2     0:3
# TASK_WEIGHTS    ?= 0.1     0.1
# TASK_TRANSFORMS ?= denoising,filtertoolong denoising,filtertoolong
#--------------------------------------------------------------------------



## if no TASKS are defined: try to get the tasks from the TASK_IDS
## --> assumes that the task follows an underscore like in "task_fin-eng"

ifeq (${TASKS},)
ifdef TASK_IDS
  # TASKS ?= $(notdir $(subst _,/,${TASK_IDS}))
  TASKS ?= $(shell echo ${TASK_IDS} | tr " " "\n" | sed 's/^[^_]*_//')
endif
endif

TASKS    ?= fin-eng
TASK_IDS ?= $(patsubst %,task_%,${TASKS})

TASK_LANGPAIRS ?= ${TASKS}


## GPU assignments: simply distribute one task per GPU/Node
## - skip the initial GPU assignments if they exist (in TASK_GPUS)
## - if NR_NODES is set: rotate over available nodes

## don't allocate more nodes than what we can fill with tasks
NR_OF_NODES ?= $(shell 	if [ $(words ${TASKS}) -gt ${MAX_GPUS_PER_NODE} ]; then \
			  echo $$(( $(words ${TASKS}) / ${MAX_GPUS_PER_NODE} )); \
			else echo 1; fi )

TASK_GPU_ASSIGNMENTS := $(shell \
	n=0; g=0; \
	tasks=(${TASKS}); \
	gpus=(${TASK_GPUS}); \
	for i in `seq $(words ${TASKS})`; do \
	  t=$${tasks[$$i-1]}; \
	  a=$${gpus[$$i-1]}; \
	  if [ "$$a" != "" ]; then \
	    echo $$a; \
	  else \
	    echo "$$n:$$g"; \
	    ((g++)); \
	    if [ $$g -eq ${MAX_GPUS_PER_NODE} ]; then \
	      ((n++)); \
	      g=0; \
	    fi; \
	    if [ "${NR_OF_NODES}" != "" ]; then \
	       if [ $$n -eq ${NR_OF_NODES} ]; then \
	         n=0; \
	       fi \
	    fi; \
	  fi \
	done )


## select a task

TASK_NR  ?= $(words $(TASKS))
TASK     := $(word ${TASK_NR},$(TASKS))
LANGPAIR ?= $(word ${TASK_NR},$(TASK_LANGPAIRS))
SRCLANG  ?= $(firstword $(subst -, ,${LANGPAIR}))
TRGLANG  ?= $(lastword  $(subst -, ,${LANGPAIR}))



## find tasks allocated for each GPU
## - ALLOCATED_GPUS: all GPUs that have a task assigned
## - GPU_TASK_PAIRS: GPU-task pairs (format = gpu/task)
## - GPU_TASKID_PAIRS: GPU-taskid pairs (format = gpu/taskid)
## - GPU_TASKS: all tasks for each GPU in the same order as ALLOCATED_GPUS
##              (tasks merged with ':' if there is more than one per GPU)
## - GPU_TASK_IDS: same as above but with task_ids

ALLOCATED_GPUS := $(sort ${TASK_GPU_ASSIGNMENTS})

ifneq ($(words ${ALLOCATED_GPUS}),$(words ${TASK_IDS}))
  MULTIPLE_JOBS_PER_GPU := 1
  GPU_TASKID_PAIRS := $(foreach t,${TASK_IDS},$(call lookup,$t,${TASK_IDS},${TASK_GPU_ASSIGNMENTS})/$t)
  GPU_TASK_PAIRS   := $(foreach t,${GPU_TASKID_PAIRS},$(dir $t)$(call lookup,$(notdir $t),${TASK_IDS},${TASKS}))
  GPU_TASKS        := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(sort $(notdir $(filter $g/%,${GPU_TASK_PAIRS}))))))
  GPU_TASK_IDS     := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(notdir $(filter $g/%,${GPU_TASKID_PAIRS})))))
endif


## path to config files

TRAIN_CONFIGFILE      ?= ${MODEL_DIR}/train.yaml
INFERENCE_CONFIGFILE  ?= ${EVAL_DIR}/inference_${TASK_ID}.yaml
CONFIGFILE            ?= ${TRAIN_CONFIGFILE}


# current task specifications - default values

ifeq (${ADD_LANGUAGE_TOKEN},true)
  DEFAULT_TRANSFORM  ?= prefix,filtertoolong
  DEFAULT_SRCPREFIX  ?= >>${TRGLANG}<<
  DEFAULT_TRGPREFIX  ?= <<${SRCLANG}>>
endif

DEFAULT_GPU        ?= 0:0
DEFAULT_TRANSFORM  ?= filtertoolong
DEFAULT_TRAINSTEP  ?= 0
DEFAULT_ENCODER    ?= "${SRCLANG}"
DEFAULT_DECODER    ?= "${TRGLANG}"
# DEFAULT_WEIGHT     ?= 1.0

# current task specifications - selected with TASK_NR or default value

TASK_ID        := $(firstword $(word ${TASK_NR},$(TASK_IDS))             task_${TASK})
TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPU_ASSIGNMENTS)) $(DEFAULT_GPU))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS))      $(DEFAULT_TRANSFORM))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS))      $(DEFAULT_TRAINSTEP))
TASK_SRCPREFIX := $(firstword $(word ${TASK_NR},$(TASK_SRCPREFIXES))     $(DEFAULT_SRCPREFIX))
TASK_TRGPREFIX := $(firstword $(word ${TASK_NR},$(TASK_TRGPREFIXES))     $(DEFAULT_TRGPREFIX))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))        $(DEFAULT_ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))        $(DEFAULT_DECODER))
# TASK_WEIGHT    := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS))         $(DEFAULT_WEIGHT))

## add prefix transform if necessary

ifneq (${TASK_SRCPREFIX}${TASK_TRGPREFIX},)
ifneq ($(findstring prefix,$(TASK_TRANSFORM)),prefix)
  TASK_TRANSFORM := prefix,${TASK_TRANSFORM}
endif
endif

#--------------------------------------------------------------
# data sets
#
# - default data sets are taken from TRAINDATA_DIR, DEVDATA_DIR and TESTDATA_DIR
# - task-specific training data can be set in TASK_TRAINDATA_SRCS and TASK_TRAINDATA_TRGS
# - task-specific dev data can be set in TASK_DEVDATA_SRCS and TASK_DEVDATA_TRGS
# - task-specific test data can be set in TASK_TESTDATA_SRCS and TASK_TESTDATA_TRGS
#--------------------------------------------------------------


## skip validation for denoising tasks
## and monolingual tasks (typically denoising tasks)
## set those variables to 0 to enable them

SKIP_SAME_LANGUAGE_VALID_TASKS ?= 0
SKIP_DENOISING_VALID_TASKS     ?= 0


## in OPUS/Tatoeba data we have sorted language IDs for language pairs

SORTED_SRCLANG  := $(firstword $(sort ${SRCLANG} ${TRGLANG}))
SORTED_TRGLANG  := $(lastword  $(sort ${SRCLANG} ${TRGLANG}))
SORTED_LANGPAIR := ${SORTED_SRCLANG}-${SORTED_TRGLANG}
REVERSE_LANGPAIR := ${SORTED_TRGLANG}-${SORTED_SRCLANG}


##---------------------------------------------------------------------------------
## datasets: training, development and testing
##---------------------------------------------------------------------------------

## data directories (train/dev/test)
##
## data directories can be specified for each task
## if not, take the default locations given in TRAINDATA, DEVDATA and TESTDATA

TRAINDATA_DIR ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_TRAINDATA)) ${TRAINDATA})
DEVDATA_DIR   ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_DEVDATA)) ${DEVDATA})
TESTDATA_DIR  ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_TESTDATA)) ${TESTDATA})


## basenames of data files (filepattern to be used within the data directories)
##
## file basenames are either given for each specific task
## or we use the default pattern, which is *${SORTED_LANGPAIR}
## (in OPUS/Tatoeba we sort language IDs alphabetically and uses them in the bitext file name)

TRAINDATA_BASENAME ?= $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_BASENAMES)) *${SORTED_LANGPAIR}*)
DEVDATA_BASENAME   ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_BASENAMES)) *${SORTED_LANGPAIR}*)
TESTDATA_BASENAME  ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_BASENAMES)) *${SORTED_LANGPAIR}*)


## file extension for source and target language files
##
## if source and target language are the same AND this is not a denoising task
## then add some digits to the source language file extensions to distinguish
##      between input and output files (e.g. eng1 and eng2)
##
## TASK_SRCLANG_EXT and TASK_TRGLANG_EXT can overwrite the default extensions
## for specific tasks

ifneq ($(findstring denoising,$(TASK_TRANSFORM)),denoising)
ifeq (${SRCLANG},${TRGLANG})
  DEFAULT_SRCLANG_EXT ?= ${SRCLANG}1.gz
  DEFAULT_TRGLANG_EXT ?= ${TRGLANG}2.gz
endif
endif

DEFAULT_SRCLANG_EXT ?= ${SRCLANG}.gz
DEFAULT_TRGLANG_EXT ?= ${TRGLANG}.gz

SRCLANG_EXT ?= $(firstword $(word ${TASK_NR},$(TASK_SRCLANG_EXT)) ${DEFAULT_SRCLANG_EXT})
TRGLANG_EXT ?= $(firstword $(word ${TASK_NR},$(TASK_TRGLANG_EXT)) ${DEFAULT_TRGLANG_EXT})


## training data
##
## default search patterns for finding training data (DEFAULT_TRAINDATA_PATTERNS)
## take the first one that matches any pattern (DEFAULT_TRAINDATA_SRC and DEFAULT_TRAINDATA_TRG)
## overwrite with task-specific training data given in TASK_TRAINDATA_SRCS and TASK_TRAINDATA_TRGS

ifdef FIND_DATA
  DEFAULT_TRAINDATA_PATTERNS ?= ${TRAINDATA_BASENAME} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCTRAIN_PATTERN   ?= $(patsubst %,${TRAINDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_TRAINDATA_PATTERNS})
  DEFAULT_TRGTRAIN_PATTERN   ?= $(patsubst %,${TRAINDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_TRAINDATA_PATTERNS})
  DEFAULT_TRAINDATA_SRC      ?= $(firstword $(wildcard ${DEFAULT_SRCTRAIN_PATTERN}))
  DEFAULT_TRAINDATA_TRG      ?= $(firstword $(wildcard ${DEFAULT_TRGTRAIN_PATTERN}))
endif

TRAINDATA_SRC ?= $(wildcard $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_SRCS)) $(DEFAULT_TRAINDATA_SRC)))
TRAINDATA_TRG ?= $(wildcard $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_TRGS)) $(DEFAULT_TRAINDATA_TRG)))

## data size in bytes (note: can be compressed data)

ifneq (${TRAINDATA_SRC},)
  ifneq (${TRAINDATA_TRG},)
    TRAINDATA_SRC_SIZE := $(shell stat -c%s ${TRAINDATA_SRC})
    TRAINDATA_TRG_SIZE := $(shell stat -c%s ${TRAINDATA_TRG})
    TRAINDATA_SIZE     := $(shell echo $$(( $(TRAINDATA_SRC_SIZE) + $(TRAINDATA_TRG_SIZE) )) )
  endif
endif


## validation data
##
## default search patterns for finding development data (DEFAULT_DEVDATA_PATTERNS)
## take the first one that matches any pattern (DEFAULT_DEVDATA_SRC and DEFAULT_DEVDATA_TRG)
## skip denoising tasks if SKIP_DENOISING_VALID_TASKS=1
## skip monolingual tasks if SKIP_SAME_LANGUAGE_VALID_TASKS=1
## overwrite with task-specific development data given in TASK_DEVDATA_SRCS and TASK_DEVDATA_TRGS

ifdef FIND_DATA
  DEFAULT_DEVDATA_PATTERNS ?= ${DEVDATA_BASENAME} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCDEV_PATTERN ?= $(patsubst %,${DEVDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_DEVDATA_PATTERNS}) ${DEVDATA_DIR}/${SRCLANG}*
  DEFAULT_TRGDEV_PATTERN ?= $(patsubst %,${DEVDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_DEVDATA_PATTERNS}) ${DEVDATA_DIR}/${TRGLANG}*
  DEFAULT_DEVDATA_SRC    ?= $(firstword $(wildcard ${DEFAULT_SRCDEV_PATTERN}))
  DEFAULT_DEVDATA_TRG    ?= $(firstword $(wildcard ${DEFAULT_TRGDEV_PATTERN}))
endif

ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_VALID_TASKS},denoising-1)
  ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_VALID_TASKS},$(TRGLANG)-1)
    DEVDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_SRCS)) $(DEFAULT_DEVDATA_SRC))
    DEVDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_TRGS)) $(DEFAULT_DEVDATA_TRG))
  endif
endif


## testdata
##
## default test data patterns (DEFAULT_SRCTEST_PATTERN and DEFAULT_TRGTEST_PATTERN)
## take the first one that matches any pattern (DEFAULT_TESTDATA_SRC and DEFAULT_TESTDATA_TRG)
## overwrite with task-specific test data given in TASK_TESTDATA_SRCS and TASK_TESTDATA_TRGS
## TESTDATA_OUTPUT: name of the output file (translations)

ifdef FIND_TESTDATA
  DEFAULT_TESTDATA_PATTERNS ?= ${TESTDATA_BASENAME} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCTEST_PATTERN ?= $(patsubst %,${TESTDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_TESTDATA_PATTERNS}) ${TESTDATA_DIR}/${SRCLANG}*
  DEFAULT_TRGTEST_PATTERN ?= $(patsubst %,${TESTDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_TESTDATA_PATTERNS}) ${TESTDATA_DIR}/${TRGLANG}*
  DEFAULT_TESTDATA_SRC    ?= $(firstword $(wildcard ${DEFAULT_SRCTEST_PATTERN}))
  DEFAULT_TESTDATA_TRG    ?= $(firstword $(wildcard ${DEFAULT_TRGTEST_PATTERN}))
endif

TESTDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_SRCS)) $(DEFAULT_TESTDATA_SRC))
TESTDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_TRGS)) $(DEFAULT_TESTDATA_TRG))

TESTDATA_OUTPUT ?= ${EVAL_DIR}/${TASK_ID}.${TESTDATA_NAME}.${SRCLANG}.${TRGLANG}


#--------------------------------------------------------------
# vocab files
#--------------------------------------------------------------

## really ugly way of getting from tasks to a unique set
## of source and target languages for the vocabs

VOCAB_SRCLANGS ?= $(sort $(patsubst %/,%,$(dir $(subst -,/,${TASKS}))))
VOCAB_TRGLANGS ?= $(sort $(notdir $(subst -,/,${TASKS})))

VOCAB_SIZE     ?= 32000
VOCAB_SRC_SIZE ?= ${VOCAB_SIZE}
VOCAB_TRG_SIZE ?= ${VOCAB_SIZE}
VOCAB_SRC_DIR  ?= ${VOCAB_DIR}
VOCAB_TRG_DIR  ?= ${VOCAB_DIR}

VOCAB_FILE     ?= ${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json
VOCAB_SRC_FILE ?= ${VOCAB_SRC_DIR}/${SRCLANG}/${VOCAB_SRC_SIZE}/tokenizer.json
VOCAB_TRG_FILE ?= ${VOCAB_TRG_DIR}/${TRGLANG}/${VOCAB_TRG_SIZE}/tokenizer.json

VOCAB_SRC_FILES ?= $(foreach l,${VOCAB_SRCLANGS},${VOCAB_SRC_DIR}/$l/${VOCAB_SRC_SIZE}/tokenizer.json)
VOCAB_TRG_FILES ?= $(foreach l,${VOCAB_TRGLANGS},${VOCAB_TRG_DIR}/$l/${VOCAB_TRG_SIZE}/tokenizer.json)


#--------------------------------------------------------------
# model architecture
#--------------------------------------------------------------


ENCODER_LAYERS     ?= 6        # Encoder layers (total size)
DECODER_LAYERS     ?= 6        # Decoder layers (total size)

MODEL_DIMENSION    ?= 768      # Transformer model dimension
MODEL_DTYPE        ?= bf16     # parameter precision and type
DROPOUT_RATE       ?= 0.1      # dropout rate

ADD_LANGUAGE_TOKEN ?= false


# X-Transformer options

XTRF_FLASH_ATTENTION       ?= true     # Flash attention (not supported on V100)
XTRF_ROTARY_POS_EMBEDDINGS ?= true     # Use rotary positional embeddings
XTRF_TIE_EMBEDDINGS        ?= false    # Tie input/output embeddings
XTRF_HEADS                 ?= 8
XTRF_PRE_NORM              ?= false
XTRF_POST_EMB_NORM         ?= true
XTRF_POST_EMB_NORM_BIAS    ?= true
XTRF_ATTN_DROPOUT          ?= 0.1
XTRF_FF_DROPOUT            ?= 0.1
XTRF_LAYERNORM_BIAS        ?= true
XTRF_USE_ABS_POS_EMB       ?= false


#--------------------------------------------------------------
# required resources (compute nodes and GPUs)
#--------------------------------------------------------------

GPU_RANKS      := $(sort $(notdir $(subst :,/,${TASK_GPU_ASSIGNMENTS})))
GPUS_PER_NODE  := $(words ${GPU_RANKS})
NR_OF_GPUS     := $(words $(sort ${TASK_GPU_ASSIGNMENTS}))
NR_OF_NODES    := $(words $(sort $(dir $(subst :,/,${TASK_GPU_ASSIGNMENTS}))))


#--------------------------------------------------------------
# training parameters
#--------------------------------------------------------------

## task distribution: sampled proportional to the given weight
## - default: uniform sampling (all tasks get weight 1.0)
## - if USE_DATASIZE_AS_TASK_WEIGHT=1: sample proportional to TRAINDATA_SIZE
## - task-specific weights can also be specified in TASK_WEIGHTS

TASK_DISTRIBUTION ?= weighted_sampling

ifeq (${USE_DATASIZE_AS_TASK_WEIGHT},1)
  DEFAULT_WEIGHT ?= ${TRAINDATA_SIZE}
else
  DEFAULT_WEIGHT ?= 1.0
endif

TASK_WEIGHT := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS)) $(DEFAULT_WEIGHT))


RANDOM_SEED          ?= 42
BATCH_TYPE           ?= tokens  # type of unit for batch size
BATCH_SIZE           ?= 8192    # per-GPU batch size
VALID_BATCH          ?= 16      # validation batch size
VALID_TIMEOUT        ?= 300     # validation time-out after 5 min
VALID_DECODE_TIMEOUT ?= 60      # validation batch decoding time-out after 1 min
VALID_MAX_LENGTH     ?= ${MAX_SEQ_LENGTH}
GRADIENT_ACCUM       ?= 20      # gradient accumulation
LOOK_AHEAD           ?= ${GRADIENT_ACCUM} # batch look-ahead to sort training examples by length
QUEUE_SIZE           ?= 80

MIN_SRCSEQ_LENGTH ?= 1
MIN_TRGSEQ_LENGTH ?= 1
MAX_SEQ_LENGTH    ?= 1024
MAX_SRCSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}
MAX_TRGSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}


VALID_FREQ       ?= 2500    # validation frequency (steps)
VALID_METRICS    ?= bleu    # validation metrics
SAVE_FREQ        ?= 2500    # checkpoint saving frequency (steps)
KEEP_CHECKPOINTS ?= 1       # nr of checkpoints to keep
REPORT_FREQ      ?= 500     # progress reporting frequency (steps)
REPORT_TFLOPS    ?= true
TENSORBOARD      ?= true
TENSORBOARD_DIR  ?= ${MODEL_DIR}/logs

OPTIMIZER        ?= adamw
LEARNING_RATE    ?= 0.0003
# LEARNING_RATE    ?= 0.0005
# LEARNING_RATE    ?= 0.0008
# LEARNING_RATE    ?= 0.00001
ADAM_BETA1       ?= 0.9
ADAM_BETA2       ?= 0.999
WEIGHT_DECAY     ?= 0.01
MAX_GRAD_NORM    ?= 1.0
LABEL_SMOOTHING  ?= 0.1
LR_DECAY         ?= 0.5     # learning rate decay
DECAY_START      ?= 10000   # steps when to start lr-decay
# AVERAGE_DECAY    ?= 0.0005
AVERAGE_DECAY    ?= 0
WARMUP_STEPS     ?= 10000
DECAY_METHOD     ?= linear_warmup
TRAINING_STEPS   ?= 100000


#--------------------------------------------------------------
# decoding parameters
#--------------------------------------------------------------

DECODING_BEAM_SIZE  ?= 4
DECODING_BATCH_SIZE ?= 32
DECODING_BATCH_TYPE ?= sents


#--------------------------------------------------------------
# generate config files
#--------------------------------------------------------------

.PHONY: train-config
train-config: ${TRAIN_CONFIGFILE}

.PHONY: inference-config
inference-config: ${INFERENCE_CONFIGFILE}

${INFERENCE_CONFIGFILE}: ${MODEL_META}
	@mkdir -p $(dir $@)
	echo 'task_id: ${TASK_ID}'                                     > $@
	@echo ''                                                      >> $@
	echo "tasks:"                                                 >> $@
	${MAKE} -s CONFIGFILE=$@ FIND_TESTDATA=1 TASK_GPU=0:0 config-add-task
	@echo ''                                                      >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${TRGLANG} \
		config-add-srcvocabs \
		config-add-trgvocabs \
		config-add-model-architecture \
		config-add-transformer-params
	@echo ''                                                      >> $@
	@echo '# Decoding parameters'                                 >> $@
	@echo 'beam_size: ${DECODING_BEAM_SIZE}'                      >> $@
	@echo 'batch_size: ${DECODING_BATCH_SIZE}'                    >> $@
	@echo 'batch_type: ${DECODING_BATCH_TYPE}'                    >> $@
	@echo 'max_length: ${MAX_SEQ_LENGTH}'                         >> $@
	@echo ''                                                      >> $@
	@echo '# GPU settings'                                        >> $@
	@echo 'gpu: 0'                                                >> $@
	@echo 'world_size: 1'                                         >> $@
	@echo 'gpu_ranks: [0]'                                        >> $@
	@echo ''                                                      >> $@
	@echo 'seed: ${RANDOM_SEED}'                                  >> $@
	@echo 'src: ${TESTDATA_SRC}'                                  >> $@
	@echo 'output: ${TESTDATA_OUTPUT}'                            >> $@
	@echo 'model: ${MODEL_PATH}'                                  >> $@


TASK_NRS := $(shell seq $(words ${TASKS}))
TASK_CONFIGFILES := $(patsubst %,${TRAIN_CONFIGFILE}.%,${TASK_NRS})

.INTERMEDIATE: ${TASK_CONFIGFILES}

${TASK_CONFIGFILES}:
	@mkdir -p $(dir $@)
	@${MAKE} -s CONFIGFILE=$@ TASK_NR=$(lastword $(subst ., ,$@)) FIND_DATA=1 config-add-traintask

${TRAIN_CONFIGFILE}: ${TASK_CONFIGFILES}
	@mkdir -p $(dir $@)
	echo "tasks:"                                                 > $@
	@-cat $^                                                     >> $@
	@echo ''                                                     >> $@
	@echo "add model/training parameters"
	${MAKE} -s -j1 CONFIGFILE=$@ \
		config-add-srcvocabs \
		config-add-trgvocabs \
		config-add-model-architecture \
		config-add-transformer-params \
		config-add-training-params \
		config-add-checkpoint-params
ifeq ($(findstring denoising,$(TASK_TRANSFORMS)),denoising)
	${MAKE} -s CONFIGFILE=$@ config-add-denoising
endif
	@echo ''                                                     >> $@
	@echo '# Model saving'                                       >> $@
	@echo 'save_model: ${MODEL_PATH}'                            >> $@
	@echo 'save_strategy: best_and_last'                         >> $@


## add a task section

.PHONY: config-add-traintask
config-add-traintask:
ifneq ($(wildcard ${TRAINDATA_SRC}),)
  ifneq ($(wildcard ${TRAINDATA_TRG}),)
	@${MAKE} -s config-add-task
  else
	@echo "WARNING: no target training data ${TRAINDATA_TRG} found! skip task ${TASK_ID}"
  endif
else
	@echo "WARNING: no source training data ${TRAINDATA_SRC} found skip task ${TASK_ID}"
endif

.PHONY: config-add-task
config-add-task:
	@echo "add task ${TASK} with ID ${TASK_ID}"
	@echo '  ${TASK_ID}:'                                     >> ${CONFIGFILE}
	@echo '    src_tgt: "${TASK}"'                            >> ${CONFIGFILE}
	@echo '    weight: ${TASK_WEIGHT}'                        >> ${CONFIGFILE}
	@echo '    introduce_at_training_step: ${TASK_TRAINSTEP}' >> ${CONFIGFILE}
	@echo '    node_gpu: "${TASK_GPU}"'                       >> ${CONFIGFILE}
	@echo '    enc_sharing_group: [${TASK_ENCODER}]'          >> ${CONFIGFILE}
	@echo '    dec_sharing_group: [${TASK_DECODER}]'          >> ${CONFIGFILE}
	@echo '    transforms: [${TASK_TRANSFORM}]'               >> ${CONFIGFILE}
ifeq (${ADD_LANGUAGE_TOKEN},true)
	@echo '    src_prefix: "${TASK_SRCPREFIX}"'               >> ${CONFIGFILE}
	@echo '    tgt_prefix: "${TASK_TRGPREFIX}"'               >> ${CONFIGFILE}
endif
ifneq (${TRAINDATA_SRC},)
  ifneq (${TRAINDATA_TRG},)
    ifneq ($(wildcard ${TRAINDATA_SRC}),)
      ifneq ($(wildcard ${TRAINDATA_TRG}),)
	@echo '    path_src: ${TRAINDATA_SRC}'                    >> ${CONFIGFILE}
	@echo '    path_tgt: ${TRAINDATA_TRG}'                    >> ${CONFIGFILE}
      endif
    endif
   endif
endif
ifneq (${DEVDATA_SRC},)
  ifneq (${DEVDATA_TRG},)
    ifneq ($(wildcard ${DEVDATA_SRC}),)
      ifneq ($(wildcard ${DEVDATA_TRG}),)
	@echo '    path_valid_src: ${DEVDATA_SRC}'                >> ${CONFIGFILE}
	@echo '    path_valid_tgt: ${DEVDATA_TRG}'                >> ${CONFIGFILE}
      endif
    endif
  endif
endif
	@echo ''                                                  >> ${CONFIGFILE}



.PHONY: config-add-vocab
config-add-vocab:
	echo '   ${LANGID}: ${VOCAB_FILE}'                        >> ${CONFIGFILE}


src-vocab-file = $(call lookup,$1,${VOCAB_SRCLANGS},${VOCAB_SRC_FILES})
trg-vocab-file = $(call lookup,$1,${VOCAB_TRGLANGS},${VOCAB_TRG_FILES})

PHONY: confg-add-srcvocabs
config-add-srcvocabs:
	@echo "src_vocab:"                                        >> ${CONFIGFILE}
	@echo $(foreach i,${VOCAB_SRCLANGS},$i:$(call src-vocab-file,$i)) \
	| tr ' ' "\n" | sed 's/:/: /' | sed 's/^/   /'            >> ${CONFIGFILE}
	@echo ''                                                  >> ${CONFIGFILE}

.PHONY: config-add-trgvocabs
config-add-trgvocabs:
	@echo "tgt_vocab:"                                        >> ${CONFIGFILE}
	@echo $(foreach i,${VOCAB_TRGLANGS},$i:$(call trg-vocab-file,$i)) \
	| tr ' ' "\n" | sed 's/:/: /' | sed 's/^/   /'            >> ${CONFIGFILE}
	@echo ''                                                  >> ${CONFIGFILE}

.PHONY: config-add-denoising
config-add-denoising:
	echo '# Denoising transform parameters'                   >> ${CONFIGFILE}
	echo 'denoising_objective: bart'                          >> ${CONFIGFILE}
	echo 'mask_ratio: 0.2              # Fraction of tokens to mask' >> ${CONFIGFILE}
	echo 'mask_length: span-poisson    # Options: "subword", "word", "span-poisson"' >> ${CONFIGFILE}
	echo 'poisson_lambda: 3.0          # Lambda for span length distribution' >> ${CONFIGFILE}
	echo 'replace_length: 1            # -1: keep N tokens, 0: remove all, 1: single mask per span' >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}


.PHONY: config-add-model-architecture
config-add-model-architecture:
	echo '# Model Architecture Options'                       >> ${CONFIGFILE}
	echo 'enc_layers: [$(strip ${ENCODER_LAYERS})]'           >> ${CONFIGFILE}
	echo 'dec_layers: [$(strip ${DECODER_LAYERS})]'           >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	echo 'model_dim: ${MODEL_DIMENSION}'                      >> ${CONFIGFILE}
	echo 'dropout: ${DROPOUT_RATE}'                           >> ${CONFIGFILE}
	echo 'model_dtype: ${MODEL_DTYPE}'                        >> ${CONFIGFILE}
	echo 'add_language_tokens: ${ADD_LANGUAGE_TOKEN}'         >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}

.PHONY: config-add-transformer-params
config-add-transformer-params:
	echo '# x-transformers specific options'                  >> ${CONFIGFILE}
	echo 'x_transformers_opts:'                               >> ${CONFIGFILE}
	echo '  attn_flash: ${XTRF_FLASH_ATTENTION}'              >> ${CONFIGFILE}
	echo '  rotary_pos_emb: ${XTRF_ROTARY_POS_EMBEDDINGS}'    >> ${CONFIGFILE}
	echo '  tie_embedding: ${XTRF_TIE_EMBEDDINGS}'            >> ${CONFIGFILE}
	echo '  heads: ${XTRF_HEADS}'                             >> ${CONFIGFILE}
	echo '  pre_norm: ${XTRF_PRE_NORM}'                       >> ${CONFIGFILE}
	echo '  post_emb_norm: ${XTRF_POST_EMB_NORM}'             >> ${CONFIGFILE}
	echo '  post_emb_norm_bias: ${XTRF_POST_EMB_NORM_BIAS}'   >> ${CONFIGFILE}
	echo '  attn_dropout: ${XTRF_ATTN_DROPOUT}'               >> ${CONFIGFILE}
	echo '  ff_dropout: ${XTRF_FF_DROPOUT}'                   >> ${CONFIGFILE}
	echo '  layernorm_bias: ${XTRF_LAYERNORM_BIAS}'           >> ${CONFIGFILE}
	echo '  use_abs_pos_emb: ${XTRF_USE_ABS_POS_EMB}'         >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}


COMMA            := ,
GPU_RANKS_STRING := $(subst $(eval ) ,${COMMA},$(GPU_RANKS))

.PHONY: config-add-training-params
config-add-training-params:
	@echo 'src_seq_length_min: ${MIN_SRCSEQ_LENGTH}'           >> ${CONFIGFILE}
	@echo 'tgt_seq_length_min: ${MIN_TRGSEQ_LENGTH}'           >> ${CONFIGFILE}
	@echo 'src_seq_length_max: ${MAX_SRCSEQ_LENGTH}'           >> ${CONFIGFILE}
	@echo 'tgt_seq_length_max: ${MAX_TRGSEQ_LENGTH}'           >> ${CONFIGFILE}
	@echo 'max_length: ${MAX_SEQ_LENGTH}'                      >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Training Configuration'                           >> ${CONFIGFILE}
	@echo 'train_steps: ${TRAINING_STEPS}'                     >> ${CONFIGFILE}
	@echo 'accum_count: [$(strip ${GRADIENT_ACCUM})]'          >> ${CONFIGFILE}
	@echo 'lookahead_minibatches: ${LOOK_AHEAD}'               >> ${CONFIGFILE}
	@echo 'batch_size: ${BATCH_SIZE}'                          >> ${CONFIGFILE}
	@echo 'batch_type: ${BATCH_TYPE}'                          >> ${CONFIGFILE}
	@echo 'normalization: ${BATCH_TYPE}'                       >> ${CONFIGFILE}
	@echo 'queue_size: ${QUEUE_SIZE}'                          >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Optimizer settings (from create_opts)'            >> ${CONFIGFILE}
	@echo 'optim: ${OPTIMIZER}'                                >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'learning_rate: ${LEARNING_RATE}'                    >> ${CONFIGFILE}
	@echo 'adam_beta1: ${ADAM_BETA1}'                          >> ${CONFIGFILE}
	@echo 'adam_beta2: ${ADAM_BETA2}'                          >> ${CONFIGFILE}
	@echo 'weight_decay: ${WEIGHT_DECAY}'                      >> ${CONFIGFILE}
	@echo 'max_grad_norm: ${MAX_GRAD_NORM}'                    >> ${CONFIGFILE}
	@echo 'label_smoothing: ${LABEL_SMOOTHING}'                >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Learning rate scheduling'                         >> ${CONFIGFILE}
	@echo 'warmup_steps: ${WARMUP_STEPS}'                      >> ${CONFIGFILE}
	@echo 'decay_method: ${DECAY_METHOD}'                      >> ${CONFIGFILE}
	@echo 'learning_rate_decay: ${LR_DECAY}'                   >> ${CONFIGFILE}
	@echo 'start_decay_steps: ${DECAY_START}'                  >> ${CONFIGFILE}
	@echo 'average_decay: ${AVERAGE_DECAY}'                    >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'world_size: ${NR_OF_GPUS}'                          >> ${CONFIGFILE}
	@echo 'gpu_ranks: [${GPU_RANKS_STRING}]'                   >> ${CONFIGFILE}
	@echo 'n_nodes: ${NR_OF_NODES}'                            >> ${CONFIGFILE}
	@echo 'task_distribution_strategy: ${TASK_DISTRIBUTION}'   >> ${CONFIGFILE}
ifeq (${NR_OF_NODES},1)
	@echo 'node_rank: 0'                                       >> ${CONFIGFILE}
endif
	@echo ''                                                   >> ${CONFIGFILE}
ifdef RANDOM_SEED
	@echo 'seed: ${RANDOM_SEED}'                               >> ${CONFIGFILE}
endif


.PHONY: config-add-checkpoint-params
config-add-checkpoint-params:
	@echo '# Decoding parameters during validation'            >> ${CONFIGFILE}
	@echo 'valid_batch_size: ${VALID_BATCH}'                   >> ${CONFIGFILE}
	@echo 'valid_steps: ${VALID_FREQ}'                         >> ${CONFIGFILE}
	@echo 'valid_timeout: ${VALID_TIMEOUT}'                    >> ${CONFIGFILE}
	@echo 'valid_decode_timeout: ${VALID_DECODE_TIMEOUT}'      >> ${CONFIGFILE}
	@echo 'valid_max_length: ${VALID_MAX_LENGTH}'              >> ${CONFIGFILE}
	@echo 'valid_metrics: [$(strip ${VALID_METRICS})]'         >> ${CONFIGFILE}
	@echo 'beam_size: 1'                                       >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'save_checkpoint_steps: ${SAVE_FREQ}'                >> ${CONFIGFILE}
	@echo 'keep_checkpoint: ${KEEP_CHECKPOINTS}'               >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Logging and Monitoring'                           >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'log_model_structure: false'                         >> ${CONFIGFILE}
	@echo 'tensorboard: ${TENSORBOARD}'                        >> ${CONFIGFILE}
	@echo 'tensorboard_log_dir: ${TENSORBOARD_DIR}'            >> ${CONFIGFILE}
	@echo 'report_tflops: ${REPORT_TFLOPS}'                    >> ${CONFIGFILE}
	@echo 'report_every: ${REPORT_FREQ}'                       >> ${CONFIGFILE}
	@echo 'report_training_accuracy: false'                    >> ${CONFIGFILE}







## data size count files (countling lines, words and bytes with wc)
## and make targets to create those files

TRAINDATA_SRC_SIZEFILE ?= ${TRAINDATA_SRC}.size
TRAINDATA_TRG_SIZEFILE ?= ${TRAINDATA_TRG}.size

MAKE_TRAINDATA_SIZEFILES := $(patsubst %,make-train-datasize-files/%,${TASK_NRS})
.PHONY: ${MAKE_TRAINDATA_SIZEFILES}
${MAKE_TRAINDATA_SIZEFILES}:
	${MAKE} TASK_NR=$(notdir $@) make-train-datasize-files

.PHONY: make-train-datasize-files
make-train-datasize-files: ${TRAINDATA_SRC_SIZEFILE} ${TRAINDATA_TRG_SIZEFILE}

${TRAINDATA_SRC_SIZEFILE}: ${TRAINDATA_SRC}
	${GZIP} -cd < $< | wc > $@

ifneq (${TRAINDATA_SRC_SIZEFILE},${TRAINDATA_TRG_SIZEFILE})
${TRAINDATA_TRG_SIZEFILE}: ${TRAINDATA_TRG}
	${GZIP} -cd < $< | wc > $@
endif
