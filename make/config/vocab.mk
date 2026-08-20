#--------------------------------------------------------------
# vocab files
#--------------------------------------------------------------


## tokenizer directory

VOCAB     ?= tatoeba
VOCAB_DIR ?= ${PROJECT_DIR}/tokenizer/${VOCAB}


## really ugly way of getting from tasks to a unique set
## of source and target languages for the vocabs

VOCAB_SRCLANGS ?= $(sort $(patsubst %/,%,$(dir $(subst -,/,${TASK_LANGPAIRS}))))
VOCAB_TRGLANGS ?= $(sort $(notdir $(subst -,/,${TASK_LANGPAIRS})))

VOCAB_SIZE     ?= 32000
VOCAB_SRC_SIZE ?= ${VOCAB_SIZE}
VOCAB_TRG_SIZE ?= ${VOCAB_SIZE}
VOCAB_SRC_DIR  ?= ${VOCAB_DIR}
VOCAB_TRG_DIR  ?= ${VOCAB_DIR}

VOCAB_FILE     ?= ${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json
VOCAB_SRC_FILE ?= ${VOCAB_SRC_DIR}/${SRCLANG}/${VOCAB_SRC_SIZE}/tokenizer.json
VOCAB_TRG_FILE ?= ${VOCAB_TRG_DIR}/${TRGLANG}/${VOCAB_TRG_SIZE}/tokenizer.json

VOCAB_SRC_FILES ?= $(foreach l,${VOCAB_SRCLANGS},${VOCAB_SRC_DIR}/$l/${VOCAB_SRC_SIZE}/tokenizer.json)
VOCAB_TRG_FILES ?= $(foreach l,${VOCAB_TRGLANGS},${VOCAB_TRG_DIR}/$l/${VOCAB_TRG_SIZE}/tokenizer.json)


src-vocab-file = $(call lookup,$1,${VOCAB_SRCLANGS},${VOCAB_SRC_FILES})
trg-vocab-file = $(call lookup,$1,${VOCAB_TRGLANGS},${VOCAB_TRG_FILES})
