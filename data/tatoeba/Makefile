#-*-makefile-*-
#----------------------------------------------------------------------
#
# fetch data from the Tatoeba translation challenge
#
#----------------------------------------------------------------------
# USAGE:
#
#   make SRC=deu TRG=eng fetch ............ fetch deu-eng
#   make LANGPAIRS="deu-eng eng-fin" all .. fetch all deu-eng and eng-fin
#   make oellm ............................ fetch OELLM all 561 language pairs
#   make oellm-eng ........................ fetch English-centric OELLM language pairs
#   make PIVOT=fin oellm-pivot ............ fetch Finnish-centric OELLM language pairs
#
# TODO:
#
# * create targets for fetching other language pairs than the ones
#   defined by OELLM (e.g. all supported Tatoeba languages)
#----------------------------------------------------------------------



SHELL := bash

SRC ?= eng
TRG ?= fin

RELEASE := v2023-09-26

## language IDs in the Tatoeba Translation Challenge are sorted alphabetically

SORTED_SRC := $(firstword $(sort ${SRC} ${TRG}))
SORTED_TRG := $(lastword $(sort ${SRC} ${TRG}))
LANGPAIR   := ${SORTED_SRC}-${SORTED_TRG}
LANGPAIRS  ?= ${LANGPAIR}

#----------------------------------------------------------------------
# non-English focus languages for the OpenEuroLLM project
#----------------------------------------------------------------------

OELLM_LANGS := 	deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos isl kat \
		mkd sqi srp_Cyrl

## language IDs used by the Tatoeba translation challenge
## (macro-languages if they exist)

# OELLM_MLANGS = $(sort $(shell iso639 -m ${OELLM_LANGS}))

OELLM_MLANGS := bul cat ces dan deu ell est \
		eus fin fra gle glg hbs hun \
		isl ita kat lav lit mkd mlt \
		nld nor pol por ron slk slv \
		spa sqi swe tur ukr



#----------------------------------------------------------------------
# OELLM language pairs
#----------------------------------------------------------------------


## all language pairs of OELLM languages (+ eng)
## --> 561 language pairs!

OELLM_LANGPAIRS := $(sort $(shell \
  for s in eng ${OELLM_MLANGS}; do \
    for t in eng ${OELLM_MLANGS}; do \
      if [ $$s \< $$t ]; then echo $$s-$$t; fi; \
    done \
  done \
))


## English-centric language pairs

PIVOT_LANG ?= eng

OELLM_PIVOT_LANGPAIRS := $(sort $(shell \
  for t in ${OELLM_MLANGS}; do \
    if [ ${PIVOT_LANG} \< $$t ]; then \
      echo ${PIVOT_LANG}-$$t; \
    else \
      echo $$t-${PIVOT_LANG}; \
    fi; \
  done \
))


#----------------------------------------------------------------------
# fetch all language pairs
#----------------------------------------------------------------------

LANGPAIR_TARGETS := $(patsubst %,data/release/${RELEASE}/%,${LANGPAIRS})

.PHONY: all
all: ${LANGPAIR_TARGETS}
	${MAKE} dev5K

.PHONY: oellm
oellm:
	${MAKE} LANGPAIRS="${OELLM_LANGPAIRS}" all

.PHONY: oellm-pivot
oellm-pivot:
	${MAKE} LANGPAIRS="${OELLM_PIVOT_LANGPAIRS}" all

.PHONY: oellm-eng
oellm-eng:
	${MAKE} PIVOT_LANG=eng LANGPAIRS="${OELLM_PIVOT_LANGPAIRS}" all


#----------------------------------------------------------------------
# fetch a Tatoeba dataset
#----------------------------------------------------------------------

STORAGE := https://object.pouta.csc.fi/Tatoeba-Challenge-${RELEASE}

.PHONY: fetch
fetch: data/release/${RELEASE}/${LANGPAIR}


DEV5K = $(patsubst dev/%,dev5K/%,$(wildcard dev/*.gz))

.PHONY: dev5K
dev5K: ${DEV5K}

## max 5K in devsets!

dev5K/%: dev/%
	@mkdir -p $(dir $@)
	zcat $< | head -5000 | gzip -c > $@

## fetch the data and divide into train/dev/test data
## NOTE: we may have several individual languages under the same macro-language ID!
##       langids contains the individual language IDs

data/release/${RELEASE}/%: %.tar
	tar -xf $<
	@for d in train dev test; do \
	  mkdir -p $$d; \
	  S=`grep "$$d source" $@/langids | cut -f2`; \
	  T=`grep "$$d target" $@/langids | cut -f2`; \
	  if [ `echo "$$S $$T" | tr ' ' "\n" | wc -l` -gt 2 ]; then \
	    for s in $$S; do \
	      for t in $$T; do \
	        echo "extract $$d/$$s-$$t"; \
	        if [ -e $@/$$d.id.gz ]; then \
	          paste <(gzip -cd < $@/$$d.src.gz) <(gzip -cd < $@/$$d.trg.gz) <(gzip -cd < $@/$$d.id.gz) |\
	          grep "	$$s	$$t$$" > $$d/$$s-$$t.tsv; \
	        elif [ -e $@/$$d.id ]; then \
	          paste $$d.src $$d.trg $$d.id | grep "	$$s	$$t$$" > $$d/$$s-$$t.tsv; \
	        fi; \
	        if [ -s $$d/$$s-$$t.tsv ]; then \
	          cut -f1 < $$d/$$s-$$t.tsv | gzip -c > $$d/$$s-$$t.$$s.gz; \
	          cut -f2 < $$d/$$s-$$t.tsv | gzip -c > $$d/$$s-$$t.$$t.gz; \
	          if [ $$d == train ]; then cut -f3 < $$d/$$s-$$t.tsv | gzip -c > $$d/$$s-$$t.corpora.gz; fi; \
	          rm -f $$d/$$s-$$t.tsv; \
	        fi; \
	      done \
	    done; \
	    rm -f $@/$$d.*; \
	  else \
	    mkdir -p $$d; \
	    if [ -e $@/$$d.id.gz ]; then \
	      mv $@/$$d.src.gz $$d/$$S-$$T.$$S.gz; \
	      mv $@/$$d.trg.gz $$d/$$S-$$T.$$T.gz; \
	      gzip -cd $@/$$d.id.gz | cut -f1 | gzip -c > $$d/$$S-$$T.corpora.gz; \
	    elif [ -e $@/$$d.id ]; then \
	      gzip -c < $@/$$d.src > $$d/$$S-$$T.$$S.gz; \
	      gzip -c < $@/$$d.trg > $$d/$$S-$$T.$$T.gz; \
	    fi \
	  fi \
	done


%.tar:
	wget ${STORAGE}/$@
