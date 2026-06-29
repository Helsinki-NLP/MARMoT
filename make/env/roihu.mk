#-*-makefile-*-
#
# specific configuration for roihu@csc
#


## default project on roihu

HPC_PROJECT  ?= project_2017852


## path to mammoth installation

ifeq (${TRANSFORMER_BACKEND},x-transformers)
  MAMMOTH_VERSION ?= mammoth_x_transformer
else
  MAMMOTH_VERSION ?= mammoth_pytorch
endif

MAMMOTH_HOME     ?= /scratch/project_2017852/mammoth-shared
MAMMOTH_DIR      ?= ${MAMMOTH_HOME}/${MAMMOTH_VERSION}/mammoth
MAMMOTH_ENV      ?= ${MAMMOTH_HOME}/.venv
LOAD_MAMMOTH_ENV ?= module purge;module load python-pytorch/2.10;export export MAMMOTH_PLATFORM=nvidia;


## roihu-specific environment

MAX_GPUS_PER_NODE         ?= 4
MAX_MEM_PER_GPU           ?= 120
MAX_CPUS_PER_GPU          ?= 72

SLURM_CPU_PARTITION       ?= medium
SLURM_MAX_CPU_TIME        ?= 1-12:00:00

SLURM_GPU_PARTITION       ?= gpularge
SLURM_GPU_SMALL_PARTITION ?= gpumedium
SLURM_GPU_LARGE_PARTITION ?= gpularge
SLURM_MAX_GPU_TIME        ?= 1-12:00:00
SLURM_GPU_GRES            ?= gpu:gh200


## is this still needed?

# SLURM_EXTRA         ?= \#SBATCH --argos=no
SRUN                ?= srun --argos=no





