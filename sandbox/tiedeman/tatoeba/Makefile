
HPC_PROJECT := project_462000964
SANDBOX_DIR := /scratch/${HPC_PROJECT}/members/tiedeman/MARMoT/sandbox/tiedeman
MODEL_NAME  := deu+eng+fin+swe
WORK_DIR    := ${SANDBOX_DIR}/tatoeba/${MODEL_NAME}
MODEL_DIR   := ${WORK_DIR}
MODEL_PATH  := ${MODEL_DIR}/model
MODEL_META  := ${MODEL_PATH}_checkpoint_metadata.json

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
#    DEFAULT_WEIGHT     := 1:0
#    DEFAULT_TRANSFORM  := filtertoolong
#
# TASK_ENCODERS and TASK_DECODERS will be set to default values (see below)
# if not specified for the corresponding task; default values are:
#
#    DEFAULT_ENCODER    := "${SRCLANG}"
#    DEFAULT_DECODER    := "${TRGLANG}"
#--------------------------------------------------------------------------

TASKS           := eng-eng fin-fin fin-eng swe-eng deu-eng eng-fin eng-swe eng-deu fin-swe swe-fin
TASK_GPUS       := 0:7     0:7     0:0     0:1     0:2     0:3     0:4     0:5     0:6     0:7
TASK_WEIGHTS    := 0.1     0.1
TASK_TRANSFORMS := denoising,filtertoolong denoising,filtertoolong
ZERO_SHOT_TASKS := fin-deu deu-fin deu-swe swe-deu

ENCODER_LAYERS  := 9        # Encoder layers (total size)
DECODER_LAYERS  := 3        # Decoder layers (total size)

MODEL_DIMENSION := 768      # Transformer model dimension
MODEL_DTYPE     := bf16     # parameter precision and type
DROPOUT_RATE    := 0.1      # dropout rate

ADD_LANGUAGE_TOKEN := false
TASK_DISTRIBUTION_STRATEGY := weighted_sampling


# X-Tranformer options

XTRF_FLASH_ATTENTION       := true     # Flash attention (not supported on V100)
XTRF_ROTARY_POS_EMBEDDINGS := true     # Use rotary positional embeddings
XTRF_TIE_EMBEDDINGS        := false    # Tie input/output embeddings
XTRF_HEADS                 := 12
XTRF_PRE_NORM              := false
XTRF_POST_EMB_NORM         := true
XTRF_POST_EMB_NORM_BIAS    := true
XTRF_ATTN_DROPOUT          := 0.1
XTRF_FF_DROPOUT            := 0.1
XTRF_LAYERNORM_BIAS        := true
XTRF_USE_ABS_POS_EMB       := true

##-----------------------------------------------------------
## experiment 1: use different model path
##
## run like 'make train.exp1'
##-----------------------------------------------------------

.PHONY: %.exp1
%.exp1:
	${MAKE} MODEL_NAME=exp1 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		DEFAULT_ENCODER="shared" \
	$(basename $@)

##-----------------------------------------------------------
## experiment 1 old: same as exp1 but with old naming
##-----------------------------------------------------------

.PHONY: %.exp1-old
%.exp1-old:
	${MAKE} WORK_DIR=${SANDBOX_DIR}/tatoeba \
		MODEL_NAME=deu+eng+fin+swe \
		MODEL_DIR=${SANDBOX_DIR}/model \
		MODEL_PATH=${SANDBOX_DIR}/model/${MODEL_NAME} \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		DEFAULT_ENCODER="shared" \
	$(basename $@)

##-----------------------------------------------------------
## experiment 2: 6x6 model
##-----------------------------------------------------------

.PHONY: %.exp2
%.exp2:
	${MAKE} MODEL_NAME=exp2 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		DEFAULT_ENCODER="shared" \
	$(basename $@)

##-----------------------------------------------------------
## experiment 3: 6x6 model, lang-specific encoders and decoders
##-----------------------------------------------------------

