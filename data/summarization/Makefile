

## combine data sets (skip cross-lingual datasets from CrossSum)

DATASPLIT := train

LANGUAGES := $(patsubst .%1,%,$(suffix $(patsubst %.gz,%,$(wildcard */${DATASPLIT}/*1.gz))))
LANGUAGE  := $(firstword ${LANGUAGES})


DATASETS_LONG  := $(sort $(wildcard */${DATASPLIT}/*.${LANGUAGE}1.gz))
DATASETS_SHORT := $(sort $(wildcard */${DATASPLIT}/*.${LANGUAGE}2.gz))

COMBINED_LONG  := ${DATASPLIT}/summarization.${LANGUAGE}1.gz
COMBINED_SHORT := ${DATASPLIT}/summarization.${LANGUAGE}2.gz

all:
	for l in ${LANGUAGES}; do \
	  for s in train dev test; do \
	    ${MAKE} LANGUAGE=$$l DATASPLIT=$$s convert; \
	  done \
	done

convert: ${COMBINED_LONG} ${COMBINED_SHORT}

${COMBINED_LONG}:
	mkdir -p $(dir $@)
	zcat ${DATASETS_LONG} | gzip -c > $@

${COMBINED_SHORT}:
	mkdir -p $(dir $@)
	zcat ${DATASETS_SHORT} | gzip -c > $@
