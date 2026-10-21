#-*-makefile-*-
#
# What is different here?
#   - use the randomized sentmt data instead of Tatoeba+HPLT
#   - slightly bigger vocabs (closer to binary numbers)
#   - combine different scripts and local variants
#   - use data from all parallel corpora that contain the language   
#

MAX_LINES       ?= 100000000
MAX_LINES_SYNT  ?= 20000000
MAX_LINE_LENGTH ?= 2048

## closer to binary numbers
## reserve 64 spots for possible extensions / extra tokens

# VOCAB_SIZE ?= 16320
VOCAB_SIZE ?= 32704
# VOCAB_SIZE ?= 65472



DATASET           ?= sentmt
DATADIR           ?= ../../data/${DATASET}
MULTISYNT_DATADIR ?= ../../data/multisynt/train/len1024


# LANGUAGES ?= $(sort $(subst -, ,$(basename $(basename $(notdir $(wildcard ${DATADIR}/*-*.*.gz))))))
LANGUAGES ?= $(shell ls ${DATADIR}/*-*.*.gz | grep -v corpora | rev | cut -f2 -d. | rev | cut -f1 -d_ | sort -u | tr "\n" ' ')
LANGUAGE  ?= $(firstword ${LANGUAGES})


MAMMOTH_HOME       ?= /scratch/project_462001509/shared/mammoth-shared/mammoth_pytorch/mammoth
TRAIN_HF_TOKENIZER := python3 ${MAMMOTH_HOME}/mammoth/bin/build_vocab.py


TOKENIZER      := ${LANGUAGE}/${VOCAB_SIZE}/tokenizer.json
TOKENIZERS     := $(patsubst %,%/${VOCAB_SIZE}/tokenizer.json,${LANGUAGES})
TOKENIZER_JOBS := $(patsubst %,%.submit,${TOKENIZERS})




METALANGS        := $(sort $(shell iso639 -3 -m -n ${LANGUAGES}))
PARENTLANGS      := $(sort $(shell langgroup -p ${METALANGS}))
GRANDPARENTLANGS := $(sort $(shell langgroup -p ${PARENTLANGS}))
ANCESTORLANGS    := $(sort $(subst :, ,$(shell langgroup -P ${METALANGS})))

LANGGROUPS       ?= $(filter-out ine mul sqj,${ANCESTORLANGS})
LANGGROUP        ?= $(lastword ${ANCESTORLANGS})

LANGGROUP_TOKENIZER      := ${LANGGROUP}/${VOCAB_SIZE}/tokenizer.json
LANGGROUP_TOKENIZERS     := $(patsubst %,%/${VOCAB_SIZE}/tokenizer.json,${LANGGROUPS})
LANGGROUP_TOKENIZER_JOBS := $(patsubst %,%.submit,${LANGGROUP_TOKENIZERS})



#-------------------------------------
# tokenizers for individual languages
#-------------------------------------

## run for all available languages

.PHONY: all all-jobs
all: ${TOKENIZERS}
all-jobs: ${TOKENIZER_JOBS}


# run for a single language (specify with LANGUAGE=...)

.PHONY: tokenizer tokenizer-job
tokenizer: ${TOKENIZER}
tokenizer-job: ${TOKENIZER}.submit


#-------------------------------------
# tokenizers for language groups
#-------------------------------------

.PHONY: langgroup-info
langgroup-info:
	@echo "$(words ${LANGGROUPS}) language groups:"
	@echo "${LANGGROUPS}"

.PHONY: langgroup-tokenizer langgroup-tokenizers langgroup-tokenizer-job langgroup-tokenizers-job langgroup-tokenizer-jobs
langgroup-tokenizer: ${LANGGROUP_TOKENIZER}
langgroup-tokenizers: ${LANGGROUP_TOKENIZERS}

langgroup-tokenizers-job: langgroup-tokenizers.submit
langgroup-tokenizer-job: ${LANGGROUP_TOKENIZER}.submit
langgroup-tokenizer-jobs: ${LANGGROUP_TOKENIZER_JOBS}


## concatenate data from all three data sets (max MAX_LINES lines each) if they exist
## shuffle the data and extract MAX_LINES from the shufled data
## and, finally, train the tokenizer model

## should we add this?
##  | grep -v '.\{${MAX_LINE_LENGTH}\}'

${TOKENIZERS}:
	mkdir -p $(dir $@)
	for d in `find $(DATADIR) -name '*.$(firstword $(subst /, ,$@)).gz'`; do \
	  zcat $$d | head -${MAX_LINES} > $(dir $@)traindata.tmp; \
	done
	for d in `find $(DATADIR) -name '*.$(firstword $(subst /, ,$@))_[A-Za-z0-9]*.gz'`; do \
	  zcat $$d | head -${MAX_LINES} > $(dir $@)traindata.tmp; \
	done
	for d in `find ${MULTISYNT_DATADIR} -name '*.$(firstword $(subst /, ,$@)).gz'`; do \
	  zcat $$d | head -${MAX_LINES_SYNT} > $(dir $@)traindata.tmp; \
	done
	for d in `find ${MULTISYNT_DATADIR} -name '*.$(firstword $(subst /, ,$@))_[A-Za-z0-9]*.gz'`; do \
	  zcat $$d | head -${MAX_LINES_SYNT} > $(dir $@)traindata.tmp; \
	done
	cat > $(dir $@)traindata.tmp | terashuf | head -${MAX_LINES} > $(dir $@)traindata.txt
	rm -f $(dir $@)traindata.tmp
	wc $(dir $@)traindata.txt
	${TRAIN_HF_TOKENIZER} --input_file $(dir $@)traindata.txt --vocab_size ${VOCAB_SIZE} --output_dir $(dir $@)
	rm -f $(dir $@)traindata.txt



${LANGGROUP_TOKENIZERS}:
	mkdir -p $(dir $@)
	rm -f $(dir $@)traindata.txt
	for l in `langgroup $(firstword $(subst /, ,$@))`; do \
	  for d in `find $(DATADIR) -name "*.$$l.gz"`; do \
	    echo "get data from $$d"; \
	    zcat $$d.gz | head -${MAX_LINES} >> $(dir $@)traindata.tmp; \
	  done; \
	  for d in `find $(DATADIR) -name "*.$${l}_[A-Za-z0-9]*.gz"`; do \
	    echo "get data from $$d"; \
	    zcat $$d.gz | head -${MAX_LINES} >> $(dir $@)traindata.tmp; \
	  done; \
	  for d in `find $(MULTISYNT_DATADIR) -name "*.$$l.gz"`; do \
	    echo "get data from $$d"; \
	    zcat $$d.gz | head -${MAX_LINES_SYNT} >> $(dir $@)traindata.tmp; \
	  done; \
	  for d in `find $(MULTISYNT_DATADIR) -name "*.$${l}_[A-Za-z0-9]*.gz"`; do \
	    echo "get data from $$d"; \
	    zcat $$d.gz | head -${MAX_LINES_SYNT} >> $(dir $@)traindata.tmp; \
	  done; \
	done
	cat > $(dir $@)traindata.tmp | terashuf | head -${MAX_LINES} > $(dir $@)traindata.txt
	rm -f $(dir $@)traindata.tmp
	wc $(dir $@)traindata.txt
	${TRAIN_HF_TOKENIZER} --input_file $(dir $@)traindata.txt --vocab_size ${VOCAB_SIZE} --output_dir $(dir $@)
	rm -f $(dir $@)traindata.txt



##---------------------------------------
## submit a slurm job
## works only on LUMI
##---------------------------------------

WHOAMI := ${shell whoami}
SLURM_MAX_NR_JOBS := 200


# HPC_PROJECT = project_462000964
# HPC_PROJECT = project_2001194
# HPC_PROJECT = project_462001087
HPC_PROJECT = project_462001509
HPC_MEM = 256G

%.submit:
	mkdir -p $(dir $@)
	if [ ! -e $(@:.submit=) ]; then \
	  while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	    echo "waiting for space in the queue";\
	    sleep 1; \
	  done; \
	  echo '#!/bin/bash'                   >$@; \
	  echo ''                             >>$@; \
	  echo '#SBATCH -A ${HPC_PROJECT}'    >>$@; \
	  echo '#SBATCH -J tokenizer'         >>$@; \
	  echo '#SBATCH -o $(dir $@)train.%j.log'  >>$@; \
	  echo '#SBATCH -e $(dir $@)train.%j.err'  >>$@; \
	  echo '#SBATCH --partition=small'    >>$@; \
	  echo '#SBATCH --nodes=1'            >>$@; \
	  echo '#SBATCH --cpus-per-task=8'    >>$@; \
	  echo '#SBATCH --mem=${HPC_MEM}'     >>$@; \
	  echo '#SBATCH --time=1-00:00:00'    >>$@; \
	  echo ''                             >>$@; \
	  echo '  echo "Starting at `date`"'  >>$@; \
	  echo ''                             >>$@; \
	  echo '# stops the script when encountering an error' >>$@; \
	  echo '# (useful if running several commands in the same script)' >>$@; \
	  echo 'set -e'                       >>$@; \
	  echo ''                             >>$@; \
	  echo 'module list'                  >>$@; \
	  echo ''                             >>$@; \
	  echo '${MAKE} $(@:.submit=)'        >>$@; \
	  echo ''                             >>$@; \
	  echo '  echo "Finishing at `date`"' >>$@; \
	  echo 'rm -f $@'                     >>$@; \
	  sbatch $@; \
	fi
