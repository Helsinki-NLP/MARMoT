

WORK_DIR   := /scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/tatoeba
MODEL_DIR  := ${WORK_DIR}/model
MODEL_NAME := deu+eng+fin+swe
MODEL_PATH := ${MODEL_DIR}/${MODEL_NAME}


TASKS           := eng-eng fin-fin fin-eng swe-eng deu-eng eng-fin eng-swe eng-deu fin-swe swe-fin
TASK_GPUS       := 0:7     0:7     0:0     0:1     0:2     0:3     0:4     0:5     0:6     0:7
TASK_WEIGHTS    := 0.1     0.1
TASK_TRANSFORMS := denoising,filtertoolong denoising,filtertoolong
TEST_TASK_NR    := 3

ENCODER_LAYERS = 9
DECODER_LAYERS = 3



TASK_NR  ?= 1
TASK     := $(word ${TASK_NR},$(TASKS))
SRCLANG  ?= $(firstword $(subst -, ,${TASK}))
TRGLANG  ?= $(lastword  $(subst -, ,${TASK}))
LANGPAIR ?= ${SRCLANG}-${TRGLANG}


DEFAULT_GPU        := 0:0
DEFAULT_WEIGHT     := 1:0
DEFAULT_TRANSFORM  := filtertoolong
DEFAULT_TRAINSTEP  := 0
DEFAULT_ENCODER    := "shared"
DEFAULT_DECODER    := "${TRGLANG}"


TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPUS))       $(DEFAULT_GPU))
TASK_WEIGHT    := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS))    $(DEFAULT_WEIGHT))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS)) $(DEFAULT_TRANSFORM))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS)) $(DEFAULT_TRAINSTEP))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))   $(DEFAULT_ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))   $(DEFAULT_DECODER))



TRAIN_CONFIGFILE     ?= train.yaml
TRAIN_SLURMSCRIPT    ?= train.sh

INFERENCE_CONFIGFILE ?= inference.yaml
CONFIGFILE           ?= ${TRAIN_CONFIGFILE}




GPU_RANKS        := $(sort $(notdir $(subst :,/,${TASK_GPUS})))
NR_OF_GPUS       := $(words ${GPU_RANKS})
TOTAL_NR_OF_GPUS := $(words $(sort ${TASK_GPUS}))
NODE_RANK        ?= 0


RANDOM_SEED := 42


MAX_SRCSEQ_LENGTH := 256
MAX_TRGSEQ_LENGTH := 256


BATCH_TYPE       := tokens  # type of unit for batch size
BATCH_SIZE       := 8196    # per-GPU batch size
VALID_BATCH      := 1024
LOOK_AHEAD       := 16      # batch look-ahead to sort training examples by length
GRADIENT_ACCUM   := 4       # gradient accumulation
QUEUE_SIZE       := 100


VALID_FREQ       := 5000    # validation frequency (steps)
VALID_METRICS    := bleu    # validation metrics
SAVE_FREQ        := 5000    # checkpoint saving frequency (steps)
KEEP_CHECKPOINTS := 5       # nr of checkpoints to keep
REPORT_FREQ      := 100     # progress reporting frequency (steps)


OPTIMIZER        := adamw
LEARNING_RATE    := 0.0005
ADAM_BETA1       := 0.9
ADAM_BETA2       := 0.999
WEIGHT_DECAY     := 0.01
MAX_GRAD_NORM    := 1.0
LABEL_SMOOTHING  := 0.1
LR_DECAY         := 0       # learning rate decay
DECAY_START      := 0       # steps when to start lr-decay

WARMUP_STEPS     := 5000
DECAY_METHOD     := linear_warmup


#--------------------------------------------------------------
# data sets
#--------------------------------------------------------------

## data directories

PROJECT_DIR   := /scratch/project_462000964/MARMoT
DATA_DIR      := ${PROJECT_DIR}/data
TRAINDATA_DIR := ${DATA_DIR}/tatoeba/train
DEVDATA_DIR   := ${DATA_DIR}/tatoeba/dev5K
# TESTDATA_DIR  := ${DATA_DIR}/tatoeba/test
TESTDATA_DIR  := ${DATA_DIR}/flores200/devtest


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

