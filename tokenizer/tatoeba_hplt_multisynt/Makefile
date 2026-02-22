#-*-makefile-*-


MAX_LINES  ?= 100000000
MAX_LINES_HPLT  ?= 20000000
MAX_LINES_SYNT  ?= 20000000
MAX_LINE_LENGTH ?= 2048

VOCAB_SIZE ?= 32000
# VOCAB_SIZE ?= 64000


DATASET   ?= tatoeba
DATADIR   ?= ../../data/${DATASET}/train

MULTISYNT_DATADIR ?= ../../data/multisynt/train/len1024
HPLT_DATADIR      ?= ../../data/opus/HPLT

LANGUAGES ?= $(sort $(subst -, ,$(basename $(basename $(notdir $(wildcard ${DATADIR}/*-*.*.gz))))))
LANGUAGE  ?= $(firstword ${LANGUAGES})


MAMMOTH_HOME       ?= ../../mammoth
TRAIN_HF_TOKENIZER := python3 ${MAMMOTH_HOME}/examples/hf_tokenizers/train.py




## OpenEuroLLM languages
## - note that we change to bos_Latn to match the data from Tatoeba training data
## - filter out languages that we don't have in Tatoeba training data (slk)

# OELLM_LANGS := 	$(filter ${LANGUAGES},\
# 		deu fin nob nno spa mlt ukr \
# 		gle glg cat ces swe tur bul \
# 		lav lit slk nld dan ell est fra \
# 		hrv hun ita pol por ron \
# 		slv eus bos isl kat \
# 		mkd sqi srp_Cyrl eng)

OELLM_LANGS := 	deu fin nob nno spa mlt ukr \
		gle glg cat ces swe tur bul \
		lav lit slk nld dan ell est fra \
		hrv hun ita pol por ron \
		slv eus bos isl kat \
		mkd sqi srp_Cyrl eng


TATOEBA_LANGS := afr ara asm awa aze_Latn bel ben bos_Latn \
		bul cat ceb ces cym dan deu ell eng \
		epo est eus fao fas fin fra gla gle \
		glg hau_Latn hbs_Cyrl hbs_Latn heb hin \
		hrv hun hye ilo isl ita jav jpn kab \
		kat kaz_Cyrl khm kor lav lit ltz mal \
		mar mkd mlt mon mri msa_Latn mya nld \
		nob nor oci pol por prs que ron rus \
		slk slv spa sqi srp_Cyrl srp_Latn swa swe \
		tam tat tel tgl_Latn tha tur uig_Arab ukr \
		urd uzb_Latn vie war yid zho_Hans zho_Hant
# zho_Hans_CN zho_Hans_TW 


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



tatoeba:
	${MAKE} LANGUAGES="${TATOEBA_LANGS}" all

tatoeba-jobs:
	${MAKE} LANGUAGES="${TATOEBA_LANGS}" all-jobs

tatoeba-job:
	${MAKE} tatoeba.submit


# run for a single language (specify with LANGUAGE=...)

.PHONY: tokenizer tokenizer-job
tokenizer: ${TOKENIZER}
tokenizer-job: ${TOKENIZER}.submit


## concatenate data from all three data sets (max MAX_LINES lines each) if they exist
## and train the tokenizer model

## should we add this?
##  | grep -v '.\{${MAX_LINE_LENGTH}\}'

${TOKENIZERS}:
	mkdir -p $(dir $@)
	if [ `find $(DATADIR) -name '*.$(firstword $(subst /, ,$@)).gz' | wc -l` -gt 0 ]; then \
	  zcat $(DATADIR)/*.$(firstword $(subst /, ,$@)).gz | head -${MAX_LINES} > $(dir $@)traindata.txt; \
	fi
	if [ `find ${MULTISYNT_DATADIR} -name '*.$(firstword $(subst /, ,$@)).gz' | wc -l` -gt 0 ]; then \
	  zcat ${MULTISYNT_DATADIR}/*.$(firstword $(subst /, ,$@)).gz | head -${MAX_LINES_SYNT} >> $(dir $@)traindata.txt; \
	fi
	if [ `find ${HPLT_DATADIR} -name '*.$(firstword $(subst /, ,$@)).gz' | wc -l` -gt 0 ]; then \
	  zcat ${HPLT_DATADIR}/*.$(firstword $(subst /, ,$@)).gz | head -${MAX_LINES_HPLT} >> $(dir $@)traindata.txt; \
	fi
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
HPC_PROJECT = project_462001087
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
