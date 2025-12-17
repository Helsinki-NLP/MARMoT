#-*-makefile-*-


MAX_LINES  ?= 100000000
VOCAB_SIZE ?= 32000


DATASET   ?= tatoeba
DATADIR   ?= ../../${DATASET}/train

LANGUAGES ?= $(sort $(subst -, ,$(basename $(basename $(notdir $(wildcard ${DATADIR}/*-*.*.gz))))))
LANGUAGE  ?= $(firstword ${LANGUAGES})

MAMMOTH_HOME       ?= ../../mammoth
TRAIN_HF_TOKENIZER := python3 ${MAMMOTH_HOME}/examples/hf_tokenizers/train.py


## OpenEuroLLM languages
## - note that we change to bos_Latn to match the data from Tatoeba training data
## - filter out languages that we don't have in Tatoeba training data (slk)

OELLM_LANGS := 	$(filter ${LANGUAGES},\
		deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos_Latn isl kat \
		mkd sqi srp_Cyrl eng)

TOKENIZER      := ${LANGUAGE}/${VOCAB_SIZE}/tokenizer.json
TOKENIZERS     := $(patsubst %,%/${VOCAB_SIZE}/tokenizer.json,${LANGUAGES})
TOKENIZER_JOBS := $(patsubst %,%.submit,${TOKENIZERS})


## run for all available languages

.PHONY: all all-jobs
all: ${TOKENIZERS}
all-jobs: ${TOKENIZER_JOBS}


## run for OpenEuroLLM languages

.PHONY: oellm oellm-jobs
oellm:
	${MAKE} LANGUAGES="${OELLM_LANGS}" all

oellm-jobs:
	${MAKE} LANGUAGES="${OELLM_LANGS}" all-jobs


# run for a single language (specify with LANGUAGE=...)

.PHONY: tokenizer tokenizer-job
tokenizer: ${TOKENIZER}
tokenizer-job: ${TOKENIZER}.submit



${TOKENIZERS}:
	mkdir -p $(dir $@)
	zcat $(DATADIR)/*.$(firstword $(subst /, ,$@)).gz | head -${MAX_LINES} > $(dir $@)traindata.txt
	wc $(dir $@)traindata.txt
	${TRAIN_HF_TOKENIZER} --input_file $(dir $@)traindata.txt --vocab_size ${VOCAB_SIZE} --output_dir $(dir $@)
	rm -f $(dir $@)traindata.txt



##---------------------------------------
## submit a slurm job
## works only on LUMI
##---------------------------------------

WHOAMI := ${shell whoami}
SLURM_MAX_NR_JOBS := 200

%.submit:
	mkdir -p $(dir $@)
	if [ ! -e $(@:.submit=) ]; then \
	  while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	    echo "waiting for space in the queue";\
	    sleep 1; \
	  done; \
	  echo '#!/bin/bash'                   >$@; \
	  echo ''                             >>$@; \
	  echo '#SBATCH -A project_462000964' >>$@; \
	  echo '#SBATCH -J tokenizer'         >>$@; \
	  echo '#SBATCH -o $(dir $@)train.%j.log'  >>$@; \
	  echo '#SBATCH -e $(dir $@)train.%j.err'  >>$@; \
	  echo '#SBATCH --partition=small'    >>$@; \
	  echo '#SBATCH --nodes=1'            >>$@; \
	  echo '#SBATCH --cpus-per-task=8'    >>$@; \
	  echo '#SBATCH --mem=48G'            >>$@; \
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

