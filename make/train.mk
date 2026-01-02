#-*-makefile-*-


#--------------------------------------------------------------
# training - submit SLURM job for training a model
#--------------------------------------------------------------


# random port for distributed training communication
MASTER_PORT := 9973

.PHONY: train
train: train-slurm
	${MAKE} ${MODEL_DIR}/train.slurmjob

.PHONY: train-slurm
train-slurm: ${TRAIN_CONFIGFILE}
	${MAKE} SLURM_TIME=2-00:00:00 \
		SLURM_NODES=${NR_OF_NODES} \
		SLURM_GPUS=${NR_OF_GPUS} \
		SLURM_MEM=96G \
		SLURM_CPUS_PER_TASK=48 \
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
	singularity exec \
		-B ${MODEL_DIR}:${MODEL_DIR}:rw \
		-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
		-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
		-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
		/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
		${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/train.py ${TRAIN_FROM} \
			-save_model ${MODEL_PATH} \
			-config $<


else

##----------------------------
## multi-node training
##----------------------------

.PHONY: ${MODEL_DIR}/train
${MODEL_DIR}/train: ${TRAIN_CONFIGFILE}
	singularity exec \
		--env MASTER_NODE="${MASTER_NODE}" \
		--env MASTER_PORT="${MASTER_PORT}" \
		-B ${MODEL_DIR}:${MODEL_DIR}:rw \
		-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
		-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
		-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
		-B /dev/shm:/dev/shm:rw \
		/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
		${MAKE} MASTER_NODE=${MASTER_NODE} MASTER_PORT=${MASTER_PORT} multi-node-train


.PHONY: multi-node-train
multi-node-train:
	echo ${TRAIN_CONFIGFILE}
	( source ${MAMMOTH_DIR}/.venv/bin/activate; \
	  echo "Node ${SLURM_NODEID} starting training"; \
	  echo "Master node: ${MASTER_NODE}"; \
	  echo "Master port: ${MASTER_PORT}"; \
	  ${MAMMOTH_DIR}/.venv/bin/python ${MAMMOTH_DIR}/train.py ${TRAIN_FROM} \
		-config ${TRAIN_CONFIGFILE} \
		-save_model ${MODEL_PATH} \
		--node_rank ${SLURM_PROCID} \
		--master_ip ${MASTER_NODE} \
		--master_port ${MASTER_PORT} )


## create a separate script instead of using make targets
## for multi-node training

# ${MODEL_DIR}/train-test: ${MODEL_DIR}/train.sh
# 	singularity exec \
# 		--env MASTER_NODE="${MASTER_NODE}" \
# 		--env MASTER_PORT="${MASTER_PORT}" \
# 		-B ${MODEL_DIR}:${MODEL_DIR}:rw \
# 		-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
# 		-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
# 		-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
# 		-B /dev/shm:/dev/shm:rw \
# 		/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
# 		$<

# ${MODEL_DIR}/train.sh: ${TRAIN_CONFIGFILE}
# 	@echo '#!/bin/bash' > $@
# 	@echo '' >>$@
# 	@echo 'source ${MAMMOTH_DIR}/.venv/bin/activate' >> $@
# 	@echo 'cd $${SLURM_SUBMIT_DIR}' >> $@
# 	@echo '' >>$@
# 	@echo 'echo "Node $${SLURM_NODEID} starting training"' >> $@
# 	@echo 'echo "Master node: $${MASTER_NODE}"' >> $@
# 	@echo 'echo "Master port: ${MASTER_PORT}"' >> $@
# 	@echo '' >>$@
# 	@echo 'python ${MAMMOTH_DIR}/train.py \
# 		-config $< \
# 		-save_model ${MODEL_PATH} \
# 		--node_rank $${SLURM_PROCID} \
# 		--master_ip $${MASTER_NODE} \
# 		--master_port ${MASTER_PORT}' >> $@
# 	@chmod +x $@

endif
