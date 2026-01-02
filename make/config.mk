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
#--------------------------------------------------------------------------

# TASKS           ?= eng-eng fin-fin fin-eng eng-fin 
# TASK_GPUS       ?= 0:0     0:1     0:2     0:3
# TASK_WEIGHTS    ?= 0.1     0.1
# TASK_TRANSFORMS ?= denoising,filtertoolong denoising,filtertoolong

TASKS           ?= fin-eng
TASK_GPUS       ?= 0:0
TASK_WEIGHTS    ?= 1.0
TASK_TRANSFORMS ?= filtertoolong



TASK_NR  ?= $(words $(TASKS))
TASK     := $(word ${TASK_NR},$(TASKS))
SRCLANG  ?= $(firstword $(subst -, ,${TASK}))
TRGLANG  ?= $(lastword  $(subst -, ,${TASK}))
LANGPAIR ?= ${SRCLANG}-${TRGLANG}


TRAIN_CONFIGFILE      ?= ${MODEL_DIR}/train.yaml
INFERENCE_CONFIGFILE  ?= ${EVAL_DIR}/inference_${TASK}.yaml
CONFIGFILE            ?= ${TRAIN_CONFIGFILE}


# current task specifications (defaults and parameters selected with TASK_NR)

DEFAULT_GPU        ?= 0:0
DEFAULT_WEIGHT     ?= 1.0
DEFAULT_TRANSFORM  ?= filtertoolong
DEFAULT_TRAINSTEP  ?= 0
DEFAULT_ENCODER    ?= "${SRCLANG}"
DEFAULT_DECODER    ?= "${TRGLANG}"

ifeq (${ADD_LANGUAGE_TOKEN},true)
  DEFAULT_TRANSFORM  ?= filtertoolong,prefix
endif


TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPUS))       $(DEFAULT_GPU))
TASK_WEIGHT    := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS))    $(DEFAULT_WEIGHT))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS)) $(DEFAULT_TRANSFORM))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS)) $(DEFAULT_TRAINSTEP))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))   $(DEFAULT_ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))   $(DEFAULT_DECODER))


#--------------------------------------------------------------
# data sets
#--------------------------------------------------------------

## in OPUS data we have sorted language IDs for language pairs

SORTED_SRCLANG  := $(firstword $(sort ${SRCLANG} ${TRGLANG}))
SORTED_TRGLANG  := $(lastword  $(sort ${SRCLANG} ${TRGLANG}))

## monolingual data: take bilingual data with English or French
## TODO: what do we do if those alignments do not exist?
## TODO: use actual monolingual data sets

ifeq (${SRCLANG},${TRGLANG})
ifeq (${SRCLANG},eng)
  SORTED_SRCLANG := eng
  SORTED_TRGLANG := fra
else
  SORTED_SRCLANG  := $(firstword $(sort eng ${TRGLANG}))
  SORTED_TRGLANG  := $(lastword  $(sort eng ${TRGLANG}))
endif
endif

SORTED_LANGPAIR := ${SORTED_SRCLANG}-${SORTED_TRGLANG}


## training data and validation data
## skip monolingual validation data (should we?)

