#-*-makefile-*-
##-----------------------------------------------------------
## testing multi-node job
##
##   the job fails with some strange error message about
##   'ValueError: ProcessGroupNCCL is only supported with GPUs, no GPUs found!'
##
##   however, manually starting the job with the same slurm script
##   and sbatch from command-line seems to work --> WHY?
##-----------------------------------------------------------

MODEL_NAME := oellm-predict

# 37 OpenEuroLLM languages
# --> right now it's problematic to have a number of tasks that
#     does not distribute well over nodes with one task per GPU
# --> need to remove 4 languages, let's leave out nno,mkd,bos,kat

OELLM_LANGS := 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr


## trying to make all kinds of language and language pairs subsets to meet our requirements
##
## 36_LANGS ............ 36 OELLM languages (leaving out bos)
## 32_LANGS ............ 32 OELLM languages (leaving out bos kat mkd nno srp_Cyrl)
##
## 36_LANGS_NOEN ....... 36 OELLM languages (leaving out eng)
## 32_LANGS_NOEN ....... 32 OELLM languages (leaving out eng bos kat mkd nno)

36_LANGS_NOEN := $(filter-out eng,${OELLM_LANGS})
32_LANGS_NOEN := $(filter-out eng bos kat mkd nno,${OELLM_LANGS})

36_LANGS := $(filter-out bos,${OELLM_LANGS})
32_LANGS := $(filter-out bos kat mkd nno srp_Cyrl,${OELLM_LANGS})


NR_LANGS ?= 32

ifeq (${NR_LANGS},36)
  LANGS         ?= ${36_LANGS}
  LANGS_NOEN    ?= ${36_LANGS_NOEN}
else
  LANGS         ?= ${32_LANGS}
  LANGS_NOEN    ?= ${32_LANGS_NOEN}
endif

META_LANGS       := $(shell iso639 -m ${LANGS} 2>/dev/null)
META_LANGS_NOEN  := $(shell iso639 -m ${LANGS_NOEN} 2>/dev/null)
LANG_GROUPS      := $(shell langgroup -p ${META_LANGS} 2>/dev/null)
LANG_GROUPS_NOEN := $(shell langgroup -p ${META_LANGS_NOEN} 2>/dev/null)

LANG_PARENTS      := $(LANG_GROUPS)
LANG_PARENTS_NOEN := $(LANG_GROUPS_NOEN)

LANG_GRANDPARENTS      := $(shell langgroup -p ${LANG_PARENTS} 2>/dev/null)
LANG_GRANDPARENTS_NOEN := $(shell langgroup -p ${LANG_PARENTS_NOEN} 2>/dev/null)



TRANSLATE_TRAIN := multisynt/train/len1024
TRANSLATE_DEV   := flores200/dev
PREDICT_TRAIN   := multisynt/textpredict/train/len1024
PREDICT_DEV     := multisynt/textpredict/dev/len1024

TRAINDATA_BASENAME := *
DEVDATA_BASENAME   := *
TRAINDATA          := ${PREDICT_TRAIN}
DEVDATA            := ${PREDICT_DEV}
MAX_SEQ_LENGTH     := 1024
KEEP_CHECKPOINTS   := 1

SKIP_SAME_LANGUAGE_VALID_TASKS := 0


## tasks for predicting the next sentences
## task encoders are shared across macro-languages!

TASK_IDS      := $(foreach l,${LANGS},predict_$l-$l)
TASK_ENCODERS := $(foreach l,${META_LANGS},"$l")

include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt


.PHONY: %.oellm-predict
%.oellm-predict:
	${MAKE} -s $(basename $@)


.PHONY: %.oellm_12x12-predict
%.oellm_12x12-predict:
	@${MAKE} -s MODEL_NAME=oellm_12x12-predict \
		ENCODER_LAYERS=12 \
		DECODER_LAYERS=12 \
	$(basename $@)




PARTSHARED_TASK_ENCODERS  := $(foreach l,${META_LANGS},"$l","all")
PARTSHARED_TASK_DECODERS  := $(foreach l,${META_LANGS},"all","$l")


