#!/bin/bash

#SBATCH -A project_462001509
#SBATCH -J mammoth
#SBATCH -o /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.%j.out
#SBATCH -e /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=18
#SBATCH --ntasks=18
#SBATCH --cpus-per-task=56
#SBATCH --mem=480G
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:8
#SBATCH --mail-type=END
#SBATCH --mail-user=jorg.tiedemann@helsinki.fi

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -eux

# mark job as running
mv /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob.running

# mark job as failed if interrupted
trap 'mv /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob.running /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob.failed' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM

export PYTORCH_ALLOC_CONF=expandable_segments:True
# Get the master node (first node in the job allocation) and set its port
MASTER_NODE=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n 1)
MASTER_PORT=9973

echo "Master node: ${MASTER_NODE}"
echo "Master port: ${MASTER_PORT}"
echo "Node list: ${SLURM_JOB_NODELIST}"

export MASTER_NODE="${MASTER_NODE}"
export MASTER_PORT="${MASTER_PORT}"
export TOKENIZERS_PARALLELISM=False

srun make -j 56 -C /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base \
             HPC_HOST=lumi \
             TRAIN_STAGE=train \
             MODEL_NAME=mammoth \
             MASTER_NODE=${MASTER_NODE} \
             MASTER_PORT=${MASTER_PORT} \
             /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train

# mark job as done
mv /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob.running /pfs/lustrep2/scratch/project_462001509/members/tiedeman/MARMoT/models/pytorch/docmt-4pivot-denoise-halfgroupsharedenc-base/mammoth/train.slurmjob.done

echo "Finishing at `date`"
