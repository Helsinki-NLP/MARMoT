

LANG2 := ar bg cs da de el en es et fa fi fr he hi hr hu id it ko lt lv ms nl no pl pt pt_BR ro ru sk sl sr sv ta te tr uk vi zh_Hans zh_Hant

LANG3 := $(shell iso639 -n -3 -k ${LANG2})

MOVIES := $(sort $(basename $(notdir $(wildcard linkset/*.*))))

SUBFILES := $(patsubst %,opensubs2024-multiset.%,${LANG3})

all: ${SUBFILES}

opensubs2024-multiset.%:
	rm -f $@
	( l=`iso639 -2 -n -k ${patsubst opensubs2024-multiset.%,%,$@} | sed 's/Hans/CN/;s/Hant/TW/;'`; \
	  for m in ${MOVIES}; do \
	    echo "cat linkset/$$m.$$l >> $@"; \
	    cat linkset/$$m.$$l >> $@; \
	  done )
