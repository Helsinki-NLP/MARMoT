
SHELL := bash

# HPC_PROJECT := project_465001864
HPC_PROJECT := project_462000964

include ../../tools/slurMake/slurm.mk

DATASET  := OELLM-synthetic/maxidl/nemotron-cc-english-run2
FILEBASE := nemotron-cc-english-run2-train-train-
SRC      := eng
TRG      := fin
FILEID   := 00
LENGTH   := 1024
FILEIDS  := $(shell seq -f "%05g" 0 499)
SOURCES  := $(patsubst %,len${LENGTH}/${FILEBASE}%.${SRC}.gz,${FILEIDS})
TARGETS  := $(patsubst %,len${LENGTH}/${FILEBASE}%.${TRG}.gz,${FILEIDS})

OELLM_LANGS := bul ces est fin gle ron swe tur ukr


CONVERT_SCRIPT := python3 ../../tools/multisynt_to_docbitext.py

.NOTINTERMEDIATE: ${SOURCES} ${TARGETS}

## create train/dev/test splits for doc-level MT training data

.PHONY: all
all:
	${MAKE} all-mt
	${MAKE} all-src-textpredict
	${MAKE} all-trg-textpredict


.PHONY: all-mt
all-mt: train/len${LENGTH}/${FILEBASE}000-498.${TRG}.gz \
	train/len${LENGTH}/${FILEBASE}000-498.${SRC}.gz \
	dev/len${LENGTH}/${FILEBASE}499-tail2000.${TRG}.gz \
	dev/len${LENGTH}/${FILEBASE}499-tail2000.${SRC}.gz \
	test/len${LENGTH}/${FILEBASE}499-head2000.${TRG}.gz \
	test/len${LENGTH}/${FILEBASE}499-head2000.${SRC}.gz

.PHONY: devtest
devtest: 	dev/len${LENGTH}/${FILEBASE}499-tail2000.${TRG}.gz \
		dev/len${LENGTH}/${FILEBASE}499-tail2000.${SRC}.gz \
		test/len${LENGTH}/${FILEBASE}499-head2000.${TRG}.gz \
		test/len${LENGTH}/${FILEBASE}499-head2000.${SRC}.gz


all-4096:
	${MAKE} LENGTH=4096 SLURM_CPUS=32 SLURM_MEM=64g all.slurmjob


# create text prediction data for source and target language


.PHONY: all-textpredict
all-textpredict:
	${MAKE} all-src-textpredict
	${MAKE} all-trg-textpredict

.PHONY: all-trg-textpredict
all-trg-textpredict: textpredict/train/len${LENGTH}/${FILEBASE}000-498.${TRG}1.gz \
		textpredict/dev/len${LENGTH}/${FILEBASE}499-tail2000.${TRG}1.gz \
		textpredict/test/len${LENGTH}/${FILEBASE}499-head2000.${TRG}1.gz

.PHONY: all-src-textpredict
all-src-textpredict: textpredict/train/len${LENGTH}/${FILEBASE}000-498.${SRC}1.gz \
		textpredict/dev/len${LENGTH}/${FILEBASE}499-tail2000.${SRC}1.gz \
		textpredict/test/len${LENGTH}/${FILEBASE}499-head2000.${SRC}1.gz



## create jobs to make the data for all OpenEuroLLM languages

.PHONY: all-oellm-mt
all-oellm-mt:
	for l in ${OELLM_LANGS}; do \
	  ${MAKE} TRG=$$l all-mt.slurmjob; \
	done

.PHONY: all-oellm-predict
all-oellm-predict:
	${MAKE} SLURM_MEM=16g SLURM_CPUS=1 all-src-textpredict.slurmjob
	for l in ${OELLM_LANGS}; do \
	  ${MAKE} TRG=$$l SLURM_MEM=16g SLURM_CPUS=1 all-trg-textpredict.slurmjob; \
	done



## test conversion and fetching

.PHONY: convert
convert: len${LENGTH}/${FILEBASE}${FILEID}.${TRG}.gz

.PHONY: fetch
fetch: jsonl/${SRC}/${FILEBASE}${FILEID}.jsonl.gz txt/${SRC}/${FILEBASE}${FILEID}.txt.gz txt/${TRG}/${FILEBASE}${FILEID}.txt.gz


## count lines

BROKEN_LANGS = bos deu hrv kat lav mkd pol slv srp_Cyrl ukr

count-broken:
	for l in ${BROKEN_LANGS}; do \
	  echo -n "$$l	"; \
	  zcat train/len${LENGTH}/*.$$l.gz | wc -l; \
	done

count-lines:
	for f in train/len${LENGTH}/*.gz; do \
	  echo -n "$$f	"; \
	  zcat $$f | wc -l; \
	done


##------------------------------------------------------------------------------------
## MT training data
##------------------------------------------------------------------------------------

TRAIN_DATA := $(filter-out len${LENGTH}/${FILEBASE}00499.${TRG}.gz,$(TARGETS))

train/len${LENGTH}/${FILEBASE}000-498.${TRG}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | gzip -c > $@


train/len${LENGTH}/${FILEBASE}000-498.${SRC}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | gzip -c > $@


## MT development and test data

DEVTEST_DATA := len${LENGTH}/${FILEBASE}00499.${TRG}.gz

dev/len${LENGTH}/${FILEBASE}499-tail2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

dev/len${LENGTH}/${FILEBASE}499-tail2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

test/len${LENGTH}/${FILEBASE}499-head2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@

test/len${LENGTH}/${FILEBASE}499-head2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@


##------------------------------------------------------------------------------------
## text prediction data
##------------------------------------------------------------------------------------

textpredict/train/len${LENGTH}/${FILEBASE}000-498.${TRG}1.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ > $@.1
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | head -n -1 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2


textpredict/train/len${LENGTH}/${FILEBASE}000-498.${SRC}1.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) > $@.1
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | head -n -1 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2



## textpredict devdata

textpredict/dev/len${LENGTH}/${FILEBASE}499-tail2000.${TRG}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | tail -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2




textpredict/dev/len${LENGTH}/${FILEBASE}499-tail2000.${SRC}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2



## textpredict test data

textpredict/test/len${LENGTH}/${FILEBASE}499-head2000.${TRG}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2



textpredict/test/len${LENGTH}/${FILEBASE}499-head2000.${SRC}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2



##------------------------------------------------------------------------------------
## intermediate converted data
##------------------------------------------------------------------------------------

jsonl/%.jsonl.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@

txt/%.txt.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/$@


len${LENGTH}/${FILEBASE}%.${TRG}.gz: jsonl/${SRC}/${FILEBASE}%.jsonl.gz txt/${SRC}/${FILEBASE}%.txt.gz txt/${TRG}/${FILEBASE}%.txt.gz
	mkdir -p $(dir $@)
	if [ -e $(@:.${TRG}.gz=.${SRC}.gz) ]; then \
	   ${CONVERT_SCRIPT} -l ${LENGTH} -j $< \
		-s $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${SRC}/%.txt.gz,$<) \
		-t $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${TRG}/%.txt.gz,$<) \
	   | cut -f2 | gzip -c > $@; \
	else \
	   ${CONVERT_SCRIPT} -l ${LENGTH} -j $< \
		-s $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${SRC}/%.txt.gz,$<) \
		-t $(patsubst jsonl/${SRC}/%.jsonl.gz,txt/${TRG}/%.txt.gz,$<) \
	   | tee >(cut -f2 | gzip -c > $@) \
	   | cut -f1 | gzip -c > ${@:.${TRG}.gz=.${SRC}.gz}; \
	fi



