#-*-makefile-*-
#
# specific configuration for lumi@csc
#


## temporarly exclude this node
# SLURM_EXCLUDE := nid005878

MAMMOTH_VERSION ?= dev
# MAMMOTH_VERSION ?= joerg


HPC_PROJECT  ?= project_462000964
MAMMOTH_HOME ?= /scratch/project_462000964/shared/mammoth-shared
MAMMOTH_DIR  ?= ${MAMMOTH_HOME}/mammoth-${MAMMOTH_VERSION}/mammoth


MAX_GPUS_PER_NODE   ?= 8
MAX_MEM_PER_GPU     ?= 60
MAX_CPUS_PER_GPU    ?= 7

QUEUE_SIZE          ?= 120

SLURM_CPU_PARTITION ?= standard
SLURM_MAX_CPU_TIME  ?= 2-00:00:00

SLURM_GPU_PARTITION ?= standard-g
SLURM_MAX_GPU_TIME  ?= 2-00:00:00
SLURM_GPU_GRES      ?= gpu


## some logfiles for energy consumption, GPU usage, Flight Recorder logs

SLURM_NODE_LOGDIR           ?= ${MODEL_LOGDIR}/job$${SLURM_JOBID}/node$${SLURM_PROCID}
START_GPU_ENERGY_MONITORING ?= /appl/local/csc/soft/ai/bin/gpu-energy --save
STOP_GPU_ENERGY_MONITORING  ?= /appl/local/csc/soft/ai/bin/gpu-energy --diff > ${SLURM_NODE_LOGDIR}/gpu-energy.txt
MONITOR_GPU_USAGE           ?= $(abspath ${MAKEFILE_DIR}..)/tools/lumi_gpu_usage.sh > ${SLURM_NODE_LOGDIR}/gpu-usage.txt &
CLEANUP_TRAP                ?= trap '${STOP_GPU_ENERGY_MONITORING}' SIGHUP SIGINT SIGABRT SIGKILL SIGTERM


## export various NCCL variables
## ──────────────────────────────────────────────────
## RCCL environment variables for Slingshot network
## ──────────────────────────────────────────────────
## Use all Slingshot network interfaces for inter-node communication
##    NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
## Enable GPU RDMA (direct GPU-to-GPU transfers over the network)
##    NCCL_NET_GDR_LEVEL=PHB
## Flight Recorder: dump RCCL collective traces on timeout
## TODO: is it enough to set them as env parameters for singularity?

NCCL_SOCKET_IFNAME ?= hsn0,hsn1,hsn2,hsn3
NCCL_NET_GDR_LEVEL ?= PHB

TORCH_ENV_VARIABLES ?= 	export NCCL_SOCKET_IFNAME=${NCCL_SOCKET_IFNAME}; \
			export NCCL_NET_GDR_LEVEL=${NCCL_NET_GDR_LEVEL}; \
			export TORCH_NCCL_TRACE_BUFFER_SIZE=2000; \
			export TORCH_NCCL_DUMP_ON_TIMEOUT=true; \
			export TORCH_FR_DUMP_TEMP_FILE=${SLURM_NODE_LOGDIR}/nccl_trace_rank_


## commands to run before the main GPU task and after finishing the main task

PREPARE_GPU_ENV ?= mkdir -p ${SLURM_NODE_LOGDIR};${START_GPU_ENERGY_MONITORING};${MONITOR_GPU_USAGE};${TORCH_ENV_VARIABLES};${CLEANUP_TRAP}
CLEANUP_GPU_ENV ?= ${STOP_GPU_ENERGY_MONITORING}



# PYTORCH_CONTAINER ?= /appl/local/containers/sif-images/lumi-pytorch-rocm-6.2.4-python-3.12-pytorch-v2.7.1.sif
# PYTORCH_CONTAINER ?= /appl/local/laifs/containers/lumi-multitorch-u24r64f21m43t29-20260225_144743/lumi-multitorch-full-u24r64f21m43t29-20260225_144743.sif
PYTORCH_CONTAINER ?= /appl/local/laifs/containers/lumi-multitorch-u24r64f21m43t29-20260319_153422/lumi-multitorch-full-u24r64f21m43t29-20260319_153422.sif


ifdef PRETRAINED_MODEL
  ifneq ($(dir ${PRETRAINED_MODEL}),${MODEL_DIR})
    EXTRA_SINGULARITY_PARAM += -B $(dir ${PRETRAINED_MODEL}):$(dir ${PRETRAINED_MODEL})
  endif
endif

SINGULARITY_PARAMS ?= 	--env MASTER_NODE="$${MASTER_NODE}" \
			--env MASTER_PORT="$${MASTER_PORT}" \
			--env NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME}" \
			--env NCCL_NET_GDR_LEVEL="${NCCL_NET_GDR_LEVEL}" \
			--env NCCL_DEBUG="INFO" \
			--env TORCH_NCCL_TRACE_BUFFER_SIZE=2000 \
			--env TORCH_NCCL_DUMP_ON_TIMEOUT=true \
			--env TORCH_FR_DUMP_TEMP_FILE=${SLURM_NODE_LOGDIR}/nccl_trace_rank_ \
			-B ${MODEL_DIR}:${MODEL_DIR}:rw \
			-B ${MAMMOTH_HOME}:${MAMMOTH_HOME}:ro \
			-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \
			-B ${MAKEFILE_DIR}:${MAKEFILE_DIR}:ro \
			${EXTRA_SINGULARITY_PARAM}


## not needed with latest PYTORCH_CONTAINER anymore
#			--env LD_PRELOAD="/usr/lib/libfabric.so.1 /opt/rocm/lib/librccl.so.1"


## not needed anymore?
# -B /dev/shm:/dev/shm:rw 



## finally the command to load the MAMMOTH environment

LOAD_MAMMOTH_ENV ?= singularity exec ${SINGULARITY_PARAMS} ${PYTORCH_CONTAINER}
MAMMOTH_ENV      ?= ${MAMMOTH_HOME}/.venv




# ──────────────────────────────────────────────────
# CPU-GPU binding masks for LUMI-G'                 
# ──────────────────────────────────────────────────
# Each GCD (GPU die) on MI250X is wired to specific CPU cores.
# These masks bind each of the 8 tasks (1 per GCD) to its 7 nearest CPU cores:
#   GCD 0 -> CPUs 49-55, GCD 1 -> CPUs 57-63,
#   GCD 2 -> CPUs 17-23, GCD 3 -> CPUs 25-31,
#   GCD 4 -> CPUs  1-7,  GCD 5 -> CPUs  9-15,
#   GCD 6 -> CPUs 33-39, GCD 7 -> CPUs 41-47


## srun with cpu-bindings

# CPU_BIND := mask_cpu:fe000000000000,fe00000000000000,fe0000,fe000000,fe,fe00,fe00000000,fe0000000000
# SRUN := srun --cpu-bind=${CPU_BIND}

# CPU_BIND_MASKS := 0x00fe000000000000,0xfe00000000000000,0x0000000000fe0000,0x00000000fe000000,0x00000000000000fe,0x000000000000fe00,0x000000fe00000000,0x0000fe0000000000

# ifeq (${GPUS_PER_NODE},8)
#   SRUN := srun --cpu-bind=mask_cpu=${CPU_BIND_MASKS}
# endif

# SRUN := srun
