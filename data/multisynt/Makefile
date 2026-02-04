
SHELL := bash

include ../../tools/slurMake/slurm.mk

DATASET  := OELLM-synthetic/maxidl/nemotron-cc-english-run1
FILEBASE := nemotron-cc-english-run1-train-
SRC      := eng
TRG      := fin
FILEID   := 00


SEG_LENGTH := 256
FILEIDS    := $(shell seq -f "%02g" 0 49)
SOURCES    := $(patsubst %,len${SEG_LENGTH}/${FILEBASE}%.${SRC}.gz,${FILEIDS})
TARGETS    := $(patsubst %,len${SEG_LENGTH}/${FILEBASE}%.${TRG}.gz,${FILEIDS})

CONVERT_SCRIPT := python3 ../../tools/multisynt_to_docbitext.py

.NOTINTERMEDIATE: ${SOURCES} ${TARGETS}

## create train/dev/test splits for doc-level MT training data

.PHONY: all
all: 	train/len${SEG_LENGTH}/${FILEBASE}00-48.${TRG}.gz \
	train/len${SEG_LENGTH}/${FILEBASE}00-48.${SRC}.gz \
	dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.${TRG}.gz \
	dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.${SRC}.gz \
	test/len${SEG_LENGTH}/${FILEBASE}49-head2000.${TRG}.gz \
	test/len${SEG_LENGTH}/${FILEBASE}49-head2000.${SRC}.gz


# create text prediction data for source and target language

.PHONY: all-textpredict
all-textpredict: textpredict/${TRG}/train/len${SEG_LENGTH}/${FILEBASE}00-48.first.gz \
		textpredict/${SRC}/train/len${SEG_LENGTH}/${FILEBASE}00-48.first.gz \
		textpredict/${TRG}/dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.first.gz \
		textpredict/${SRC}/dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.first.gz \
		textpredict/${TRG}/test/len${SEG_LENGTH}/${FILEBASE}49-head2000.first.gz \
		textpredict/${SRC}/test/len${SEG_LENGTH}/${FILEBASE}49-head2000.first.gz





.PHONY: convert
convert: len${SEG_LENGTH}/${FILEBASE}${FILEID}.${TRG}.gz

.PHONY: fetch
fetch: jsonl/${SRC}/${FILEBASE}${FILEID}.jsonl.gz txt/${SRC}/${FILEBASE}${FILEID}.txt.gz txt/${TRG}/${FILEBASE}${FILEID}.txt.gz




## MT training data

TRAIN_DATA := $(filter-out len${SEG_LENGTH}/${FILEBASE}49.${TRG}.gz,$(TARGETS))

train/len${SEG_LENGTH}/${FILEBASE}00-48.${TRG}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep -v 'END_OF_DOCUMENT' | gzip -c > $@

train/len${SEG_LENGTH}/${FILEBASE}00-48.${SRC}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep -v 'END_OF_DOCUMENT' | gzip -c > $@


## MT development and test data

DEVTEST_DATA := len${SEG_LENGTH}/${FILEBASE}49.${TRG}.gz

dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

test/len${SEG_LENGTH}/${FILEBASE}49-head2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@

test/len${SEG_LENGTH}/${FILEBASE}49-head2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@



## text prediction data

textpredict/${TRG}/train/len${SEG_LENGTH}/${FILEBASE}00-48.first.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -n -1 > $@.1
	zcat $^ | tail -n +2 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}

textpredict/${SRC}/train/len${SEG_LENGTH}/${FILEBASE}00-48.first.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -n -1 > $@.1
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -n +2 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}

textpredict/${TRG}/dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -n -1 | tail -2000 > $@.1
	zcat $^ | tail -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}

textpredict/${SRC}/dev/len${SEG_LENGTH}/${FILEBASE}49-tail2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -n -1 | tail -2000 > $@.1
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}

textpredict/${TRG}/test/len${SEG_LENGTH}/${FILEBASE}49-head2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -2000 > $@.1
	zcat $^ | tail -n +2 | head -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}

textpredict/${SRC}/test/len${SEG_LENGTH}/${FILEBASE}49-head2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -2000 > $@.1
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -n +2 | head -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}






## converted data


jsonl/%.jsonl.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@

txt/%.txt.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@


len${SEG_LENGTH}/${FILEBASE}%.${TRG}.gz: jsonl/${SRC}/${FILEBASE}%.jsonl.gz txt/${SRC}/${FILEBASE}%.txt.gz txt/${TRG}/${FILEBASE}%.txt.gz
	mkdir -p $(dir $@)
	if [ -e $(@:.${TRG}.gz=.${SRC}.gz) ]; then \
	   ${CONVERT_SCRIPT} -l ${SEG_LENGTH} -j $< \
		-s $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${SRC}/%.txt.gz,$<) \
		-t $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${TRG}/%.txt.gz,$<) \
	   | cut -f2 | gzip -c > $@; \
	else \
	   ${CONVERT_SCRIPT} -l ${SEG_LENGTH} -j $< \
		-s $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${SRC}/%.txt.gz,$<) \
		-t $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${TRG}/%.txt.gz,$<) \
	   | tee >(cut -f2 | gzip -c > $@) \
	   | cut -f1 | gzip -c > ${@:.${TRG}.gz=.${SRC}.gz}; \
	fi


