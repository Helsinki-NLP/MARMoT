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



.PHONY: print-train-stats
print-train-stats: ${MODEL_DIR}/stats/train-progress.txt \
		${MODEL_DIR}/stats/valid-scores-bleu.txt \
		${MODEL_DIR}/stats/valid-scores-ppl.txt \
		${MODEL_DIR}/stats/valid-diff-bleu.txt \
		${MODEL_DIR}/stats/valid-diff-ppl.txt

.PHONY: print-valid-stats
print-valid-stats: ${MODEL_DIR}/stats/valid-scores-bleu.txt \
		${MODEL_DIR}/stats/valid-scores-ppl.txt


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

ifdef LAST_LOGFILE
  TRAIN_LOGFILES := ${TRAIN_LOGFILE}
endif


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
	@grep ' Step ' ${TRAIN_LOGFILES} | grep 'GPU ${TASK_GPU}' \
	| cut -f2 -d] | sed 's/ *: Step/${TASK_ID}:/' \
	| sed 's/\/[0-9]*;/;/' | tr ';' "\t" ${SELECT_LINES_CMD}



## print information from validation steps

PRINT_METRIC   ?= bleu

## print table of validation scores for each task
## (some alternative names as short-cuts)

PRINT_VALID_SCORE_ALIASES := 	print-valid-score \
				print-valid-scores \
				print-validation-score \
				print-validation-scores



## if we have one task per GPU then we can use a faster variant
## of printing validation scores
## (it fails if there are steps for which no score have been reported)

ifneq (${MULTIPLE_JOBS_PER_GPU},1)

.PHONY: print-valid-scores-table
print-valid-scores-table:
	@( tasks=(${TASKS}); \
	   taskids=(${TASK_IDS}); \
	   gpus=(${TASK_GPU_ASSIGNMENTS}); \
	   steps=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | tr ',}' "\n\n" | grep "\"step\":" | cut -f2 -d: \
	    | uniq ${SELECT_LINES_CMD} | xargs printf "%5d	" ); \
	   echo "gpu	task-ids	$${steps}"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    task=$${tasks[$$i]}; \
	    taskid=$${taskids[$$i]:=$${tasks[$$i]}}; \
	    if [ ${PRINT_METRIC} == 'perplexity' ]; then \
	      pattern="${PRINT_METRIC}"; \
	    else \
	      pattern="${PRINT_METRIC}/$${task}"; \
	    fi; \
	    score=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_LINES_CMD} \
	    | tr ',}' "\n\n" \
	    | grep "\"$${pattern}\":" \
	    | cut -f2 -d: | xargs printf "%.3f	" ); \
	    if [ "$${score}" != "0.000	" ]; then \
	      echo "$${gpus[$$i]}	$${taskid}	$${score}"; \
	    fi \
	   done )

else

## get all validation scores, step by step
## this is slower but does not skip steps if there is no score

.PHONY: print-valid-scores-table
print-valid-scores-table:
	@( tasks=(${TASKS}); \
	   taskids=(${TASK_IDS}); \
	   gpus=(${TASK_GPU_ASSIGNMENTS}); \
	   steps=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | tr ',}' "\n\n" | grep "\"step\":" | cut -f2 -d: \
	    | uniq ${SELECT_LINES_CMD} | xargs printf "%5d	" ); \
	   echo "gpu	task-ids	$${steps}"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    task=$${tasks[$$i]}; \
	    taskid=$${taskids[$$i]:=$${tasks[$$i]}}; \
	    if [ ${PRINT_METRIC} == 'perplexity' ]; then \
	      pattern="${PRINT_METRIC}"; \
	    else \
	      pattern="${PRINT_METRIC}/$${task}"; \
	    fi; \
	    echo -n "$${gpus[$$i]}	$${taskid}"; \
	    for s in $${steps}; do \
	      score=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	      | grep "\"step\": $${s}," \
	      | grep "GPU *$${gpus[$$i]}" \
	      | tr ',}' "\n\n" \
	      | grep "\"$${pattern}\":" \
	      | cut -f2 -d: | xargs printf "%.3f" ); \
	      echo -n "	$${score}"; \
	    done; \
	    echo ""; \
	   done )


## print ppl table per GPU rather than per task
## --> join all tasks on each GPU
## --> this is because perplexity is computed collectively per GPU

