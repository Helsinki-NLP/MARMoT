#
# document-level Finnish-English MT model


MODEL_NAME := mammoth-fineng


## all English-centric translation tasks in both directions
TASKS := eng-fin


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk


