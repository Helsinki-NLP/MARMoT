

## data directories (assuming that we have data prepared in the project dir)
## - default training data from the Tatoeba translation challenge
## - default dev and test data from Flores200 if the exists (Tatoeba otherwise)

DATA_DIR        ?= ${PROJECT_DIR}/data
TRAINDATA       ?= tatoeba/train
TRAINDATA_NAME  ?= tatoeba-test-v2023-09-26

ifneq ($(wildcard ${DATA_DIR}/flores200/dev),)
  DEVDATA       ?= flores200/dev
  DEVDATA_NAME  ?= flores200-dev
else
  DEVDATA       ?= tatoeba/dev5K
  DEVDATA_NAME  ?= tatoeba-test-v2023-09-26
endif

ifneq ($(wildcard ${DATA_DIR}/flores200/devtest),)
  TESTDATA      ?= flores200/devtest
  TESTDATA_NAME ?= flores200-devtest
else
  TESTDATA      ?= tatoeba/test
  TESTDATA_NAME ?= tatoeba-test-v2023-09-26
endif


#--------------------------------------------------------------
# data sets
#
# - default data sets are taken from TRAINDATA_DIR, DEVDATA_DIR and TESTDATA_DIR
# - task-specific training data can be set in TASK_TRAINDATA_SRCS and TASK_TRAINDATA_TRGS
# - task-specific dev data can be set in TASK_DEVDATA_SRCS and TASK_DEVDATA_TRGS
# - task-specific test data can be set in TASK_TESTDATA_SRCS and TASK_TESTDATA_TRGS
#--------------------------------------------------------------


## skip validation for denoising tasks
## and monolingual tasks (typically denoising tasks)
## set those variables to 0 to enable them

SKIP_SAME_LANGUAGE_VALID_TASKS ?= 0
SKIP_DENOISING_VALID_TASKS     ?= 0


## in OPUS/Tatoeba data we have sorted language IDs for language pairs

SORTED_SRCLANG  := $(firstword $(sort ${SRCLANG} ${TRGLANG}))
SORTED_TRGLANG  := $(lastword  $(sort ${SRCLANG} ${TRGLANG}))
SORTED_LANGPAIR := ${SORTED_SRCLANG}-${SORTED_TRGLANG}
REVERSE_LANGPAIR := ${SORTED_TRGLANG}-${SORTED_SRCLANG}


##---------------------------------------------------------------------------------
## datasets: training, development and testing
##---------------------------------------------------------------------------------

## data directories (train/dev/test)
##
## data directories can be specified for each task
## if not, take the default locations given in TRAINDATA, DEVDATA and TESTDATA

TRAINDATA_DIR ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_TRAINDATA)) ${TRAINDATA})
DEVDATA_DIR   ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_DEVDATA)) ${DEVDATA})
TESTDATA_DIR  ?= ${DATA_DIR}/$(firstword $(word ${TASK_NR},$(TASK_TESTDATA)) ${TESTDATA})


## basenames of data files (filepattern to be used within the data directories)
##
## file basenames are either given for each specific task
## or we use the default pattern, which is *${SORTED_LANGPAIR}
## (in OPUS/Tatoeba we sort language IDs alphabetically and uses them in the bitext file name)

TRAINDATA_BASENAME ?= $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_BASENAMES)) *${SORTED_LANGPAIR}*)
DEVDATA_BASENAME   ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_BASENAMES)) *${SORTED_LANGPAIR}*)
TESTDATA_BASENAME  ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_BASENAMES)) *${SORTED_LANGPAIR}*)


# replace variables if they exist

TRAINDATA_BASENAME_PATTERN := $(subst {langpair},${LANGPAIR},$(subst {reverse_langpair},${REVERSE_LANGPAIR},$(subst {sorted_langpair},${SORTED_LANGPAIR},${TRAINDATA_BASENAME})))
DEVDATA_BASENAME_PATTERN := $(subst {langpair},${LANGPAIR},$(subst {reverse_langpair},${REVERSE_LANGPAIR},$(subst {sorted_langpair},${SORTED_LANGPAIR},${DEVDATA_BASENAME})))
TESTDATA_BASENAME_PATTERN := $(subst {langpair},${LANGPAIR},$(subst {reverse_langpair},${REVERSE_LANGPAIR},$(subst {sorted_langpair},${SORTED_LANGPAIR},${TESTDATA_BASENAME})))


## file extension for source and target language files
##
## if source and target language are the same AND this is not a denoising task
## then add some digits to the source language file extensions to distinguish
##      between input and output files (e.g. eng1 and eng2)
##
## TASK_SRCLANG_EXT and TASK_TRGLANG_EXT can overwrite the default extensions
## for specific tasks

ifneq ($(findstring denoising,$(TASK_TRANSFORM)),denoising)
ifeq (${SRCLANG},${TRGLANG})
  DEFAULT_SRCLANG_EXT ?= ${SRCLANG}1.gz
  DEFAULT_TRGLANG_EXT ?= ${TRGLANG}2.gz
endif
endif

DEFAULT_SRCLANG_EXT ?= ${SRCLANG}.gz
DEFAULT_TRGLANG_EXT ?= ${TRGLANG}.gz

SRCLANG_EXT ?= $(firstword $(word ${TASK_NR},$(TASK_SRCLANG_EXT)) ${DEFAULT_SRCLANG_EXT})
TRGLANG_EXT ?= $(firstword $(word ${TASK_NR},$(TASK_TRGLANG_EXT)) ${DEFAULT_TRGLANG_EXT})


## training data
##
## default search patterns for finding training data (DEFAULT_TRAINDATA_PATTERNS)
## take the first one that matches any pattern (DEFAULT_TRAINDATA_SRC and DEFAULT_TRAINDATA_TRG)
## overwrite with task-specific training data given in TASK_TRAINDATA_SRCS and TASK_TRAINDATA_TRGS

ifdef FIND_DATA
  DEFAULT_TRAINDATA_PATTERNS ?= ${TRAINDATA_BASENAME_PATTERN} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCTRAIN_PATTERN   ?= $(patsubst %,${TRAINDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_TRAINDATA_PATTERNS})
  DEFAULT_TRGTRAIN_PATTERN   ?= $(patsubst %,${TRAINDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_TRAINDATA_PATTERNS})
  DEFAULT_TRAINDATA_SRC      ?= $(firstword $(wildcard ${DEFAULT_SRCTRAIN_PATTERN}))
  DEFAULT_TRAINDATA_TRG      ?= $(firstword $(wildcard ${DEFAULT_TRGTRAIN_PATTERN}))
endif

TRAINDATA_SRC ?= $(wildcard $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_SRCS)) $(DEFAULT_TRAINDATA_SRC)))
TRAINDATA_TRG ?= $(wildcard $(firstword $(word ${TASK_NR},$(TASK_TRAINDATA_TRGS)) $(DEFAULT_TRAINDATA_TRG)))

## data size in bytes (note: can be compressed data)

ifneq (${TRAINDATA_SRC},)
  ifneq (${TRAINDATA_TRG},)
    TRAINDATA_SRC_SIZE := $(shell stat -c%s ${TRAINDATA_SRC})
    TRAINDATA_TRG_SIZE := $(shell stat -c%s ${TRAINDATA_TRG})
    TRAINDATA_SIZE     := $(shell echo $$(( $(TRAINDATA_SRC_SIZE) + $(TRAINDATA_TRG_SIZE) )) )
  endif
endif


## validation data
##
## default search patterns for finding development data (DEFAULT_DEVDATA_PATTERNS)
## take the first one that matches any pattern (DEFAULT_DEVDATA_SRC and DEFAULT_DEVDATA_TRG)
## skip denoising tasks if SKIP_DENOISING_VALID_TASKS=1
## skip monolingual tasks if SKIP_SAME_LANGUAGE_VALID_TASKS=1
## overwrite with task-specific development data given in TASK_DEVDATA_SRCS and TASK_DEVDATA_TRGS

ifdef FIND_DATA
  DEFAULT_DEVDATA_PATTERNS ?= ${DEVDATA_BASENAME_PATTERN} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCDEV_PATTERN ?= $(patsubst %,${DEVDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_DEVDATA_PATTERNS}) ${DEVDATA_DIR}/${SRCLANG}*
  DEFAULT_TRGDEV_PATTERN ?= $(patsubst %,${DEVDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_DEVDATA_PATTERNS}) ${DEVDATA_DIR}/${TRGLANG}*
  DEFAULT_DEVDATA_SRC    ?= $(firstword $(wildcard ${DEFAULT_SRCDEV_PATTERN}))
  DEFAULT_DEVDATA_TRG    ?= $(firstword $(wildcard ${DEFAULT_TRGDEV_PATTERN}))
endif

ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_VALID_TASKS},denoising-1)
  ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_VALID_TASKS},$(TRGLANG)-1)
    DEVDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_SRCS)) $(DEFAULT_DEVDATA_SRC))
    DEVDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_DEVDATA_TRGS)) $(DEFAULT_DEVDATA_TRG))
  endif
endif


## testdata
##
## default test data patterns (DEFAULT_SRCTEST_PATTERN and DEFAULT_TRGTEST_PATTERN)
## take the first one that matches any pattern (DEFAULT_TESTDATA_SRC and DEFAULT_TESTDATA_TRG)
## overwrite with task-specific test data given in TASK_TESTDATA_SRCS and TASK_TESTDATA_TRGS
## TESTDATA_OUTPUT: name of the output file (translations)

ifdef FIND_TESTDATA
  DEFAULT_TESTDATA_PATTERNS ?= ${TESTDATA_BASENAME_PATTERN} *${SORTED_LANGPAIR}* *${REVERSE_LANGPAIR}* *
  DEFAULT_SRCTEST_PATTERN ?= $(patsubst %,${TESTDATA_DIR}/%.${SRCLANG_EXT},${DEFAULT_TESTDATA_PATTERNS}) ${TESTDATA_DIR}/${SRCLANG}*
  DEFAULT_TRGTEST_PATTERN ?= $(patsubst %,${TESTDATA_DIR}/%.${TRGLANG_EXT},${DEFAULT_TESTDATA_PATTERNS}) ${TESTDATA_DIR}/${TRGLANG}*
  DEFAULT_TESTDATA_SRC    ?= $(firstword $(wildcard ${DEFAULT_SRCTEST_PATTERN}))
  DEFAULT_TESTDATA_TRG    ?= $(firstword $(wildcard ${DEFAULT_TRGTEST_PATTERN}))
endif

TESTDATA_SRC ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_SRCS)) $(DEFAULT_TESTDATA_SRC))
TESTDATA_TRG ?= $(firstword $(word ${TASK_NR},$(TASK_TESTDATA_TRGS)) $(DEFAULT_TESTDATA_TRG))

TESTDATA_OUTPUT ?= ${EVAL_DIR}/${TASK_ID}.${TESTDATA_NAME}.${SRCLANG}.${TRGLANG}






## data size count files (countling lines, words and bytes with wc)
## and make targets to create those files

TRAINDATA_SRC_SIZEFILE ?= ${TRAINDATA_SRC}.size
TRAINDATA_TRG_SIZEFILE ?= ${TRAINDATA_TRG}.size

MAKE_TRAINDATA_SIZEFILES := $(patsubst %,make-train-datasize-files/%,${TASK_NRS})
.PHONY: ${MAKE_TRAINDATA_SIZEFILES}
${MAKE_TRAINDATA_SIZEFILES}:
	${MAKE} TASK_NR=$(notdir $@) make-train-datasize-files

.PHONY: make-train-datasize-files
make-train-datasize-files: ${TRAINDATA_SRC_SIZEFILE} ${TRAINDATA_TRG_SIZEFILE}

${TRAINDATA_SRC_SIZEFILE}: ${TRAINDATA_SRC}
	${GZIP} -cd < $< | wc > $@

ifneq (${TRAINDATA_SRC_SIZEFILE},${TRAINDATA_TRG_SIZEFILE})
${TRAINDATA_TRG_SIZEFILE}: ${TRAINDATA_TRG}
	${GZIP} -cd < $< | wc > $@
endif



