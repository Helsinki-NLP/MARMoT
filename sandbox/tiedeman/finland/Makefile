#-*-makefile-*-
##-----------------------------------------------------------
## testing multi-node job
##-----------------------------------------------------------

MONO_TASKS           := eng-eng fin-fin swe-swe
MONO_TASK_WEIGHTS    := 0.1     0.1     0.1
MONO_TASK_TRANSFORMS := denoising,filtertoolong denoising,filtertoolong denoising,filtertoolong
MONO_TASK_IDS        := $(patsubst %,denoising_%,${MONO_TASKS})

REGULAR_TASKS := fin-eng eng-fin swe-eng eng-swe fin-swe swe-fin


MODEL_NAME      := finland-language-specific
TASKS           := ${MONO_TASKS} ${REGULAR_TASKS}
TASK_WEIGHTS    := ${MONO_TASK_WEIGHTS}
TASK_TRANSFORMS := ${MONO_TASK_TRANSFORMS}
ENCODER_LAYERS  := 9
DECODER_LAYERS  := 3


## include common configuration and make targets

include ../../../make/marmot.mk



#-----------------------------------------------------
# other experiments with slightly different settings
#-----------------------------------------------------

OS24_TASKS           := fin-eng eng-fin fin-swe swe-fin
OS24_TASK_IDS        := $(patsubst %,os24_%,${OS24_TASKS})
OS24_TASK_TRANSFORMS := $(patsubst %,filtertoolong,${OS24_TASKS})

OS24_TASK_TRAINDATA_SRCS := ${DATA_DIR}/opus/OpenSubtitles/fin-eng.fin.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-eng.eng.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-swe.fin.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-swe.swe.gz

OS24_TASK_TRAINDATA_TRGS := ${DATA_DIR}/opus/OpenSubtitles/fin-eng.eng.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-eng.fin.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-swe.swe.gz \
			${DATA_DIR}/opus/OpenSubtitles/fin-swe.fin.gz


BT_TASKS           := fin-eng eng-fin swe-eng eng-swe fin-swe swe-fin
BT_TASK_IDS        := $(patsubst %,wiki_%,${BT_TASKS})
BT_TASK_TRANSFORMS := $(patsubst %,filtertoolong,${BT_TASKS})


BT_TASK_TRAINDATA_SRCS := 	${DATA_DIR}/synthetic/Wikipedia/eng-fin.fin.gz \
				${DATA_DIR}/synthetic/Wiki/fin-eng.eng.gz \
				${DATA_DIR}/synthetic/Wikipedia/eng-swe.swe.gz \
				${DATA_DIR}/synthetic/Wiki/swe-eng.eng.gz \
				${DATA_DIR}/synthetic/Wiki/swe-fin.fin.gz \
				${DATA_DIR}/synthetic/Wiki/fin-swe.swe.gz

BT_TASK_TRAINDATA_TRGS := 	${DATA_DIR}/synthetic/Wikipedia/eng-fin.eng.gz \
				${DATA_DIR}/synthetic/Wiki/fin-eng.fin.gz \
				${DATA_DIR}/synthetic/Wikipedia/eng-swe.eng.gz \
				${DATA_DIR}/synthetic/Wiki/swe-eng.swe.gz \
				${DATA_DIR}/synthetic/Wiki/swe-fin.swe.gz \
				${DATA_DIR}/synthetic/Wiki/fin-swe.fin.gz

.PHONY: %.bt
%.bt:
	@${MAKE} -s MODEL_NAME=finland-langspecific-bt \
		TASKS="${OS24_TASKS} ${BT_TASKS} ${REGULAR_TASKS}" \
		TASK_IDS="${OS24_TASK_IDS} ${BT_TASK_IDS}" \
		TASK_TRAINDATA_SRCS="${OS24_TASK_TRAINDATA_SRCS} ${BT_TASK_TRAINDATA_SRCS}" \
		TASK_TRAINDATA_TRGS="${OS24_TASK_TRAINDATA_TRGS} ${BT_TASK_TRAINDATA_TRGS}" \
		TASK_WEIGHTS= \
		TASK_TRANSFORMS= \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
	$(basename $@)


# .PHONY: %.bt
# %.bt:
# 	@${MAKE} MODEL_NAME=finland-langspecific-bt \
# 		TASKS="${OS24_TASKS} ${BT_TASKS} ${MONO_TASKS} ${REGULAR_TASKS}" \
# 		TASK_IDS="${OS24_TASK_IDS} ${BT_TASK_IDS} ${MONO_TASK_IDS}" \
# 		TASK_TRAINDATA_SRCS="${OS24_TASK_TRAINDATA_SRCS} ${BT_TASK_TRAINDATA_SRCS}" \
# 		TASK_TRAINDATA_TRGS="${OS24_TASK_TRAINDATA_TRGS} ${BT_TASK_TRAINDATA_TRGS}" \
# 		TASK_WEIGHTS= \
# 		TASK_TRANSFORMS="${OS24_TASK_TRANSFORMS} ${BT_TASK_TRANSFORMS} ${MONO_TASK_TRANSFORMS}" \
# 		ENCODER_LAYERS=6 \
# 		DECODER_LAYERS=6 \
# 	$(basename $@)


