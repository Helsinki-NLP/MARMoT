
SHELL := bash

HPC_PROJECT := project_465001864

include ../../tools/slurMake/slurm.mk

DATASET  := OELLM-synthetic/maxidl/nemotron-cc-english-run1
FILEBASE := nemotron-cc-english-run1-train-
SRC      := eng
TRG      := fin
FILEID   := 00
LENGTH   := 1024
FILEIDS  := $(shell seq -f "%02g" 0 49)
SOURCES  := $(patsubst %,len${LENGTH}/${FILEBASE}%.${SRC}.gz,${FILEIDS})
TARGETS  := $(patsubst %,len${LENGTH}/${FILEBASE}%.${TRG}.gz,${FILEIDS})

OELLM_LANGS := 	deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos isl kat \
		mkd sqi srp_Cyrl


CONVERT_SCRIPT := python3 ../../tools/multisynt_to_docbitext.py

.NOTINTERMEDIATE: ${SOURCES} ${TARGETS}

## create train/dev/test splits for doc-level MT training data

.PHONY: all
all:
	${MAKE} all-mt
	${MAKE} all-src-textpredict
	${MAKE} all-trg-textpredict


.PHONY: all-mt
all-mt: train/len${LENGTH}/${FILEBASE}00-48.${TRG}.gz \
	train/len${LENGTH}/${FILEBASE}00-48.${SRC}.gz \
	dev/len${LENGTH}/${FILEBASE}49-tail2000.${TRG}.gz \
	dev/len${LENGTH}/${FILEBASE}49-tail2000.${SRC}.gz \
	test/len${LENGTH}/${FILEBASE}49-head2000.${TRG}.gz \
	test/len${LENGTH}/${FILEBASE}49-head2000.${SRC}.gz


all-4096:
	${MAKE} LENGTH=4096 SLURM_CPUS=32 SLURM_MEM=64g all.slurmjob


# create text prediction data for source and target language


.PHONY: all-textpredict
all-textpredict:
	${MAKE} all-src-textpredict
	${MAKE} all-trg-textpredict

.PHONY: all-trg-textpredict
all-trg-textpredict: textpredict/train/len${LENGTH}/${FILEBASE}00-48.${TRG}1.gz \
		textpredict/dev/len${LENGTH}/${FILEBASE}49-tail2000.${TRG}1.gz \
		textpredict/test/len${LENGTH}/${FILEBASE}49-head2000.${TRG}1.gz

.PHONY: all-src-textpredict
all-src-textpredict: textpredict/train/len${LENGTH}/${FILEBASE}00-48.${SRC}1.gz \
		textpredict/dev/len${LENGTH}/${FILEBASE}49-tail2000.${SRC}1.gz \
		textpredict/test/len${LENGTH}/${FILEBASE}49-head2000.${SRC}1.gz



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
##
## TODO: for some languages, zcat with many files seems to break without error
##       --> some files contain only a fraction of the data (e.g. bos, deu, ukr, ...)
##       --> fall back to concatenating individual files in a loop for now
##------------------------------------------------------------------------------------

TRAIN_DATA := $(filter-out len${LENGTH}/${FILEBASE}49.${TRG}.gz,$(TARGETS))

train/len${LENGTH}/${FILEBASE}00-48.${TRG}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | gzip -c > $@
#	rm -f $(@:.gz=)
#	for d in $^; do \
#	  echo "adding $$d"; \
#	  gzip -cd < $$d | grep --text -v 'END_OF_DOCUMENT' >> $(@:.gz=); \
#	done
#	gzip -f $(@:.gz=)


train/len${LENGTH}/${FILEBASE}00-48.${SRC}.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | gzip -c > $@
#	rm -f $(@:.gz=)
#	for d in $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^); do \
#	  echo "adding $$d"; \
#	  gzip -cd < $$d | grep --text -v 'END_OF_DOCUMENT' >> $(@:.gz=); \
#	done
#	gzip -f $(@:.gz=)


## MT development and test data

DEVTEST_DATA := len${LENGTH}/${FILEBASE}49.${TRG}.gz

dev/len${LENGTH}/${FILEBASE}49-tail2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

dev/len${LENGTH}/${FILEBASE}49-tail2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | tail -2000 | gzip -c > $@

test/len${LENGTH}/${FILEBASE}49-head2000.${TRG}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | grep --text -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@

test/len${LENGTH}/${FILEBASE}49-head2000.${SRC}.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | grep --text -v 'END_OF_DOCUMENT' | head -2000 | gzip -c > $@


##------------------------------------------------------------------------------------
## text prediction data
##------------------------------------------------------------------------------------