.PHONY: %.oellm-predict-partially-shared
%.oellm-predict-partially-shared:
	@${MAKE} -s MODEL_NAME=oellm-predict-partially-shared \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		TASK_ENCODERS='${PARTSHARED_TASK_ENCODERS}' \
		TASK_DECODERS='${PARTSHARED_TASK_DECODERS}' \
	$(basename $@)



CROSS_TASK_IDS      := $(foreach l,${LANGS_NOEN},predict_$l-eng)
CROSS_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l")

.PHONY: %.oellm-crosspredict
%.oellm-crosspredict:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict \
		TASK_IDS="${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${TASK_ENCODERS}' \
	$(basename $@)



## add translation tasks

MT_XXEN_TASK_IDS   := $(foreach l,${LANGS_NOEN},mt_$l-eng)
MT_ENXX_TASK_IDS   := $(foreach l,${LANGS_NOEN},mt_eng-$l)
MTXX_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l")
MTEN_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"eng")

MT_TRAINDATA := $(foreach l,${LANGS_NOEN},${TRANSLATE_TRAIN})
MT_DEVDATA   := $(foreach l,${LANGS_NOEN},${TRANSLATE_DEV})

.PHONY: %.oellm-predict-translate
%.oellm-predict-translate:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)


.PHONY: %.oellm-crosspredict-translate
%.oellm-crosspredict-translate:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict-translate \
		TASK_IDS="${MT_TASK_IDS} ${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${TASK_ENCODERS} ${CROSS_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)



## text prediction and translate in both directions

.PHONY: %.oellm-predict-translate2
%.oellm-predict-translate2:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate2 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)


## translate in both directions
## can also do that over all 36 languages!

.PHONY: %.oellm-translate2
%.oellm-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm-translate2-${NR_LANGS}
%.oellm-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)



## translate in both directions
## can also do that over all 36 languages!

.PHONY: %.oellm_12x12-translate2
%.oellm_12x12-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_12x12-translate2-${NR_LANGS}
%.oellm_12x12-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_12x12-translate2-${NR_LANGS} \
		ENCODER_LAYERS=12 DECODER_LAYERS=12 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)


## do the 12x12 model with fewer validation tasks

.PHONY: %.oellm_12x12-translate2-halfdev
%.oellm_12x12-translate2-halfdev:
	@${MAKE} -s NR_LANGS=36 $@-36

NODEV_DEVDATA   := $(foreach l,${LANGS_NOEN},nodev)

.PHONY: %.oellm_12x12-translate2-halfdev-${NR_LANGS}
%.oellm_12x12-translate2-halfdev-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_12x12-translate2-halfdev-${NR_LANGS} \
		ENCODER_LAYERS=12 DECODER_LAYERS=12 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${NODEV_DEVDATA}" \
	$(basename $@)




## completely shared parameters

.PHONY: %.oellm_shared-translate2
%.oellm_shared-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_shared-translate2-${NR_LANGS}
%.oellm_shared-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_shared-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" ADD_LANGUAGE_TOKEN=true \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_ENCODERS= \
	$(basename $@)


## shared encoder

.PHONY: %.oellm_sharedenc-translate2
%.oellm_sharedenc-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_sharedenc-translate2-${NR_LANGS}
%.oellm_sharedenc-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_sharedenc-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_ENCODERS= \
	$(basename $@)




## denoise and translate in both directions

DENOISE_TASK_IDS   := $(foreach l,${LANGS},denoise_$l-$l)
DENOISE_TRANSFORMS := $(foreach l,${LANGS},filtertoolong,denoising)

.PHONY: %.oellm-denoise-translate2
%.oellm-denoise-translate2:
	@${MAKE} -s MODEL_NAME=oellm-denoise-translate2 \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
	$(basename $@)



## add denoising tasks
##
## NOTE: here we can use all OELLM languages as we have enough tasks
##       to distribute evenly on compute nodes with 8 GPUs each


