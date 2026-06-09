#--------------------------------------------------------------
# model architecture
#--------------------------------------------------------------


MODEL_ARCHITECTURE ?= transformer-base

ifeq (${MODEL_ARCHITECTURE},transformer-tiny)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 2
  MODEL_DIMENSION ?= 256
  XTRF_HEADS      ?= 8
  BATCH_SIZE      ?= 32768
else ifeq (${MODEL_ARCHITECTURE},transformer-small)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 2
  MODEL_DIMENSION ?= 512
  XTRF_HEADS      ?= 8
  BATCH_SIZE      ?= 32768
else ifeq (${MODEL_ARCHITECTURE},transformer-base)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 6
  MODEL_DIMENSION ?= 512
  XTRF_HEADS      ?= 8
else ifeq (${MODEL_ARCHITECTURE},transformer-big)
  ENCODER_LAYERS  ?= 6
  DECODER_LAYERS  ?= 6
  MODEL_DIMENSION ?= 1024
  XTRF_HEADS      ?= 16
else ifeq (${MODEL_ARCHITECTURE},transformer-xl)
  ENCODER_LAYERS  ?= 12
  DECODER_LAYERS  ?= 12
  MODEL_DIMENSION ?= 1024
  XTRF_HEADS      ?= 16
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
