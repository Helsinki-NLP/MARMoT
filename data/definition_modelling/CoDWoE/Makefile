
# from https://codwoe.atilf.fr

SHELL := bash

.PHONY: all
all:
	${MAKE} LANG2=en LANG3=eng convert
	${MAKE} LANG2=fr LANG3=fra convert
	${MAKE} LANG2=ru LANG3=rus convert

.PHONY: convert
convert: train/codwoe.${LANG3}1.gz train/codwoe.${LANG3}2.gz \
	dev/codwoe.${LANG3}1.gz dev/codwoe.${LANG3}2.gz


full_dataset/${LANG2}.complete.csv full_dataset/${LANG2}.trial.complete.csv:
	wget https://codwoe.atilf.fr/data/full_dataset.zip
	unzip full_dataset.zip
	rm -f full_dataset.zip


train/codwoe.${LANG3}1.gz: full_dataset/${LANG2}.complete.csv
	mkdir -p $(dir $@)
	python3 codwoe_csv2tsv.py < $< \
	| tee >(cut -f1 | tail -n +2 | sed 's/$$/:/' > $@.word) \
	| cut -f4 | tail -n +2 > $@.example
	paste -d ' ' $@.word $@.example | gzip -c > $@
	rm -f $@.word $@.example

train/codwoe.${LANG3}2.gz: full_dataset/${LANG2}.complete.csv
	mkdir -p $(dir $@)
	python3 codwoe_csv2tsv.py < $< | cut -f3 | tail -n +2 | gzip -c > $@


dev/codwoe.${LANG3}1.gz: full_dataset/${LANG2}.trial.complete.csv
	mkdir -p $(dir $@)
	python3 codwoe_csv2tsv.py < $< \
	| tee >(cut -f1 | tail -n +2 | sed 's/$$/:/' > $@.word) \
	| cut -f4 | tail -n +2 > $@.example
	paste -d ' ' $@.word $@.example | gzip -c > $@
	rm -f $@.word $@.example

dev/codwoe.${LANG3}2.gz: full_dataset/${LANG2}.trial.complete.csv
	mkdir -p $(dir $@)
	python3 codwoe_csv2tsv.py < $< | cut -f3 | tail -n +2 | gzip -c > $@


