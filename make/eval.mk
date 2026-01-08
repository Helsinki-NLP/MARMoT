#-*-makefile-*-


#--------------------------------------------------------------
# evaluation
#--------------------------------------------------------------

## submit SLURM jobs to evaluate all tasks (one job per task)

.PHONY: eval
eval:
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} TASK_NR=$$t eval-task; \
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
EVAL_CPUS_PER_TASK ?= 7
EVAL_MEM_PER_NODE  ?= 16G
EVAL_WALLTIME      ?= 00:30:00

.PHONY: eval-task
eval-task: eval-slurm
ifneq ($(wildcard ${TESTDATA_SRC}),)
	${MAKE} ${EVAL_DIR}/eval_${TASK}.slurmjob
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
	${EVAL_DIR}/eval_${TASK}.slurm


##-------------------------------------------------------------------------------
## translate and evaluate
##-------------------------------------------------------------------------------

MT_METRICS = bleu chrf ter

.PHONY: ${EVAL_DIR}/eval-task
${EVAL_DIR}/eval-task: ${EVAL_DIR}/eval_${TASK}

${EVAL_DIR}/eval_${TASK}: ${TESTDATA_OUTPUT}
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
DASHBOARD_API := https://opus.nlpl.eu/dashboard/api.php?test=${TESTDATA_NAME}&model=top&metric=${PRINT_METRIC}&pkg=opusmt
PRINT_METRIC  ?= bleu

.PHONY: ${PRINT_EVAL_SCORE_ALIASES}
${PRINT_EVAL_SCORE_ALIASES}:
	@( tasks=(${TASKS}); \
	   echo "task	score	opus	diff"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    if [ -s ${EVAL_DIR}/eval_$${tasks[$$i]} ]; then \
	      score=$$( grep -i -A1 ${PRINT_METRIC} ${EVAL_DIR}/eval_$${tasks[$$i]} \
	      | grep '"score":' | cut -f2 -d: | tr ',' "\t" ); \
	      best=$$( curl -s "${DASHBOARD_API}&scoreslang=$${tasks[$$i]}" \
	      | grep -A1 '"scores":' | tail -1 | cut -f2 -d: | tr ',}' "\t0" ); \
	      diff=`echo "$${score} $${best}" | awk '{print $$1-$$2}'`; \
	      echo "$${tasks[$$i]}	$${score}$${best}$${diff}"; \
	    fi \
	   done )
