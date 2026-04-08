#
# document-level English-Finnish MT model


MODEL_NAME     := mammoth-engfin
TASKS          := eng-fin
TASK_LANGPAIRS := gmw-fin


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB          := tatoeba_hplt_multisynt
VOCAB_SRC_SIZE := 65472


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk


