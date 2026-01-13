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



MODEL_NAME      := finland-language-specific
TASKS           := eng-eng fin-fin swe-swe fin-eng eng-fin swe-eng eng-swe
TASK_GPUS       := 0:0     0:1     0:2
TASK_WEIGHTS    := 0.1     0.1     0.1
TASK_TRANSFORMS := denoising,filtertoolong denoising,filtertoolong denoising,filtertoolong
ENCODER_LAYERS  := 9
DECODER_LAYERS  := 3


## include common configuration and make targets

include ../../../make/marmot.mk


#-----------------------------------------------------
# other experiments with slightly different settings
#-----------------------------------------------------


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
