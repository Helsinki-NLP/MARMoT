#-*-makefile-*-
#
#----------------------------------------------------------------------------
#   make eval ....... submit evaluation job on default test set for all tasks
#   make eval-jobs .. submit indvidual evaluation jobs, one per task
#   make eval-task .. submit an evaluation job for one task
#                     (select by setting any of the variables TASK_NR, TASK, TASK_ID)
#
#----------------------------------------------------------------------------
# reporting:
#
#   make print-eval-scores ............ print evaluation score table
#   make print-eval-score-comparison .. print the table with a comparison to the OPUS dashboard
#   make print-eval-stats ............. print the score tables to files (BLEU and chrF)
#
# set the evaluation metrics using the variable RPINT_METRIC (bleu, chrf - see MT_METRICS)
#
#
#----------------------------------------------------------------------------
# for running with other data sets (see list of test sets below):
# - append the name of the data set as a sub-directory to the evaluation make target
# - the list of possible evaluation targets is given in EVAL_TARGETS below
# some examples:
#
#   make eval/newstest2012
#   make eval-jobs/newstest2020
#   make print-eval-scores/newstest2012
#
#----------------------------------------------------------------------------


## eval metrics to be used (sacrebleu)

# MT_METRICS = bleu chrf ter
MT_METRICS = bleu chrf


EVAL_TARGETS := eval eval-task eval-tasks eval-jobs \
		print-eval-scores print-eval-score-comparison print-eval-stats

##----------------------------------------------------------------------------------
## define evaluation test sets
## - define testsets (need to be found in those data locations)
## - assuption: test set name is the name of the last sub-directory
##----------------------------------------------------------------------------------

WMT_TESTSETS := testsets/wmt/florestest2021 \
		testsets/wmt/newsdev2014 \
		testsets/wmt/newsdev2015 \
		testsets/wmt/newsdev2016 \
		testsets/wmt/newsdev2017 \
		testsets/wmt/newsdev2018 \
		testsets/wmt/newsdev2019 \
		testsets/wmt/newsdev2020 \
		testsets/wmt/newsdev2021 \
		testsets/wmt/newsdiscussdev2015 \
		testsets/wmt/newsdiscusstest2015 \
		testsets/wmt/newstest2008 \
		testsets/wmt/newstest2009 \
		testsets/wmt/newstest2010 \
		testsets/wmt/newstest2011 \
		testsets/wmt/newstest2012 \
		testsets/wmt/newstest2013 \
		testsets/wmt/newstest2014 \
		testsets/wmt/newstest2015 \
		testsets/wmt/newstest2016 \
		testsets/wmt/newstest2017 \
		testsets/wmt/newstest2018 \
		testsets/wmt/newstest2019 \
		testsets/wmt/newstest2020 \
		testsets/wmt/newstest2021 \
		testsets/wmt/newstestB2017 \
		testsets/wmt/wmttest2022 \
		testsets/wmt/wmttest2023 \
		testsets/wmt/wmttest2024

TESTSETS      := ${WMT_TESTSETS}
TESTSET_NAMES := $(notdir ${TESTSETS})


## multi-parallal data sets are treated separately
## because the file naming conventions are different

MULTI_TESTSETS      := 	testsets/wmt24pp \
			testsets/ntrex
MULTI_TESTSET_NAMES := $(notdir ${MULTI_TESTSETS})





## eval results for the current task and testdata will be stored in this file

EVAL_TASK_RESULT := ${EVAL_DIR}/eval_${TASK_ID}_${TESTDATA_NAME}


## selected tasks to be evaluated
## default: select all

ifdef EVAL_TASKS
  EVAL_TASK_NRS  := $(foreach t,${EVAL_TASKS},$(call pos,$t,$(TASK_IDS)))
else
  EVAL_TASKS     := ${TASK_IDS}
  EVAL_TASK_NRS  := ${TASK_NRS}
endif


## skip evaluation of denoising tasks
## and monolingual tasks (typically denosiing tasks)
## set to 0 to enable them