.PHONY: %.exp3
%.exp3:
	${MAKE} MODEL_NAME=exp3 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 4: 6x6 model, lang-specific encoders and decoders
##-----------------------------------------------------------

.PHONY: %.exp4
%.exp4:
	${MAKE} MODEL_NAME=exp4 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		DEFAULT_ENCODER="shared_enc" \
		DEFAULT_DECODER="shared_dec" \
		ADD_LANGUAGE_TOKEN=true \
	$(basename $@)

##-----------------------------------------------------------
## experiment 5: 9x3 model, shared encoder + language prefix, lang-specific decoders
##-----------------------------------------------------------

.PHONY: %.exp5
%.exp5:
	${MAKE} MODEL_NAME=exp5 \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		ADD_LANGUAGE_TOKEN=true \
	$(basename $@)

##-----------------------------------------------------------
## experiment 6: 3x9 model, shared encoder, lang-specific decoders
##-----------------------------------------------------------

.PHONY: %.exp6
%.exp6:
	${MAKE} MODEL_NAME=exp6 \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=3 \
		DECODER_LAYERS=9 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 7: standard bilingual base-transformer
##-----------------------------------------------------------

.PHONY: %.exp7
%.exp7:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
	$(basename $@)

##-----------------------------------------------------------
## experiment 8: 12x6 model
##-----------------------------------------------------------

.PHONY: %.exp8
%.exp8:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=12 \
		DECODER_LAYERS=6 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 9: standard bilingual base-transformer with lower learning rate
##-----------------------------------------------------------

.PHONY: %.exp9
%.exp9:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		LEARNING_RATE=0.00001 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 10: standard bilingual base-transformer with lr decay
##-----------------------------------------------------------

.PHONY: %.exp10
%.exp10:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 11: standard bilingual base-transformer with lr decay and average decay
##-----------------------------------------------------------

.PHONY: %.exp11
%.exp11:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 12: standard bilingual base-transformer with average decay
##-----------------------------------------------------------

.PHONY: %.exp12
%.exp12:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		ACERAGE_DECAY=0.00001 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 13: standard bilingual base-transformer with bigger average decay
##-----------------------------------------------------------

.PHONY: %.exp13
%.exp13:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		ACERAGE_DECAY=0.0005 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 14: standard bilingual base-transformer with lr decay and average decay and accum_delay=1
##-----------------------------------------------------------

.PHONY: %.exp14
%.exp14:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=1 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 15: standard bilingual base-transformer with lr decay and average decay and accum_delay=10
##-----------------------------------------------------------

.PHONY: %.exp15
%.exp15:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASKS="fin-eng" \
		TASK_GPUS="0:0" \
		TASK_WEIGHTS="1.0" \
		TASK_TRANSFORMS="filtertoolong" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		FLASH_ATTENTION=false \
		ROTARY_POS_EMBEDDINGS=false \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 16: multilingual model with shared encoder accum_delay=10
##-----------------------------------------------------------

.PHONY: %.exp16
%.exp16:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 17: multilingual model with shared encoder accum_delay=10 and only average decay
##-----------------------------------------------------------

.PHONY: %.exp17
%.exp17:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.00001 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 18: multilingual model with shared encoder accum_delay=10 without average decay
##-----------------------------------------------------------

.PHONY: %.exp18
%.exp18:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 19: multilingual model with shared encoder accum_delay=10 without decay
##-----------------------------------------------------------

.PHONY: %.exp19
%.exp19:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 20: multilingual model with shared encoder accum_delay=10 and LR=0.0088
##-----------------------------------------------------------

.PHONY: %.exp20
%.exp20:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 21: multilingual model with shared encoder accum_delay=10 and only average decay
##-----------------------------------------------------------

.PHONY: %.exp21
%.exp21:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.0005 \
		GRADIENT_ACCUM=10 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 22: multilingual model with shared encoder accum_delay=20 and LR=0.0088
