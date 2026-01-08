#-*-makefile-*-
#
# specific configuration for lumi@csc
#


HPC_PROJECT ?= project_462000964
MAMMOTH_DIR ?= /scratch/project_462000964/shared/mammoth


MAX_GPUS_PER_NODE   ?= 8

SLURM_CPU_PARTITION ?= standard
SLURM_MAX_CPU_TIME  ?= 2-00:00:00

SLURM_GPU_PARTITION ?= standard-g
SLURM_MAX_GPU_TIME  ?= 2-00:00:00
SLURM_GPU_GRES      ?= gpu

START_GPU_ENERGY_MONITORING ?= /appl/local/csc/soft/ai/bin/gpu-energy --save
STOP_GPU_ENERGY_MONITORING  ?= /appl/local/csc/soft/ai/bin/gpu-energy --diff
MONITOR_GPU_USAGE           ?= $(abspath ${MAKEFILE_DIR}..)/tools/lumi_gpu_usage.sh

PYTORCH_CONTAINER ?= /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif

SINGULARITY_PARAMS ?= 	-B ${MODEL_DIR}:${MODEL_DIR}:rw \
			-B ${MAMMOTH_DIR}:${MAMMOTH_DIR}:ro \
			-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
			-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
			-B /dev/shm:/dev/shm:rw \

LOAD_MAMMOTH_ENV ?= singularity exec ${SINGULARITY_PARAMS} ${PYTORCH_CONTAINER}
