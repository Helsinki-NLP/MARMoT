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



## set experiment parameters (if different from defaults)

LANGS := $(sort deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos isl kat \
		mkd sqi srp_Cyrl)

META_LANGS  := $(shell iso639 -m ${LANGS} 2>/dev/null)

TASKS := $(foreach l,${LANGS},$l-eng eng-$l)
TASK_ENCODERS := $(foreach l,${META_LANGS},"$l","all" "eng","all")
TASK_DECODERS := $(foreach l,${LANGS},"all","eng" "all","$l")


MODEL_NAME      := eucore
ENCODER_LAYERS  := 3,3
DECODER_LAYERS  := 3,3


## include common configuration and make targets

include ../../../make/marmot.mk



.PHONY: %.puhti6
%.puhti6:
	@${MAKE} -s NR_OF_NODES=6 MODEL_NAME=puhti-6nodes $(basename $@)


.PHONY: %.exp2
%.exp2:
	${MAKE} -s \
		MODEL_NAME=eucore2 \
		LEARNING_RATE=0.0005 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)


.PHONY: %.exp3
%.exp3:
	${MAKE} -s \
		MODEL_NAME=eucore3 \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
	$(basename $@)


.PHONY: %.exp4
%.exp4:
	${MAKE} -s \
		MODEL_NAME=shared \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
		DEFAULT_ENCODER="shared" \
		DEFAULT_DECODER="shared" \
		ADD_LANGUAGE_TOKEN=true \
	$(basename $@)

.PHONY: %.exp4b
%.exp4b:
	${MAKE} -s \
		MODEL_NAME=shared-no-prefix \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
		DEFAULT_ENCODER="shared" \
		DEFAULT_DECODER="shared" \
	$(basename $@)


.PHONY: %.exp5
%.exp5:
	${MAKE} -s \
		MODEL_NAME=separate \
		LEARNING_RATE=0.0003 \
		KEEP_CHECKPOINTS=1 \
		ENCODER_LAYERS=6 \
		DECODER_LAYERS=6 \
		TASK_ENCODERS= \
		TASK_DECODERS= \
	$(basename $@)
