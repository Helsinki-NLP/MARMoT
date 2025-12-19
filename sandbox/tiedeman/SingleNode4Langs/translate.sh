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


path_to_data=/scratch/project_462000964/MARMoT/data
path_to_tokenizer=/scratch/project_462000964/MARMoT/tokenizer
path_to_tools=/scratch/project_462000964/MARMoT/tools
path_to_mammoth=/scratch/project_462000964/MARMoT/mammoth
# path_to_mammoth=/scratch/project_462000964/shared/mammoth

# path_to_workspace=/scratch/project_462000964/MARMoT/sandbox/tiedeman
path_to_workspace=/scratch/project_462000964/members/tiedeman/MARMoT/sandbox/tiedeman/SingleNode4Langs
# path_to_workspace=`pwd`

singularity exec \
	    -B $path_to_workspace:$path_to_workspace:rw \
	    -B $path_to_mammoth:$path_to_mammoth:ro \
	    -B $path_to_data:$path_to_data:ro \
	    -B $path_to_tokenizer:$path_to_tokenizer:ro \
	    /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif \
	    $path_to_mammoth/.venv/bin/python $path_to_mammoth/translate.py \
	    -config $path_to_workspace/inference-ende.yaml \
	    -model $path_to_workspace/best-model/de-en-fi-sv \
	    -src $path_to_data/tatoeba/test/deu-eng.eng.gz \
	    -output $path_to_workspace/deu-eng.eng.90000.deu

#	    -src $path_to_data/tatoeba/test/deu-eng.deu.gz \
#	    -output $path_to_workspace/deu-eng.deu.90000.eng


echo "Finishing at `date`"

