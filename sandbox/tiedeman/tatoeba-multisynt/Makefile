


TATOEBA_RELEASE_URL := https://raw.githubusercontent.com/Helsinki-NLP/Tatoeba-Challenge/refs/heads/master/data/release
TATOEBA_RELEASE := v2023-09-26

HIGHEST_RESOURCE := released-bitexts-highest.txt
HIGHER_RESOURCE  := released-bitexts-higher.txt
MEDIUM_RESOURCE  := released-bitexts-medium.txt

TC_BIGGER_THAN_1G := afr-eng ara-deu ara-eng ara-fra ara-ita ara-pol ara-rus ara-spa ara-tur aze_Latn-eng bel-eng bel-rus ben-eng bul-deu bul-eng bul-fra bul-ita bul-rus bul-spa cat-eng cat-spa ces-deu ces-eng ces-fra ces-hun ces-ita ces-pol ces-rus ces-slv ces-spa dan-deu dan-eng dan-fin dan-fra dan-hun dan-ita dan-nld dan-nor dan-por dan-spa dan-swe deu-ell deu-eng deu-est deu-fin deu-fra deu-hun deu-ita deu-lav deu-lit deu-msa_Latn deu-nld deu-nor deu-pol deu-por deu-ron deu-rus deu-slv deu-spa deu-swe deu-tur ell-eng ell-fra ell-ita ell-nld ell-por ell-rus ell-spa ell-swe ell-tur eng-bos eng-epo eng-est eng-fas eng-fin eng-fra eng-heb eng-hin eng-hrv eng-hun eng-ita eng-jpn eng-kaz_Cyrl eng-kor eng-lav eng-lit eng-mal eng-mar eng-msa_Latn eng-nld eng-nor eng-pol eng-por eng-ron eng-rus eng-slk eng-slv eng-spa eng-sqi eng-swe eng-tam eng-tel eng-tgl_Latn eng-tur eng-ukr eng-urd eng-vie eng-zho_Hans est-fin fin-fra fin-hun fin-ita fin-nld fin-pol fin-por fin-spa fin-swe fra-hun fra-ita fra-msa_Latn fra-nld fra-nor fra-pol fra-por fra-ron fra-rus fra-slv fra-spa fra-swe fra-tur fra-zho_Hans glg-por glg-spa heb-por heb-spa hun-ita hun-nld hun-pol hun-por hun-rus hun-spa hun-swe ita-lit ita-nld ita-nor ita-pol ita-por ita-ron ita-rus ita-spa ita-swe ita-tur lit-pol lit-spa msa_Latn-spa nld-nor nld-pol nld-por nld-ron nld-rus nld-spa nld-tur nor-por nor-spa nor-swe pol-por pol-ron pol-rus pol-spa pol-swe pol-tur por-ron por-rus por-spa por-swe por-tur ron-spa rus-spa rus-swe rus-tur rus-ukr rus-zho_Hans spa-swe spa-tur spa-vie spa-zho_Hans


OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

OELLM_LANGS_NOEN := $(filter-out eng,${OELLM_LANGS})





## translation tasks, tatoeba challenge and oellm-multisynt (altogether 444 tasks)

reverse = $(lastword $(subst -, ,$(1)))-$(firstword $(subst -, ,$(1)))

DOCMT_TASKS1 := $(foreach l,${OELLM_LANGS_NOEN},$l-eng)
DOCMT_TASKS2 := $(foreach l,${DOCMT_TASKS1},$(call reverse,$l))
DOCMT_TASKS  := $(patsubst %,mt_%,${DOCMT_TASKS1} ${DOCMT_TASKS2})

TCMT_TASKS1  := ${TC_BIGGER_THAN_1G}
TCMT_TASKS2  := $(foreach l,${TCMT_TASKS1},$(call reverse,$l))
TCMT_TASKS   := $(patsubst %,tc_%,${TCMT_TASKS1} ${TCMT_TASKS2})

MT_TASKS     := ${DOCMT_TASKS} ${TCMT_TASKS}


## text-prediction tasks (36 languages, leave our Bosnian)

PREDICT_LANGS := $(filter-out bos,${OELLM_LANGS})
PREDICT_TASKS := $(foreach l,${PREDICT_LANGS},predict_$l-$l)


## meta-languages are used in task encoders

srclang = $(word 2,$(subst _, ,$(subst -, ,$(1))))

MT_SRCLANGS           := $(foreach l,${MT_TASKS},$(call srclang,$l))
PREDICT_SRCLANGS      := $(foreach l,${PREDICT_TASKS},$(call srclang,$l))

MT_META_SRCLANGS      := $(shell iso639 -m ${MT_SRCLANGS} 2>/dev/null)
PREDICT_META_SRCLANGS := $(shell iso639 -m ${PREDICT_SRCLANGS} 2>/dev/null)

MT_TASK_ENCODERS      := $(foreach l,${MT_META_SRCLANGS},"$l")
PREDICT_TASK_ENCODERS := $(foreach l,${PREDICT_META_SRCLANGS},"$l")


## data directories

TRANSLATE_TRAIN_MS := multisynt/train/len1024
TRANSLATE_TRAIN_TC := tatoeba/train
TRANSLATE_DEV      := flores200/dev
PREDICT_TRAIN      := multisynt/textpredict/train/len1024
PREDICT_DEV        := multisynt/textpredict/dev/len1024

MT_TRAINDATA      := $(foreach l,${DOCMT_TASKS},${TRANSLATE_TRAIN_MS}) $(foreach l,${TCMT_TASKS},${TRANSLATE_TRAIN_TC})
MT_DEVDATA        := $(foreach l,${MT_TASKS},${TRANSLATE_DEV})
PREDICT_TRAINDATA := $(foreach l,${PREDICT_TASKS},${PREDICT_TRAIN})
PREDICT_DEVDATA   := $(foreach l,${PREDICT_TASKS},${PREDICT_DEV})



## final model parameters

MODEL_NAME := mammoth-t5

DEVDATA_BASENAME               := *
MAX_SEQ_LENGTH                 := 1024
KEEP_CHECKPOINTS               := 1
SKIP_SAME_LANGUAGE_VALID_TASKS := 0

TASK_IDS       := ${PREDICT_TASKS} ${MT_TASKS}
TASK_ENCODERS  := ${PREDICT_TASK_ENCODERS} ${MT_TASK_ENCODERS}
TASK_TRAINDATA := ${PREDICT_TRAINDATA} ${MT_TRAINDATA}
TASK_DEVDATA   := ${PREDICT_DEVDATA} ${MT_DEVDATA}



include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt




## tatoeba data subsets

SELECTED_RESOURCES := ${HIGHEST_RESOURCE} ${HIGHER_RESOURCE} ${MEDIUM_RESOURCE}

${SELECTED_RESOURCES}:
	wget -O $@ -q ${TATOEBA_RELEASE_URL}/${TATOEBA_RELEASE}/$@

selected-langpairs.txt: ${SELECTED_RESOURCES}
	grep '^eng-' $^ | cut -f1 > $@
	grep '-eng	' $^ | cut -f1 >> $@
