#-*-makefile-*-


#--------------------------------------------------------------
# training - submit SLURM job for training a model
#--------------------------------------------------------------


# random port for distributed training communication
MASTER_PORT ?= 9973

# default resource allocations
TRAIN_NR_OF_NODES   ?= ${NR_OF_NODES}
TRAIN_GPUS_PER_NODE ?= ${GPUS_PER_NODE}
TRAIN_CPUS_PER_TASK ?= $(shell echo $$(( ${GPUS_PER_NODE} * ${MAX_CPUS_PER_GPU} )) )
TRAIN_MEM_PER_NODE  ?= $(shell echo $$(( ${GPUS_PER_NODE} * ${MAX_MEM_PER_GPU} )) )G
TRAIN_WALLTIME      ?= ${SLURM_MAX_GPU_TIME}

.PHONY: train
train: train-slurm
	${MAKE} ${MODEL_DIR}/train.slurmjob

.PHONY: train-slurm
train-slurm: ${TRAIN_CONFIGFILE}
	@echo "make ${MODEL_DIR}/train.slurm"
	${MAKE} SLURM_TIME=${TRAIN_WALLTIME} \
		SLURM_NODES=${TRAIN_NR_OF_NODES} \
		SLURM_GPUS=${TRAIN_GPUS_PER_NODE} \
		SLURM_CPUS_PER_TASK=$(TRAIN_CPUS_PER_TASK) \
		SLURM_MEM=$(TRAIN_MEM_PER_NODE) \
	${MODEL_DIR}/train.slurm





##------------------------------------------------------------------
## train a model
##------------------------------------------------------------------


## if the mode meta file exits: continue from existing checkpoint

ifneq ($(wildcard ${MODEL_META}),)
  TRAIN_FROM = --train_from ${MODEL_PATH} --reset_optim none
endif

## for multi-node runs: need to set communication parameters

ifneq (${NR_OF_NODES},1)
  MAMMOTH_COMMUNICATION_PARAMS = --node_rank ${SLURM_PROCID} \
				--master_ip ${MASTER_NODE} \
				--master_port ${MASTER_PORT}
endif

.PHONY: ${MODEL_DIR}/train
${MODEL_DIR}/train: ${TRAIN_CONFIGFILE}
	${LOAD_MAMMOTH_ENV} ${MAMMOTH_ENV_PYTHON} \
	${MAMMOTH_DIR}/train.py ${MAMMOTH_COMMUNICATION_PARAMS} ${TRAIN_FROM} \
		-save_model ${MODEL_PATH} \
		-config $<








##------------------------------------------------------------------
## reporting targets:
## show scores for each task and validation step
##
## - select the last n validation steps with SELECT_LAST_VALID=n
## - select the first n validation steps with SELECT_FIRST_VALID=n
## - PRINT_METRIC: set name of validation metric to be reported
##   possible values: perplexity, accuracy, crossentropy, bleu
##------------------------------------------------------------------


## show a list of tasks and their GPU assignments

task-info:
	@( tasks=(${TASKS}); \
	  gpus=(${TASK_GPU_ASSIGNMENTS}); \
	  for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    echo "$${gpus[$$i]}	$${tasks[$$i]}"; \
	  done )


TRAIN_LOGFILES := $(sort $(wildcard ${MODEL_DIR}/train.*.err))
TRAIN_LOGFILE  ?= $(lastword ${TRAIN_LOGFILES})


## select only a certain sub-set of logfiles )can be used for any line-selection command

ifdef PRINT_LAST
  SELECT_LINES_CMD := | tail -${PRINT_LAST}
endif

ifdef PRINT_FIRST
  SELECT_LINES_CMD := | head -${PRINT_FIRST}
endif

## select first and last N validation steps:
## adapted from from https://stackoverflow.com/questions/28615961/how-can-i-read-first-n-and-last-n-lines-from-a-file
## sed ':a;$q;N;(n+1),(n*2)P;(n+1),$D;ba'

ifdef PRINT_FIRST_LAST
  SELECT_LINES_CMD := | sed ":a;\$$q;N;$$(( ${PRINT_FIRST_LAST}+1 )),$$(( ${PRINT_FIRST_LAST}*2 ))P;$$(( ${PRINT_FIRST_LAST}+1 )),\$$D;ba"
endif



## print information from the reporting steps

.PHONY: print-train-progress print-training-progress
print-training-progress print-train-progress:
	@for t in `seq $(words ${TASKS})`; do \
	  ${MAKE} -s TASK_NR=$$t print-task-progress; \
	  echo ''; \
	done

.PHONY: print-task-progress
print-task-progress:
	@grep ' Step ' ${TRAIN_LOGFILE} | grep 'GPU ${TASK_GPU}' \
	| cut -f2 -d] | sed 's/ *: Step/${TASK}:/' \
	| sed 's/\/[0-9]*;/;/' | tr ';' "\t" ${SELECT_LINES_CMD}



## print information from validation steps

PRINT_METRIC   ?= bleu

## print table of validation scores for each task
## (some alternative names as short-cuts)

PRINT_VALID_SCORE_ALIASES := 	print-valid-score \
				print-valid-scores \
				print-validation-score \
				print-validation-scores

.PHONY: ${PRINT_VALID_SCORE_ALIASES}
${PRINT_VALID_SCORE_ALIASES}:
	@( tasks=(${TASKS}); \
	   gpus=(${TASK_GPU_ASSIGNMENTS}); \
	   echo "gpu	task	scores"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    score=$$( grep '"type": *"validation"' ${TRAIN_LOGFILE} \
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_LINES_CMD} \
	    | tr ',}' "\n\n" \
	    | grep "\"${PRINT_METRIC}.*\":" \
	    | cut -f2 -d: | xargs printf "%.3f	" ); \
	    if [ "$${score}" != "0.000	" ]; then \
	      echo "$${gpus[$$i]}	$${tasks[$$i]}	$${score}"; \
	    fi \
	   done )


## display score differences between validation steps
## (some alternative names as short-cuts)

PRINT_VALID_DIFF_ALIASES := 	print-valid-diff \
				print-valid-diffs \
				print-validation-diff \
				print-validation-diffs \
				print-validation-differences \
				print-validation-difference

.PHONY: ${PRINT_VALID_DIFF_ALIASES}
${PRINT_VALID_DIFF_ALIASES}:
	@( tasks=(${TASKS}); \
	   gpus=(${TASK_GPU_ASSIGNMENTS}); \
	   echo "gpu	task	first	diffs"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    score=($$( grep '"type": *"validation"' ${TRAIN_LOGFILE} \
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_LINES_CMD} \
	    | tr ',}' "\n\n" \
	    | grep "\"${PRINT_METRIC}\":" \
	    | cut -f2 -d: | xargs printf "%.3f	" )); \
	    echo -n "$${gpus[$$i]}	$${tasks[$$i]}	$${score[0]}"; \
	    last=$${score[0]}; \
	    for (( j=1; j<$${#score[@]}; j++ )); do \
	      diff=`echo "$${score[$$j]} $${last}" | awk '{print $$1-$$2}'`; \
	      echo -n "	$${diff}"; \
	      last=$${score[$$j]}; \
	    done; \
	    echo ''; \
	   done )


