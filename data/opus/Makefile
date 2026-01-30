

SHELL := bash

CORPUS ?= OpenSubtitles

SRC ?= fin
TRG ?= eng

SRC2 := $(shell iso639 -2 -n ${SRC})
TRG2 := $(shell iso639 -2 -n ${TRG})


LANGPAIR := ${SRC}-${TRG}

all: ${CORPUS}/${LANGPAIR}.${SRC}.gz

${CORPUS}/${LANGPAIR}.${SRC}.gz:
	mkdir -p $@.d
	opus_get -d ${CORPUS} -s ${SRC2} -t ${TRG2} -p moses -q -dl $@.d
	cd $@.d && unzip *.zip
	gzip -c $@.d/*.${SRC2} > $@
	gzip -c $@.d/*.${TRG2} > $(@:${SRC}.gz=${TRG}.gz)
	rm -f $@.d/*
	rmdir $@.d

