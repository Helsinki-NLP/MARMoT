#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J deenfisv
#SBATCH -o ./log/training.%j.out
#SBATCH -e ./log/training.%j.err
#SBATCH --partition=standard-g     
#SBATCH --nodes=1
#SBATCH --cpus-per-task=48
#SBATCH --mem=96G
#SBATCH --time=2-00:00:00
#SBATCH --gres=gpu:8

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -e


path_to_shared=/scratch/project_462000964/MARMoT
path_to_mammoth=/scratch/project_462000964/shared/mammoth
path_to_workspace=/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/tatoeba


/appl/local/csc/soft/ai/bin/gpu-energy --save

${path_to_shared}/tools/lumi_gpu_usage.sh > log/training.gpu-usage &
singularity exec \
	    -B $path_to_workspace:$path_to_workspace:rw \
	    -B $path_to_mammoth:$path_to_mammoth:ro \
	    -B $path_to_shared:$path_to_shared:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    $path_to_mammoth/.venv/bin/python $path_to_mammoth/train.py \
	    -config $path_to_workspace/train.yaml \
	    -save_model $path_to_workspace/model/deu+eng+fin+swe

/appl/local/csc/soft/ai/bin/gpu-energy --diff
echo "Finishing at `date`"