##-----------------------------------------------------------

.PHONY: %.exp22
%.exp22:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.0005 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=20 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 23: fully shared multilingual model accum_delay=20 and LR=0.0088
##    TODO: language token is missing
##          would be needed in this setup!
## 		ADD_LANGUAGE_TOKEN=true
##-----------------------------------------------------------

.PHONY: %.exp23
%.exp23:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		DEFAULT_ENCODER="shared_enc" \
		DEFAULT_DECODER="shared_dec" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		ACERAGE_DECAY=0.0005 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=20 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 24: lang-specific multilingual model accum_delay=20 and LR=0.0088
##-----------------------------------------------------------

.PHONY: %.exp24
%.exp24:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		ACERAGE_DECAY=0.0005 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=20 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 25: 
##-----------------------------------------------------------

.PHONY: %.exp25
%.exp25:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		ACERAGE_DECAY=0.0005 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=20 \
		LEARNING_RATE=0.0008 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 26: 
##-----------------------------------------------------------

.PHONY: %.exp26
%.exp26:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 27: 
##-----------------------------------------------------------

.PHONY: %.exp27
%.exp27:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=2,4 \
		DECODER_LAYERS=4,2 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 28: 
##-----------------------------------------------------------

.PHONY: %.exp28
%.exp28:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=1,5 \
		DECODER_LAYERS=5,1 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 29: 
##-----------------------------------------------------------

.PHONY: %.exp29
%.exp29:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		ENCODER_LAYERS=3,6 \
		DECODER_LAYERS=3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 30: 
##-----------------------------------------------------------

.PHONY: %.exp30
%.exp30:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=3,6 \
		DECODER_LAYERS=6,3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 31: 
##-----------------------------------------------------------

.PHONY: %.exp31
%.exp31:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=6,3 \
		DECODER_LAYERS=3,6 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 32: 
##-----------------------------------------------------------

.PHONY: %.exp32
%.exp32:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=6,1 \
		DECODER_LAYERS=1,6 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 33: 
##-----------------------------------------------------------

.PHONY: %.exp33
%.exp33:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=3,1 \
		DECODER_LAYERS=1,3 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 34: 
##-----------------------------------------------------------

.PHONY: %.exp34
%.exp34:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=2,1 \
		DECODER_LAYERS=1,2 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)

##-----------------------------------------------------------
## experiment 35: 
##-----------------------------------------------------------

.PHONY: %.exp35
%.exp35:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_ENCODERS='"eng","allenc" "fin","allenc" "fin","allenc" "swe","allenc" "deu","allenc" "eng","allenc" "eng","allenc" "eng","allenc" "fin","allenc" "swe","allenc"' \
		TASK_DECODERS='"alldec","eng" "alldec","fin" "alldec","eng" "alldec","eng" "alldec","eng" "alldec","fin" "alldec","swe" "alldec","deu" "alldec","swe" "alldec","fin"' \
		ENCODER_LAYERS=1,2 \
		DECODER_LAYERS=2,1 \
		ACERAGE_DECAY=0.00001 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=10 \
		LEARNING_RATE=0.0008 \
	$(basename $@)


##-----------------------------------------------------------
## experiment 36: fully shared multilingual model accum_delay=20 and LR=0.0088
##-----------------------------------------------------------

.PHONY: %.exp36
%.exp36:
	${MAKE} MODEL_NAME=$(patsubst .%,%,$(suffix $@)) \
		TASK_TRANSFORMS="denoising,filtertoolong,prefix denoising,filtertoolong,prefix" \
		DEFAULT_ENCODER="shared_enc" \
		DEFAULT_DECODER="shared_dec" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		ACERAGE_DECAY=0.0005 \
		LR_DECAY=0.5 \
		DECAY_START=50000 \
		GRADIENT_ACCUM=20 \
		LEARNING_RATE=0.0008 \
		ADD_LANGUAGE_TOKEN=true \
	$(basename $@)

