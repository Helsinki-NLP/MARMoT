#-*-makefile-*-
#--------------------------------------------------------------
# generate SLURM scripts
#--------------------------------------------------------------


NR_OF_NODES ?= 1
NR_OF_GPUS  ?= 1

WHOAMI              ?= $(shell whoami)
SLURM_MAX_NR_JOBS   ?= 200
SLURM_PARTITION     ?= standard-g
SLURM_NODES         ?= ${NR_OF_NODES}
SLURM_CPUS_PER_TASK ?= $(shell echo $$(( ${NR_OF_GPUS} * 6 )) )
SLURM_MEM           ?= $(shell echo $$(( ${NR_OF_GPUS} * 12 )) )G
# SLURM_CPUS_PER_TASK ?= 16
# SLURM_MEM           ?= 48G
SLURM_TIME          ?= 2-00:00:00
SLURM_GPUS          ?= ${NR_OF_GPUS}

ifdef SLURM_GPUS
ifneq (${SLURM_GPUS},0)
  SLURM_GRES := \#SBATCH --gres=gpu:${SLURM_GPUS}
endif
endif


## create a slurm script and submit it

%.slurm:
	@while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	  echo "waiting for space in the queue";\
	  sleep 1; \
	done
	@mkdir -p $(dir $@)
	@echo '#!/bin/bash' >> $@
	@echo '' >> $@
	@echo '#SBATCH -A ${HPC_PROJECT}' >> $@
	@echo '#SBATCH -J ${MODEL_NAME}' >> $@
	@echo '#SBATCH -o $(@:.slurm=).%j.out' >> $@
	@echo '#SBATCH -e $(@:.slurm=).%j.err' >> $@
	@echo '#SBATCH --partition=${SLURM_PARTITION}' >> $@
	@echo '#SBATCH --nodes=${SLURM_NODES}' >> $@
	@echo '#SBATCH --ntasks=${SLURM_NODES}' >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}' >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}' >> $@
	@echo '#SBATCH --time=${SLURM_TIME}' >> $@
	echo '${SLURM_GRES}' >> $@
	@echo '' >> $@
	@echo 'echo "Starting at `date`"' >> $@
	@echo '' >> $@
	@echo '# stops the script when encountering an error' >> $@
	@echo '# (useful if running several commands in the same script)' >> $@
	@echo 'set -eux' >> $@
	@echo '' >> $@
	@echo '# Get the master node (first node in the job allocation)' >> $@
	@echo 'MASTER_NODE=$$(scontrol show hostnames "$${SLURM_JOB_NODELIST}" | head -n 1)' >> $@
	@echo '' >> $@
	@echo 'echo "Master node: $${MASTER_NODE}"' >> $@
	@echo 'echo "Master port: ${MASTER_PORT}"' >> $@
	@echo 'echo "Node list: $${SLURM_JOB_NODELIST}"' >> $@
	@echo '' >> $@
	@echo 'srun /appl/local/csc/soft/ai/bin/gpu-energy --save' >> $@
	@echo '${PROJECT_DIR}/tools/lumi_gpu_usage.sh > $(@:.slurm=.gpu-usage) &' >> $@
	@echo '' >> $@
	@echo 'srun ${MAKE} -C ${EXPERIMENT_DIR} MASTER_NODE=$${MASTER_NODE} $(@:.slurm=)' >> $@
	@echo '' >> $@
	@echo 'srun /appl/local/csc/soft/ai/bin/gpu-energy --diff' >> $@
	@echo 'mv $@ $@.done' >> $@
	@echo 'echo "Finishing at `date`"' >> $@
	sbatch $@






%.slurm-train: %.sh
	@while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	  echo "waiting for space in the queue";\
	  sleep 1; \
	done
	@mkdir -p $(dir $@)
	@echo '#!/bin/bash' >> $@
	@echo '' >> $@
	@echo '#SBATCH -A ${HPC_PROJECT}' >> $@
	@echo '#SBATCH -J ${MODEL_NAME}' >> $@
	@echo '#SBATCH -o $(@:.slurm-train=).%j.out' >> $@
	@echo '#SBATCH -e $(@:.slurm-train=).%j.err' >> $@
	@echo '#SBATCH --partition=${SLURM_PARTITION}' >> $@
	@echo '#SBATCH --nodes=${SLURM_NODES}' >> $@
	@echo '#SBATCH --ntasks=${SLURM_NODES}' >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}' >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}' >> $@
	@echo '#SBATCH --time=${SLURM_TIME}' >> $@
	echo '${SLURM_GRES}' >> $@
	@echo '' >> $@
	@echo 'echo "Starting at `date`"' >> $@
	@echo '' >> $@
	@echo '# stops the script when encountering an error' >> $@
	@echo '# (useful if running several commands in the same script)' >> $@
	@echo 'set -eux' >> $@
	@echo '' >> $@
	@echo '# Get the master node (first node in the job allocation)' >> $@
	@echo 'MASTER_NODE=$$(scontrol show hostnames "$${SLURM_JOB_NODELIST}" | head -n 1)' >> $@
	@echo '' >> $@
	@echo 'echo "Master node: $${MASTER_NODE}"' >> $@
	@echo 'echo "Master port: ${MASTER_PORT}"' >> $@
	@echo 'echo "Node list: $${SLURM_JOB_NODELIST}"' >> $@
	@echo '' >> $@
	@echo '/appl/local/csc/soft/ai/bin/gpu-energy --save' >> $@
	@echo '${PROJECT_DIR}/tools/lumi_gpu_usage.sh > $(@:.slurm-train=.gpu-usage) &' >> $@
	@echo '' >> $@
	@echo 'srun singularity exec \
		--env MASTER_NODE="$${MASTER_NODE}" \
		--env MASTER_PORT="${MASTER_PORT}" \
		-B ${MODEL_DIR}:${MODEL_DIR}:rw \
		-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
		-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
		-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
		-B /dev/shm:/dev/shm:rw \
		/appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
		$<' >> $@
	@echo '' >> $@
	@echo '/appl/local/csc/soft/ai/bin/gpu-energy --diff' >> $@
	@echo 'mv $@ $@.done' >> $@
	@echo 'echo "Finishing at `date`"' >> $@
	sbatch $@
