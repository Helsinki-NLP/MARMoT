

# INSTRUCT_LANGPAIRS := ces-eng deu-eng eng-ces eng-deu eng-eng eng-fin eng-fra eng-ron fin-eng fra-eng ron-eng


INSTRUCT_LANGPAIRS := bul-bul bul-ell bul-eng cat-cat cat-eng ces-eng deu-deu deu-eng deu-fra deu-spa eng-bul eng-cat eng-ces eng-deu eng-eng eng-fin eng-fra eng-glg eng-hrv eng-ita eng-pol eng-por eng-ron eng-spa eng-swe eng-tur est-eng fin-eng fra-deu fra-eng fra-fra fra-slk fra-spa glg-eng glg-ita glg-pol glg-por glg-spa hrv-eng hrv-hrv ita-eng ita-glg ita-ita ita-pol ita-por ita-spa nld-eng nld-nld nld-por pol-eng pol-glg pol-ita pol-por pol-spa por-eng por-glg por-ita por-pol por-spa ron-eng spa-deu spa-eng spa-fra spa-glg spa-ita spa-lit spa-pol spa-por spa-spa swe-eng tur-eng

TASK_IDS           := $(patsubst %,instruct_%,${INSTRUCT_LANGPAIRS})

## data directories

TRAINDATA          := instruct/train
TRAINDATA_BASENAME := {langpair}.data

DEVDATA            := instruct/dev
DEVDATA_BASENAME   := {langpair}.data


# vocabularies / tokenizers

VOCAB := tatoeba_hplt_multisynt


## very big model architecture

MODEL_ARCHITECTURE := transformer-xl

## set the encoder to be shared among all langages

ENCODER         := "{lang}","all"
ENCODER_LAYERS  := 6,6


NR_OF_NODES                 := 1
USE_DATASIZE_AS_TASK_WEIGHT := 1
SAMPLING_TEMP               := 2



PRETRAINED_MODEL := ../predict-halfshared-xl/mammoth




include ../../make/marmot.mk

info:
	@echo $(words ${TASK_IDS})

