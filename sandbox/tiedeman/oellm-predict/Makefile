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

PARTSHARED_TASK_ENCODERS  := $(foreach l,${META_LANGS},"$l","all")
PARTSHARED_TASK_DECODERS  := $(foreach l,${META_LANGS},"all","$l")


.PHONY: %.partially-shared
%.partially-shared:
	@${MAKE} -s MODEL_NAME=oellm-predict-partially-shared \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		TASK_ENCODERS='${PARTSHARED_TASK_ENCODERS}' \
		TASK_DECODERS='${PARTSHARED_TASK_DECODERS}' \
	$(basename $@)



CROSS_TASK_IDS      := $(foreach l,${LANGS_NOEN},predict_$l-eng)
CROSS_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l")

.PHONY: %.crosspredict
%.crosspredict:
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

.PHONY: %.predict-translate
%.predict-translate:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)


.PHONY: %.crosspredict-translate
%.crosspredict-translate:
	@${MAKE} -s MODEL_NAME=oellm-crosspredict-translate \
		TASK_IDS="${MT_TASK_IDS} ${TASK_IDS} ${CROSS_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${TASK_ENCODERS} ${CROSS_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA}" \
	$(basename $@)



## text prediction and translate in both directions

.PHONY: %.predict-translate2
%.predict-translate2:
	@${MAKE} -s MODEL_NAME=oellm-predict-translate2 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)


## translate in both directions
## can also do that over all 36 languages!

.PHONY: %.translate2
%.translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.translate2-${NR_LANGS}
%.translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-translate2-${NR_LANGS} \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
	$(basename $@)


## completely shared parameters

.PHONY: %.shared_translate2
%.shared_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.shared_translate2-${NR_LANGS}
%.shared_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_shared-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" ADD_LANGUAGE_TOKEN=true \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_ENCODERS= \
	$(basename $@)


## shared encoder

.PHONY: %.sharedenc_translate2
%.sharedenc_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.sharedenc_translate2-${NR_LANGS}
%.sharedenc_translate2-${NR_LANGS}:
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

.PHONY: %.denoise-translate2
%.denoise-translate2:
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


.PHONY: %.predict-denoise-translate2
%.predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.predict-denoise-translate2-${NR_LANGS}
%.predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm-predict-denoise-translate2 \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_ENCODERS='${TASK_ENCODERS} ${MTXX_TASK_ENCODERS} ${MTEN_TASK_ENCODERS} ${TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
	$(basename $@)



## completely shared parameters

.PHONY: %.shared_predict-denoise-translate2
%.shared_predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.shared_predict-denoise-translate2-${NR_LANGS}
%.shared_predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_shared-predict-denoise-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" ADD_LANGUAGE_TOKEN=true \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		TASK_ENCODERS= \
	$(basename $@)


## shared encoder

.PHONY: %.sharedenc_predict-denoise-translate2
%.sharedenc_predict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.sharedenc_predict-denoise-translate2-${NR_LANGS}
%.sharedenc_predict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_sharedenc-predict-denoise-translate2-${NR_LANGS} \
		DEFAULT_ENCODER="shared" \
		TASK_IDS="${DENOISE_TASK_IDS} ${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS} ${TASK_IDS}" \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA} ${MT_DEVDATA}" \
		TASK_TRANSFORMS="${DENOISE_TRANSFORMS}" \
		TASK_ENCODERS= \
	$(basename $@)




## add cross-lingual prediction



.PHONY: %.crosspredict-denoise-translate2
%.crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

CROSS_TASK_IDS      := $(foreach l,${LANGS_NOEN},predict_$l-eng predict_eng-$l)
CROSS_TASK_ENCODERS := $(foreach l,${META_LANGS_NOEN},"$l" "eng")

.PHONY: %.crosspredict-denoise-translate2-${NR_LANGS}
%.crosspredict-denoise-translate2-${NR_LANGS}:
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


.PHONY: %.3c_crosspredict-denoise-translate2
%.3c_crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.3c_crosspredict-denoise-translate2-${NR_LANGS}
%.3c_crosspredict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3c-crosspredict-denoise-translate2 \
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

.PHONY: %.3Cenc_crosspredict-denoise-translate2
%.3Cenc_crosspredict-denoise-translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.3Cenc_crosspredict-denoise-translate2-${NR_LANGS}
%.3Cenc_crosspredict-denoise-translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3Cenc-crosspredict-denoise-translate2 \
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

.PHONY: %.3Cenc_translate2
%.3Cenc_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.3Cenc_translate2-${NR_LANGS}
%.3Cenc_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_3Cenc-translate2 \
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


## grandparent encoder

.PHONY: %.Genc_translate2
%.Genc_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.Genc_translate2-${NR_LANGS}
%.Genc_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_Genc-translate2 \
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

.PHONY: %.PGAenc_translate2
%.PGAenc_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.PGAenc_translate2-${NR_LANGS}
%.PGAenc_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_PGAenc-translate2 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${PGA_XXEN_TASK_ENCODERS} ${PGA_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=3,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)




.PHONY: %.PGAenc6x6_translate2
%.PGAenc6x6_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.PGAenc6x6_translate2-${NR_LANGS}
%.PGAenc6x6_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_PGAenc6x6-translate2 \
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

.PHONY: %.LPGAenc_translate2
%.LPGAenc_translate2:
	@${MAKE} -s NR_LANGS=36 $@-36

.PHONY: %.LPGAenc_translate2-${NR_LANGS}
%.LPGAenc_translate2-${NR_LANGS}:
	@${MAKE} -s MODEL_NAME=oellm_LPGAenc-translate2 \
		TASK_IDS="${MT_XXEN_TASK_IDS} ${MT_ENXX_TASK_IDS}" \
		TASK_ENCODERS='${PGA_XXEN_TASK_ENCODERS} ${PGA_ENXX_TASK_ENCODERS}' \
		TASK_TRAINDATA="${MT_TRAINDATA} ${MT_TRAINDATA}" \
		TASK_DEVDATA="${MT_DEVDATA} ${MT_DEVDATA}" \
		ENCODER_LAYERS=1,2,3,3 \
		DECODER_LAYERS=3 \
	$(basename $@)