textpredict/train/len${LENGTH}/${FILEBASE}00-48.${TRG}1.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $^ > $@.1
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | head -n -1 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	rm -f $@.1 $@.2
#	for d in $^; do \
#	  gzip -cd $$d >> $@.1; \
#	done
#	tail -n +2 $@.1 > $@.2


#	zcat $^ | head -n -1 > $@.1
#	zcat $^ | tail -n +2 > $@.2
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' | cut -f1 | gzip -c > $@
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' | cut -f2 | gzip -c > ${@:1.gz=2.gz}
#	rm -f $@.1 $@.2

textpredict/train/len${LENGTH}/${FILEBASE}00-48.${SRC}1.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) > $@.1
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | head -n -1 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	rm -f $@.1 $@.2
#	for d in $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^); do \
#	  gzip -cd $$d >> $@.1; \
#	done
#	tail -n +2 $@.1 > $@.2

#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' | cut -f1 | gzip -c > $@
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' | cut -f2 | gzip -c > ${@:1.gz=2.gz}
#	rm -f $@.1 $@.2


## textpredict devdata

textpredict/dev/len${LENGTH}/${FILEBASE}49-tail2000.${TRG}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | tail -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	zcat $^ | head -n -1 | tail -2000 > $@.1
#	zcat $^ | tail -2000 > $@.2
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' \



textpredict/dev/len${LENGTH}/${FILEBASE}49-tail2000.${SRC}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -n -1 | tail -2000 > $@.1
#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -2000 > $@.2
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' \


## textpredict test data

textpredict/test/len${LENGTH}/${FILEBASE}49-head2000.${TRG}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	zcat $^ | head -2000 > $@.1
#	zcat $^ | tail -n +2 | head -2000 > $@.2
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' \


textpredict/test/len${LENGTH}/${FILEBASE}49-head2000.${SRC}1.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -2001 > $@.1
	tail -2000 $@.1 > $@.2
	paste $@.1 $@.2 | head -2000 | grep --text -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:1.gz=2.gz}
	rm -f $@.1 $@.2

#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -2000 > $@.1
#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -n +2 | head -2000 > $@.2
#	paste $@.1 $@.2 | grep --text -v 'END_OF_DOCUMENT' \



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














##------------------------------------------------------------------------------------
## OLD AND DEPRECATED
## text prediction data
## OLD AND DEPRECATED
##------------------------------------------------------------------------------------

textpredict/${TRG}/train/len${LENGTH}/${FILEBASE}00-48.first.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	rm -f $@.1 $@.2
	for d in $^; do \
	  gzip -cd $$d >> $@.1; \
	done
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' | cut -f1 | gzip -c > $@
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' | cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2

#	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
#	| tee >(cut -f1 | gzip -c > $@) \
#	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
#	rm -f $@.1 $@.2
#
#	mkdir -p $(dir $@)
#	zcat $^ | head -n -1 > $@.1
#	zcat $^ | tail -n +2 > $@.2
#	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
#	| tee >(cut -f1 | gzip -c > $@) \
#	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
#	rm -f $@.1 $@.2

textpredict/${SRC}/train/len${LENGTH}/${FILEBASE}00-48.first.gz: ${TRAIN_DATA}
	mkdir -p $(dir $@)
	rm -f $@.1 $@.2
	for d in $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^); do \
	  gzip -cd $$d >> $@.1; \
	done
	tail -n +2 $@.1 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' | cut -f1 | gzip -c > $@
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' | cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2

#	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
#	| tee >(cut -f1 | gzip -c > $@) \
#	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
#	rm -f $@.1 $@.2
#
#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -n -1 > $@.1
#	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -n +2 > $@.2
#	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
#	| tee >(cut -f1 | gzip -c > $@) \
#	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
#	rm -f $@.1 $@.2

textpredict/${TRG}/dev/len${LENGTH}/${FILEBASE}49-tail2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -n -1 | tail -2000 > $@.1
	zcat $^ | tail -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2

textpredict/${SRC}/dev/len${LENGTH}/${FILEBASE}49-tail2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -n -1 | tail -2000 > $@.1
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2

textpredict/${TRG}/test/len${LENGTH}/${FILEBASE}49-head2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $^ | head -2000 > $@.1
	zcat $^ | tail -n +2 | head -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2

textpredict/${SRC}/test/len${LENGTH}/${FILEBASE}49-head2000.first.gz: ${DEVTEST_DATA}
	mkdir -p $(dir $@)
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | head -2000 > $@.1
	zcat $(patsubst %.${TRG}.gz,%.${SRC}.gz,$^) | tail -n +2 | head -2000 > $@.2
	paste $@.1 $@.2 | grep -v 'END_OF_DOCUMENT' \
	| tee >(cut -f1 | gzip -c > $@) \
	| cut -f2 | gzip -c > ${@:.first.gz=.second.gz}
	rm -f $@.1 $@.2