.PHONY: %.oellm-predict-denoise-translate2
%.oellm-predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm-predict-denoise-translate2-${NR_LANGS}
%.oellm-predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-predict-denoise-translate2 \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
	$(basename $@)



## completely shared parameters

.PHONY: %.oellm_shared-predict-denoise-translate2
%.oellm_shared-predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_shared-predict-denoise-translate2-${NR_LANGS}
%.oellm_shared-predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_shared-predict-denoise-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" ADD_LANGUAGE_TOKEN=true \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		TASK_ENCODERS= \
	$(basename $@)


## shared encoder

.PHONY: %.oellm_sharedenc-predict-denoise-translate2
%.sharedenc_predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_sharedenc-predict-denoise-translate2-${NR_LANGS}
%.oellm_sharedenc-predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_sharedenc-predict-denoise-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		TASK_ENCODERS= \
	$(basename $@)




## add cross-lingual prediction

.PHONY: %.oellm-crosspredict-denoise-translate2
%.oellm-crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

CROSS_TASK_IDS      := $(foreach l,${LANGS_NOEN},predict_$l-eng predict_eng-$l)
CROSS_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l" "eng")

.PHONY: %.oellm-crosspredict-denoise-translate2-${NR_LANGS}
%.oellm-crosspredict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict-denoise-translate2 \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS} ${TASK_ENCODERS} ${CROSS_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
	$(basename $@)




##--------------------------------------------------
## setups with partially shared components
##--------------------------------------------------

LANG_NRS      := $(shell seq $(words ${LANGS}))
LANG_NOEN_NRS := $(shell seq $(words ${LANGS}))

3C_MONO_TASK_ENCODERS := $(foreach l,${LANG_NRS},"$(word $l,${META_LANGS})","$(word $l,${LANG_GROUPS})","all")
3C_XXEN_TASK_ENCODERS := $(foreach l,${LANG_NRS},"$(word $l,${META_LANGS_NOEN})","$(word $l,${LANG_GROUPS_NOEN})","all")
3C_ENXX_TASK_ENCODERS := $(foreach l,${LANG_NRS},"eng","gmw","all")

3C_MONO_TASK_DECODERS := $(foreach l,${LANG_NRS},"all,","$(word $l,${LANG_GROUPS})","$(word $l,${LANGS})")
3C_ENXX_TASK_DECODERS := $(foreach l,${LANG_NRS},"all","$(word $l,${LANG_GROUPS_NOEN})","$(word $l,${LANGS_NOEN})")
3C_XXEN_TASK_DECODERS := $(foreach l,${LANG_NRS},"all","gmw","eng")

CROSS_XXEN_TASK_IDS   := $(foreach l,${LANGS_NOEN},predict_$l-eng)
CROSS_ENXX_TASK_IDS   := $(foreach l,${LANGS_NOEN},predict_eng-$l)


.PHONY: %.oellm_3c-crosspredict-denoise-translate2
%.oellm_3c-crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_3c-crosspredict-denoise-translate2-${NR_LANGS}
%.oellm_3c-crosspredict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3c-crosspredict-denoise-translate2-${NR_LANGS} \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS} ${CROSS_XXEN_TASK_IDS} ${CROSS_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${3C_MONO_TASK_ENCODERS} ${3C_XXEN_TASK_ENCODERS} ${3C_ENXX_TASK_ENCODERS} ${3C_MONO_TASK_ENCODERS} ${3C_XXEN_TASK_ENCODERS} ${3C_ENXX_TASK_ENCODERS}' \
		TASK_DECODERS='${3C_MONO_TASK_DECODERS} ${3C_XXEN_TASK_DECODERS} ${3C_ENXX_TASK_DECODERS} ${3C_MONO_TASK_DECODERS} ${3C_XXEN_TASK_DECODERS} ${3C_ENXX_TASK_DECODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3,3,3 \
	$(basename $@)




## 3-component encoder and language-specific 3-layer decoders

.PHONY: %.oellm_3Cenc-crosspredict-denoise-translate2
%.oellm-3Cenc-crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_3Cenc-crosspredict-denoise-translate2-${NR_LANGS}
%.oellm_3Cenc-crosspredict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3Cenc-crosspredict-denoise-translate2-${NR_LANGS} \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS} ${CROSS_XXEN_TASK_IDS} ${CROSS_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${3C_MONO_TASK_ENCODERS} ${3C_XXEN_TASK_ENCODERS} ${3C_ENXX_TASK_ENCODERS} ${3C_MONO_TASK_ENCODERS} ${3C_XXEN_TASK_ENCODERS} ${3C_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)



## 3-component encoder and language-specific 3-layer decoders
## translation only

.PHONY: %.oellm_3Cenc-translate2
%.oellm_3Cenc-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_3Cenc-translate2-${NR_LANGS}
%.oellm_3Cenc-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3Cenc-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${3C_XXEN_TASK_ENCODERS} ${3C_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)





P_XXEN_TASK_ENCODERS := $(foreach l,${LANG_PARENTS_NOEN},"$l")
P_ENXX_TASK_ENCODERS := $(foreach l,${LANG_PARENTS_NOEN},"gmw")

G_XXEN_TASK_ENCODERS := $(foreach l,${LANG_GRANDPARENTS_NOEN},"$l")
G_ENXX_TASK_ENCODERS := $(foreach l,${LANG_GRANDPARENTS_NOEN},"gem")



## grandparent encoder 6x6

.PHONY: %.oellm_Genc6x6-translate2
%.oellm_Genc6x6_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_Genc6x6-translate2-${NR_LANGS}
%.oellm_Genc6x6-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_Genc6x6-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${G_XXEN_TASK_ENCODERS} ${G_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)



## grandparent encoder 9x3

.PHONY: %.oellm_Genc-translate2
%.oellm_Genc-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_Genc-translate2-${NR_LANGS}
%.oellm_Genc-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_Genc-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${G_XXEN_TASK_ENCODERS} ${G_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=3 \
	$(basename $@)


## parent-grandparent-all encoder

PGA_XXEN_TASK_ENCODERS := $(foreach l,${LANG_NRS},"$(word $l,${LANG_PARENTS_NOEN})","$(word $l,${LANG_GRANDPARENTS_NOEN})","all")
PGA_ENXX_TASK_ENCODERS := $(foreach l,${LANG_NRS},"gmw","gem","all")

.PHONY: %.oellm_PGAenc-translate2
%.oellm_PGAenc-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_PGAenc-translate2-${NR_LANGS}
%.oellm_PGAenc-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_PGAenc-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${PGA_XXEN_TASK_ENCODERS} ${PGA_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)



.PHONY: %.oellm_PGAenc6x6-translate2
%.oellm_PGAenc6x6-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_PGAenc6x6-translate2-${NR_LANGS}
%.oellm_PGAenc6x6-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_PGAenc6x6-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${PGA_XXEN_TASK_ENCODERS} ${PGA_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=2,2,2 \
		DECODER_LAYERS=6 \
	$(basename $@)





## language-parent-grandparent-all encoder

LPGA_XXEN_TASK_ENCODERS := $(foreach l,${LANG_NRS},"$(word $l,${META_LANGS_NOEN})","$(word $l,${LANG_PARENTS_NOEN})","$(word $l,${LANG_GRANDPARENTS_NOEN})","all")
LPGA_ENXX_TASK_ENCODERS := $(foreach l,${LANG_NRS},"eng","gmw","gem","all")

.PHONY: %.oellm_LPGAenc-translate2
%.oellm_LPGAenc-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.oellm_LPGAenc-translate2-${NR_LANGS}
%.oellm_LPGAenc-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_LPGAenc-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${PGA_XXEN_TASK_ENCODERS} ${PGA_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=1,2,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)



## set languages to 36 languages instead of 32

ifneq (${NR_LANGS},36)
.PHONY: %-translate2-36
%-translate2-36:
	@${MAKE} -s NR_LANGS=36 $@
endif
