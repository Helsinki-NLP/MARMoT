#-*-makefile-*-
#
# specific configuration for lumi@csc
#


HPC_PROJECT ?= project_462000964

SLURM_CPU_PARTITION ?= standard
SLURM_MAX_CPU_TIME  ?= 2-00:00:00

SLURM_GPU_PARTITION ?= standard-g
SLURM_MAX_GPU_TIME  ?= 2-00:00:00
SLURM_GPU_GRES      ?= gpu


PYTORCH_CONTAINER ?= /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif
