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

TASKS ?= fin-eng


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
SRCLANG  ?= $(firstword $(subst -, ,${TASK}))
TRGLANG  ?= $(lastword  $(subst -, ,${TASK}))
LANGPAIR ?= ${SRCLANG}-${TRGLANG}


## path to config files

TRAIN_CONFIGFILE      ?= ${MODEL_DIR}/train.yaml
INFERENCE_CONFIGFILE  ?= ${EVAL_DIR}/inference_${TASK_ID}.yaml
CONFIGFILE            ?= ${TRAIN_CONFIGFILE}


# current task specifications - default values

ifeq (${ADD_LANGUAGE_TOKEN},true)
  DEFAULT_TRANSFORM  ?= filtertoolong,prefix
endif

DEFAULT_GPU        ?= 0:0
DEFAULT_WEIGHT     ?= 1.0
DEFAULT_TRANSFORM  ?= filtertoolong
DEFAULT_TRAINSTEP  ?= 0
DEFAULT_SRCPREFIX  ?= >>${TRGLANG}<<
DEFAULT_TRGPREFIX  ?= <<${SRCLANG}>>
DEFAULT_ENCODER    ?= "${SRCLANG}"
DEFAULT_DECODER    ?= "${TRGLANG}"

# current task specifications - selected with TASK_NR or default value

TASK_ID        := $(firstword $(word ${TASK_NR},$(TASK_IDS))             task_${TASK})
TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPU_ASSIGNMENTS)) $(DEFAULT_GPU))
TASK_WEIGHT    := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS))         $(DEFAULT_WEIGHT))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS))      $(DEFAULT_TRANSFORM))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS))      $(DEFAULT_TRAINSTEP))
TASK_SRCPREFIX := $(firstword $(word ${TASK_NR},$(TASK_SRCPREFIXES))     $(DEFAULT_SRCPREFIX))
TASK_TRGPREFIX := $(firstword $(word ${TASK_NR},$(TASK_TRGPREFIXES))     $(DEFAULT_TRGPREFIX))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))        $(DEFAULT_ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))        $(DEFAULT_DECODER))


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

SKIP_SAME_LANGUAGE_VALID_TASKS ?= 1
SKIP_DENOISING_VALID_TASKS     ?= 1


## in OPUS/Tatoeba data we have sorted language IDs for language pairs

SORTED_SRCLANG  := $(firstword $(sort ${SRCLANG} ${TRGLANG}))
SORTED_TRGLANG  := $(lastword  $(sort ${SRCLANG} ${TRGLANG}))


## monolingual data and denoising tasks: take bilingual data with English or French
##
## TODO: what do we do if those alignments do not exist?
## TODO: use actual monolingual data sets

ifeq ($(findstring denoising,$(TASK_TRANSFORM)),denoising)
ifeq (${SRCLANG},${TRGLANG})
ifeq (${SRCLANG},eng)
  SORTED_SRCLANG := eng
  SORTED_TRGLANG := fra
else
  SORTED_SRCLANG := $(firstword $(sort eng ${TRGLANG}))
  SORTED_TRGLANG := $(lastword  $(sort eng ${TRGLANG}))
endif
endif
endif

SORTED_LANGPAIR  := ${SORTED_SRCLANG}-${SORTED_TRGLANG}
REVERSE_LANGPAIR := ${SORTED_TRGLANG}-${SORTED_SRCLANG}



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

TRAINDATA_BASENAME ?= $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_BASENAMES)) *${SORTED_LANGPAIR})
DEVDATA_BASENAME   ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_BASENAMES)) *${SORTED_LANGPAIR})
TESTDATA_BASENAME  ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_BASENAMES)) *${SORTED_LANGPAIR})


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



##---------------------------------------------------------------------------------
## training data
##
##
## look for training data in the TRAININDATA_DIR using different file patterns:
##
## (1) ${TRAINDATA_BASENAME}.${SRCLANG_EXT} and ${TRAINDATA_BASENAME}.${TRGLANG_EXT}
## (2) ${TRAINDATA_BASENAME}.${SRCLANG}1.gz and ${TRAINDATA_BASENAME}.${TRGLANG}2.gz
## (3) *${LANGPAIR}.${SRCLANG_EXT}          and *${LANGPAIR}.${TRGLANG_EXT}
## (4) *${SORTED_LANGPAIR}.${SRCLANG_EXT}   and *${SORTED_LANGPAIR}.${TRGLANG_EXT}
## (5) *${REVERSE_LANGPAIR}.${SRCLANG_EXT}  and *${REVERSE_LANGPAIR}.${TRGLANG_EXT}
##
## the first one that is found will be taken as a default set
## this can be overwritten with task specific data specified in
##    TASK_TRAINDATA_SRCS and TASK_TRAINDATA_TRGS
##
## TODO: is this too much magic and does this cause a lot of potential problems?
##---------------------------------------------------------------------------------