##-----------------------------------------------------------





# TASK_NR  ?= 1
TASK_NR  ?= $(words $(TASKS))
TASK     := $(word ${TASK_NR},$(TASKS))
SRCLANG  ?= $(firstword $(subst -, ,${TASK}))
TRGLANG  ?= $(lastword  $(subst -, ,${TASK}))
LANGPAIR ?= ${SRCLANG}-${TRGLANG}


DEFAULT_GPU        := 0:0
DEFAULT_WEIGHT     := 1.0
DEFAULT_TRANSFORM  := filtertoolong
DEFAULT_TRAINSTEP  := 0
# DEFAULT_ENCODER  := "shared"
DEFAULT_ENCODER    := "${SRCLANG}"
DEFAULT_DECODER    := "${TRGLANG}"

ifeq (${ADD_LANGUAGE_TOKEN},true)
  DEFAULT_TRANSFORM  := filtertoolong,prefix
endif


TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPUS))       $(DEFAULT_GPU))
TASK_WEIGHT    := $(firstword $(word ${TASK_NR},$(TASK_WEIGHTS))    $(DEFAULT_WEIGHT))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS)) $(DEFAULT_TRANSFORM))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS)) $(DEFAULT_TRAINSTEP))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))   $(DEFAULT_ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))   $(DEFAULT_DECODER))



TRAIN_CONFIGFILE      ?= ${WORK_DIR}/train.yaml
TRAIN_SLURMSCRIPT     ?= ${WORK_DIR}/train.sh

INFERENCE_CONFIGFILE  ?= ${WORK_DIR}/inference_${TASK}.yaml
INFERENCE_SLURMSCRIPT ?= ${WORK_DIR}/inference.sh

CONFIGFILE            ?= ${TRAIN_CONFIGFILE}




GPU_RANKS        := $(sort $(notdir $(subst :,/,${TASK_GPUS})))
NR_OF_GPUS       := $(words ${GPU_RANKS})
TOTAL_NR_OF_GPUS := $(words $(sort ${TASK_GPUS}))
NR_OF_NODES      := $(words $(sort $(dir $(subst :,/,${TASK_GPUS}))))
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
REPORT_FREQ      := 500     # progress reporting frequency (steps)


OPTIMIZER        := adamw
LEARNING_RATE    := 0.0005
# LEARNING_RATE    := 0.00001
ADAM_BETA1       := 0.9
ADAM_BETA2       := 0.999
WEIGHT_DECAY     := 0.01
MAX_GRAD_NORM    := 1.0
LABEL_SMOOTHING  := 0.1
LR_DECAY         := 0       # learning rate decay
DECAY_START      := 0       # steps when to start lr-decay
AVERAGE_DECAY    := 0
WARMUP_STEPS     := 5000
DECAY_METHOD     := linear_warmup
# TRAINING_STEPS   := 500000
TRAINING_STEPS   := 250000


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
# training and evaluation
#--------------------------------------------------------------

PROJECT_SPACE      := /scratch/project_462000964
SHARED_PROJECT_DIR := ${PROJECT_SPACE}/MARMoT
MAMMOTH_DIR        := ${PROJECT_SPACE}/shared/mammoth


## submit SLURM job for training a model

.PHONY: train eval
train: ${WORK_DIR}/train.slurm


## submit SLURM jobs to evaluate all tasks

.PHONY: eval-all-tasks
eval-all-tasks:
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} TASK_NR=$$t eval; \
	done

.PHONY: eval-zero-shot-tasks
eval-zero-shot-tasks:
	@for t in $(shell seq $(words ${ZERO_SHOT_TASKS})); do \
	  ${MAKE} TASKS="${ZERO_SHOT_TASKS}" TASK_NR=$$t eval; \
	done


