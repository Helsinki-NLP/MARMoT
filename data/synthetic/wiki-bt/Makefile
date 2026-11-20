#
# merge and shuffle all wikimedia-based back-translations
# also reverse the language direction to properly indicate
# the back-translation direction (original language becomes target)
#

SHELL := bash


reverse = $(lastword $(subst -, ,$(1)))-$(firstword $(subst -, ,$(1)))

FWD_LANGPAIRS := $(sort $(basename $(basename $(notdir $(wildcard ../Wiki*/*.gz)))))

FWD_LANGPAIR ?= $(firstword ${FWD_LANGPAIRS})
BCK_LANGPAIR := $(call reverse,${FWD_LANGPAIR})

SRC := $(firstword $(subst -, ,$(BCK_LANGPAIR)))
TRG := $(lastword $(subst -, ,$(BCK_LANGPAIR)))


.PHONY: all
all: ${FWD_LANGPAIRS}

.PHONY: merge
merge: ${BCK_LANGPAIR}.${SRC}.gz




.PHONY: ${FWD_LANGPAIRS}
${FWD_LANGPAIRS}:
	${MAKE} FWD_LANGPAIR=$@ merge


FWD_LANGPAIR_SRC := $(wildcard ../Wiki*/${FWD_LANGPAIR}.${SRC}.gz)
FWD_LANGPAIR_TRG := $(patsubst %.${SRC}.gz,%.${TRG}.gz,${FWD_LANGPAIR_SRC})

.INTERMEDIATE: ${BCK_LANGPAIR}.tmp.${SRC} ${BCK_LANGPAIR}.tmp.${TRG}

${BCK_LANGPAIR}.tmp.${SRC}: ${FWD_LANGPAIR_SRC}
	pigz -cd $^ > $@

${BCK_LANGPAIR}.tmp.${TRG}: ${FWD_LANGPAIR_TRG}
	pigz -cd $^ > $@

${BCK_LANGPAIR}.${SRC}.gz: ${BCK_LANGPAIR}.tmp.${SRC} ${BCK_LANGPAIR}.tmp.${TRG} 
	export TMPDIR=${PWD} && \
	paste $^ | terashuf \
	| tee >(cut -f1 | pigz -c > $@) \
	| cut -f2 | pigz -c > $(@:.${SRC}.gz=.${TRG}.gz)



info:
	@echo ${FWD_LANGPAIR}
	@echo ${BCK_LANGPAIR}
	@echo ${FWD_LANGPAIR_SRC}
	@echo ${FWD_LANGPAIR_TRG}
