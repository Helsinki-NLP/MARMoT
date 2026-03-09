

SHELL := bash

include ../../tools/slurMake/slurm.mk


CORPUS ?= OpenSubtitles

# SRC ?= eng
# TRG ?= fin

SRC ?= $(firstword $(subst -, ,${LANGPAIR}))
TRG ?= $(lastword $(subst -, ,${LANGPAIR}))

SRC2 := $(shell iso639 -2 -n ${SRC})
TRG2 := $(shell iso639 -2 -n ${TRG})


ifndef LANGPAIR
  LANGPAIR := ${SRC}-${TRG}
endif

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



OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

## all OELLM language pairs that exist in OpenSubtitles2024

OPENSUBS_OELLM_LANGPAIRS := bos-cat bos-ces bos-dan bos-deu bos-ell bos-eng bos-est bos-eus bos-fin bos-fra bos-gle bos-glg bos-hrv bos-hun bos-isl bos-ita bos-kat bos-lav bos-lit bos-mkd bos-nld bos-nno bos-pol bos-por bos-ron bos-slk bos-slv bos-spa bos-sqi bos-srp bos-swe bos-tur bos-ukr bul-bos bul-cat bul-ces bul-dan bul-deu bul-ell bul-eng bul-est bul-eus bul-fin bul-fra bul-gle bul-glg bul-hrv bul-hun bul-isl bul-ita bul-kat bul-lav bul-lit bul-mkd bul-nld bul-nno bul-pol bul-por bul-ron bul-slk bul-slv bul-spa bul-sqi bul-srp bul-swe bul-tur bul-ukr cat-ces cat-dan cat-deu cat-ell cat-eng cat-est cat-eus cat-fin cat-fra cat-glg cat-hrv cat-hun cat-isl cat-ita cat-kat cat-lav cat-lit cat-mkd cat-nld cat-pol cat-por cat-ron cat-slk cat-slv cat-spa cat-sqi cat-srp cat-swe cat-tur cat-ukr ces-dan ces-deu ces-ell ces-eng ces-est ces-eus ces-fin ces-fra ces-gle ces-glg ces-hrv ces-hun ces-isl ces-ita ces-kat ces-lav ces-lit ces-mkd ces-nld ces-nno ces-pol ces-por ces-ron ces-slk ces-slv ces-spa ces-sqi ces-srp ces-swe ces-tur ces-ukr dan-deu dan-ell dan-eng dan-est dan-eus dan-fin dan-fra dan-gle dan-glg dan-hrv dan-hun dan-isl dan-ita dan-kat dan-lav dan-lit dan-mkd dan-nld dan-nno dan-pol dan-por dan-ron dan-slk dan-slv dan-spa dan-sqi dan-srp dan-swe dan-tur dan-ukr deu-ell deu-eng deu-est deu-eus deu-fin deu-fra deu-gle deu-glg deu-hrv deu-hun deu-isl deu-ita deu-kat deu-lav deu-lit deu-mkd deu-nld deu-nno deu-pol deu-por deu-ron deu-slk deu-slv deu-spa deu-sqi deu-srp deu-swe deu-tur deu-ukr ell-eng ell-est ell-eus ell-fin ell-fra ell-gle ell-glg ell-hrv ell-hun ell-isl ell-ita ell-kat ell-lav ell-lit ell-mkd ell-nld ell-nno ell-pol ell-por ell-ron ell-slk ell-slv ell-spa ell-sqi ell-srp ell-swe ell-tur ell-ukr eng-est eng-eus eng-fin eng-fra eng-gle eng-glg eng-hrv eng-hun eng-isl eng-ita eng-kat eng-lav eng-lit eng-mkd eng-nld eng-nno eng-pol eng-por eng-ron eng-slk eng-slv eng-spa eng-sqi eng-srp eng-swe eng-tur eng-ukr est-eus est-fin est-fra est-gle est-glg est-hrv est-hun est-isl est-ita est-kat est-lav est-lit est-mkd est-nld est-nno est-pol est-por est-ron est-slk est-slv est-sqi est-srp est-swe est-tur est-ukr eus-fin eus-fra eus-glg eus-hrv eus-hun eus-isl eus-ita eus-kat eus-lav eus-lit eus-mkd eus-nld eus-pol eus-por eus-ron eus-slk eus-slv eus-sqi eus-srp eus-swe eus-tur eus-ukr fin-fra fin-gle fin-glg fin-hrv fin-hun fin-isl fin-ita fin-kat fin-lav fin-lit fin-mkd fin-nld fin-nno fin-pol fin-por fin-ron fin-slk fin-slv fin-sqi fin-srp fin-swe fin-tur fin-ukr fra-gle fra-glg fra-hrv fra-hun fra-isl fra-ita fra-kat fra-lav fra-lit fra-mkd fra-nld fra-nno fra-pol fra-por fra-ron fra-slk fra-slv fra-sqi fra-srp fra-swe fra-tur fra-ukr gle-hrv gle-hun gle-isl gle-ita gle-lav gle-lit gle-mkd gle-nld gle-pol gle-por gle-ron gle-slk gle-slv gle-srp gle-swe gle-tur gle-ukr glg-hrv glg-hun glg-isl glg-ita glg-kat glg-lav glg-lit glg-mkd glg-nld glg-pol glg-por glg-ron glg-slk glg-slv glg-sqi glg-srp glg-swe glg-tur glg-ukr hrv-hun hrv-isl hrv-ita hrv-kat hrv-lav hrv-lit hrv-mkd hrv-nld hrv-nno hrv-pol hrv-por hrv-ron hrv-slk hrv-slv hrv-sqi hrv-srp hrv-swe hrv-tur hrv-ukr hun-isl hun-ita hun-kat hun-lav hun-lit hun-mkd hun-nld hun-nno hun-pol hun-por hun-ron hun-slk hun-slv hun-sqi hun-srp hun-swe hun-tur hun-ukr isl-ita isl-kat isl-lav isl-lit isl-mkd isl-nld isl-nno isl-pol isl-por isl-ron isl-slk isl-slv isl-sqi isl-srp isl-swe isl-tur isl-ukr ita-kat ita-lav ita-lit ita-mkd ita-nld ita-nno ita-pol ita-por ita-ron ita-slk ita-slv ita-sqi ita-srp ita-swe ita-tur ita-ukr kat-lav kat-lit kat-mkd kat-nld kat-pol kat-por kat-ron kat-slk kat-slv kat-sqi kat-srp kat-swe kat-tur kat-ukr lav-mkd lav-nld lav-pol lav-por lav-ron lav-slk lav-slv lav-sqi lav-srp lav-swe lav-tur lav-ukr lit-lav lit-mkd lit-nld lit-pol lit-por lit-ron lit-slk lit-slv lit-sqi lit-srp lit-swe lit-tur lit-ukr mkd-nld mkd-pol mkd-por mkd-ron mkd-slk mkd-slv mkd-sqi mkd-srp mkd-swe mkd-tur mkd-ukr nld-nno nld-pol nld-por nld-ron nld-slk nld-slv nld-sqi nld-srp nld-swe nld-tur nld-ukr nno-pol nno-por nno-ron nno-slk nno-slv nno-srp nno-swe nno-tur pol-por pol-ron pol-slk pol-slv pol-sqi pol-srp pol-swe pol-tur pol-ukr por-ron por-slk por-slv por-sqi por-srp por-swe por-tur por-ukr ron-slk ron-slv ron-sqi ron-srp ron-swe ron-tur ron-ukr slk-slv slk-sqi slk-srp slk-swe slk-tur slk-ukr slv-sqi slv-srp slv-swe slv-tur slv-ukr spa-est spa-eus spa-fin spa-fra spa-gle spa-glg spa-hrv spa-hun spa-isl spa-ita spa-kat spa-lav spa-lit spa-mkd spa-nld spa-nno spa-pol spa-por spa-ron spa-slk spa-slv spa-sqi spa-srp spa-swe spa-tur spa-ukr sqi-srp sqi-swe sqi-tur sqi-ukr srp-swe srp-tur srp-ukr swe-tur swe-ukr tur-ukr

ifndef OPENSUBS_OELLM_LANGPAIRS

  OELLM_LANGS2 := $(shell iso639 -2 -n ${OELLM_LANGS})
  ALL_OELLM_LANGPAIRS2 := $(foreach s,${OELLM_LANGS2},$(foreach t,${OELLM_LANGS2},$s-$t))
  OPENSUBS_OELLM_LANGPAIRS2 := $(filter $(patsubst %.txt.zip,%,$(notdir $(shell opus_get -l -d OpenSubtitles -r v2024 -p moses | cut -f2 -d:))),${ALL_OELLM_LANGPAIRS2})

  OPENSUBS_OELLM_LANGPAIRS := ${shell iso639 -n -3 -p ${OPENSUBS_OELLM_LANGPAIRS2}}

endif


opensubs:
	for l in ${OPENSUBS_OELLM_LANGPAIRS}; do \
	    ${MAKE} CORPUS=OpenSubtitles RELEASE=v2024 LANGPAIR=$$l all; \
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