TRAINDATA_SRC := ${TRAINDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz
TRAINDATA_TRG := ${TRAINDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz


## validation data

ifneq (${SRCLANG},${TRGLANG})
  DEVDATA_SRC := ${DEVDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz
  DEVDATA_TRG := ${DEVDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz
endif


## testdata

ifneq (${SRCLANG},${TRGLANG})
  TESTDATA_SRC := $(wildcard ${TESTDATA_DIR}/${SORTED_LANGPAIR}.${SRCLANG}.gz) \
			$(wildcard ${TESTDATA_DIR}/${SRCLANG}_*)
  TESTDATA_TRG := $(wildcard ${TESTDATA_DIR}/${SORTED_LANGPAIR}.${TRGLANG}.gz) \
			$(wildcard ${TESTDATA_DIR}/${TRGLANG}_*)
endif


TESTDATA_OUTPUT := ${MODEL_PATH}_translate_$(basename $(notdir $(TESTDATA_SRC))).${TRGLANG}


#--------------------------------------------------------------
# vocab files
#--------------------------------------------------------------

## really ugly way of getting from tasks to a unique set
## of source and target languages for the vocabs

VOCAB_SRCLANGS := $(sort $(patsubst %/,%,$(dir $(subst -,/,${TASKS}))))
VOCAB_TRGLANGS := $(sort $(notdir $(subst -,/,${TASKS})))

VOCAB_DIR      := ${PROJECT_DIR}/tokenizer/tatoeba
VOCAB_SIZE     := 32000
VOCAB_FILE     := ${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json




#--------------------------------------------------------------
# generate SLURM scripts
#--------------------------------------------------------------



train.sh: train-template.sh
	sed -e 's+WORKSPACE+${WORK_DIR}+'  \
	    -e 's+NR_OF_GPUS+${NR_OF_GPUS}+' \
	    -e 's+CONFIGFILE+${TRAIN_CONFIGFILE}+' \
	    -e 's/MODELNAME/${MODEL_NAME}/' \
	< $< > $@

inference.sh: inference-template.sh
	sed -e 's+WORKSPACE+${WORK_DIR}+'  \
	    -e 's+CONFIGFILE+${INFERENCE_CONFIGFILE}+' \
	    -e 's/MODELNAME/${MODEL_NAME}/' \
	< $< > $@


#--------------------------------------------------------------
# generate config files
#--------------------------------------------------------------

train-config: ${TRAIN_CONFIGFILE}

inference-config:
	${MAKE} TASK_NR=${TEST_TASK_NR} ${INFERENCE_CONFIGFILE}

${INFERENCE_CONFIGFILE}:
	echo 'task_id: task_${TASK}' >> $@
	@echo '' >> $@
	echo "tasks:" >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-task
	@echo '' >> $@
	echo "src_vocab:" >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${SRCLANG} config-add-vocab
	echo "tgt_vocab:" >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${TRGLANG} config-add-vocab
	${MAKE} -s config-add-model-architecture
	${MAKE} -s config-add-transformer-params
	@echo '' >> $@
	echo 'seed: ${RANDOM_SEED}' >> $@
	echo 'src: ${TESTDATA_SRC}' >> $@
	echo 'output: ${TESTDATA_OUTPUT}' >> $@
	echo 'model: ${MODEL_PATH}' >> $@


${TRAIN_CONFIGFILE}:
	echo "tasks:" >> $@
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} -s CONFIGFILE=$@ TASK_NR=$$t config-add-task; \
	done
	@echo '' >> $@
	echo "src_vocab:" >> $@
	@for l in $(VOCAB_SRCLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	echo "tgt_vocab:" >> $@
	@for l in $(VOCAB_TRGLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	@echo '' >> $@
	${MAKE} -s config-add-denoising
	${MAKE} -s config-add-model-architecture
	${MAKE} -s config-add-transformer-params
	${MAKE} -s config-add-training-params
	${MAKE} -s config-add-checkpoint-params
	@echo '' >> $@
	echo '# Model saving' >> ${CONFIGFILE}
	echo 'save_model: ${MODEL_PATH}' >> ${CONFIGFILE}


## add a task section

config-add-task:
	@echo "add task ${TASK}"
	@echo '  task_${TASK}:' >> ${CONFIGFILE}
	@echo '    src_tgt: "${TASK}"  # Source-target language pair' >> ${CONFIGFILE}
	@echo '    weight: ${TASK_WEIGHT}       # Task weight for sampling' >> ${CONFIGFILE}
	@echo '    introduce_at_training_step: ${TASK_TRAINSTEP}' >> ${CONFIGFILE}
	@echo '    node_gpu: ${TASK_GPU}   # Single GPU configuration' >> ${CONFIGFILE}
	@echo '    enc_sharing_group: [${TASK_ENCODER}]' >> ${CONFIGFILE}
	@echo '    dec_sharing_group: [${TASK_DECODER}]' >> ${CONFIGFILE}
	@echo '    transforms: [${TASK_TRANSFORM}]' >> ${CONFIGFILE}
ifneq (${TRAINDATA_SRC},)
ifneq (${TRAINDATA_TRG},)
	@echo '    path_src: ${TRAINDATA_SRC}' >> ${CONFIGFILE}
	@echo '    path_tgt: ${TRAINDATA_TRG}' >> ${CONFIGFILE}
endif
endif
ifneq (${DEVDATA_SRC},)
ifneq (${DEVDATA_TRG},)
	@echo '    path_valid_src: ${DEVDATA_SRC}' >> ${CONFIGFILE}
	@echo '    path_valid_tgt: ${DEVDATA_TRG}' >> ${CONFIGFILE}
endif
endif
	@echo '' >> ${CONFIGFILE}



config-add-vocab:
	echo '   ${LANGID}: ${VOCAB_FILE}' >> ${CONFIGFILE}

config-add-denoising:
	echo '# Denoising transform parameters' >> ${CONFIGFILE}
	echo 'denoising_objective: bart' >> ${CONFIGFILE}
	echo 'mask_ratio: 0.2              # Fraction of tokens to mask' >> ${CONFIGFILE}
	echo 'mask_length: span-poisson    # Options: "subword", "word", "span-poisson"' >> ${CONFIGFILE}
	echo 'poisson_lambda: 3.0          # Lambda for span length distribution' >> ${CONFIGFILE}
	echo 'replace_length: 1            # -1: keep N tokens, 0: remove all, 1: single mask per span' >> ${CONFIGFILE}
	echo '' >> ${CONFIGFILE}


config-add-model-architecture:
	echo '# Model Architecture Options' >> ${CONFIGFILE}
	echo 'enc_layers: [${ENCODER_LAYERS}]                   # Encoder layers' >> ${CONFIGFILE}
	echo 'dec_layers: [${DECODER_LAYERS}]                   # Decoder layers' >> ${CONFIGFILE}
	echo '' >> ${CONFIGFILE}
	echo 'model_dim: 768                    # Transformer model dimension' >> ${CONFIGFILE}
	echo 'dropout: 0.1                      # Dropout rate' >> ${CONFIGFILE}
	echo 'model_dtype: bf16' >> ${CONFIGFILE}
	echo '' >> ${CONFIGFILE}

config-add-transformer-params:
	echo '# x-transformers specific options' >> ${CONFIGFILE}
	echo 'x_transformers_opts:' >> ${CONFIGFILE}
	echo '  attn_flash: true          # Flash attention (not supported on V100)' >> ${CONFIGFILE}
	echo '  rotary_pos_emb: true      # Use rotary positional embeddings' >> ${CONFIGFILE}
	echo '  tie_embedding: false      # Tie input/output embeddings' >> ${CONFIGFILE}
	echo '  heads: 12'                >> ${CONFIGFILE}
	echo '  pre_norm: false'          >> ${CONFIGFILE}
	echo '  post_emb_norm: true'      >> ${CONFIGFILE}
	echo '  post_emb_norm_bias: true' >> ${CONFIGFILE}
	echo '  attn_dropout: 0.1'        >> ${CONFIGFILE}
	echo '  ff_dropout: 0.1'          >> ${CONFIGFILE}
	echo '  layernorm_bias: true'     >> ${CONFIGFILE}
	echo '  use_abs_pos_emb: true'    >> ${CONFIGFILE}
	echo ''                           >> ${CONFIGFILE}


COMMA            := ,
GPU_RANKS_STRING  := $(subst $(eval ) ,${COMMA},$(GPU_RANKS))

config-add-training-params:
	echo 'src_seq_length_max: ${MAX_SRCSEQ_LENGTH}' >> ${CONFIGFILE}
	echo 'tgt_seq_length_max: ${MAX_TRGSEQ_LENGTH}' >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
	echo '# Training Configuration'                >> ${CONFIGFILE}
	echo 'train_steps: 500000'                     >> ${CONFIGFILE}
	echo 'accum_count: [${GRADIENT_ACCUM}]'        >> ${CONFIGFILE}
	echo 'lookahead_minibatches: ${LOOK_AHEAD}'    >> ${CONFIGFILE}
	echo 'batch_size: ${BATCH_SIZE}'               >> ${CONFIGFILE}
	echo 'batch_type: ${BATCH_TYPE}'               >> ${CONFIGFILE}
	echo 'valid_batch_size: ${VALID_BATCH}'        >> ${CONFIGFILE}
	echo 'normalization: ${BATCH_TYPE}'            >> ${CONFIGFILE}
	echo 'queue_size: ${QUEUE_SIZE}'               >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
	echo '# Optimizer settings (from create_opts)' >> ${CONFIGFILE}
	echo 'optim: ${OPTIMIZER}'                     >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
	echo 'learning_rate: ${LEARNING_RATE}'         >> ${CONFIGFILE}
	echo 'adam_beta1: ${ADAM_BETA1}'               >> ${CONFIGFILE}
	echo 'adam_beta2: ${ADAM_BETA1}'               >> ${CONFIGFILE}
	echo 'weight_decay: ${WEIGHT_DECAY}'           >> ${CONFIGFILE}
	echo 'max_grad_norm: ${MAX_GRAD_NORM}'         >> ${CONFIGFILE}
	echo 'label_smoothing: ${LABEL_SMOOTHING}'     >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
	echo '# Learning rate scheduling'              >> ${CONFIGFILE}
	echo 'warmup_steps: ${WARMUP_STEPS}'           >> ${CONFIGFILE}
	echo 'decay_method: ${DECAY_METHOD}'           >> ${CONFIGFILE}
	echo 'learning_rate_decay: ${LR_DECAY}'        >> ${CONFIGFILE}
	echo 'start_decay_steps: ${DECAY_START}'       >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
	echo 'world_size: ${TOTAL_NR_OF_GPUS}'         >> ${CONFIGFILE}
	echo 'gpu_ranks: [${GPU_RANKS_STRING}]'        >> ${CONFIGFILE}
	echo 'task_distribution_strategy: weighted_sampling' >> ${CONFIGFILE}
	echo 'node_rank: ${NODE_RANK}'                 >> ${CONFIGFILE}
	echo ''                                        >> ${CONFIGFILE}
ifdef RANDOM_SEED
	echo 'seed: ${RANDOM_SEED}'                    >> ${CONFIGFILE}
endif


config-add-checkpoint-params:
	echo 'valid_steps: ${VALID_FREQ}'           >> ${CONFIGFILE}
	echo 'valid_metrics: [${VALID_METRICS}]'    >> ${CONFIGFILE}
	echo 'save_checkpoint_steps: ${SAVE_FREQ}'  >> ${CONFIGFILE}
	echo 'keep_checkpoint: ${KEEP_CHECKPOINTS}' >> ${CONFIGFILE}
	echo ''                                     >> ${CONFIGFILE}
	echo '# Logging and Monitoring'             >> ${CONFIGFILE}
	echo ''                                     >> ${CONFIGFILE}
	echo 'log_model_structure: false        # log model structure' >> ${CONFIGFILE}
	echo '# tensorboard: true               # enable tensorboard logging' >> ${CONFIGFILE}
	echo '# tensorboard_log_dir: ./logs     # tensorboard log directory' >> ${CONFIGFILE}
	echo 'report_every: ${REPORT_FREQ}'         >> ${CONFIGFILE}
	echo 'report_training_accuracy: true'       >> ${CONFIGFILE}