SKIP_SAME_LANGUAGE_EVAL_TASKS ?= 1
SKIP_DENOISING_EVAL_TASKS     ?= 1

#--------------------------------------------------------------
# evaluation
#--------------------------------------------------------------


## submit one SLURM job for evaluating all tasks of the model
## (see ${EVAL_DIR}/eval_tasks target)

.PHONY: eval eval-tasks
eval eval-tasks: eval-slurmjob


## submit SLURM jobs to evaluate all tasks (one job per task)

EVAL_TASK_JOBS = $(patsubst %,eval-task/%,${EVAL_TASK_NRS})

.PHONY: eval-jobs
eval-jobs: ${EVAL_TASK_JOBS}

.PHONY: ${EVAL_TASK_JOBS}
${EVAL_TASK_JOBS}:
	@${MAKE} -s TASK_NR=$(notdir $@) eval-task






## create all evaluation targets with the testsetname as an extra string, e.g
##     eval/newstest2013
##     print-eval-scores/newstest2013
##     ....

EVAL_TESTSET_TARGETS := $(foreach t,${EVAL_TARGETS},$(patsubst %,$t/%,${TESTSET_NAMES}))

.PHONY: ${EVAL_TESTSET_TARGETS}
${EVAL_TESTSET_TARGETS}:
	@${MAKE} -s 	TESTDATA=$(call lookup,$(notdir $@),${TESTSET_NAMES},${TESTSETS}) \
			TESTDATA_NAME=$(notdir $@) \
	$(patsubst %/,%,$(dir $@))



##----------------------------------------------------------------------------------
## multi-test sets are different: there are no language pairs in the file name!
## --> need to change the TESTDATA_BASENAME pattern!
##----------------------------------------------------------------------------------

EVAL_MULTI_TESTSET_TARGETS := $(foreach t,${EVAL_TARGETS},$(patsubst %,$t/%,${MULTI_TESTSET_NAMES}))

.PHONY: ${EVAL_MULTI_TESTSET_TARGETS}
${EVAL_MULTI_TESTSET_TARGETS}:
	@${MAKE} -s 	TESTDATA=$(call lookup,$(notdir $@),${MULTI_TESTSET_NAMES},${MULTI_TESTSETS}) \
			TESTDATA_NAME=$(notdir $@) \
			TESTDATA_BASENAME=* \
	$(patsubst %/,%,$(dir $@))






##-------------------------------------------------------------------------------
## submit SLURM jobs for evaluating a model
##-------------------------------------------------------------------------------

EVAL_NR_OF_NODES    ?= 1
EVAL_GPUS_PER_NODE  ?= 1
EVAL_CPUS_PER_TASK  ?= ${MAX_CPUS_PER_GPU}
EVAL_MEM_PER_NODE   ?= ${MAX_MEM_PER_GPU}G
EVAL_TASK_WALLTIME  ?= 00:30:00
EVAL_TASKS_WALLTIME ?= 24:00:00
EVAL_SLURM_TASKS    ?= 1
EVAL_PARALLEL_JOBS  ?= 1




## PHONY eval targets for all tasks

EVAL_TASK_TARGET  := ${EVAL_DIR}/eval-task-${TESTDATA_NAME}
EVAL_TASKS_TARGET := ${EVAL_DIR}/eval-tasks-${TESTDATA_NAME}
EVAL_TASKS_TARGETS := $(patsubst %,${EVAL_DIR}/eval-task/%,${EVAL_TASK_NRS})






.PHONY: eval-slurm eval-slurmjob
eval-slurm eval-slurmjob:
	@mkdir -p ${EVAL_DIR}
	${MAKE} SLURM_TIME=${EVAL_TASKS_WALLTIME} \
		SLURM_GPUS=${EVAL_GPUS_PER_NODE} \
		SLURM_NODES=${EVAL_NR_OF_NODES} \
		SLURM_MEM=${EVAL_MEM_PER_NODE} \
		SLURM_TASKS=${EVAL_SLURM_TASKS} \
		SLURM_CPUS_PER_TASK=${EVAL_CPUS_PER_TASK} \
		SLURM_PARALLEL_JOBS=${EVAL_PARALLEL_JOBS} \
	${EVAL_TASKS_TARGET}.$(patsubst eval-%,%,$@)



