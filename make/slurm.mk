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

WHOAMI ?= $(shell whoami)
ifeq ("$(WHOAMI)","tiedeman")
  EMAIL ?= jorg.tiedemann@helsinki.fi
endif

SLURM_CPU_PARTITION ?= small
SLURM_GPU_PARTITION ?= gpu
SLURM_MAX_CPU_TIME  ?= 3-00:00:00
SLURM_MAX_GPU_TIME  ?= 3-00:00:00
SLURM_GPU_GRES      ?= gpu:v100
SLURM_MAX_NR_JOBS   ?= 200
SLURM_CPUS_PER_TASK ?= 16
SLURM_MEM           ?= 48G
SLURM_NODES         ?= ${NR_OF_NODES}
SLURM_TASKS         ?= ${SLURM_NODES}
SLURM_GPUS          ?= ${GPUS_PER_NODE}




## number of parallel jobs that make can run
## default = number of CPU cores we have allocated

SLURM_PARALLEL_JOBS ?= ${SLURM_CPUS_PER_TASK}


ifneq (${SLURM_GPUS},0)
  SLURM_PARTITION ?= ${SLURM_GPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_GPU_TIME}
  SLURM_GRES      ?= ${SLURM_GPU_GRES}:${SLURM_GPUS}
else
  SLURM_PARTITION ?= ${SLURM_CPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_CPU_TIME}
endif

SRUN ?= srun


##---------------------------
## submit a slurm job
##---------------------------

## add slurm dependencies

ifneq (${SLURM_DEPENDENCIES},)
  SLURM_DEPENDENCY_FILES := $(wildcard ${SLURM_DEPENDENCIES} $(addsuffix .running,${SLURM_DEPENDENCIES}))
  ifneq (${SLURM_DEPENDENCY_FILES},)
    SLURM_DEPENDENCY_JOBIDS := $(shell cat ${SLURM_DEPENDENCY_FILES} | rev | cut -f1 -d' ' | rev )
    SBATCH_ARGS += -d afterok:$(subst $(space),:,${SLURM_DEPENDENCY_JOBIDS})
  endif
endif

%.slurmjob: %.slurm
	@if [ -e $@.done ]; then \
	  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"; \
	  echo "Job $@ is already done!"; \
	  echo "Delete $@.done if you want to restart it!"; \
	  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"; \
	elif [ -e $@.running ] && [ "${SLURM_RESTART_JOB}" != "1" ] ; then \
	  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"; \
	  echo "Job $@ is running!"; \
	  echo "Delete $@.running if the job is stalled!"; \
	  echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"; \
	else \
	  while [ `squeue -u ${WHOAMI} | wc -l` -gt ${SLURM_MAX_NR_JOBS} ]; do \
	    echo "waiting for space in the queue";\
	    sleep 10; \
	  done; \
	  echo "sbatch ${SBATCH_ARGS} $<"; \
	  sbatch ${SBATCH_ARGS} $< >> $@; \
	  echo "tail -1 $@"; \
	fi


##---------------------------
## create a slurm script
##---------------------------


## define how many restarts of slurm training jobs we
## can submit in case a jobs times out or breaks
##
## SLURM_RESTART_COUNT = current iteration
## SLURM_MAX_RESTARTS  = maximum number of restarts

SLURM_RESTART_COUNT ?= 0
SLURM_MAX_RESTARTS  ?= 0


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
	@echo '#SBATCH --ntasks=${SLURM_TASKS}'                                              >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}'                               >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}'                                                   >> $@
	@echo '#SBATCH --time=${SLURM_TIME}'                                                 >> $@
ifdef SLURM_EXCLUDE
	@echo '#SBATCH --exclude=${SLURM_EXCLUDE}'                                           >> $@
endif
ifdef SLURM_GRES
	@echo '#SBATCH --gres=${SLURM_GRES}'                                                 >> $@