.PHONY: %.bt-1node
%.bt-1node:
	@${MAKE} -s MODEL_NAME=finland-langspecific-bt-1node \
		NR_OF_NODES=1 \
		TASKS="${BT_TASKS} ${MONO_TASKS} ${REGULAR_TASKS}" \
		TASK_IDS="${BT_TASK_IDS} ${MONO_TASK_IDS}" \
		TASK_TRAINDATA_SRCS="${BT_TASK_TRAINDATA_SRCS}" \
		TASK_TRAINDATA_TRGS="${BT_TASK_TRAINDATA_TRGS}" \
		TASK_WEIGHTS= \
		TASK_TRANSFORMS="${BT_TASK_TRANSFORMS} ${MONO_TASK_TRANSFORMS}" \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
	$(basename $@)





.PHONY: %.sharedenc
%.sharedenc:
	@${MAKE} -s MODEL_NAME=finland-shared-encoder DEFAULT_ENCODER="shared" $(basename $@)

.PHONY: %.shared
%.shared:
	@${MAKE} -s MODEL_NAME=finland-shared DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" \
		ADD_LANGUAGE_TOKEN=true \
		TASK_TRANSFORMS="denoising,filtertoolong,prefix denoising,filtertoolong,prefix denoising,filtertoolong,prefix" \
	$(basename $@)

.PHONY: %.mixedenc
%.mixedenc:
	@${MAKE} -s MODEL_NAME=finland-mixed-encoder \
		ENCODER_LAYERS=3,6 \
		TASK_ENCODERS="eng,all fin,all swe,all fin,all eng,all swe,all eng,all" \
		$(basename $@)

.PHONY: %.mixed
%.mixed:
	@${MAKE} -s MODEL_NAME=finland-mixed \
		ENCODER_LAYERS=3,6 \
		DECODER_LAYERS=2,1 \
		TASK_ENCODERS="eng,all fin,all swe,all fin,all eng,all swe,all eng,all" \
		TASK_DECODERS="all,eng all,fin all,swe all,eng all,fin all,eng all,swe" \
		$(basename $@)


.PHONY: %.onion
%.onion:
	@${MAKE} -s MODEL_NAME=finland-onion \
		ENCODER_LAYERS=3 \
		DECODER_LAYERS=2,5,2 \
		TASK_DECODERS="eng1,all,eng2 fin1,all,fin2 swe1,all,swe2 eng1,all,eng2 fin1,all,fin2 eng1,all,eng2 swe1,all,swe2" \
		$(basename $@)

.PHONY: %.onion2
%.onion2:
	@${MAKE} -s MODEL_NAME=finland-onion2 \
		ENCODER_LAYERS=3 \
		DECODER_LAYERS=1,2,3,2,1 \
		TASK_DECODERS="eng1,gem1,all,gem2,eng2 fin1,fiu1,all,fiu2,fin2 swe1,gem1,all,gem2,swe2 eng1,gem1,all,gem2,eng2 fin1,fiu1,all,fiu2,fin2 eng1,gem1,all,gem2,eng2 swe1,gem1,all,gem2,swe2" \
		$(basename $@)


.PHONY: %.onion3
%.onion3:
	@${MAKE} -s MODEL_NAME=finland-onion3 \
		ENCODER_LAYERS=9 \
		DECODER_LAYERS=1,1,1 \
		TASK_DECODERS="eng,all,eng fin,all,fin swe,all,swe eng,all,eng fin,all,fin eng,all,eng swe,all,swe" \
		$(basename $@)

.PHONY: %.onion4
%.onion4:
	@${MAKE} -s MODEL_NAME=finland-onion4 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=2,2,2 \
		TASK_DECODERS="eng,all,eng fin,all,fin swe,all,swe eng,all,eng fin,all,fin eng,all,eng swe,all,swe" \
		$(basename $@)

.PHONY: %.onion5
%.onion5:
	@${MAKE} -s MODEL_NAME=finland-onion5 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=1,2,3,2,1 \
		TASK_DECODERS="eng,gem,all,gem,eng fin,fiu,all,fiu,fin swe,gem,all,gem,swe eng,gem,all,gem,eng fin,fiu,all,fiu,fin eng,gem,all,gem,eng swe,gem,all,gem,swe" \
		$(basename $@)

.PHONY: %.onion6
%.onion6:
	@${MAKE} -s MODEL_NAME=finland-onion6 \
		ENCODER_LAYERS=6 \
		DEFAULT_ENCODER="shared" \
		DECODER_LAYERS=1,2,3,2,1 \
		TASK_DECODERS="eng,gem,all,gem,eng fin,fiu,all,fiu,fin swe,gem,all,gem,swe eng,gem,all,gem,eng fin,fiu,all,fiu,fin eng,gem,all,gem,eng swe,gem,all,gem,swe" \
		$(basename $@)
