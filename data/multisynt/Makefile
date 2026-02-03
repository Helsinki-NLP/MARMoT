
SHELL := bash

include ../../tools/slurMake/slurm.mk

DATASET  := OELLM-synthetic/maxidl/nemotron-cc-english-run1
FILEBASE := nemotron-cc-english-run1-train-
SRC      := eng
TRG      := fin
FILEID   := 00


MIN_SEG_LENGTH := 256
FILEIDS  := $(shell seq -f "%02g" 0 49)
TARGETS  := $(patsubst %,len${MIN_SEG_LENGTH}/${FILEBASE}%.${SRC}.gz,${FILEIDS})

CONVERT_SCRIPT := python3 ../../tools/multisynt_to_docbitext.py



.PHONY: all
all: ${TARGETS}

.PHONY: convert
convert: len${MIN_SEG_LENGTH}/${FILEBASE}${FILEID}.${SRC}.gz

fetch: jsonl/${SRC}/${FILEBASE}${FILEID}.jsonl.gz txt/${SRC}/${FILEBASE}${FILEID}.txt.gz txt/${TRG}/${FILEBASE}${FILEID}.txt.gz


jsonl/${SRC}/${FILEBASE}%.jsonl.gz: txt/${SRC}/${FILEBASE}%.txt.gz
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@

txt/${SRC}/${FILEBASE}%.txt.gz: txt/${TRG}/${FILEBASE}%.txt.gz
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@

txt/${TRG}/${FILEBASE}%.txt.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@


len${MIN_SEG_LENGTH}/${FILEBASE}%.${SRC}.gz: jsonl/${SRC}/${FILEBASE}%.jsonl.gz
	mkdir -p $(dir $@)
	${CONVERT_SCRIPT} -l ${MIN_SEG_LENGTH} \
		-j jsonl/${SRC}/${FILEBASE}${FILEID}.jsonl.gz \
		-s txt/${SRC}/${FILEBASE}${FILEID}.txt.gz \
		-t txt/${TRG}/${FILEBASE}${FILEID}.txt.gz \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.${SRC}.gz=.${TRG}.gz}


