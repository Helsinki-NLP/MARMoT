#-*-makefile-*-
#-----------------------------------------------------------
# tain a model for Finnish, Swedish and English
#-----------------------------------------------------------


MODEL_NAME   := finland

TASK_IDS     := wiki_fin-eng wiki_eng-fin wiki_swe-eng wiki_eng-swe wiki_fin-swe wiki_swe-fin \
		os24_fin-eng os24_eng-fin os24_fin-swe os24_swe-fin \
		task_fin-eng task_eng-fin task_swe-eng task_eng-swe task_fin-swe task_swe-fin

TASK_TRAINDATA := synthetic/Wikipedia synthetic/Wiki synthetic/Wikipedia synthetic/Wiki synthetic/Wiki synthetic/Wiki \
		opus/OpenSubtitles opus/OpenSubtitles opus/OpenSubtitles opus/OpenSubtitles

ENCODER_LAYERS := 6
DECODER_LAYERS := 6



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
	@${MAKE} -s MODEL_NAME=finland-shared DEFAULT_ENCODER="shared" DEFAULT_DECODER="shared" ADD_LANGUAGE_TOKEN=true $(basename $@)

