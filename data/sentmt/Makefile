#
# combine sentence-level MT training data and shuffle them
# - requires opus and tatoeba data sets
# - requires terashuf and pigz commands
#

SHELL := bash

include ../../tools/slurMake/slurm.mk


LANGPAIRS := $(sort $(basename $(basename $(notdir $(wildcard ../opus/*/*.gz) $(wildcard ../tatoeba/train/*.gz)))))
STATS := $(patsubst %,%.stats,${LANGPAIRS})

all: ${STATS}

${STATS}:
	@( l=$(basename $@); \
	  s=$(firstword $(subst -, ,$(basename $@))); \
	  t=$(lastword $(subst -, ,$(basename $@))); \
	  rm -f $@.src $@.trg; \
	  echo "create shuffled sent-MT data for $$l"; \
	  for S in `ls ../tatoeba/train/$$l.$$s.gz ../opus/*/$$l.$$s.gz | sort`; do \
	    echo "add $$S"; \
	    pigz -cd $$S >> $@.src; \
	  done; \
	  for T in `ls ../tatoeba/train/$$l.$$t.gz ../opus/*/$$l.$$t.gz | sort`; do \
	    echo "add $$T"; \
	    pigz -cd $$T >> $@.trg; \
	  done; \
	  paste $@.src $@.trg | terashuf \
	  | tee >(cut -f1 | pigz -c > $$l.$$s.gz) | cut -f2 | pigz -c > $$l.$$t.gz; \
	  pigz -cd < $$l.$$s.gz | wc -lw > $@; \
	  pigz -cd < $$l.$$t.gz | wc -lw >> $@; \
	  rm -f $@.src $@.trg; )