## submit SLURM job for evaluating a model
## - copy the best model according to validation (only of the checkpoint exists)
## - otherwise: use the last checkpoint
## - translate the selected task (set TASK_NR) with the best mode
##

BEST_MODEL_STEP := $(strip $(shell grep -A2 "best_checkpoint" ${MODEL_META} | grep 'step' | cut -f2 -d: | cut -f1 -d,))
BEST_MODEL      := ${MODEL_PATH}_step_${BEST_MODEL_STEP}

.PHONY: eval
eval:
ifneq ($(wildcard ${TESTDATA_SRC}),)
ifneq ($(wildcard ${BEST_MODEL}_*),)
	mkdir -p $(dir ${MODEL_PATH})best-model
	find $(dir ${MODEL_PATH})best-model -type l -delete
	-ln -s ${BEST_MODEL}_* $(dir ${MODEL_PATH})best-model/
	-ln -s ${MODEL_META} $(dir ${MODEL_PATH})best-model/
	${MAKE} SLURM_TIME=00:30:00 \
		SLURM_GPUS=1 \
		SLURM_MEM=16G \
		SLURM_CPUS_PER_TASK=8 \
		MODEL_PATH=$(dir ${MODEL_PATH})best-model/$(notdir ${MODEL_PATH}) \
	${WORK_DIR}/eval_${TASK}.slurm
else
	${MAKE} SLURM_TIME=00:30:00 \
		SLURM_GPUS=1 \
		SLURM_MEM=16G \
		SLURM_CPUS_PER_TASK=8 \
	${WORK_DIR}/eval_${TASK}.slurm
endif
endif




## train a model

