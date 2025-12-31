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


## submit SLURM job for evaluating a model
## - copy the best model according to validation (only of the checkpoint exists)
## - otherwise: use the last checkpoint
## - translate the selected task (set TASK_NR) with the best mode
##

ifneq ($(wildcard ${MODEL_META}),)
  BEST_MODEL_STEP := $(strip $(shell grep -A2 "best_checkpoint" ${MODEL_META} | grep 'step' | cut -f2 -d: | cut -f1 -d,))
  BEST_MODEL      := ${MODEL_PATH}_step_${BEST_MODEL_STEP}
endif

.PHONY: eval
eval:
ifneq ($(wildcard ${TESTDATA_SRC}),)
ifneq ($(wildcard ${BEST_MODEL}_*),)
	mkdir -p $(dir ${MODEL_PATH})best-model
	find $(dir ${MODEL_PATH})best-model -type l -delete
	-ln -s ${BEST_MODEL}_* $(dir ${MODEL_PATH})best-model/
	-ln -s ${MODEL_META} $(dir ${MODEL_PATH})best-model/
	${MAKE} SLURM_TIME=00:30:00 \
		SLURM_GPUS=1 \
		SLURM_MEM=16G \
		SLURM_CPUS_PER_TASK=8 \
		MODEL_PATH=$(dir ${MODEL_PATH})best-model/$(notdir ${MODEL_PATH}) \
	${EVAL_DIR}/eval_${TASK}.slurm
else
	${MAKE} SLURM_TIME=00:30:00 \
		SLURM_GPUS=1 \
		SLURM_MEM=16G \
		SLURM_CPUS_PER_TASK=8 \
	${EVAL_DIR}/eval_${TASK}.slurm
endif
endif


## translate and evaluate

.PHONY: ${EVAL_DIR}/eval
${EVAL_DIR}/eval: ${EVAL_DIR}/eval_${TASK}

${EVAL_DIR}/eval_${TASK}: ${TESTDATA_OUTPUT}
	sacrebleu ${TESTDATA_TRG} < $< > $@

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

