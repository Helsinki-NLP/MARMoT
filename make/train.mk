#-*-makefile-*-


#--------------------------------------------------------------
# training
#--------------------------------------------------------------

## submit SLURM job for training a model

GPU_RANKS        := $(sort $(notdir $(subst :,/,${TASK_GPUS})))
NR_OF_GPUS       := $(words ${GPU_RANKS})
NR_OF_NODES      := $(words $(sort $(dir $(subst :,/,${TASK_GPUS}))))

.PHONY: train
train:
	${MAKE} SLURM_TIME=2-00:00:00 \
		SLURM_NODES=${NR_OF_NODES} \
		SLURM_GPUS=${NR_OF_GPUS} \
		SLURM_MEM=96G \
		SLURM_CPUS_PER_TASK=48 \
	${WORK_DIR}/train.slurm

## train a model

.PHONY: ${WORK_DIR}/train
${WORK_DIR}/train: ${TRAIN_CONFIGFILE}
	singularity exec \
	    -B ${WORK_DIR}:${WORK_DIR}:rw \
	    -B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
	    -B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    ${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/train.py \
	    -save_model ${MODEL_PATH} \
	    -config $<


