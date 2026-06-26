

TASKS     := eng-eng
TRAINDATA := multisynt/textpredict/train/len1024
DEVDATA   := multisynt/textpredict/dev/len1024
VOCAB     := tatoeba_hplt_multisynt

MODEL_ARCHITECTURE := transformer-xl
BATCH_SIZE         := 16384
GRADIENT_ACCUM     := 50
LOOK_AHEAD         := 100
QUEUE_SIZE         := 200


PRETRAINED_MODEL   := ../docmt-denoise-xl/mammoth


include ../../../make/marmot.mk
