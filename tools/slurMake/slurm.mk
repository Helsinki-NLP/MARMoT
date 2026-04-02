#-*-makefile-*-
#--------------------------------------------------------------
# generate SLURM scripts
#--------------------------------------------------------------


MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include ${MAKEFILE_DIR}env.mk


NR_OF_NODES   ?= 1
GPUS_PER_NODE ?= 0


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
SLURM_MEM           ?= 48G
SLURM_CPUS          ?= 16
SLURM_CPUS_PER_TASK ?= ${SLURM_CPUS}
SLURM_NODES         ?= ${NR_OF_NODES}
SLURM_TASKS         ?= ${SLURM_NODES}
SLURM_GPUS          ?= ${GPUS_PER_NODE}

ifneq (${SLURM_GPUS},0)
  SLURM_PARTITION ?= ${SLURM_GPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_GPU_TIME}
  SLURM_GRES      ?= ${SLURM_GPU_GRES}:${SLURM_GPUS}
else
  SLURM_PARTITION ?= ${SLURM_CPU_PARTITION}
  SLURM_TIME      ?= ${SLURM_MAX_CPU_TIME}
endif



## number of parallel jobs that make can run
## default = number of CPU cores we have allocated

SLURM_PARALLEL_JOBS ?= ${SLURM_CPUS_PER_TASK}


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
	@echo '#SBATCH -J $(@:.slurm=)'                                                      >> $@
	@echo '#SBATCH -o $(@:.slurm=).%j.out'                                               >> $@
	@echo '#SBATCH -e $(@:.slurm=).%j.err'                                               >> $@
	@echo '#SBATCH --partition=${SLURM_PARTITION}'                                       >> $@
	@echo '#SBATCH --nodes=${SLURM_NODES}'                                               >> $@
	@echo '#SBATCH --ntasks=${SLURM_TASKS}'                                              >> $@
	@echo '#SBATCH --cpus-per-task=${SLURM_CPUS_PER_TASK}'                               >> $@
	@echo '#SBATCH --mem=${SLURM_MEM}'                                                   >> $@
	@echo '#SBATCH --time=${SLURM_TIME}'                                                 >> $@
ifdef SLURM_GRES
	@echo '#SBATCH --gres=${SLURM_GRES}'                                                 >> $@
endif
ifdef EMAIL
	@echo '#SBATCH --mail-type=END'                                                      >> $@
	@echo '#SBATCH --mail-user=${EMAIL}'                                                 >> $@
endif
	@echo ''                                                                             >> $@
	@echo 'echo "Starting at `date`"'                                                    >> $@
ifneq (${SLURM_GPUS},0)
ifdef START_GPU_ENERGY_MONITORING
	@echo 'srun ${START_GPU_ENERGY_MONITORING}'                                          >> $@
endif
endif
	@echo ''                                                                             >> $@
	@echo "srun ${MAKE} -j ${SLURM_PARALLEL_JOBS} $(@:.slurm=)"                          >> $@
	@echo ''                                                                             >> $@
ifneq (${SLURM_GPUS},0)
ifdef STOP_GPU_ENERGY_MONITORING
	@echo 'srun ${STOP_GPU_ENERGY_MONITORING}'                                           >> $@
endif
endif
	@echo 'mv $@ $@.done'                                                                >> $@
	@echo 'echo "Finishing at `date`"'                                                   >> $@

