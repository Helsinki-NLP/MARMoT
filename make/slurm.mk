#-*-makefile-*-
#--------------------------------------------------------------
# generate SLURM scripts
#
# TODO's:
#   * fast local disk allocation option
#   * enable restarting jobs with dependencies
#--------------------------------------------------------------


NR_OF_NODES   ?= 1
GPUS_PER_NODE ?= 1

WHOAMI              ?= $(shell whoami)

SLURM_CPU_PARTITION ?= small
SLURM_GPU_PARTITION ?= gpu
SLURM_MAX_CPU_TIME  ?= 3-00:00:00
SLURM_MAX_GPU_TIME  ?= 3-00:00:00
SLURM_GPU_GRES      ?= gpu:v100
SLURM_MAX_NR_JOBS   ?= 200
SLURM_CPUS_PER_TASK ?= 16
SLURM_MEM           ?= 48G
SLURM_NODES         ?= ${NR_OF_NODES}
SLURM_GPUS          ?= ${GPUS_PER_NODE}

ifneq (${SLURM_GPUS},0)
  SLURM_PARTITION ?= ${SLURM_GPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_GPU_TIME}
  SLURM_GRES      ?= ${SLURM_GPU_GRES}:${SLURM_GPUS}
else
  SLURM_PARTITION ?= ${SLURM_CPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_CPU_TIME}
endif


## create a slurm script and submit it

.PHONY: %.slurmjob
%.slurmjob: %.slurm
	@while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	  echo "waiting for space in the queue";\
	  sleep 1; \
	done
	sbatch $<


## create a slurm script

%.slurm:
	@mkdir -p $(dir $@)
	@echo '#!/bin/bash'                                                                  >> $@
	@echo ''                                                                             >> $@
	@echo '#SBATCH -A ${HPC_PROJECT}'                                                    >> $@
	@echo '#SBATCH -J ${MODEL_NAME}'                                                     >> $@
	@echo '#SBATCH -o $(@:.slurm=).%j.out'                                               >> $@
	@echo '#SBATCH -e $(@:.slurm=).%j.err'                                               >> $@
	@echo '#SBATCH --partition=${SLURM_PARTITION}'                                       >> $@
	@echo '#SBATCH --nodes=${SLURM_NODES}'                                               >> $@
	@echo '#SBATCH --ntasks=${SLURM_NODES}'                                              >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}'                               >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}'                                                   >> $@
	@echo '#SBATCH --time=${SLURM_TIME}'                                                 >> $@
ifdef SLURM_GRES
	@echo '#SBATCH --gres=${SLURM_GRES}'                                                 >> $@
endif
	@echo ''                                                                             >> $@
	@echo 'echo "Starting at `date`"'                                                    >> $@
	@echo ''                                                                             >> $@
	@echo '# stops the script when encountering an error'                                >> $@
	@echo '# (useful if running several commands in the same script)'                    >> $@
	@echo 'set -eux'                                                                     >> $@
	@echo ''                                                                             >> $@
	@echo '#--------------------------------------------------------------------------'  >> $@
	@echo '# define a function for finishing up interrupted jobs'                        >> $@
	@echo 'abort_function()'                                                             >> $@
	@echo '{'                                                                            >> $@
	@echo '    echo "abort_function called at `date`"'                                   >> $@
	@echo '    ${${STOP_GPU_ENERGY_MONITORING}}'                                         >> $@
	@echo '}'                                                                            >> $@
	@echo "trap 'abort_function' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM"                  >> $@
	@echo '#--------------------------------------------------------------------------'  >> $@
	@echo ''                                                                             >> $@
	@echo '# Get the master node (first node in the job allocation) and set its port'    >> $@
	@echo 'MASTER_NODE=$$(scontrol show hostnames "$${SLURM_JOB_NODELIST}" | head -n 1)' >> $@
	@echo 'MASTER_PORT="$${MASTER_PORT:-$$((29500 + SLURM_JOB_ID % 1000))}"'             >> $@
	@echo ''                                                                             >> $@
	@echo 'echo "Master node: $${MASTER_NODE}"'                                          >> $@
	@echo 'echo "Master port: $${MASTER_PORT}"'                                          >> $@
	@echo 'echo "Node list: $${SLURM_JOB_NODELIST}"'                                     >> $@
	@echo ''                                                                             >> $@
ifneq (${SLURM_GPUS},0)
ifdef START_GPU_ENERGY_MONITORING
	@echo 'srun ${START_GPU_ENERGY_MONITORING}'                                          >> $@
endif
ifdef MONITOR_GPU_USAGE
	@echo '${MONITOR_GPU_USAGE} > $(@:.slurm=).$${SLURM_JOBID}.gpu-usage &'              >> $@
endif
endif
	@echo ''                                                                             >> $@
	@echo '# finally, the actual target to be done'                                      >> $@
	@echo "srun ${MAKE} -C ${EXPERIMENT_DIR} \\"                                         >> $@
	@echo "             MODEL_NAME=${MODEL_NAME} \\"                                     >> $@
	@echo "             MASTER_NODE=\$${MASTER_NODE} \\"                                 >> $@
	@echo "             MASTER_PORT=\$${MASTER_PORT} \\"                                 >> $@
	@echo "             $(@:.slurm=)"                                                    >> $@
	@echo ''                                                                             >> $@
ifneq (${SLURM_GPUS},0)
ifdef STOP_GPU_ENERGY_MONITORING
	@echo 'srun ${${STOP_GPU_ENERGY_MONITORING}}'                                        >> $@
endif
endif
	@echo 'mv $@ $@.done'                                                                >> $@
	@echo 'echo "Finishing at `date`"'                                                   >> $@