## translate the selected task (set TASK_NR) with the best mode
## only start evaluation jobs if the testdata source file exists
## skip evaluation jobs for denoising tasks (unless the skip-variable is not 1)
## skip evaluation jobs for tasks with the same source and target language
##                      (unless the skip-variable is not 1)


.PHONY: eval-task
eval-task:
	@${MAKE} -s FIND_TESTDATA=1 eval-task-target

.PHONY: eval-task-target
eval-task-target:
ifneq ($(wildcard ${TESTDATA_SRC}),)
  ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_EVAL_TASKS},denoising-1)
    ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_EVAL_TASKS},$(TRGLANG)-1)
	@echo "evaluate ${TASK}"
	@${MAKE} -s eval-task-slurmjob
    else
	@echo "skip task ${TASK} (same source and target language)"
    endif
  else
	@echo "skip denoising task ${TASK}"
  endif
else
	@echo "ERROR: cannot find testdata ${TESTDATA_SRC}"
endif


.PHONY: eval-task-slurm eval-task-slurmjob
eval-task-slurm eval-task-slurmjob:
	@mkdir -p ${EVAL_DIR}
	@${MAKE} SLURM_TIME=${EVAL_TASK_WALLTIME} \
		SLURM_GPUS=${EVAL_GPUS_PER_NODE} \
		SLURM_NODES=${EVAL_NR_OF_NODES} \
		SLURM_MEM=${EVAL_MEM_PER_NODE} \
		SLURM_TASKS=${EVAL_SLURM_TASKS} \
		SLURM_CPUS_PER_TASK=${EVAL_CPUS_PER_TASK} \
		SLURM_PARALLEL_JOBS=${EVAL_PARALLEL_JOBS} \
	${EVAL_DIR}/eval_${TASK_ID}_${TESTDATA_NAME}.$(patsubst eval-task-%,%,$@)



##-------------------------------------------------------------------------------
## translate and evaluate
##-------------------------------------------------------------------------------

## increase max length to something big to avoid filtering test data
## remove length filter

EVAL_MAX_LENGTH      ?= 1024
SINGLE_COMMA         := ,
DOUBLE_COMMA         := ,,
EVAL_TRANSFORM       ?= $(subst ${DOUBLE_COMMA},${SINGLE_COMMA},${subst filtertoolong,,${TRANSFORM}})
EVAL_TASK_TRANSFORMS ?= $(subst ${DOUBLE_COMMA},${SINGLE_COMMA},${subst filtertoolong,,${TASK_TRANSFORMS}})



.PHONY: ${EVAL_TASKS_TARGET}
${EVAL_TASKS_TARGET}: ${EVAL_TASKS_TARGETS}

.PHONY: ${EVAL_TASKS_TARGETS}
${EVAL_TASKS_TARGETS}:
	${MAKE} TASK_NR=$(notdir $@) FIND_TESTDATA=1 ${EVAL_TASK_TARGET}



## eval currently selected task

.PHONY: ${EVAL_TASK_TARGET}
${EVAL_TASK_TARGET}: ${EVAL_TASK_RESULT}



## only start mammoth if there is an input file
## otherwise just report input is missing


.PRECIOUS: ${TESTDATA_OUTPUT}