endif
ifdef EMAIL
	echo '#SBATCH --mail-type=END'                                                       >> $@
	echo '#SBATCH --mail-user=${EMAIL}'                                                  >> $@
endif
	@echo ''                                                                             >> $@
	@echo 'echo "Starting at `date`"'                                                    >> $@
	@echo ''                                                                             >> $@
	@echo '# stops the script when encountering an error'                                >> $@
	@echo '# (useful if running several commands in the same script)'                    >> $@
	@echo 'set -eux'                                                                     >> $@
	@echo ''                                                                             >> $@
	@echo '# mark job as running'                                                        >> $@
	@echo "mv $@job $@job.running"                                                       >> $@
	@echo ''                                                                             >> $@
	@echo '# mark job as failed if interrupted'                                          >> $@
	@echo "trap 'mv $@job.running $@job.failed' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM"   >> $@
	@echo ''                                                                             >> $@
ifneq (${SLURM_MAX_RESTARTS},0)
  ifneq (${SLURM_MAX_RESTARTS},${SLURM_RESTART_COUNT})
	@echo '# submit job that continues in case the current one breaks or times out'      >> $@
	@echo "# current iteration: ${SLURM_RESTART_COUNT}/${SLURM_MAX_RESTARTS}"            >> $@
	@echo "${MAKE} -C ${EXPERIMENT_DIR} $@job \\"                                        >> $@
	@echo "	SLURM_RESTART_JOB=1 \\"                                                      >> $@
	@echo "	SLURM_RESTART_COUNT=$$(( ${SLURM_RESTART_COUNT} + 1 )) \\"                   >> $@
	@echo '	SBATCH_ARGS="-d afternotok:$${SLURM_JOBID}"'                                 >> $@
	@echo ''                                                                             >> $@
  endif
endif
ifneq (${SLURM_NODES},1)
	@echo '# Get the master node (first node in the job allocation) and set its port'    >> $@
	@echo 'MASTER_NODE=$$(scontrol show hostnames "$${SLURM_JOB_NODELIST}" | head -n 1)' >> $@
#	@echo 'MASTER_PORT="$${MASTER_PORT:-$$((29500 + SLURM_JOB_ID % 1000))}"'             >> $@
	@echo 'MASTER_PORT=${MASTER_PORT}'                                                   >> $@
	@echo ''                                                                             >> $@
	@echo 'echo "Master node: $${MASTER_NODE}"'                                          >> $@
	@echo 'echo "Master port: $${MASTER_PORT}"'                                          >> $@
	@echo 'echo "Node list: $${SLURM_JOB_NODELIST}"'                                     >> $@
	@echo ''                                                                             >> $@
	@echo 'export MASTER_NODE="$${MASTER_NODE}"'                                         >> $@
	@echo 'export MASTER_PORT="$${MASTER_PORT}"'                                         >> $@
	@echo 'export TOKENIZERS_PARALLELISM=False'                                          >> $@
	@echo ''                                                                             >> $@
endif
	@echo "${SRUN} ${MAKE} -j ${SLURM_PARALLEL_JOBS} -C ${EXPERIMENT_DIR} \\"            >> $@
	@echo "             HPC_HOST=${HPC_HOST} \\"                                         >> $@
	@echo "             TRAIN_STAGE=${TRAIN_STAGE} \\"                                   >> $@
	@echo "             MODEL_NAME=${MODEL_NAME} \\"                                     >> $@
ifneq (${SLURM_NODES},1)
	@echo "             MASTER_NODE=\$${MASTER_NODE} \\"                                 >> $@
	@echo "             MASTER_PORT=\$${MASTER_PORT} \\"                                 >> $@
endif
	@echo "             $(@:.slurm=)"                                                    >> $@
	@echo ''                                                                             >> $@
	@echo '# mark job as done'                                                           >> $@
	@echo 'mv $@job.running $@job.done'                                                  >> $@
	@echo ''                                                                             >> $@
	@echo 'echo "Finishing at `date`"'                                                   >> $@

