


LANGNAME := English
LANGID   := eng
SPLIT    := train


all:
	${MAKE} LANGNAME='Brazilian Portuguese' LANGID=por_BR all-splits
	${MAKE} LANGNAME=English LANGID=eng all-splits
	${MAKE} LANGNAME=French LANGID=fra all-splits
	${MAKE} LANGNAME=German LANGID=deu all-splits
	${MAKE} LANGNAME=Italian LANGID=ita all-splits
	${MAKE} LANGNAME=Japanese LANGID=jpn all-splits
	${MAKE} LANGNAME=Russian LANGID=rus all-splits
	${MAKE} LANGNAME=Slovene LANGID=slv all-splits


all-splits:
	for s in train dev test; do \
	  ${MAKE} SPLIT=$$s convert; \
	done

multisim_tsv:
	python3 fetch_tsv.py

convert: ${SPLIT}/multisim.${LANGID}1.gz ${SPLIT}/multisim.${LANGID}2.gz


${SPLIT}/multisim.${LANGID}1.gz: multisim_tsv
	mkdir -p $(dir $@)
	tail -n +2 "multisim_tsv/${LANGNAME}_${SPLIT}.tsv" | cut -f1 | gzip -c > $@

${SPLIT}/multisim.${LANGID}2.gz: multisim_tsv
	mkdir -p $(dir $@)
	tail -n +2 "multisim_tsv/${LANGNAME}_${SPLIT}.tsv" | cut -f2 | gzip -c > $@

