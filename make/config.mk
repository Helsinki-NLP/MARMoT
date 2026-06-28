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


EXPERIMENT_DIR ?= ${PWD}
MODEL_NAME     ?= mammoth
MODEL_DIR      ?= ${EXPERIMENT_DIR}/${MODEL_NAME}
MODEL_PATH     ?= ${MODEL_DIR}/model
MODEL_META     ?= ${MODEL_PATH}_checkpoint_metadata.json
EVAL_DIR       ?= ${MODEL_DIR}/eval


## transformer backend (x-transformers or pytorch)
TRANSFORMER_BACKEND ?= x-transformers


MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

include ${MAKEFILE_DIR}config/tasks.mk
include ${MAKEFILE_DIR}config/data.mk
include ${MAKEFILE_DIR}config/vocab.mk
include ${MAKEFILE_DIR}config/model.mk
include ${MAKEFILE_DIR}config/training.mk
include ${MAKEFILE_DIR}config/inference.mk



#--------------------------------------------------------------
# required resources (compute nodes and GPUs)
#--------------------------------------------------------------

GPU_RANKS      := $(sort $(notdir $(subst :,/,${TASK_GPU_ASSIGNMENTS})))
GPUS_PER_NODE  := $(words ${GPU_RANKS})
NR_OF_GPUS     := $(words $(sort ${TASK_GPU_ASSIGNMENTS}))
NR_OF_NODES    := $(words $(sort $(dir $(subst :,/,${TASK_GPU_ASSIGNMENTS}))))


#--------------------------------------------------------------
# generate config files
#--------------------------------------------------------------

## path to config files

TRAIN_STAGE           ?= train
TRAIN_CONFIGFILE      ?= ${MODEL_DIR}/${TRAIN_STAGE}.yaml
INFERENCE_CONFIGFILE  ?= ${EVAL_DIR}/inference_${TASK_ID}.yaml
CONFIGFILE            ?= ${TRAIN_CONFIGFILE}


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


TASK_CONFIGFILES := $(patsubst %,${TRAIN_CONFIGFILE}.d/%,${TASK_NRS})

.INTERMEDIATE: ${TASK_CONFIGFILES}

${TASK_CONFIGFILES}:
	@mkdir -p $(dir $@)
	@${MAKE} -s CONFIGFILE=$@ TASK_NR=$(notdir $@) FIND_DATA=1 config-add-traintask

${TRAIN_CONFIGFILE}: ${TASK_CONFIGFILES}
	@mkdir -p $(dir $@)
	echo "tasks:"                                                 > $@
	@find $(dir $<) -name '[0-9]*' \
	| awk -F/  '{print $$NF "/" $$0}' \
	| sort -n | cut -d / -f 2- | xargs cat                       >> $@
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
	@echo 'reset_optim: ${RESET_OPTIMIZER}'                      >> $@
ifdef PRETRAINED_MODEL
	@echo 'train_from: $(shell realpath ${PRETRAINED_MODEL})/'   >> $@
endif




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
	@echo '    src_tgt: "${TASK_LANGPAIR}"'                   >> ${CONFIGFILE}
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



ifeq (${TRANSFORMER_BACKEND},x-transformers)

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

else

TRF_FF_ACTIVATION ?= swiglu

# # Native pytorch transformer options
# heads: 16              # attention heads (model_dim must be divisible by heads)
# rotary_pos_emb: true   # rotary positional embeddings (RoPE, currently the only option)
# post_emb_norm: true    # RMSNorm applied after token embedding (RMSNorm, the only option)
# attn_dropout: 0.1
# ff_dropout: 0.1
# ff_activation: swiglu  # choose between "swiglu" and "gelu", "swiglu" by default

.PHONY: config-add-transformer-params
config-add-transformer-params:
	echo 'heads: ${XTRF_HEADS}'                             >> ${CONFIGFILE}
	echo 'rotary_pos_emb: ${XTRF_ROTARY_POS_EMBEDDINGS}'    >> ${CONFIGFILE}
	echo 'post_emb_norm: ${XTRF_POST_EMB_NORM}'             >> ${CONFIGFILE}
	echo 'attn_dropout: ${XTRF_ATTN_DROPOUT}'               >> ${CONFIGFILE}
	echo 'ff_dropout: ${XTRF_FF_DROPOUT}'                   >> ${CONFIGFILE}
	echo 'ff_activation: ${TRF_FF_ACTIVATION}'              >> ${CONFIGFILE}
	echo ''                                                 >> ${CONFIGFILE}

endif




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
	@echo 'early_stopping: ${EARLY_STOPPING}'                  >> ${CONFIGFILE}
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
# 	@echo 'adamw_fused: ${ADAMW_FUSED}'                        >> ${CONFIGFILE}
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
ifdef RANDOM_SEED
	@echo 'seed: ${RANDOM_SEED}'                               >> ${CONFIGFILE}
endif
	@echo ''                                                   >> ${CONFIGFILE}


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




