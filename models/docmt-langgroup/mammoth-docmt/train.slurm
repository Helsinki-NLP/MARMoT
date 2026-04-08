#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J mammoth-docmt
#SBATCH -o /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train.%j.out
#SBATCH -e /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=9
#SBATCH --ntasks=9
#SBATCH --cpus-per-task=56
#SBATCH --mem=480G
#SBATCH --time=2-00:00:00
#SBATCH --exclude=nid005878
#SBATCH --gres=gpu:8
#SBATCH --mail-type=END
#SBATCH --mail-user=jorg.tiedemann@helsinki.fi

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -eux

#--------------------------------------------------------------------------
# define a function for finishing up interrupted jobs
abort_function()
{
    echo "abort_function called at `date`"
    /appl/local/csc/soft/ai/bin/gpu-energy --diff
}
trap 'abort_function' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM
#--------------------------------------------------------------------------

# Get the master node (first node in the job allocation) and set its port
MASTER_NODE=$(scontrol show hostnames "${SLURM_JOB_NODELIST}" | head -n 1)
MASTER_PORT=9973

echo "Master node: ${MASTER_NODE}"
echo "Master port: ${MASTER_PORT}"
echo "Node list: ${SLURM_JOB_NODELIST}"

export MASTER_NODE="${MASTER_NODE}"
export MASTER_PORT="${MASTER_PORT}"
export TOKENIZERS_PARALLELISM=False

# ──────────────────────────────────────────────────
# RCCL environment variables for Slingshot network
# ──────────────────────────────────────────────────
# Use all Slingshot network interfaces for inter-node communication
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
# Enable GPU RDMA (direct GPU-to-GPU transfers over the network)
export NCCL_NET_GDR_LEVEL=PHB
srun /appl/local/csc/soft/ai/bin/gpu-energy --save
/pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/tools/lumi_gpu_usage.sh > /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train.${SLURM_JOBID}.gpu-usage &

srun make -j 56 -C /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder \
             HPC_HOST=lumi \
             MODEL_NAME=mammoth-docmt \
             MASTER_NODE=${MASTER_NODE} \
             MASTER_PORT=${MASTER_PORT} \
             /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train

srun /appl/local/csc/soft/ai/bin/gpu-energy --diff
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train.slurm /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/docmt-langgroup-encoder/mammoth-docmt/train.slurm.done
echo "Finishing at `date`"
