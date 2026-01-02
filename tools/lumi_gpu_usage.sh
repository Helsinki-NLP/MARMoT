#!/usr/bin/bash

while [ 1 ]; do
    # rocm-smi -u | grep 'GPU use' | sed "s/^/${SLURM_PROCID}: /" >> $1
    rocm-smi -u | grep 'GPU use'
    # rocm-smi --showmemuse   ## doesn't seem to work?!
    sleep 10
done
