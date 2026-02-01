#-*-makefile-*-


EVAL_TASKS ?= ${TASKS}


## skip evaluation of denoising tasks
## and monolingual tasks (typically denosiing tasks)
## set to 0 to enable them

SKIP_SAME_LANGUAGE_EVAL_TASKS ?= 1
SKIP_DENOISING_EVAL_TASKS     ?= 1

#--------------------------------------------------------------
# evaluation
#--------------------------------------------------------------

## submit SLURM jobs to evaluate all tasks (one job per task)

.PHONY: eval
eval:
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} -s TASK_NR=$$t eval-task; \
	done

.PHONY: eval-zero-shot-tasks
eval-zero-shot-tasks:
	@for t in $(shell seq $(words ${ZERO_SHOT_TASKS})); do \
	  ${MAKE} TASKS="${ZERO_SHOT_TASKS}" TASK_NR=$$t eval-task; \
	done


##-------------------------------------------------------------------------------
## submit SLURM job for evaluating a model
## - translate the selected task (set TASK_NR) with the best mode
##-------------------------------------------------------------------------------

EVAL_NR_OF_NODES   ?= 1
EVAL_GPUS_PER_NODE ?= 1
EVAL_CPUS_PER_TASK ?= ${MAX_CPUS_PER_GPU}
EVAL_MEM_PER_NODE  ?= ${MAX_MEM_PER_GPU}G
EVAL_WALLTIME      ?= 00:30:00

## only start evaluation jobs if the testdata source file exists
## skip evaluation jobs for denoising tasks (unless the skip-variable is not 1)
## skip evaluation jobs for tasks with the same source and target language
##                      (unless the skip-variable is not 1)

.PHONY: eval-task
eval-task: eval-slurm
ifneq ($(wildcard ${TESTDATA_SRC}),)
  ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_EVAL_TASKS},denoising-1)
    ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_EVAL_TASKS},$(TRGLANG)-1)
	@echo "evaluate ${TASK}"
	@${MAKE} ${EVAL_DIR}/eval_${TASK_ID}.slurmjob
    else
	@echo "skip task ${TASK} (same source and target language)"
    endif
  else
	@echo "skip denoising task ${TASK}"
  endif
else
	@echo "ERROR: cannot find ${TESTDATA_SRC}"
endif

.PHONY: eval-slurm
eval-slurm: ${INFERENCE_CONFIGFILE}
	${MAKE} SLURM_TIME=${EVAL_WALLTIME} \
		SLURM_GPUS=${EVAL_GPUS_PER_NODE} \
		SLURM_NODES=${EVAL_NR_OF_NODES} \
		SLURM_MEM=${EVAL_MEM_PER_NODE} \
		SLURM_CPUS_PER_TASK=${EVAL_CPUS_PER_TASK} \
	${EVAL_DIR}/eval_${TASK_ID}.slurm


##-------------------------------------------------------------------------------
## translate and evaluate
##-------------------------------------------------------------------------------

MT_METRICS = bleu chrf ter

.PHONY: ${EVAL_DIR}/eval-task
${EVAL_DIR}/eval-task: ${EVAL_DIR}/eval_${TASK_ID}

${EVAL_DIR}/eval_${TASK_ID}: ${TESTDATA_OUTPUT}
	sacrebleu ${TESTDATA_TRG} --metrics ${MT_METRICS} < $< > $@

${TESTDATA_OUTPUT}: ${INFERENCE_CONFIGFILE}
	${LOAD_MAMMOTH_ENV} ${MAMMOTH_ENV_PYTHON} ${MAMMOTH_DIR}/translate.py \
		-model ${MODEL_PATH} \
		-config $<






##-------------------------------------------------------------------------------
## reporting targets
##-------------------------------------------------------------------------------

PRINT_EVAL_SCORE_ALIASES := 	print-eval-score \
				print-eval-scores \
				print-evaluation-score \
				print-evaluation-scores

# to compare with OPUS-MT dashboard:
DASHBOARD_API := https://opus.nlpl.eu/legacy/dashboard/api.php?test=${TESTDATA_NAME}&model=top&metric=${PRINT_METRIC}&pkg=opusmt
PRINT_METRIC  ?= bleu

.PHONY: ${PRINT_EVAL_SCORE_ALIASES}
${PRINT_EVAL_SCORE_ALIASES}:
	@( tasks=(${TASKS}); \
	   taskids=(${TASK_IDS}); \
	   echo "taskid	task	score	opus	diff"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    if [ $(words ${TASK_IDS}) -le $$i ]; then \
	      taskid="task_$${tasks[$$i]}"; \
	    else \
	      taskid=$${taskids[$$i]}; \
	    fi; \
	    if [ -s ${EVAL_DIR}/eval_$${taskid} ]; then \
	      score=$$( grep -i -A1 ${PRINT_METRIC} ${EVAL_DIR}/eval_$${taskid} \
	      | grep '"score":' | cut -f2 -d: | tr ',' "\t" ); \
	      best=$$( curl -s "${DASHBOARD_API}&scoreslang=$${tasks[$$i]}" \
	      | grep -A1 '"scores":' | tail -1 | cut -f2 -d: | tr ',}' "\t0" ); \
	      diff=`echo "$${score} $${best}" | awk '{print $$1-$$2}'`; \
	      echo "$${taskid}	$${tasks[$$i]}	$${score}$${best}$${diff}"; \
	    fi \
	   done )
