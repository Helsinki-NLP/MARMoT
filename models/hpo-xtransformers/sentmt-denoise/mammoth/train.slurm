#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J mammoth
#SBATCH -o /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.%j.out
#SBATCH -e /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=10
#SBATCH --ntasks=10
#SBATCH --cpus-per-task=56
#SBATCH --mem=480G
#SBATCH --time=2-00:00:00
#SBATCH --gres=gpu:8
#SBATCH --mail-type=END
#SBATCH --mail-user=jorg.tiedemann@helsinki.fi

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -eux

# mark job as running
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob.running

# mark job as failed if interrupted
trap 'mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob.running /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob.failed' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM

# Get the master node (first node in the job allocation) and set its port
MASTER_NODE=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n 1)
MASTER_PORT=9973

echo "Master node: ${MASTER_NODE}"
echo "Master port: ${MASTER_PORT}"
echo "Node list: ${SLURM_JOB_NODELIST}"

export MASTER_NODE="${MASTER_NODE}"
export MASTER_PORT="${MASTER_PORT}"
export TOKENIZERS_PARALLELISM=False

srun make -j 56 -C /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise \
             HPC_HOST=lumi \
             TRAIN_STAGE=train \
             MODEL_NAME=mammoth \
             MASTER_NODE=${MASTER_NODE} \
             MASTER_PORT=${MASTER_PORT} \
             /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train

# mark job as done
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob.running /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/sentmt-denoise/mammoth/train.slurmjob.done

echo "Finishing at `date`"