.PHONY: ${WORK_DIR}/train
${WORK_DIR}/train: ${TRAIN_CONFIGFILE}
	singularity exec \
	    -B ${WORK_DIR}:${WORK_DIR}:rw \
	    -B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
	    -B ${SHARED_PROJECT_DIR}:${SHARED_PROJECT_DIR}:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    ${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/train.py \
	    -save_model ${MODEL_PATH} \
	    -config $<


## translate and evaluate

.PHONY: ${WORK_DIR}/eval
${WORK_DIR}/eval: ${WORK_DIR}/eval_${TASK}

${WORK_DIR}/eval_${TASK}: ${TESTDATA_OUTPUT}
	sacrebleu ${TESTDATA_TRG} < $< > $@

${TESTDATA_OUTPUT}: ${INFERENCE_CONFIGFILE}
	singularity exec \
	    -B ${WORK_DIR}:${WORK_DIR}:rw \
	    -B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
	    -B ${SHARED_PROJECT_DIR}:${SHARED_PROJECT_DIR}:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    ${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/translate.py \
	    -model ${MODEL_PATH} \
	    -config $<


#--------------------------------------------------------------
# generate SLURM scripts
#--------------------------------------------------------------


${WORK_DIR}/train.sh: train-template.sh
	sed -e 's+WORKSPACE+${WORK_DIR}+'  \
	    -e 's+NR_OF_GPUS+${NR_OF_GPUS}+' \
	    -e 's+CONFIGFILE+${TRAIN_CONFIGFILE}+' \
	    -e 's/MODELPATH/${MODEL_PATH}/' \
	< $< > $@

${WORK_DIR}/inference.sh: inference-template.sh
	sed -e 's+WORKSPACE+${WORK_DIR}+'  \
	    -e 's+CONFIGFILE+${INFERENCE_CONFIGFILE}+' \
	    -e 's/MODELPATH/${MODEL_PATH}/' \
	< $< > $@


## create a slurm script and submit it

WHOAMI := $(shell whoami)
SLURM_MAX_NR_JOBS := 200
SLURM_PARTITION := standard-g
SLURM_NODES := ${NR_OF_NODES}
SLURM_CPUS_PER_TASK := 48
SLURM_MEM := 96G
SLURM_TIME := 2-00:00:00
SLURM_GPUS := ${NR_OF_GPUS}

ifdef SLURM_GPUS
ifneq (${SLURM_GPUS},0)
  SLURM_GRES := \#SBATCH --gres=gpu:${SLURM_GPUS}
endif
endif

%.slurm:
	@while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	  echo "waiting for space in the queue";\
	  sleep 1; \
	done
	@mkdir -p $(dir $@)
	@echo '#!/bin/bash' >> $@
	@echo '' >> $@
	@echo '#SBATCH -A ${HPC_PROJECT}' >> $@
	@echo '#SBATCH -J ${MODEL_NAME}' >> $@
	@echo '#SBATCH -o $(@:.slurm=).%j.out' >> $@
	@echo '#SBATCH -e $(@:.slurm=).%j.err' >> $@
	@echo '#SBATCH --partition=${SLURM_PARTITION}' >> $@
	@echo '#SBATCH --nodes=${SLURM_NODES}' >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}' >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}' >> $@
	@echo '#SBATCH --time=${SLURM_TIME}' >> $@
	echo '${SLURM_GRES}' >> $@
	@echo '' >> $@
	@echo 'echo "Starting at `date`"' >> $@
	@echo '' >> $@
	@echo '# stops the script when encountering an error' >> $@
	@echo '# (useful if running several commands in the same script)' >> $@
	@echo 'set -e' >> $@
	@echo '' >> $@
	@echo '/appl/local/csc/soft/ai/bin/gpu-energy --save' >> $@
	@echo '${SHARED_PROJECT_DIR}/tools/lumi_gpu_usage.sh > $(@:.slurm=.gpu-usage) &' >> $@
	@echo '' >> $@
	@echo '${MAKE} $(@:.slurm=)' >> $@
	@echo '' >> $@
	@echo '/appl/local/csc/soft/ai/bin/gpu-energy --diff' >> $@
	@echo 'mv $@ $@.done' >> $@
	@echo 'echo "Finishing at `date`"' >> $@
	sbatch $@


#--------------------------------------------------------------
# generate config files
#--------------------------------------------------------------

train-config: ${TRAIN_CONFIGFILE}

inference-config:
	${MAKE} ${INFERENCE_CONFIGFILE}

${INFERENCE_CONFIGFILE}: ${MODEL_META}
	echo 'task_id: task_${TASK}'       > $@
	@echo ''                          >> $@
	echo "tasks:"                     >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-task
	@echo ''                          >> $@
	echo "src_vocab:"                 >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${SRCLANG} config-add-vocab
	echo "tgt_vocab:"                 >> $@
	${MAKE} -s CONFIGFILE=$@ LANGID=${TRGLANG} config-add-vocab
	${MAKE} -s CONFIGFILE=$@ config-add-model-architecture
	${MAKE} -s CONFIGFILE=$@ config-add-transformer-params
	@echo ''                          >> $@
	echo '# Decoding parameters'      >> $@
	echo 'beam_size: 5'               >> $@
	echo 'batch_size: 32'             >> $@
	echo 'batch_type: sents'          >> $@
	echo ''                           >> $@
	echo '# GPU settings'             >> $@
	echo 'gpu: 0'                     >> $@
	echo 'world_size: 1'              >> $@
	echo 'gpu_ranks: [0]'             >> $@
	echo ''                           >> $@
	echo 'seed: ${RANDOM_SEED}'       >> $@
	echo 'src: ${TESTDATA_SRC}'       >> $@
	echo 'output: ${TESTDATA_OUTPUT}' >> $@
	echo 'model: ${MODEL_PATH}'       >> $@


${TRAIN_CONFIGFILE}:
	echo "tasks:"                        > $@
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} -s CONFIGFILE=$@ TASK_NR=$$t config-add-task; \
	done
	@echo ''                            >> $@
	echo "src_vocab:"                   >> $@
	@for l in $(VOCAB_SRCLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	echo "tgt_vocab:"                   >> $@
	@for l in $(VOCAB_TRGLANGS); do \
	  ${MAKE} -s CONFIGFILE=$@ LANGID=$$l config-add-vocab; \
	done
	@echo ''                            >> $@
	${MAKE} -s CONFIGFILE=$@ config-add-denoising
	${MAKE} -s CONFIGFILE=$@ config-add-model-architecture
	${MAKE} -s CONFIGFILE=$@ config-add-transformer-params
	${MAKE} -s CONFIGFILE=$@ config-add-training-params
	${MAKE} -s CONFIGFILE=$@ config-add-checkpoint-params
	@echo ''                            >> $@
	echo '# Model saving'               >> $@
	echo 'save_model: ${MODEL_PATH}'    >> $@
	echo 'save_strategy: best_and_last' >> $@


## add a task section

config-add-task:
	@echo "add task ${TASK}"
	@echo '  task_${TASK}:'                                             >> ${CONFIGFILE}
	@echo '    src_tgt: "${TASK}"' >> ${CONFIGFILE}
	@echo '    weight: ${TASK_WEIGHT}       # Task weight for sampling' >> ${CONFIGFILE}
	@echo '    introduce_at_training_step: ${TASK_TRAINSTEP}' >> ${CONFIGFILE}
	@echo '    node_gpu: ${TASK_GPU}   # Single GPU configuration' >> ${CONFIGFILE}
	@echo '    enc_sharing_group: [${TASK_ENCODER}]' >> ${CONFIGFILE}
	@echo '    dec_sharing_group: [${TASK_DECODER}]' >> ${CONFIGFILE}
	@echo '    transforms: [${TASK_TRANSFORM}]' >> ${CONFIGFILE}
ifeq (${ADD_LANGUAGE_TOKEN},true)
	@echo '    src_prefix: ">>${TRGLANG}<<"'  >> ${CONFIGFILE}
	@echo '    tgt_prefix: "<<${SRCLANG}>>"'  >> ${CONFIGFILE}
endif
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
	echo '# Model Architecture Options'               >> ${CONFIGFILE}
	echo 'enc_layers: [$(strip ${ENCODER_LAYERS})]'   >> ${CONFIGFILE}
	echo 'dec_layers: [$(strip ${DECODER_LAYERS})]'   >> ${CONFIGFILE}
	echo ''                                           >> ${CONFIGFILE}
	echo 'model_dim: ${MODEL_DIMENSION}'              >> ${CONFIGFILE}
	echo 'dropout: ${DROPOUT_RATE}'                   >> ${CONFIGFILE}
	echo 'model_dtype: ${MODEL_DTYPE}'                >> ${CONFIGFILE}
	echo 'add_language_tokens: ${ADD_LANGUAGE_TOKEN}' >> ${CONFIGFILE}
	echo ''                                           >> ${CONFIGFILE}

config-add-transformer-params:
	echo '# x-transformers specific options'                >> ${CONFIGFILE}
	echo 'x_transformers_opts:'                             >> ${CONFIGFILE}
	echo '  attn_flash: ${XTRF_FLASH_ATTENTION}'            >> ${CONFIGFILE}
	echo '  rotary_pos_emb: ${XTRF_ROTARY_POS_EMBEDDINGS}'  >> ${CONFIGFILE}
	echo '  tie_embedding: ${XTRF_TIE_EMBEDDINGS}'          >> ${CONFIGFILE}
	echo '  heads: ${XTRF_HEADS}'                           >> ${CONFIGFILE}
	echo '  pre_norm: ${XTRF_PRE_NORM}'                     >> ${CONFIGFILE}
	echo '  post_emb_norm: ${XTRF_POST_EMB_NORM}'           >> ${CONFIGFILE}
	echo '  post_emb_norm_bias: ${XTRF_POST_EMB_NORM_BIAS}' >> ${CONFIGFILE}
	echo '  attn_dropout: ${XTRF_ATTN_DROPOUT}'             >> ${CONFIGFILE}
	echo '  ff_dropout: ${XTRF_FF_DROPOUT}'                 >> ${CONFIGFILE}
	echo '  layernorm_bias: ${XTRF_LAYERNORM_BIAS}'         >> ${CONFIGFILE}
	echo '  use_abs_pos_emb: ${XTRF_USE_ABS_POS_EMB}'       >> ${CONFIGFILE}
	echo ''                                                 >> ${CONFIGFILE}


COMMA            := ,
GPU_RANKS_STRING := $(subst $(eval ) ,${COMMA},$(GPU_RANKS))

config-add-training-params:
	echo 'src_seq_length_max: ${MAX_SRCSEQ_LENGTH}' >> ${CONFIGFILE}
	echo 'tgt_seq_length_max: ${MAX_TRGSEQ_LENGTH}' >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
	echo '# Training Configuration'                 >> ${CONFIGFILE}
	echo 'train_steps: ${TRAINING_STEPS}'           >> ${CONFIGFILE}
	echo 'accum_count: [${GRADIENT_ACCUM}]'         >> ${CONFIGFILE}
	echo 'lookahead_minibatches: ${LOOK_AHEAD}'     >> ${CONFIGFILE}
	echo 'batch_size: ${BATCH_SIZE}'                >> ${CONFIGFILE}
	echo 'batch_type: ${BATCH_TYPE}'                >> ${CONFIGFILE}
	echo 'valid_batch_size: ${VALID_BATCH}'         >> ${CONFIGFILE}
	echo 'normalization: ${BATCH_TYPE}'             >> ${CONFIGFILE}
	echo 'queue_size: ${QUEUE_SIZE}'                >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
	echo '# Optimizer settings (from create_opts)'  >> ${CONFIGFILE}
	echo 'optim: ${OPTIMIZER}'                      >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
	echo 'learning_rate: ${LEARNING_RATE}'          >> ${CONFIGFILE}
	echo 'adam_beta1: ${ADAM_BETA1}'                >> ${CONFIGFILE}
	echo 'adam_beta2: ${ADAM_BETA1}'                >> ${CONFIGFILE}
	echo 'weight_decay: ${WEIGHT_DECAY}'            >> ${CONFIGFILE}
	echo 'max_grad_norm: ${MAX_GRAD_NORM}'          >> ${CONFIGFILE}
	echo 'label_smoothing: ${LABEL_SMOOTHING}'      >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
	echo '# Learning rate scheduling'               >> ${CONFIGFILE}
	echo 'warmup_steps: ${WARMUP_STEPS}'            >> ${CONFIGFILE}
	echo 'decay_method: ${DECAY_METHOD}'            >> ${CONFIGFILE}
	echo 'learning_rate_decay: ${LR_DECAY}'         >> ${CONFIGFILE}
	echo 'start_decay_steps: ${DECAY_START}'        >> ${CONFIGFILE}
	echo 'average_decay: ${AVERAGE_DECAY}'          >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
	echo 'world_size: ${TOTAL_NR_OF_GPUS}'          >> ${CONFIGFILE}
	echo 'gpu_ranks: [${GPU_RANKS_STRING}]'         >> ${CONFIGFILE}
	echo 'task_distribution_strategy: ${TASK_DISTRIBUTION_STRATEGY}' >> ${CONFIGFILE}
	echo 'node_rank: ${NODE_RANK}'                  >> ${CONFIGFILE}
	echo ''                                         >> ${CONFIGFILE}
ifdef RANDOM_SEED
	echo 'seed: ${RANDOM_SEED}'                     >> ${CONFIGFILE}
endif


config-add-checkpoint-params:
	echo 'valid_steps: ${VALID_FREQ}'                 >> ${CONFIGFILE}
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



