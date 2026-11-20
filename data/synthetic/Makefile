

CORPUS  ?= Wiki
VERSION ?= v1syn

# CORPUS ?= Europarl
# VERSION ?= v8syn

LANGPAIRS2 ?= $(shell curl --silent "https://opus.nlpl.eu/synthetic-api/items?name=${CORPUS}&version=${VERSION}"  | tr ':,' "\n\n" | grep -A1 'lang_pair' | grep '"' | grep -v lang_pair | sed 's/\"//g' | sort -u | tr "\n" ' ')
# LANGPAIR2 ?= $(firstword ${LANGPAIRS2})

ifdef LANGPAIR2
  SRC2 := $(firstword $(subst -, ,$(LANGPAIR2)))
  TRG2 := $(lastword $(subst -, ,$(LANGPAIR2)))
  SRC  := $(shell iso639 -3 -n ${SRC2})
  TRG  := $(shell iso639 -3 -n ${TRG2})
endif

SRC  ?= fin
TRG  ?= eng
SRC2 ?= $(shell iso639 -2 -n ${SRC})
TRG2 ?= $(shell iso639 -2 -n ${TRG})

LANGPAIR  := ${SRC}-${TRG}
LANGPAIR2 ?= ${SRC2}-${TRG2}


.PHONY: all
all: ${LANGPAIRS2}

.PHONY: Europarl
Europarl:
	${MAKE} CORPUS=$@ VERSION=v8syn all

.PHONY: Wiki Wikipedia Wikibooks Wikisource Wikinews Wikiquote
Wiki Wikipedia Wikibooks Wikisource Wikinews Wikiquote:
	${MAKE} CORPUS=$@ VERSION=v1syn all


nordic:
	for w in Wiki Wikipedia Wikibooks Wikisource Wikinews Wikiquote; do \
	  for l in dan fin nob swe; do \
	    ${MAKE} SRC=$$l TRG=eng CORPUS=$$w download; \
	    ${MAKE} TRG=$$l SRC=eng CORPUS=$$w download; \
	  done \
	done

.PHONY: download
download: ${CORPUS}/${LANGPAIR}.${SRC}.gz

fin-eng:
	${MAKE} CORPUS=Wiki VERSION=v1syn SRC=fin TRG=eng all

eng-fin:
	${MAKE} CORPUS=Wikipedia VERSION=v1syn SRC=eng TRG=fin all


.PHONY: ${LANGPAIRS2}
${LANGPAIRS2}:
	${MAKE} LANGPAIR2=$@ download


DOWNLOAD_URL := https://opus.nlpl.eu/legacy/synthetic/download.php?f=

${CORPUS}/${LANGPAIR}.${SRC}.gz:
	mkdir -p $@.d
	wget -q -O $@.d/data.zip "${DOWNLOAD_URL}${CORPUS}/${VERSION}/moses/${SRC2}-${TRG2}.txt.zip"
	cd $@.d && unzip data.zip
	gzip -f $@.d/*.*
	mv $@.d/*.${SRC2}.gz $@
	mv $@.d/*.${TRG2}.gz $(@:.${SRC}.gz=.${TRG}.gz)
	rm -f $@.d/*
	rmdir $@.d






