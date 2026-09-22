

LANGUAGES := $(notdir ${wildcard wikilingua_tsv/*})
LANGUAGE  := $(firstword ${LANGUAGES})
DATASPLIT := train

all:
	for l in ${LANGUAGES}; do \
	  for s in train dev test; do \
	    ${MAKE} LANGUAGE=$$l DATASPLIT=$$s convert; \
	  done \
	done


wikilingua_tsv:
	python3 download_wikilingua.py


convert: ${DATASPLIT}/wikilingua.${LANGUAGE}1.gz ${DATASPLIT}/wikilingua.${LANGUAGE}2.gz

${DATASPLIT}/wikilingua.${LANGUAGE}1.gz: wikilingua_tsv
	mkdir -p $(dir $@)
	tail -n +2 < wikilingua_tsv/${LANGUAGE}/${DATASPLIT}.tsv | cut -f1 | gzip -c > $@

${DATASPLIT}/wikilingua.${LANGUAGE}2.gz: wikilingua_tsv
	mkdir -p $(dir $@)
	tail -n +2 < wikilingua_tsv/${LANGUAGE}/${DATASPLIT}.tsv | cut -f2 | gzip -c > $@
