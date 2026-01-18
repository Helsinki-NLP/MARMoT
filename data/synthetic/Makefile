

CORPUS  ?= Wiki
VERSION ?= v1syn
SRC     ?= fin
TRG     ?= eng


SRC2 := $(shell iso639 -2 -n ${SRC})
TRG2 := $(shell iso639 -2 -n ${TRG})

LANGPAIR := ${SRC}-${TRG}
LANGPAIR2 := ${SRC2}-${TRG2}


.PHONY: all
all: ${CORPUS}/${LANGPAIR}.${SRC}.gz

fin-eng:
	${MAKE} CORPUS=Wiki VERSION=v1syn SRC=fin TRG=eng all

eng-fin:
	${MAKE} CORPUS=Wikipedia VERSION=v1syn SRC=eng TRG=fin all

DOWNLOAD_URL := https://opus.nlpl.eu/synthetic/download.php?f=

${CORPUS}/${LANGPAIR}.${SRC}.gz:
	mkdir -p $@.d
	wget -q -O $@.d/data.zip "${DOWNLOAD_URL}${CORPUS}/${VERSION}/moses/${SRC2}-${TRG2}.txt.zip"
	cd $@.d && unzip data.zip
	gzip -f $@.d/*.*
	mv $@.d/*.${SRC2}.gz $@
	mv $@.d/*.${TRG2}.gz $(@:.${SRC}.gz=.${TRG}.gz)
	rm -f $@.d/*
	rmdir $@.d




