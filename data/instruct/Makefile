
include ../../tools/slurMake/slurm.mk


FLANDATA_LANGS := $(sort $(notdir $(patsubst %/,%,$(dir $(wildcard ../FLAN_perlang_*_mt_*/*/data*)))))
FLAN_TRAINDATA := $(patsubst %,train/%.stats,${FLANDATA_LANGS})
FLAN_DEVDATA   := $(patsubst %,dev/%.stats,${FLANDATA_LANGS})

.PHONY: all dev train
all: ${FLAN_DEVDATA} ${FLAN_TRAINDATA}
train: ${FLAN_TRAINDATA}
dev: ${FLAN_DEVDATA}

${FLAN_TRAINDATA}:
	mkdir -p $(dir $@)
	for d in $(wildcard $(patsubst train/%.stats,../FLAN_perlang_*_mt_*/%/data.*,$@)); do \
	  b=`basename $$d`; \
	  tail -n +201 $$d >> $(@:.stats=).$$b; \
	done
	wc $(@:.stats=.*) > $@
	pigz $(@:.stats=.*)
	gunzip $@.gz

${FLAN_DEVDATA}:
	mkdir -p $(dir $@)
	for d in $(wildcard $(patsubst dev/%.stats,../FLAN_perlang_*_mt_*/%/data.*,$@)); do \
	  b=`basename $$d`; \
	  head -200 $$d >> $(@:.stats=).$$b; \
	done
	wc $(@:.stats=.*) > $@
	pigz $(@:.stats=.*)
	gunzip $@.gz


# ${FLAN_TRAINDATA}:
# 	mkdir -p $(dir $@)
# 	mkdir -p $(dir $(patsubst train/%,dev/%,$@))
# 	for d in $(wildcard $(patsubst train/%.stats,../FLAN_perlang_*_mt_*/%/data.*,$@)); do \
# 	  b=`basename $$d`; \
# 	  head -200 $$d >> $(patsubst train/%,dev/%,$(@:.stats=)).$$b; \
# 	  tail -n +201 $$d >> $(@:.stats=).$$b; \
# 	done
# 	wc $(@:.stats=.*) > $@
# 	pigz $(@:.stats=.*) $(patsubst train/%,dev/%,$(@:.stats=.*))
# 	gunzip $@.gz


LANG_GROUPS  := bat ccs cel euq gmq gmw gem grk ine mul roa sem sla trk urj zle zls zlw

.PHONY: info
info:
	@echo ${FLAN_TRAINDATA}

INSTRUCT_DATASETS := $(sort $(basename $(notdir $(wildcard train/*.stats))))


## merge data into language groups (on input side)

.PHONY: merge-langgroups
merge-langgroups:
	mkdir -p langgroups/train langgroups/dev
	@for p in ${INSTRUCT_DATASETS}; do \
	  echo "process $$p ..."; \
	  for l in ${LANG_GROUPS}; do \
	    s=`echo $$p | cut -f1 -d-`; \
	    t=`echo $$p | cut -f2 -d-`; \
	    x=`echo "$$s" | tr '+' ' ' | xargs langgroup -P | tr ':' ' ' | tr ' ' "\n" | grep $$l | uniq -c | sed 's/^ *//' | cut -f1 -d' '`; \
	    y=`echo "$$s" | tr '+' ' ' | wc -w`; \
	    if [ "$$x" == "$$y" ]; then \
	      echo "add $$p to $$l-$$t"; \
	      if [ $$s == $$t ]; then \
	        pigz -cd < train/$$p.data.$${s}1.gz >> langgroups/train/$$l-$$t.$$l; \
	        pigz -cd < train/$$p.data.$${t}2.gz >> langgroups/train/$$l-$$t.$$t; \
	        pigz -cd < dev/$$p.data.$${s}1.gz >> langgroups/dev/$$l-$$t.$$l; \
	        pigz -cd < dev/$$p.data.$${t}2.gz >> langgroups/dev/$$l-$$t.$$t; \
	      else \
	        pigz -cd < train/$$p.data.$${s}.gz >> langgroups/train/$$l-$$t.$$l; \
	        pigz -cd < train/$$p.data.$${t}.gz >> langgroups/train/$$l-$$t.$$t; \
	        pigz -cd < dev/$$p.data.$${s}.gz >> langgroups/dev/$$l-$$t.$$l; \
	        pigz -cd < dev/$$p.data.$${t}.gz >> langgroups/dev/$$l-$$t.$$t; \
	      fi \
	    fi \
	  done \
	done
	find langgroups -empty -delete
	for f in `find langgroups/train -type f -not -name '*.gz' | cut -f1 -d. | sort-u`; do \
	  wc $$f.* > $$f.stats; \
	done
	find langgroups/dev -type f -not -name '*.gz' | xargs pigz -f
	find langgroups/train -type f -not -name '*.gz' | xargs pigz -f





#### OLD OLD OLD ##########


FLANDATA := ../FLAN_proc

ZEROSHOT := $(wildcard ${FLANDATA}/*_zsopt_data)
FEWSHOT  := $(wildcard ${FLANDATA}/*_fsopt_data)

SUBSET  := zeroshot
DATADIRS := ${ZEROSHOT}


.PHONY: all-original
all-original:
	${MAKE} SUBSET=zeroshot DATADIRS="${ZEROSHOT}" subsets
	${MAKE} SUBSET=fewshot DATADIRS="${FEWSHOT}" subsets



.PHONY: subsets
subsets: ${SUBSET}/dev/data.eng1.gz ${SUBSET}/dev/data.eng2.gz \
	${SUBSET}/train/data.eng1.gz ${SUBSET}/train/data.eng2.gz


${SUBSET}/dev/data.eng1.gz:
	mkdir -p $(dir $@)
	rm -f $(@:.gz=)
	for d in ${DATADIRS}; do \
	  head -200 $$d/data.in >> $(@:.gz=); \
	done
	pigz $(@:.gz=)

${SUBSET}/dev/data.eng2.gz:
	mkdir -p $(dir $@)
	rm -f $(@:.gz=)
	for d in ${DATADIRS}; do \
	  head -200 $$d/data.out >> $(@:.gz=); \
	done
	pigz $(@:.gz=)

${SUBSET}/train/data.eng1.gz:
	mkdir -p $(dir $@)
	rm -f $(@:.gz=)
	for d in ${DATADIRS}; do \
	  tail -n +201 $$d/data.in >> $(@:.gz=); \
	done
	pigz $(@:.gz=)

${SUBSET}/train/data.eng2.gz:
	mkdir -p $(dir $@)
	rm -f $(@:.gz=)
	for d in ${DATADIRS}; do \
	  tail -n +201 $$d/data.out >> $(@:.gz=); \
	done
	pigz $(@:.gz=)



