#!/bin/bash

#SBATCH -A project_462000964
#SBATCH -J training
#SBATCH -o ./log/translating.%j.out
#SBATCH -e ./log/translating.%j.err
#SBATCH --partition=dev-g     
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=0-00:30:00
#SBATCH --gres=gpu:1 

echo "Starting at `date`"

# stops the script when encountering an error
# (useful if running several commands in the same script)
set -e

path_to_shared=/scratch/project_462000964/shared
path_to_workspace=/scratch/project_462000964/members/tiedemann/MARMoT
path_to_mammoth=/scratch/project_462000964/shared/mammoth

singularity exec \
	    -B $path_to_workspace:$path_to_workspace:rw \
	    -B $path_to_shared:$path_to_shared:ro \
    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
    $path_to_mammoth/.venv/bin/python $path_to_mammoth/translate.py \
    -config inference.yaml \
    -src /scratch/project_462000964/shared/tatoeba/dev5K/deu-eng.deu.gz \
    -output deu-eng.dev.deu.eng


echo "Finishing at `date`"

