#-*-makefile-*-
#
# specific configuration for puhti@csc
#

HPC_PROJECT  ?= project_2001194
MAMMOTH_HOME ?= /scratch/project_2001194/mammoth-shared
MAMMOTH_DIR  ?= ${MAMMOTH_HOME}/mammoth_dev/mammoth
# MAMMOTH_DIR  ?= ${MAMMOTH_HOME}/mammoth_stable/mammoth


MAX_GPUS_PER_NODE   ?= 4
MAX_MEM_PER_GPU     ?= 32
MAX_CPUS_PER_GPU    ?= 10

SLURM_CPU_PARTITION ?= small
SLURM_MAX_CPU_TIME  ?= 3-00:00:00

SLURM_GPU_PARTITION ?= gpu
SLURM_MAX_GPU_TIME  ?= 3-00:00:00
SLURM_GPU_GRES      ?= gpu:v100


MODEL_DTYPE          ?= fp32
XTRF_FLASH_ATTENTION ?= false
BATCH_SIZE           ?= 4096    # per-GPU batch size
VALID_BATCH          ?= 64

LOAD_MAMMOTH_ENV     ?= module purge; module load pytorch; 
MAMMOTH_ENV          ?= ${MAMMOTH_HOME}/.venv

## do we need to load the pytorch module once again?
#
# MAMMOTH_ENV_ACTIVATE ?= ${LOAD_MAMMOTH_ENV} source ${MAMMOTH_ENV}/bin/activate
