


LANG2 := de
LANG3 := deu

DATASPLIT := train
MAXLINES  := 1000000


all:
	for s in test dev train; do \
	  ${MAKE} DATASPLIT=$$s LANG2=de LANG3=deu convert; \
	  ${MAKE} DATASPLIT=$$s LANG2=en LANG3=eng convert; \
	  ${MAKE} DATASPLIT=$$s LANG2=fi LANG3=fin convert; \
	  ${MAKE} DATASPLIT=$$s LANG2=fr LANG3=fra convert; \
	  ${MAKE} DATASPLIT=$$s LANG2=ru LANG3=rus convert; \
	  ${MAKE} DATASPLIT=$$s LANG2=sv LANG3=swe convert; \
	done

opusparcus_v1:
	for l in de en fi fr ru sv; do \
	  wget https://www.kielipankki.fi/download/opusparcus/opusparcus_$$l.zip; \
	  unzip opusparcus_$$l.zip; \
	  rm -f opusparcus_$$l.zip; \
	done
	wget -O $@/README.txt https://www.kielipankki.fi/download/opusparcus/README.txt

convert: ${DATASPLIT}/opusparcus.${LANG3}1.gz ${DATASPLIT}/opusparcus.${LANG3}2.gz


ifneq ($(wildcard opusparcus_v1/${LANG2}/${DATASPLIT}/${LANG2}-${DATASPLIT}.txt.bz2),)
  CAT_TSVFILE = bunzip2 -c opusparcus_v1/${LANG2}/${DATASPLIT}/${LANG2}-${DATASPLIT}.txt.bz2
else
  CAT_TSVFILE = cat opusparcus_v1/${LANG2}/${DATASPLIT}/${LANG2}-${DATASPLIT}.txt
endif

${DATASPLIT}/opusparcus.${LANG3}1.gz: opusparcus_v1
	mkdir -p $(dir $@)
	${CAT_TSVFILE} | head -${MAXLINES} | cut -f2 | python3 detokenize.py -l ${LANG2} | gzip -c > $@

${DATASPLIT}/opusparcus.${LANG3}2.gz: opusparcus_v1
	mkdir -p $(dir $@)
	${CAT_TSVFILE} | head -${MAXLINES} | cut -f3 | python3 detokenize.py -l ${LANG2} | gzip -c > $@

