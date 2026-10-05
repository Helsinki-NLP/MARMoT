

.PHONY: all
all: wmt_devsets
	${MAKE} convert-all
	${MAKE} cleanup

.PHONY: cleanup
cleanup:
	find wmt_devsets -delete

wmt_devsets:
	wget https://data.statmt.org/wmt24/general-mt/wmt24_GeneralMT-devsets.zip
	unzip wmt24_GeneralMT-devsets.zip
	rm -f wmt24_GeneralMT-devsets.zip


XMLFILES  := $(wildcard wmt_devsets/xml/*.xml)
CONVERTED := $(addsuffix .done,${XMLFILES})

TESTSETS  := $(sort $(basename $(basename $(notdir $(XMLFILES)))))
TESTSET   ?= $(firstword $(TESTSETS))

.PHONY: convert-all
convert-all: ${CONVERTED}

${CONVERTED}: %.done: %
	${MAKE} TESTSET=$(basename $(basename $(notdir $<))) \
		LANGPAIR=$(patsubst .%,%,$(suffix $(basename $(notdir $<)))) \
	convert
	touch $@


LANGPAIRS := $(patsubst $(TESTSET).%.xml,%,$(notdir $(wildcard wmt_devsets/xml/${TESTSET}.*.xml)))
LANGPAIR  ?= $(firstword ${LANGPAIRS})
SRC       := $(firstword $(subst -, ,${LANGPAIR}))
TRG       := $(lastword $(subst -, ,${LANGPAIR}))

LANGPAIR3 := $(shell iso639 -3 -n -p ${LANGPAIR})
SRC3      := $(firstword $(subst -, ,${LANGPAIR3}))
TRG3      := $(lastword $(subst -, ,${LANGPAIR3}))

.PHONY: convert
convert: $(TESTSET)/$(TESTSET).${LANGPAIR3}.${SRC3}.gz \
	$(TESTSET)/$(TESTSET).${LANGPAIR3}.${TRG3}.gz


$(TESTSET)/$(TESTSET).${LANGPAIR3}.${SRC3}.gz: wmt_devsets/xml/$(TESTSET).${LANGPAIR}.xml
	@mkdir -p $(dir $@)
	python3 wmt_devsets/xml/extract.py -o $(basename $(basename $@)) $<
	if [ $(basename $(basename $@)).${SRC} != $(basename $(basename $@)).${SRC3} ]; then \
	  mv $(basename $(basename $@)).${SRC} $(basename $(basename $@)).${SRC3}; \
	fi
	gzip -f $(basename $(basename $@)).${SRC3}

$(TESTSET)/$(TESTSET).${LANGPAIR3}.${TRG3}.gz: $(TESTSET)/$(TESTSET).${LANGPAIR3}.${SRC3}.gz
	if [ $(basename $(basename $@)).${TRG} != $(basename $(basename $@)).${TRG3} ]; then \
	  mv $(basename $(basename $@)).${TRG} $(basename $(basename $@)).${TRG3}; \
	fi
	gzip -f $(basename $(basename $@)).${TRG3}
