#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J mammoth-engfin
#SBATCH -o /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train.%j.out
#SBATCH -e /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train.%j.err
#SBATCH --partition=standard-g
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --mem=60G
#SBATCH --time=2-00:00:00
#SBATCH --exclude=nid005878
#SBATCH --gres=gpu:1
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


# ──────────────────────────────────────────────────
# RCCL environment variables for Slingshot network
# ──────────────────────────────────────────────────
# Use all Slingshot network interfaces for inter-node communication
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
# Enable GPU RDMA (direct GPU-to-GPU transfers over the network)
export NCCL_NET_GDR_LEVEL=PHB
srun /appl/local/csc/soft/ai/bin/gpu-energy --save
/pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/tools/lumi_gpu_usage.sh > /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train.${SLURM_JOBID}.gpu-usage &

srun make -j 7 -C /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki \
             HPC_HOST=lumi \
             MODEL_NAME=mammoth-engfin \
             /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train

srun /appl/local/csc/soft/ai/bin/gpu-energy --diff
mv /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train.slurm /pfs/lustrep1/scratch/project_462000964/members/tiedeman/MARMoT/models/eng-fin-opuswiki/mammoth-engfin/train.slurm.done
echo "Finishing at `date`"
