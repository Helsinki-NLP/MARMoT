

.PHONY: all
all: NTREX
	${MAKE} move
	rm -fr NTREX

NTREX:
	git clone https://github.com/MicrosoftTranslator/NTREX.git


TXT_FILES := $(wildcard NTREX/NTREX-128/*.txt)
LANGUAGES := $(patsubst .%,%,$(suffix $(basename $(notdir $(TXT_FILES)))))


.PHONY: move
move:
	for l in ${LANGUAGES}; do \
	  echo "moving $$l"; \
	  n=`echo $$l | tr '-' '_'`; \
	  mv -f NTREX/NTREX-128/newstest2019-???.$$l.txt newstest2019.$$n; \
	  gzip -f newstest2019.$$n; \
	done
