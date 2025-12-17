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


path_to_data=/scratch/project_462000964/marmot/data
path_to_tokenizer=/scratch/project_462000964/marmot/tokenizer
path_to_tools=/scratch/project_462000964/marmot/tools
path_to_workspace=/scratch/project_462000964/marmot/sandbox/tiedemann
path_to_mammoth=/scratch/project_462000964/marmot/mammoth


/appl/local/csc/soft/ai/bin/gpu-energy --save

${path_to_tools}/lumi_gpu_usage.sh > log/training.gpu-usage &
singularity exec \
	    -B $path_to_workspace:$path_to_workspace:rw \
	    -B $path_to_data:$path_to_data:ro \
	    -B $path_to_tokenizer:$path_to_tokenizer:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    $path_to_mammoth/.venv/bin/python $path_to_mammoth/train.py \
	    -config train.yaml

/appl/local/csc/soft/ai/bin/gpu-energy --diff
echo "Finishing at `date`"
