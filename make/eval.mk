#-*-makefile-*-


#--------------------------------------------------------------
# evaluation
#--------------------------------------------------------------

## submit SLURM jobs to evaluate all tasks

.PHONY: eval-all-tasks
eval-all-tasks:
	@for t in $(shell seq $(words ${TASKS})); do \
	  ${MAKE} TASK_NR=$$t eval; \
	done

.PHONY: eval-zero-shot-tasks
eval-zero-shot-tasks:
	@for t in $(shell seq $(words ${ZERO_SHOT_TASKS})); do \
	  ${MAKE} TASKS="${ZERO_SHOT_TASKS}" TASK_NR=$$t eval; \
	done


##-------------------------------------------------------------------------------
## submit SLURM job for evaluating a model
## - translate the selected task (set TASK_NR) with the best mode
##-------------------------------------------------------------------------------


.PHONY: eval
eval: eval-slurm
ifneq ($(wildcard ${TESTDATA_SRC}),)
	${MAKE} ${EVAL_DIR}/eval_${TASK}.slurmjob
else
	@echo "ERROR: cannot find ${TESTDATA_SRC}"
endif

.PHONY: eval-slurm
eval-slurm: ${INFERENCE_CONFIGFILE}
	${MAKE} SLURM_TIME=00:30:00 \
		SLURM_GPUS=1 \
		SLURM_NODES=1 \
		SLURM_MEM=16G \
		SLURM_CPUS_PER_TASK=7 \
	${EVAL_DIR}/eval_${TASK}.slurm



##-------------------------------------------------------------------------------
## translate and evaluate
##-------------------------------------------------------------------------------

MT_METRICS = bleu chrf ter

.PHONY: ${EVAL_DIR}/eval
${EVAL_DIR}/eval: ${EVAL_DIR}/eval_${TASK}

${EVAL_DIR}/eval_${TASK}: ${TESTDATA_OUTPUT}
	sacrebleu ${TESTDATA_TRG} --metrics ${MT_METRICS} < $< > $@

${TESTDATA_OUTPUT}: ${INFERENCE_CONFIGFILE}
	singularity exec \
		-B ${EVAL_DIR}:${EVAL_DIR}:rw \
		-B ${MODEL_DIR}:${MODEL_DIR}:ro \
		-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
		-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
		-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
		/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
		${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/translate.py \
			-model ${MODEL_PATH} \
			-config $<