TRAINDATA_SRC ?= ${TRAINDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz
TRAINDATA_TRG ?= ${TRAINDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz


## validation data

ifneq (${SRCLANG},${TRGLANG})
  DEVDATA_SRC ?= ${DEVDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz
  DEVDATA_TRG ?= ${DEVDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz
endif


## testdata

ifneq (${SRCLANG},${TRGLANG})
  TESTDATA_SRC ?= $(wildcard ${TESTDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz) \
			$(wildcard ${TESTDATA_DIR}/${SRCLANG}_*)
  TESTDATA_TRG ?= $(wildcard ${TESTDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz) \
			$(wildcard ${TESTDATA_DIR}/${TRGLANG}_*)
endif


# TESTDATA_OUTPUT ?= ${MODEL_PATH}_translate_$(basename $(notdir $(TESTDATA_SRC))).${TRGLANG}
TESTDATA_OUTPUT ?= ${EVAL_DIR}/$(basename $(notdir $(TESTDATA_SRC))).${TRGLANG}


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

GPU_RANKS        := $(sort $(notdir $(subst :,/,${TASK_GPUS})))
NR_OF_GPUS       := $(words ${GPU_RANKS})
TOTAL_NR_OF_GPUS := $(words $(sort ${TASK_GPUS}))
NR_OF_NODES      := $(words $(sort $(dir $(subst :,/,${TASK_GPUS}))))
NODE_RANK        ?= 0


#--------------------------------------------------------------
# training parameters
#--------------------------------------------------------------

RANDOM_SEED      ?= 42
BATCH_TYPE       ?= tokens  # type of unit for batch size
BATCH_SIZE       ?= 8196    # per-GPU batch size
VALID_BATCH      ?= 1024
LOOK_AHEAD       ?= 16      # batch look-ahead to sort training examples by length
GRADIENT_ACCUM   ?= 20      # gradient accumulation
QUEUE_SIZE       ?= 40

TASK_DISTRIBUTION ?= weighted_sampling
MIN_SRCSEQ_LENGTH ?= 1
MIN_TRGSEQ_LENGTH ?= 1
MAX_SRCSEQ_LENGTH ?= 512
MAX_TRGSEQ_LENGTH ?= 512
# MAX_SRCSEQ_LENGTH ?= 256
# MAX_TRGSEQ_LENGTH ?= 256

## for validation during training
MAX_SEQ_LENGTH ?= 512

VALID_FREQ       ?= 5000    # validation frequency (steps)
VALID_METRICS    ?= bleu    # validation metrics
SAVE_FREQ        ?= 5000    # checkpoint saving frequency (steps)
KEEP_CHECKPOINTS ?= 5       # nr of checkpoints to keep
REPORT_FREQ      ?= 500     # progress reporting frequency (steps)

OPTIMIZER        ?= adamw
LEARNING_RATE    ?= 0.0008
# LEARNING_RATE    ?= 0.00001
ADAM_BETA1       ?= 0.9
ADAM_BETA2       ?= 0.999
WEIGHT_DECAY     ?= 0.01
MAX_GRAD_NORM    ?= 1.0
LABEL_SMOOTHING  ?= 0.1
LR_DECAY         ?= 0.5     # learning rate decay
DECAY_START      ?= 50000   # steps when to start lr-decay
AVERAGE_DECAY    ?= 0.0005
WARMUP_STEPS     ?= 5000
DECAY_METHOD     ?= linear_warmup
# TRAINING_STEPS   ?= 500000
TRAINING_STEPS   ?= 250000




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
	echo 'task_id: task_${TASK}'                                  > $@
	@echo ''                                                     >> $@
	echo "tasks:"                                                >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-task
	@echo ''                                                     >> $@
	echo "src_vocab:"                                            >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${SRCLANG} config-add-vocab
	echo "tgt_vocab:"                                            >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${TRGLANG} config-add-vocab
	${MAKE} -s CONFIGFILE=$@ config-add-model-architecture
	${MAKE} -s CONFIGFILE=$@ config-add-transformer-params
	@echo ''                                                     >> $@
	@echo '# Decoding parameters'                                 >> $@
	@echo 'beam_size: 4'                                          >> $@
	@echo 'batch_size: 32'                                        >> $@
	@echo 'batch_type: sents'                                     >> $@
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
	echo "src_vocab:"                                            >> $@
	@for l in $(VOCAB_SRCLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	echo "tgt_vocab:"                                            >> $@
	@for l in $(VOCAB_TRGLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	@echo ''                                                     >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-denoising
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
	@echo "add task ${TASK}"
	@echo '  task_${TASK}:'                                   >> ${CONFIGFILE}
	@echo '    src_tgt: "${TASK}"'                            >> ${CONFIGFILE}
	@echo '    weight: ${TASK_WEIGHT}'                        >> ${CONFIGFILE}
	@echo '    introduce_at_training_step: ${TASK_TRAINSTEP}' >> ${CONFIGFILE}
	@echo '    node_gpu: "${TASK_GPU}"'                       >> ${CONFIGFILE}
	@echo '    enc_sharing_group: [${TASK_ENCODER}]'          >> ${CONFIGFILE}
	@echo '    dec_sharing_group: [${TASK_DECODER}]'          >> ${CONFIGFILE}
	@echo '    transforms: [${TASK_TRANSFORM}]'               >> ${CONFIGFILE}
ifeq (${ADD_LANGUAGE_TOKEN},true)
	@echo '    src_prefix: ">>${TRGLANG}<<"'  >> ${CONFIGFILE}
	@echo '    tgt_prefix: "<<${SRCLANG}>>"'  >> ${CONFIGFILE}
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
	echo 'src_seq_length_min: ${MIN_SRCSEQ_LENGTH}'           >> ${CONFIGFILE}
	echo 'tgt_seq_length_min: ${MIN_TRGSEQ_LENGTH}'           >> ${CONFIGFILE}
	echo 'src_seq_length_max: ${MAX_SRCSEQ_LENGTH}'           >> ${CONFIGFILE}
	echo 'tgt_seq_length_max: ${MAX_TRGSEQ_LENGTH}'           >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	echo '# Training Configuration'                           >> ${CONFIGFILE}
	echo 'train_steps: ${TRAINING_STEPS}'                     >> ${CONFIGFILE}
	echo 'accum_count: [$(strip ${GRADIENT_ACCUM})]'          >> ${CONFIGFILE}
	echo 'lookahead_minibatches: ${LOOK_AHEAD}'               >> ${CONFIGFILE}
	echo 'batch_size: ${BATCH_SIZE}'                          >> ${CONFIGFILE}
	echo 'batch_type: ${BATCH_TYPE}'                          >> ${CONFIGFILE}
	echo 'normalization: ${BATCH_TYPE}'                       >> ${CONFIGFILE}
	echo 'queue_size: ${QUEUE_SIZE}'                          >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	@echo '# Decoding parameters during validation'           >> ${CONFIGFILE}
	@echo 'valid_batch_size: ${VALID_BATCH}'                  >> ${CONFIGFILE}
	@echo 'beam_size: 1'                                      >> ${CONFIGFILE}
	@echo 'max_length: ${MAX_SEQ_LENGTH}'                     >> ${CONFIGFILE}
	@echo ''                                                  >> ${CONFIGFILE}
	echo '# Optimizer settings (from create_opts)'            >> ${CONFIGFILE}
	echo 'optim: ${OPTIMIZER}'                                >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	echo 'learning_rate: ${LEARNING_RATE}'                    >> ${CONFIGFILE}
	echo 'adam_beta1: ${ADAM_BETA1}'                          >> ${CONFIGFILE}
	echo 'adam_beta2: ${ADAM_BETA1}'                          >> ${CONFIGFILE}
	echo 'weight_decay: ${WEIGHT_DECAY}'                      >> ${CONFIGFILE}
	echo 'max_grad_norm: ${MAX_GRAD_NORM}'                    >> ${CONFIGFILE}
	echo 'label_smoothing: ${LABEL_SMOOTHING}'                >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	echo '# Learning rate scheduling'                         >> ${CONFIGFILE}
	echo 'warmup_steps: ${WARMUP_STEPS}'                      >> ${CONFIGFILE}
	echo 'decay_method: ${DECAY_METHOD}'                      >> ${CONFIGFILE}
	echo 'learning_rate_decay: ${LR_DECAY}'                   >> ${CONFIGFILE}
	echo 'start_decay_steps: ${DECAY_START}'                  >> ${CONFIGFILE}
	echo 'average_decay: ${AVERAGE_DECAY}'                    >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
	echo 'world_size: ${TOTAL_NR_OF_GPUS}'                    >> ${CONFIGFILE}
	echo 'gpu_ranks: [${GPU_RANKS_STRING}]'                   >> ${CONFIGFILE}
	echo 'n_nodes: ${NR_OF_NODES}'                            >> ${CONFIGFILE}
	echo 'task_distribution_strategy: ${TASK_DISTRIBUTION}'   >> ${CONFIGFILE}
	echo 'node_rank: ${NODE_RANK}'                            >> ${CONFIGFILE}
	echo ''                                                   >> ${CONFIGFILE}
ifdef RANDOM_SEED
	echo 'seed: ${RANDOM_SEED}'                               >> ${CONFIGFILE}
endif


config-add-checkpoint-params:
	echo 'valid_steps: ${VALID_FREQ}'                         >> ${CONFIGFILE}
	echo 'valid_metrics: [$(strip ${VALID_METRICS})]' >> ${CONFIGFILE}
	echo 'save_checkpoint_steps: ${SAVE_FREQ}'        >> ${CONFIGFILE}
	echo 'keep_checkpoint: ${KEEP_CHECKPOINTS}'       >> ${CONFIGFILE}
	echo ''                                           >> ${CONFIGFILE}
	echo '# Logging and Monitoring'                   >> ${CONFIGFILE}
	echo ''                                           >> ${CONFIGFILE}
	echo 'log_model_structure: false'                 >> ${CONFIGFILE}
	echo '# tensorboard: true               # enable tensorboard logging' >> ${CONFIGFILE}
	echo '# tensorboard_log_dir: ./logs     # tensorboard log directory' >> ${CONFIGFILE}
	echo 'report_every: ${REPORT_FREQ}'               >> ${CONFIGFILE}
	echo 'report_training_accuracy: true'             >> ${CONFIGFILE}



