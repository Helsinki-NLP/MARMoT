

SHELL := bash

include ../../tools/slurMake/slurm.mk


CORPUS ?= OpenSubtitles

SRC ?= eng
TRG ?= fin

SRC2 := $(shell iso639 -2 -n ${SRC})
TRG2 := $(shell iso639 -2 -n ${TRG})


LANGPAIR := ${SRC}-${TRG}


all: ${CORPUS}/${LANGPAIR}.${SRC}.gz



# targets for retrieving HPLT data (release v2 and v3)

HPLT2_LANGS := af ar az be bg bn bs ca cy eo et eu fa fi ga gl gu he hi hr is ja kk kn ko lt lv mk ml mr ms mt nb ne nn si sk sl sq sr sw ta te th tr uk ur uz vi xh
HPLT3_LANGS := bg bs ca cs da el et eu fi ga gl hr hu is ka lt lv mk mt nb nn ro sk sl sq sr tr uk

HPLT3_LANGS3 := $(shell iso639 -3 -n ${HPLT3_LANGS})
HPLT2_LANGS3 := $(shell iso639 -3 -n ${HPLT2_LANGS})

hplt:
	for l in ${HPLT3_LANGS3}; do \
	  if [ $$l \< eng ]; then \
	    ${MAKE} CORPUS=HPLT SRC=$$l TRG=eng all; \
	  else \
	    ${MAKE} CORPUS=HPLT SRC=eng TRG=$$l all; \
	  fi \
	done

hplt2:
	for l in $(filter-out ${HPLT3_LANGS},${HPLT2_LANGS3}); do \
	  if [ $$l \< eng ]; then \
	    ${MAKE} CORPUS=HPLT RELEASE=v2 SRC=$$l TRG=eng all; \
	  else \
	    ${MAKE} CORPUS=HPLT RELEASE=v2 SRC=eng TRG=$$l all; \
	  fi \
	done



## add release parameter if the variable is set (use latest release otherwise)

ifdef RELEASE
  OPUSGET_EXTRA_PARAM := -r ${RELEASE}
endif


${CORPUS}/${LANGPAIR}.${SRC}.gz:
	mkdir -p $@.d
	opus_get -d ${CORPUS} ${OPUSGET_EXTRA_PARAM} -s ${SRC2} -t ${TRG2} -p moses -q -dl $@.d
	cd $@.d && unzip *.zip
	gzip -c $@.d/*.${SRC2} > $@
	gzip -c $@.d/*.${TRG2} > $(@:${SRC}.gz=${TRG}.gz)
	rm -f $@.d/*
	rmdir $@.d

