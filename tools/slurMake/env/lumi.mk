#-*-makefile-*-
#
# specific configuration for lumi@csc
#

HPC_PROJECT  ?= project_462000964

MAX_GPUS_PER_NODE   ?= 8
MAX_MEM_PER_GPU     ?= 16
MAX_CPUS_PER_GPU    ?= 7

SLURM_CPU_PARTITION ?= standard
SLURM_MAX_CPU_TIME  ?= 2-00:00:00

SLURM_GPU_PARTITION ?= standard-g
SLURM_MAX_GPU_TIME  ?= 2-00:00:00
SLURM_GPU_GRES      ?= gpu

START_GPU_ENERGY_MONITORING ?= /appl/local/csc/soft/ai/bin/gpu-energy --save
STOP_GPU_ENERGY_MONITORING  ?= /appl/local/csc/soft/ai/bin/gpu-energy --diff
MONITOR_GPU_USAGE           ?= $(abspath ${MAKEFILE_DIR}..)/tools/lumi_gpu_usage.sh

