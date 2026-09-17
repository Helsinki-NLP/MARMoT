#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J mammoth
#SBATCH -o /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.%j.out
#SBATCH -e /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
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
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob.running

# mark job as failed if interrupted
trap 'mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob.running /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob.failed' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM

srun make -j 56 -C /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl \
             HPC_HOST=lumi \
             TRAIN_STAGE=train \
             MODEL_NAME=mammoth \
             /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train

# mark job as done
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob.running /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/flan-halfshared-xl/mammoth/train.slurmjob.done

echo "Finishing at `date`"
