
# MODEL_NAME := textpredict
# TASK_IDS   := predict_eng-eng

TRANSLATE_TRAIN := multisynt/train/len1024
TRANSLATE_DEV   := multisynt/dev/len1024
PREDICT_TRAIN   := multisynt/textpredict/train/len1024
PREDICT_DEV     := multisynt/textpredict/dev/len1024

TRAINDATA_BASENAME := *
DEVDATA_BASENAME   := *
TRAINDATA          := ${TRANSLATE_TRAIN}
MAX_SEQ_LENGTH     := 1024

# SKIP_SAME_LANGUAGE_EVAL_TASKS := 0

include ../../../make/marmot.mk

VOCAB_DIR := ${PROJECT_DIR}/tokenizer/tatoeba_hplt_multisynt


.PHONY: %.eng
%.eng:
	@${MAKE} -s MODEL_NAME=english \
		TASK_IDS=predict_eng-eng \
		TRAINDATA=${PREDICT_TRAIN} \
		DEVDATA=${PREDICT_DEV} \
	$(basename $@)

.PHONY: %.swe
%.swe:
	@${MAKE} -s MODEL_NAME=swedish \
		TASK_IDS=predict_swe-swe \
		TRAINDATA=${PREDICT_TRAIN} \
		DEVDATA=${PREDICT_DEV} \
	$(basename $@)



.PHONY: %.finland-predict
%.finland-predict:
	@${MAKE} -s MODEL_NAME=finland-predict \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe" \
		TRAINDATA=${PREDICT_TRAIN} \
		DEVDATA=${PREDICT_DEV} \
	$(basename $@)


CROSS_TASKS := 	predict_eng-eng predict_fin-fin predict_swe-swe \
		predict_eng-fin predict_fin-eng predict_eng-swe predict_swe-fin predict_fin-swe

.PHONY: %.finland-crosspredict
%.finland-crosspredict:
	@${MAKE} -s MODEL_NAME=finland-crosspredict \
		TASK_IDS="${CROSS_TASKS}" \
		TRAINDATA=${PREDICT_TRAIN} \
		DEVDATA=${PREDICT_DEV} \
	$(basename $@)


CROSSTRANS_TASKS :=  predict_eng-eng predict_fin-fin predict_swe-swe \
		predict_eng-fin predict_fin-eng predict_swe-fin predict_fin-swe predict_eng-swe predict_swe-eng \
		mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng mt_eng-swe

CROSSTRANS_TRAINDATA := ${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN} \
			${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN} \
			${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}
CROSSTRANS_DEVDATA   := ${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV} \
			${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV} \
			${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}

BT_TRAIN_SRC  := ${DATA_DIR}/synthetic/Wiki/fin-eng.eng.gz
BT_TRAIN_TRG  := ${DATA_DIR}/synthetic/Wiki/fin-eng.fin.gz


.PHONY: %.finland-crosspredict-translate
%.finland-crosspredict-translate:
	@${MAKE} -s MODEL_NAME=finland-crosspredict-translate \
		TASK_IDS="wiki_eng-fin ${CROSSTRANS_TASKS}" \
		TASK_TRAINDATA="${TRANSLATE_TRAIN} ${CROSSTRANS_TRAINDATA}" \
		TASK_DEVDATA="${TRANSLATE_DEV} ${CROSSTRANS_DEVDATA}" \
		TASK_TRAINDATA_SRCS="${BT_TRAIN_SRC}" \
		TASK_TRAINDATA_TRGS="${BT_TRAIN_TRG}" \
	$(basename $@)





## include denoising

.PHONY: %.crosspredict-translate
%.crosspredict-translate:
	@${MAKE} -s MODEL_NAME=crosspredict-translate-denoise \
		TASK_IDS="denoise_fin-fin ${CROSSTRANS_TASKS}" \
		TASK_TRAINDATA="${TRANSLATE_TRAIN} ${CROSSTRANS_TRAINDATA}" \
		TASK_DEVDATA="${TRANSLATE_TRAIN} ${CROSSTRANS_DEVDATA}" \
		TASK_TRANSFORMS="denoising" \
	$(basename $@)



## text predict and translate
## leave out one translation task (eng-swe) to fit on one node with one task per GPU)

.PHONY: %.finland-predict-translate
%.finland-predict-translate:
	@${MAKE} -s MODEL_NAME=finland-predict-translate \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng" \
		TASK_TRAINDATA="${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}" \
		TASK_DEVDATA="${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}" \
	$(basename $@)

.PHONY: %.finland-predict-translate-shared
%.finland-predict-translate-shared:
	@${MAKE} -s MODEL_NAME=finland-predict-translate-shared \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng" \
		DEFAULT_ENCODER="shared" \
		DEFAULT_DECODER="shared" \
		ADD_LANGUAGE_TOKEN=true \
		TASK_TRAINDATA="${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}" \
		TASK_DEVDATA="${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}" \
	$(basename $@)

.PHONY: %.finland-predict-translate-shared-encoder
%.finland-predict-translate-shared-encoder:
	@${MAKE} -s MODEL_NAME=finland-predict-translate-shared-encoder \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng" \
		DEFAULT_ENCODER="shared" \
		TASK_TRAINDATA="${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}" \
		TASK_DEVDATA="${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}" \
	$(basename $@)

.PHONY: %.finland-predict-translate-shared-decoder
%.finland-predict-translate-shared-decoder:
	@${MAKE} -s MODEL_NAME=finland-predict-translate-shared-decoder \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng" \
		DEFAULT_DECODER="shared" \
		ADD_LANGUAGE_TOKEN=true \
		TASK_TRAINDATA="${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}" \
		TASK_DEVDATA="${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}" \
	$(basename $@)

.PHONY: %.finland-predict-translate-partially-shared
%.finland-predict-translate-partially-shared:
	@${MAKE} -s MODEL_NAME=finland-predict-translate-partially-shared \
		TASK_IDS="predict_eng-eng predict_fin-fin predict_swe-swe mt_eng-fin mt_fin-eng mt_fin-swe mt_swe-fin mt_swe-eng" \
		ENCODER_LAYERS=3,3 \
		DECODER_LAYERS=3,3 \
		TASK_ENCODERS='"eng","all" "fin","all" "swe","all" "eng","all" "fin","all" "fin","all" "swe","all" "swe","all"' \
		TASK_DECODERS='"all","eng" "all","fin" "all","swe" "all","fin" "all","eng" "all","swe" "all","fin" "all","eng"' \
		TASK_TRAINDATA="${PREDICT_TRAIN} ${PREDICT_TRAIN} ${PREDICT_TRAIN}" \
		TASK_DEVDATA="${PREDICT_DEV} ${PREDICT_DEV} ${PREDICT_DEV}" \
	$(basename $@)




