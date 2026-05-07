#
# document-level Finnish-English MT model


MODEL_NAME := mammoth-fineng


## all English-centric translation tasks in both directions
TASKS := eng-fin


## select MultiSynth doc-level training data
TRAINDATA := multisynt/train/len1024


## use document-level tokenizers trained on Tatoeba/HPLT/MultiSynth
VOCAB := tatoeba_hplt_multisynt

DEFAULT_ENCODER := "{LANG}","{LANGGROUP}","all"
DEFAULT_DECODER := "all,{LANGGROUP},{LANG}"


## include this at the end to set all variables and
## to include all makefile targets for marmot experiments
include ../../make/marmot.mk



info:
	echo ${TASK_ENCODER}
	echo ${TASK_DECODER}

tt:
	@echo $(call langgroup,deu)
	@echo $(call langgroup,rus)

tt2:
	@echo $(call langgroup2,deu)
	@echo $(call langgroup2,rus)


