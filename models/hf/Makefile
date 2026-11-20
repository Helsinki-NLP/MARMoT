

include ../../make/env.mk


MODEL_HOME := ../flagship
MODEL_NAME := opus-big

HF_ORG     := Helsinki-NLP
HF_NAME    := mammoth-G2A4-L6-L32L32-H4D1024


MODEL_DIR     := ${MODEL_HOME}/${MODEL_NAME}/mammoth
CONVERT_TO_HF := ${MAMMOTH_DIR}/mammoth/hf_integration/to_hf/convert_mammoth_to_hf.py
# CONVERT_TO_HF := mammoth_convert2hf
# PUSH_TO_HF    := mammoth_push2hf


.PHONY: convert
convert: ${HF_NAME}

${HF_NAME}:
	python ${CONVERT_TO_HF} --modular \
		--checkpoint-dir ${MODEL_DIR} \
		--output-dir ${HF_NAME} \

.PHONY: push
push: ${HF_NAME}
	${PUSH_TO_HF} --model-dir $@ --repo-dir ${HF_ORG}/$@

