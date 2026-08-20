#--------------------------------------------------------------
# model architecture
#--------------------------------------------------------------


## some pre-defined model architectures

MODEL_ARCHITECTURE ?= transformer-base

ifeq (${MODEL_ARCHITECTURE},transformer-tiny)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 2
  MODEL_DIMENSION ?= 256
  TRF_HEADS       ?= 8
  BATCH_SIZE      ?= 32768
else ifeq (${MODEL_ARCHITECTURE},transformer-small)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 2
  MODEL_DIMENSION ?= 512
  TRF_HEADS       ?= 8
  BATCH_SIZE      ?= 32768
else ifeq (${MODEL_ARCHITECTURE},transformer-base)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 6
  MODEL_DIMENSION ?= 512
  TRF_HEADS       ?= 8
else ifeq (${MODEL_ARCHITECTURE},transformer-big)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 6
  MODEL_DIMENSION ?= 1024
  TRF_HEADS       ?= 16
else ifeq (${MODEL_ARCHITECTURE},transformer-xl)
  ENCODER_LAYERS  ?= 12
  DECODER_LAYERS  ?= 12
  MODEL_DIMENSION ?= 1024
  TRF_HEADS       ?= 16
else ifeq (${MODEL_ARCHITECTURE},transformer-xxl)
  ENCODER_LAYERS  ?= 24
  DECODER_LAYERS  ?= 24
  MODEL_DIMENSION ?= 2048
  TRF_HEADS       ?= 24
endif


# total nr of encoder and decoder layers

ENCODER_LAYERS     ?= 6
DECODER_LAYERS     ?= 6

# Transformer model dimension
# parameter precision and type
# dropout rate

MODEL_DIMENSION    ?= 768
MODEL_DTYPE        ?= bf16
DROPOUT_RATE       ?= 0.1


# Transformer options

TRF_HEADS                  ?= 8
TRF_ROTARY_POS_EMBEDDINGS  ?= true
TRF_POST_EMB_NORM          ?= true
TRF_ATTN_DROPOUT           ?= 0.1
TRF_FF_DROPOUT             ?= 0.1
TRF_FF_ACTIVATION          ?= swiglu


# X-Transformer options (some are not implemented in pytorch backend)
# - Flash attention (not supported on V100)

XTRF_ROTARY_POS_EMBEDDINGS ?= ${TRF_ROTARY_POS_EMBEDDINGS}
XTRF_ATTN_DROPOUT          ?= ${TRF_ATTN_DROPOUT}
XTRF_FF_DROPOUT            ?= ${TRF_FF_DROPOUT}
XTRF_HEADS                 ?= ${TRF_HEADS}
XTRF_POST_EMB_NORM         ?= ${TRF_POST_EMB_NORM}
XTRF_POST_EMB_NORM_BIAS    ?= true
XTRF_PRE_NORM              ?= false
XTRF_LAYERNORM_BIAS        ?= true
XTRF_USE_ABS_POS_EMB       ?= false
XTRF_TIE_EMBEDDINGS        ?= false
XTRF_FLASH_ATTENTION       ?= true
