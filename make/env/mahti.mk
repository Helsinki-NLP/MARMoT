#-*-makefile-*-
#
# specific configuration for puhti@csc
#

HPC_PROJECT ?= project_2001194


SLURM_CPU_PARTITION ?= small
SLURM_MAX_CPU_TIME  ?= 3-00:00:00

SLURM_GPU_PARTITION ?= gpumedium
SLURM_MAX_GPU_TIME  ?= 1-12:00:00
SLURM_GPU_GRES      ?= gpu:a100
