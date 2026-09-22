

LANGUAGES := $(notdir ${wildcard xlsum_tsv/*})
LANGUAGE  := $(firstword ${LANGUAGES})
DATASPLIT := train

all:
	for l in ${LANGUAGES}; do \
	  for s in train dev test; do \
	    ${MAKE} LANGUAGE=$$l DATASPLIT=$$s convert; \
	  done \
	done


xlsum_tsv:
	python3 download_xlsum.py


convert: ${DATASPLIT}/xlsum.${LANGUAGE}1.gz ${DATASPLIT}/xlsum.${LANGUAGE}2.gz

${DATASPLIT}/xlsum.${LANGUAGE}1.gz: xlsum_tsv
	mkdir -p $(dir $@)
	tail -n +2 < xlsum_tsv/${LANGUAGE}/${DATASPLIT}.tsv | cut -f2 | gzip -c > $@

${DATASPLIT}/xlsum.${LANGUAGE}2.gz: xlsum_tsv
	mkdir -p $(dir $@)
	tail -n +2 < xlsum_tsv/${LANGUAGE}/${DATASPLIT}.tsv | cut -f3 | gzip -c > $@
