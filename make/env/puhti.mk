#-*-makefile-*-
#
# specific configuration for puhti@csc
#

HPC_PROJECT ?= project_2001194
MAMMOTH_DIR ?= /scratch/project_2001194/mammoth-shared/mammoth


MAX_GPUS_PER_NODE   ?= 4

SLURM_CPU_PARTITION ?= small
SLURM_MAX_CPU_TIME  ?= 3-00:00:00

SLURM_GPU_PARTITION ?= gpu
SLURM_MAX_GPU_TIME  ?= 3-00:00:00
SLURM_GPU_GRES      ?= gpu:v100


MODEL_DTYPE          ?= fp32
XTRF_FLASH_ATTENTION ?= false
BATCH_SIZE           ?= 4096    # per-GPU batch size


MAMMOTH_ENV_ACTIVATE ?= module load pytorch && source ${MAMMOTH_ENV}/bin/activate
