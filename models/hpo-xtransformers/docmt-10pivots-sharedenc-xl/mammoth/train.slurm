#!/bin/bash

#SBATCH -A project_2017852
#SBATCH -J mammoth
#SBATCH -o /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.%j.out
#SBATCH -e /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.%j.err
#SBATCH --partition=gpupilot
#SBATCH --nodes=32
#SBATCH --ntasks=32
#SBATCH --cpus-per-task=288
#SBATCH --mem=480G
#SBATCH --time=2-00:00:00
#SBATCH --gres=gpu:gh200:4
#SBATCH --mail-type=END
#SBATCH --mail-user=jorg.tiedemann@helsinki.fi

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -eux

# mark job as running
mv /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob.running

# mark job as failed if interrupted
trap 'mv /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob.running /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob.failed' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM

# Get the master node (first node in the job allocation) and set its port
MASTER_NODE=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n 1)
MASTER_PORT=9973

echo "Master node: ${MASTER_NODE}"
echo "Master port: ${MASTER_PORT}"
echo "Node list: ${SLURM_JOB_NODELIST}"

export MASTER_NODE="${MASTER_NODE}"
export MASTER_PORT="${MASTER_PORT}"
export TOKENIZERS_PARALLELISM=False

srun --argos=no make -j 288 -C /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl \
             HPC_HOST=roihu \
             TRAIN_STAGE=train \
             MODEL_NAME=mammoth \
             MASTER_NODE=${MASTER_NODE} \
             MASTER_PORT=${MASTER_PORT} \
             /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train

# mark job as done
mv /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob.running /scratch/project_2017852/members/tiedemann/MARMoT/sandbox/roihu/docmt-denoise-xl/mammoth/train.slurmjob.done

echo "Finishing at `date`"
