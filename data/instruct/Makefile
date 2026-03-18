
include ../../tools/slurMake/slurm.mk


FLANDATA_LANGS := $(sort $(notdir $(patsubst %/,%,$(dir $(wildcard ../FLAN_perlang_*_mt_*/*/data*)))))
FLAN_TRAINDATA := $(patsubst %,train/%.stats,${FLANDATA_LANGS})

all: ${FLAN_TRAINDATA}

${FLAN_TRAINDATA}:
	mkdir -p $(dir $@)
	mkdir -p $(dir $(patsubst train/%,dev/%,$@))
	for d in $(wildcard $(patsubst train/%.stats,../FLAN_perlang_*_mt_*/%/data.*,$@)); do \
	  b=`basename $$d`; \
	  head -20 $$d >> $(patsubst train/%,dev/%,$(@:.stats=)).$$b; \
	  tail -n +201 $$d >> $(@:.stats=).$$b; \
	done
	wc $(@:.stats=.*) > $@
	pigz $(@:.stats=.*) $(patsubst train/%,dev/%,$(@:.stats=.*))
	gunzip $@.gz


info:
	@echo ${FLAN_TRAINDATA}



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



