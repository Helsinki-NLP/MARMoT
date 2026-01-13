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



## if the mode meta file exits: continue from existing checkpoint

ifneq ($(wildcard ${MODEL_META}),)
  TRAIN_FROM = --train_from ${MODEL_PATH} --reset_optim none
endif



## train a model

.PHONY: ${MODEL_DIR}/train

ifeq (${NR_OF_NODES},1)

##----------------------------
## single-node training
##----------------------------

${MODEL_DIR}/train: ${TRAIN_CONFIGFILE}
	${LOAD_MAMMOTH_ENV} ${MAMMOTH_ENV_PYTHON} ${MAMMOTH_DIR}/train.py ${TRAIN_FROM} \
		-save_model ${MODEL_PATH} \
		-config $<


else

##----------------------------
## multi-node training
##----------------------------


.PHONY: ${MODEL_DIR}/train
${MODEL_DIR}/train: ${TRAIN_CONFIGFILE}
	${LOAD_MAMMOTH_ENV} ${MAKE} MASTER_NODE=${MASTER_NODE} MASTER_PORT=${MASTER_PORT} multi-node-train


.PHONY: multi-node-train
multi-node-train:
	( ${MAMMOTH_ENV_ACTIVATE}; \
	  echo "Node ${SLURM_NODEID} starting training"; \
	  echo "Master node: ${MASTER_NODE}"; \
	  echo "Master port: ${MASTER_PORT}"; \
	  export TOKENIZERS_PARALLELISM=False; \
	  ${MAMMOTH_ENV_PYTHON} ${MAMMOTH_DIR}/train.py ${TRAIN_FROM} \
		-config ${TRAIN_CONFIGFILE} \
		-save_model ${MODEL_PATH} \
		--node_rank ${SLURM_PROCID} \
		--master_ip ${MASTER_NODE} \
		--master_port ${MASTER_PORT} )

endif







##----------------------------
## simplified training target
##----------------------------


.PHONY: train2
train2: train2-slurm
	${MAKE} ${MODEL_DIR}/train.slurmjob

.PHONY: train2-slurm
train2-slurm: ${TRAIN_CONFIGFILE}
	@echo "make ${MODEL_DIR}/train2.slurm"
	${MAKE} SLURM_TIME=${TRAIN_WALLTIME} \
		SLURM_NODES=${TRAIN_NR_OF_NODES} \
		SLURM_GPUS=${TRAIN_GPUS_PER_NODE} \
		SLURM_CPUS_PER_TASK=$(TRAIN_CPUS_PER_TASK) \
		SLURM_MEM=$(TRAIN_MEM_PER_NODE) \
	${MODEL_DIR}/train2.slurm


ifneq (${NR_OF_NODES},1)
  MAMMOTH_COMMUNICATION_PARAMS = --node_rank ${SLURM_PROCID} \
				--master_ip ${MASTER_NODE} \
				--master_port ${MASTER_PORT}
endif

.PHONY: ${MODEL_DIR}/train2
${MODEL_DIR}/train2: ${TRAIN_CONFIGFILE}
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


## print information from the reporting steps

.PHONY: print-train-progress
print-train-progress:
	@for t in `seq $(words ${TASKS})`; do \
	  ${MAKE} -s TASK_NR=$$t print-task-progress; \
	  echo ''; \
	done

.PHONY: print-task-progress
print-task-progress:
	@grep ' Step ' ${TRAIN_LOGFILE} | grep 'GPU ${TASK_GPU}' \
	| cut -f2 -d] | sed 's/ *: Step/${TASK}:/' \
	| sed 's/\/[0-9]*;/;/' | tr ';' "\t"



## print information from validation steps

PRINT_METRIC   ?= bleu

ifdef SELECT_LAST_VALID
  SELECT_VALID_CMD := | tail -${SELECT_LAST_VALID}
endif

ifdef SELECT_FIRST_VALID
  SELECT_VALID_CMD := | head -${SELECT_FIRST_VALID}
endif

## select first and last N validation steps:
## adapted from from https://stackoverflow.com/questions/28615961/how-can-i-read-first-n-and-last-n-lines-from-a-file
## sed ':a;$q;N;(n+1),(n*2)P;(n+1),$D;ba'

ifdef SELECT_FIRST_LAST_VALID
  SELECT_VALID_CMD := | sed ":a;\$$q;N;$$(( ${SELECT_FIRST_LAST_VALID}+1 )),$$(( ${SELECT_FIRST_LAST_VALID}*2 ))P;$$(( ${SELECT_FIRST_LAST_VALID}+1 )),\$$D;ba"
endif


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
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_VALID_CMD} \
	    | tr ',}' "\n\n" \
	    | grep "\"${PRINT_METRIC}\":" \
	    | cut -f2 -d: | xargs printf "%.3f	" ); \
	    echo "$${gpus[$$i]}	$${tasks[$$i]}	$${score}"; \
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
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_VALID_CMD} \
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


