# English-Finnish MT model

MODEL_NAME := mammoth-engfin


## doc-level and wiki translation tasks
## run all on one GPU
TASK_IDS  := docmt_eng-fin wiki_eng-fin
TASK_GPUS := 0:0 0:0


## select MultiSynth doc-level translations and Wiki backtranslations as training data
## use file size as weight for data sampling
TRANSLATE_TRAIN_DOC  := multisynt/train/len1024
TRANSLATE_TRAIN_WIKI := synthetic/Wiki
TRANSLATE_TRAIN_SENT := sentmt

TASK_TRAINDATA := ${TRANSLATE_TRAIN_DOC} ${TRANSLATE_TRAIN_WIKI}
USE_DATASIZE_AS_TASK_WEIGHT := 1


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk


