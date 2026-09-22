

DATASPLIT := train

all:
	for s in train dev test; do \
	  ${MAKE} DATASPLIT=$$s convert; \
	done

samsum_tsv:
	python3 download_samsum.py

convert: ${DATASPLIT}/samsum.eng1.gz ${DATASPLIT}/samsum.eng2.gz

${DATASPLIT}/samsum.eng1.gz: samsum_tsv
	mkdir -p $(dir $@)
	tail -n +2 < samsum_tsv/${DATASPLIT}.tsv | cut -f2 | gzip -c > $@

${DATASPLIT}/samsum.eng2.gz: samsum_tsv
	mkdir -p $(dir $@)
	tail -n +2 < samsum_tsv/${DATASPLIT}.tsv | cut -f3 | gzip -c > $@