.PHONY: print-valid-ppl-table
print-valid-ppl-table:
	@( tasks=(${GPU_TASKS}); \
	   taskids=(${GPU_TASK_IDS}); \
	   gpus=(${ALLOCATED_GPUS}); \
	   steps=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | tr ',}' "\n\n" | grep "\"step\":" | cut -f2 -d: \
	    | uniq ${SELECT_LINES_CMD} | xargs printf "%5d	" ); \
	   echo "gpu	task-ids	$${steps}"; \
	   for i in $$(seq 0 $$(( $(words $(GPU_TASKS))-1 )) ); do \
	    task=$${tasks[$$i]}; \
	    taskid=$${taskids[$$i]}; \
	    score=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_LINES_CMD} \
	    | tr ',}' "\n\n" \
	    | grep '"perplexity":' \
	    | cut -f2 -d: | xargs printf "%.3f	" ); \
	    if [ "$${score}" != "0.000	" ]; then \
	      echo "$${gpus[$$i]}	$${taskid}	$${score}"; \
	    fi \
	   done )

endif



.PHONY: ${PRINT_VALID_SCORE_ALIASES}
${PRINT_VALID_SCORE_ALIASES}:
	@${MAKE} -s print-valid-scores-table | perl -e '$$_=<>;print;while (<>){ print;chomp;$$i++; @s=split(/\t/); foreach (2..$$#s){ $$t[$$_-2]+=$$s[$$_]; } }; @a = map { sprintf "%5.3f",$$_/$$i } @t; print "all\taverage-score\t"; print join("\t",@a); print "\n";'



## display score differences between validation steps
## (some alternative names as short-cuts)

PRINT_VALID_DIFF_ALIASES := 	print-valid-diff \
				print-valid-diffs \
				print-validation-diff \
				print-validation-diffs \
				print-validation-differences \
				print-validation-difference

.PHONY: print-valid-diff-table
print-valid-diff-table:
	@( tasks=(${TASKS}); \
	   taskids=(${TASK_IDS}); \
	   gpus=(${TASK_GPU_ASSIGNMENTS}); \
	   steps=$$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | tr ',}' "\n\n" | grep "\"step\":" | cut -f2 -d: \
	    | uniq ${SELECT_LINES_CMD} | xargs printf "%5d	" ); \
	   echo "gpu	task-ids	$${steps}"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    task=$${tasks[$$i]}; \
	    taskid=$${taskids[$$i]:=$${tasks[$$i]}}; \
	    if [ ${PRINT_METRIC} == 'perplexity' ]; then \
	      pattern="${PRINT_METRIC}"; \
	    else \
	      pattern="${PRINT_METRIC}/$${task}"; \
	    fi; \
	    score=($$( grep '"type": *"validation"' ${TRAIN_LOGFILES} \
	    | grep "GPU *$${gpus[$$i]}" ${SELECT_LINES_CMD} \
	    | tr ',}' "\n\n" \
	    | grep "\"$${pattern}\":" \
	    | cut -f2 -d: | xargs printf "%.3f	" )); \
	    echo -n "$${gpus[$$i]}	$${taskid}	$${score[0]}"; \
	    last=$${score[0]}; \
	    for (( j=1; j<$${#score[@]}; j++ )); do \
	      diff=`echo "$${score[$$j]} $${last}" | awk '{print $$1-$$2}' | sed 's/^/+/;s/+-/-/;'`; \
	      echo -n "	$${diff}"; \
	      last=$${score[$$j]}; \
	    done; \
	    echo ''; \
	   done )


.PHONY: ${PRINT_VALID_DIFF_ALIASES}
${PRINT_VALID_DIFF_ALIASES}:
	@${MAKE} -s print-valid-diff-table | perl -e '$$_=<>;print;while (<>){ print;chomp;$$i++; @s=split(/\t/); foreach (2..$$#s){ $$t[$$_-2]+=$$s[$$_]; } }; @a = map { sprintf "+%5.3f",$$_/$$i } @t; print "all\taverage-score\t"; $$s=join("\t",@a);$$s=~s/\+\-/\-/g;$$s=~s/^\+//;print $$s; print "\n";'




${MODEL_DIR}/stats/train-progress.txt: ${MODEL_DIR}/model_checkpoint_metadata.json
	@echo "print train progress"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-train-progress > $@

${MODEL_DIR}/stats/valid-scores-bleu.txt: ${MODEL_DIR}/model_checkpoint_metadata.json
	@echo "print validation BLEU scores"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-valid-scores PRINT_METRIC=bleu > $@

${MODEL_DIR}/stats/valid-scores-ppl.txt: ${MODEL_DIR}/model_checkpoint_metadata.json
	@echo "print validation perplexity scores"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-valid-scores PRINT_METRIC=perplexity > $@


${MODEL_DIR}/stats/valid-diff-bleu.txt: ${MODEL_DIR}/model_checkpoint_metadata.json
	@echo "print validation BLEU differences"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-valid-diffs PRINT_METRIC=bleu > $@

${MODEL_DIR}/stats/valid-diff-ppl.txt: ${MODEL_DIR}/model_checkpoint_metadata.json
	@echo "print validation perplexity differences"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-valid-diffs PRINT_METRIC=perplexity > $@