DEFAULT_TRAINDATA_SRC ?= $(firstword 	$(wildcard ${TRAINDATA_DIR}/${TRAINDATA_BASENAME}.${SRCLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/${TRAINDATA_BASENAME}.${SRCLANG}1.gz) \
					$(wildcard ${TRAINDATA_DIR}/*${LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/*${SORTED_LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/*${REVERSE_LANGPAIR}.${SRCLANG_EXT}))
DEFAULT_TRAINDATA_TRG ?= $(firstword 	$(wildcard ${TRAINDATA_DIR}/${TRAINDATA_BASENAME}.${TRGLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/${TRAINDATA_BASENAME}.${TRGLANG}2.gz) \
					$(wildcard ${TRAINDATA_DIR}/*${LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/*${SORTED_LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${TRAINDATA_DIR}/*${REVERSE_LANGPAIR}.${TRGLANG_EXT}))

TRAINDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_SRCS)) $(DEFAULT_TRAINDATA_SRC))
TRAINDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_TRGS)) $(DEFAULT_TRAINDATA_TRG))



## validation data
##
## same principles as for training data (see above)
## but using the DEVDATA variables

DEFAULT_DEVDATA_SRC ?= $(firstword 	$(wildcard ${DEVDATA_DIR}/${DEVDATA_BASENAME}.${SRCLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/${DEVDATA_BASENAME}.${SRCLANG}1.gz) \
					$(wildcard ${DEVDATA_DIR}/*${LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/*${SOFRTED_LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/*${REVERSE_LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/${SRCLANG}_*))
DEFAULT_DEVDATA_TRG ?= $(firstword 	$(wildcard ${DEVDATA_DIR}/${DEVDATA_BASENAME}.${TRGLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/${DEVDATA_BASENAME}.${TRGLANG}2.gz) \
					$(wildcard ${DEVDATA_DIR}/*${LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/*${SORTED_LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/*${REVERSE_LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${DEVDATA_DIR}/${TRGLANG}_*))


ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_VALID_TASKS},denoising-1)
  ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_VALID_TASKS},$(TRGLANG)-1)
    DEVDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_SRCS)) $(DEFAULT_DEVDATA_SRC))
    DEVDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_TRGS)) $(DEFAULT_DEVDATA_TRG))
  endif
endif



## testdata
##
## same principles as for training data (see above)
## but using the TESTDATA variables


DEFAULT_TESTDATA_SRC ?= $(firstword 	$(wildcard ${TESTDATA_DIR}/${TESTDATA_BASENAME}.${SRCLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/${TESTDATA_BASENAME}.${SRCLANG}1.gz) \
					$(wildcard ${TESTDATA_DIR}/*${LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/*${SORTED_LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/*${REVERSE_LANGPAIR}.${SRCLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/${SRCLANG}_*))
DEFAULT_TESTDATA_TRG ?= $(firstword 	$(wildcard ${TESTDATA_DIR}/${TESTDATA_BASENAME}.${TRGLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/${TESTDATA_BASENAME}.${TRGLANG}2.gz) \
					$(wildcard ${TESTDATA_DIR}/*${LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/*${SORTED_LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/*${REVERSE_LANGPAIR}.${TRGLANG_EXT}) \
					$(wildcard ${TESTDATA_DIR}/${TRGLANG}_*))


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
VOCAB_FILE     ?= ${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json



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
XTRF_HEADS                 ?= 12
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

RANDOM_SEED      ?= 42
BATCH_TYPE       ?= tokens  # type of unit for batch size
BATCH_SIZE       ?= 8192    # per-GPU batch size
VALID_BATCH      ?= 32      # validation batch size
GRADIENT_ACCUM   ?= 20      # gradient accumulation
LOOK_AHEAD       ?= ${GRADIENT_ACCUM} # batch look-ahead to sort training examples by length
QUEUE_SIZE       ?= 40

TASK_DISTRIBUTION ?= weighted_sampling
MIN_SRCSEQ_LENGTH ?= 1
MIN_TRGSEQ_LENGTH ?= 1
MAX_SEQ_LENGTH    ?= 512
MAX_SRCSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}
MAX_TRGSEQ_LENGTH ?= ${MAX_SEQ_LENGTH}


VALID_FREQ       ?= 5000    # validation frequency (steps)
VALID_METRICS    ?= bleu    # validation metrics
SAVE_FREQ        ?= 5000    # checkpoint saving frequency (steps)
KEEP_CHECKPOINTS ?= 5       # nr of checkpoints to keep
REPORT_FREQ      ?= 500     # progress reporting frequency (steps)

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
TRAINING_STEPS   ?= 250000


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
inference-config:
	${MAKE} ${INFERENCE_CONFIGFILE}

${INFERENCE_CONFIGFILE}: ${MODEL_META}
	@mkdir -p $(dir $@)
	echo 'task_id: ${TASK_ID}'                                     > $@
	@echo ''                                                      >> $@
	echo "tasks:"                                                 >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-task
	@echo ''                                                      >> $@
	echo "src_vocab:"                                             >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${SRCLANG} config-add-vocab
	echo "tgt_vocab:"                                             >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${TRGLANG} config-add-vocab
	${MAKE} -s CONFIGFILE=$@ config-add-model-architecture
	${MAKE} -s CONFIGFILE=$@ config-add-transformer-params
	@echo ''                                                      >> $@
	@echo '# Decoding parameters'                                 >> $@
	@echo 'beam_size: ${DECODING_BEAM_SIZE}'                      >> $@
	@echo 'batch_size: ${DECODING_BATCH_SIZE}'                    >> $@
	@echo 'batch_type: ${DECODING_BATCH_TYPE}'                    >> $@
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


${TRAIN_CONFIGFILE}:
	@mkdir -p $(dir $@)
	echo "tasks:"                                                 > $@
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} -s CONFIGFILE=$@ TASK_NR=$$t config-add-task; \
	done
	@echo ''                                                     >> $@
	@echo "add vocabularies"
	echo "src_vocab:"                                            >> $@
	@for l in $(VOCAB_SRCLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	echo "tgt_vocab:"                                            >> $@
	@for l in $(VOCAB_TRGLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	@echo ''                                                     >> $@
	@echo "add model/training parameters"
ifeq ($(findstring denoising,$(TASK_TRANSFORMS)),denoising)
	${MAKE} -s CONFIGFILE=$@ config-add-denoising
endif
	${MAKE} -s CONFIGFILE=$@ config-add-model-architecture
	${MAKE} -s CONFIGFILE=$@ config-add-transformer-params
	${MAKE} -s CONFIGFILE=$@ config-add-training-params
	${MAKE} -s CONFIGFILE=$@ config-add-checkpoint-params
	@echo ''                                                     >> $@
	@echo '# Model saving'                                       >> $@
	@echo 'save_model: ${MODEL_PATH}'                            >> $@
	@echo 'save_strategy: best_and_last'                         >> $@


## add a task section

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



config-add-vocab:
	echo '   ${LANGID}: ${VOCAB_FILE}'                        >> ${CONFIGFILE}

config-add-denoising:
	echo '# Denoising transform parameters'                   >> ${CONFIGFILE}
	echo 'denoising_objective: bart'                          >> ${CONFIGFILE}
	echo 'mask_ratio: 0.2              # Fraction of tokens to mask' >> ${CONFIGFILE}
	echo 'mask_length: span-poisson    # Options: "subword", "word", "span-poisson"' >> ${CONFIGFILE}
	echo 'poisson_lambda: 3.0          # Lambda for span length distribution' >> ${CONFIGFILE}
	echo 'replace_length: 1            # -1: keep N tokens, 0: remove all, 1: single mask per span' >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}


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
	@echo '# Decoding parameters during validation'            >> ${CONFIGFILE}
	@echo 'valid_batch_size: ${VALID_BATCH}'                   >> ${CONFIGFILE}
	@echo 'beam_size: 1'                                       >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Optimizer settings (from create_opts)'            >> ${CONFIGFILE}
	@echo 'optim: ${OPTIMIZER}'                                >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'learning_rate: ${LEARNING_RATE}'                    >> ${CONFIGFILE}
	@echo 'adam_beta1: ${ADAM_BETA1}'                          >> ${CONFIGFILE}
	@echo 'adam_beta2: ${ADAM_BETA1}'                          >> ${CONFIGFILE}
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


config-add-checkpoint-params:
	@echo 'valid_steps: ${VALID_FREQ}'                         >> ${CONFIGFILE}
	@echo 'valid_metrics: [$(strip ${VALID_METRICS})]'         >> ${CONFIGFILE}
	@echo 'save_checkpoint_steps: ${SAVE_FREQ}'                >> ${CONFIGFILE}
	@echo 'keep_checkpoint: ${KEEP_CHECKPOINTS}'               >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo '# Logging and Monitoring'                           >> ${CONFIGFILE}
	@echo ''                                                   >> ${CONFIGFILE}
	@echo 'log_model_structure: false'                         >> ${CONFIGFILE}
	@echo '# tensorboard: true               # enable tensorboard logging' >> ${CONFIGFILE}
	@echo '# tensorboard_log_dir: ./logs     # tensorboard log directory'  >> ${CONFIGFILE}
	@echo 'report_every: ${REPORT_FREQ}'                       >> ${CONFIGFILE}
	@echo 'report_training_accuracy: false'                    >> ${CONFIGFILE}



