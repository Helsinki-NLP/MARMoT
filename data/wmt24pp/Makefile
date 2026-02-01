

SRC  := en
TRG  := fi_FI

SRC2 := $(firstword $(subst _, ,${SRC}))
TRG2 := $(firstword $(subst _, ,${TRG}))

SRC3 := $(shell iso639 -3 -n ${SRC})
TRG3 := $(shell iso639 -3 -n ${TRG})



.PHONY: all
all: 	next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${SRC3}.in.gz \
	next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${TRG3}.in.gz

${SRC}-${TRG}.jsonl:
	wget -q -O $@ https://huggingface.co/datasets/google/wmt24pp/raw/main/$@

next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${SRC3}.in.gz: ${SRC}-${TRG}.jsonl
	mkdir -p $(dir $@)
	python3 ../../tools/wmt24_to_predict.py -l ${SRC2} -i $< -f source > $@.tsv
	cut -f1 $@.tsv | gzip -c > $@
	cut -f2 $@.tsv | gzip -c > $(@:.in.gz=.out.gz)
	rm -f $@.tsv

next_sent_predict/wmt24pp_${SRC3}-${TRG3}.${TRG3}.in.gz: ${SRC}-${TRG}.jsonl
	mkdir -p $(dir $@)
	python3 ../../tools/wmt24_to_predict.py -l ${TRG2} -i $< -f target > $@.tsv
	cut -f1 $@.tsv | gzip -c > $@
	cut -f2 $@.tsv | gzip -c > $(@:.in.gz=.out.gz)
	rm -f $@.tsv
