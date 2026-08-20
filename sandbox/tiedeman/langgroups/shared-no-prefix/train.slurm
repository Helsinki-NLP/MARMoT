#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J shared
#SBATCH -o /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train.%j.out
#SBATCH -e /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=9
#SBATCH --ntasks=9
#SBATCH --cpus-per-task=56
#SBATCH --mem=128G
#SBATCH --time=1-00:00:00
#SBATCH --gres=gpu:8

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -eux

#--------------------------------------------------------------------------
# Get the master node (first node in the job allocation)
MASTER_NODE=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n 1)

echo "Master node: ${MASTER_NODE}"
echo "Master port: 9973"
echo "Node list: ${SLURM_JOB_NODELIST}"
#--------------------------------------------------------------------------
# ask SLURM to send the USR1 signal 30 seconds before end of the time limit
#SBATCH --signal=B:USR1@30
timeup_function()
{
    echo "timeup_function called at `date`"
    srun /appl/local/csc/soft/ai/bin/gpu-energy --diff
}
abort_function()
{
    echo "abort_function called at `date`"
    /appl/local/csc/soft/ai/bin/gpu-energy --diff
}
trap 'timeup_function' USR1
trap 'abort_function' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM
#--------------------------------------------------------------------------

srun /appl/local/csc/soft/ai/bin/gpu-energy --save
/scratch/project_462000964/MARMoT/tools/lumi_gpu_usage.sh > /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train.${SLURM_JOBID}.gpu-usage &

# finally, the actual target to be done
srun make -C /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups \
             MODEL_NAME=shared \
             MASTER_NODE=${MASTER_NODE} \
             /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train

srun /appl/local/csc/soft/ai/bin/gpu-energy --diff
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train.slurm /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/langgroups/shared/train.slurm.done
echo "Finishing at `date`"