${EVAL_TASK_RESULT}:
ifneq ($(wildcard ${TESTDATA_SRC}),)
  ifneq ($(findstring denoising,$(TASK_TRANSFORM))-${SKIP_DENOISING_EVAL_TASKS},denoising-1)
    ifneq ($(SRCLANG)-${SKIP_SAME_LANGUAGE_EVAL_TASKS},$(TRGLANG)-1)
	-${MAKE} ${TESTDATA_OUTPUT} \
		TRANSFORM=${EVAL_TRANSFORM} \
		TASK_TRANSFORMS="${EVAL_TASK_TRANSFORMS}" \
		MAX_SEQ_LENGTH=${EVAL_MAX_LENGTH} \
		MAX_SRCSEQ_LENGTH=${EVAL_MAX_LENGTH} \
		MAX_TRGSEQ_LENGTH=${EVAL_MAX_LENGTH}
	-sacrebleu ${TESTDATA_TRG} --metrics ${MT_METRICS} < ${TESTDATA_OUTPUT} > $@
    else
	@echo "skip task ${TASK_ID} (same source and target language)"
    endif
  else
	@echo "skip denoising task ${TASK_ID}"
  endif
else
	@echo "ERROR: cannot find testdata ${TESTDATA_SRC}"
endif


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
	   echo "taskid_lang	task	${PRINT_METRIC}"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    if [ $(words ${TASK_IDS}) -le $$i ]; then \
	      taskid="task_$${tasks[$$i]}"; \
	    else \
	      taskid=$${taskids[$$i]}; \
	    fi; \
	    if [ -s ${EVAL_DIR}/eval_$${taskid}_${TESTDATA_NAME} ]; then \
	      langpair=`echo $${taskid} | cut -f2- -d_`; \
	      score=$$( grep -i -A1 ${PRINT_METRIC} ${EVAL_DIR}/eval_$${taskid}_${TESTDATA_NAME} \
	      | grep '"score":' | cut -f2 -d: | tr ',' "\t" ); \
	      echo "$${taskid}	$${tasks[$$i]}	$${score}"; \
	    fi \
	   done )


.PHONY: print-eval-score-comparison
print-eval-score-comparison:
	@( tasks=(${TASKS}); \
	   taskids=(${TASK_IDS}); \
	   echo "taskid_lang	task	score	opus	diff"; \
	   for i in $$(seq 0 $$(( $(words $(TASKS))-1 )) ); do \
	    if [ $(words ${TASK_IDS}) -le $$i ]; then \
	      taskid="task_$${tasks[$$i]}"; \
	    else \
	      taskid=$${taskids[$$i]}; \
	    fi; \
	    if [ -s ${EVAL_DIR}/eval_$${taskid}_${TESTDATA_NAME} ]; then \
	      langpair=`echo $${taskid} | cut -f2- -d_`; \
	      score=$$( grep -i -A1 ${PRINT_METRIC} ${EVAL_DIR}/eval_$${taskid}_${TESTDATA_NAME} \
	      | grep '"score":' | cut -f2 -d: | tr ',' "\t" ); \
	      best=$$( curl -s "${DASHBOARD_API}&scoreslang=$${langpair}" \
	      | grep -A1 '"scores":' | tail -1 | cut -f2 -d: | tr ',}' "\t0" ); \
	      diff=`echo "$${score} $${best}" | awk '{print $$1-$$2}'`; \
	      echo "$${taskid}	$${tasks[$$i]}	$${score}$${best}$${diff}"; \
	    fi \
	   done )



.PHONY: print-eval-stats
print-eval-stats: ${MODEL_DIR}/stats/eval-scores-bleu.txt ${MODEL_DIR}/stats/eval-scores-chrf.txt



ifneq ($(wildcard ${EVAL_DIR}),)

${MODEL_DIR}/stats/eval-scores-bleu.txt: ${EVAL_DIR}
	@echo "print evaluation BLEU scores"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-eval-scores PRINT_METRIC=bleu > $@

${MODEL_DIR}/stats/eval-scores-chrf.txt: ${EVAL_DIR}
	@echo "print evaluation ChrF scores"
	@mkdir -p $(dir $@)
	@${MAKE} -s print-eval-scores PRINT_METRIC=chrf > $@

else

${MODEL_DIR}/stats/eval-scores-bleu.txt ${MODEL_DIR}/stats/eval-scores-chrf.txt:
	@echo "no model evaluation done for ${MODEL_DIR}"

endif
