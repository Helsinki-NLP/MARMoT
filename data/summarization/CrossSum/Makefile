

LANGPAIRS := english-french french-english english-english french-french
SRCLANG   := eng
TRGLANG   := fra
DATASPLIT := train

ifeq (${SRCLANG},${TRGLANG})
  SRCEXT := ${SRCLANG}1
  TRGEXT := ${TRGLANG}2
else
  SRCEXT := ${SRCLANG}
  TRGEXT := ${TRGLANG}
endif


all: crosssum_tsv
	for s in train dev test; do \
	  ${MAKE} SRCLANG=eng TRGLANG=fra DATASPLIT=$$s convert; \
	  ${MAKE} SRCLANG=fra TRGLANG=eng DATASPLIT=$$s convert; \
	  ${MAKE} SRCLANG=eng TRGLANG=eng DATASPLIT=$$s convert; \
	  ${MAKE} SRCLANG=fra TRGLANG=fra DATASPLIT=$$s convert; \
	done


crosssum_tsv:
	python3 download_cross_sum.py --pairs ${LANGPAIRS}

convert: ${DATASPLIT}/CrossSum.${SRCLANG}-${TRGLANG}.${SRCEXT}.gz \
	${DATASPLIT}/CrossSum.${SRCLANG}-${TRGLANG}.${TRGEXT}.gz

${DATASPLIT}/CrossSum.${SRCLANG}-${TRGLANG}.${SRCEXT}.gz:
	mkdir -p $(dir $@)
	tail -n +2 < crosssum_tsv/${SRCLANG}/${TRGLANG}/${DATASPLIT}.tsv | cut -f1 | gzip -c > $@

${DATASPLIT}/CrossSum.${SRCLANG}-${TRGLANG}.${TRGEXT}.gz:
	mkdir -p $(dir $@)
	tail -n +2 < crosssum_tsv/${SRCLANG}/${TRGLANG}/${DATASPLIT}.tsv | cut -f2 | gzip -c > $@
