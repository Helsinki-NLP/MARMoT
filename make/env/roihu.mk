#-*-makefile-*-
#
# specific configuration for lumi@csc
#


HPC_PROJECT  ?= project_2017852
MAMMOTH_HOME ?= /scratch/project_2017852/mammoth-shared
MAMMOTH_DIR  ?= ${MAMMOTH_HOME}/mammoth


MAX_GPUS_PER_NODE   ?= 4
MAX_MEM_PER_GPU     ?= 120
MAX_CPUS_PER_GPU    ?= 72

QUEUE_SIZE          ?= 120

SLURM_CPU_PARTITION ?= medium
SLURM_MAX_CPU_TIME  ?= 1-12:00:00

SLURM_GPU_PARTITION ?= gpupilot
SLURM_MAX_GPU_TIME  ?= 2-00:00:00
SLURM_GPU_GRES      ?= gpu:gh200

# SLURM_EXTRA         ?= \#SBATCH --argos=no

SRUN                ?= srun --argos=no


LOAD_MAMMOTH_ENV    ?= module purge;module load python-pytorch/2.10;export export MAMMOTH_PLATFORM=nvidia;
MAMMOTH_ENV         ?= ${MAMMOTH_HOME}/.venv



