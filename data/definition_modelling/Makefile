

SHELL := bash

#############################################
# 3D-EX
# https://github.com/F-Almeman/3D-EX
#############################################

PHONY: 3d-ex-data
3d-ex-data:
	${MAKE} 3D-EX
	${MAKE} 3D-EX/train/3d_ex.eng1.gz 3D-EX/train/3d_ex.eng2.gz \
		3D-EX/dev/3d_ex.eng1.gz 3D-EX/dev/3d_ex.eng2.gz \
		3D-EX/test/3d_ex.eng1.gz 3D-EX/test/3d_ex.eng2.gz


3D-EX-DATA = $(patsubst %.csv,%.tsv,$(wildcard 3D-EX/datasets/complete_datasets/*.csv))

3D-EX:
	git clone https://github.com/F-Almeman/3D-EX.git

3D-EX/datasets/complete_datasets/CHA_train.csv:
	wget -O $@ https://drive.google.com/uc?export=download&id=1JK5m2cJy9G9W6xacGLxDesesWsFH3dod

${3D-EX-DATA}: %.tsv: %.csv
	python3 3D-EX_to_tsv.py < $< | tail -n +2 > $@

3D-EX/train/3d_ex.eng1.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*.tsv' \
	| grep -v '_test' | grep -v '_valid' | grep -v 'CODWOE' \
	| sort | xargs cat \
	| tee >(cut -f1 | sed 's/$$/:/' > $@.word) \
	| cut -f3 > $@.example
	paste -d ' ' $@.word $@.example | gzip -c > $@
	rm -f $@.word $@.example

3D-EX/train/3d_ex.eng2.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*.tsv' \
	| grep -v '_test' | grep -v '_valid' | grep -v 'CODWOE' \
	| sort | xargs cat | cut -f2 | gzip -c > $@


3D-EX/dev/3d_ex.eng1.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*_valid.tsv' \
	| sort | xargs cat \
	| tee >(cut -f1 | sed 's/$$/:/' > $@.word) \
	| cut -f3 > $@.example
	paste -d ' ' $@.word $@.example | gzip -c > $@
	rm -f $@.word $@.example

3D-EX/dev/3d_ex.eng2.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*_valid.tsv' \
	| sort | xargs cat | cut -f2 | gzip -c > $@


3D-EX/test/3d_ex.eng1.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*_test.tsv' \
	| sort | xargs cat \
	| tee >(cut -f1 | sed 's/$$/:/' > $@.word) \
	| cut -f3 > $@.example
	paste -d ' ' $@.word $@.example | gzip -c > $@
	rm -f $@.word $@.example

3D-EX/test/3d_ex.eng2.gz: ${3D-EX-DATA}
	mkdir -p $(dir $@)
	find 3D-EX/datasets/complete_datasets -name '*_test.tsv' \
	| sort | xargs cat | cut -f2 | gzip -c > $@

