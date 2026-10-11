# MARMoT Experiment Makefiles - SLURM Configuration

The SLURM-related targets are defined in [slurm.mk](../slurm.mk) and can be used for any job type. Both the training targets ([train.mk](../train.mk)) and the evaluation targets ([eval.mk](../eval.mk)) build on top of them.

## Targets

| target | purpose |
|---|---|
| `make train` | generate the training config + SLURM script and submit the job |
| `make train-slurm` | generate the training config and the SLURM script `${MODEL_DIR}/train.slurm` (without submitting) |
| `make stop` / `make trainstop` | cancel the running training job (`scancel`) |
| `make eval` | generate evaluation configs + SLURM script and submit one job evaluating all tasks |
| `make eval-jobs` | submit one evaluation job per task |
| `make eval-task` | submit an evaluation job for the current task (select with `TASK_NR`, `TASK` or `TASK_ID`) |

The generic SLURM machinery:

* `${MODEL_DIR}/train.slurm` etc.: generated SLURM scripts
* `${MODEL_DIR}/train.slurmjob`: submitted jobs are recorded here; `sbatch` output is appended
* `.slurmjob.running`: marker file set while the job is running (the script moves the file at start and end)
* `.slurmjob.done`: marker file set after the job finished successfully; as long as it exists, `make` will refuse to resubmit the job. Delete it to restart the job.
* `.slurmjob.failed`: marker file set if the job is interrupted

You can also create these files manually with the pattern rules in [slurm.mk](../slurm.mk), e.g. any target `foo.slurm` generates a script and `foo.slurmjob` submits it.

## How jobs are generated

The SLURM script is generated from the variables below. `SLURM_PARTITION`, `SLURM_TIME` and `SLURM_GRES` are set automatically based on the requested resources:

* if `SLURM_GPUS > 0`, the GPU partition is used (`SLURM_GPU_PARTITION`), the time limit is `SLURM_MAX_GPU_TIME` and the generic resource request is `SLURM_GPU_GRES:${SLURM_GPUS}` (e.g. `gpu:v100:2`)
* otherwise the CPU partitions and `SLURM_MAX_CPU_TIME` are used
* single-node jobs use the "small" partition variants (`SLURM_GPU_SMALL_PARTITION`), multi-node jobs the "large" ones (`SLURM_GPU_LARGE_PARTITION`); by default the small and large variants are identical

## Variables

| variable | default | description |
|---|---|---|
| `SLURM_NODES` | `${NR_OF_NODES}` | `--nodes` |
| `SLURM_TASKS` | `${SLURM_NODES}` | `--ntasks` |
| `SLURM_GPUS` | `${GPUS_PER_NODE}` | number of GPUs per node |
| `SLURM_CPUS_PER_TASK` | `16` | `--cpus-per-task` |
| `SLURM_MEM` | `48G` | `--mem` |
| `SLURM_TIME` | max GPU/CPU time | `--time` |
| `SLURM_PARTITION` | auto | partition selected as described above |
| `SLURM_GPU_GRES` | host-specific (`gpu:v100`) | type of GPU resource |
| `SLURM_EXCLUDE` | - | comma-separated list of nodes to exclude (`--exclude`) |
| `SLURM_EXTRA` | - | extra lines appended to the SLURM script |
| `SLURM_MAX_NR_JOBS` | `200` | maximum number of queued jobs for your user; `make` waits if the queue is full |
| `EMAIL` | set for the `tiedeman` user | e-mail address for job end notifications (`--mail-type=END`) |
| `SRUN` | `srun` | command used to start the job (e.g. `srun --argos=no` on ROI-HU) |
| `SLURM_PARALLEL_JOBS` | `${SLURM_CPUS_PER_TASK}` | number of parallel make jobs inside the SLURM script (`make -j ...`) |
| `HPC_PROJECT` | host-specific | SLURM account (`-A`) |

### Job dependencies

* `SLURM_DEPENDENCIES`: list of `.slurmjob` files of previous stages; if those jobs exist (or are still running), the new job is submitted with `--dependency=afterok:jobid`. The training targets set this automatically through `TRAIN_DEPENDENCIES` (based on `PREV_TRAIN_STAGE`).
* `SBATCH_ARGS`: additional arguments passed to `sbatch`.

## Restarting jobs

Training jobs can automatically restart themselves when they time out or are interrupted:

* `TRAIN_RESTARTS` (training) and `SLURM_MAX_RESTARTS` (generic): maximum number of automatic restarts. When set, the generated script submits a follow-up job that continues training from the saved checkpoint.
* `SLURM_RESTART_COUNT`: current restart iteration (internal).
* `SLURM_RESTART_JOB=1`: allows resubmitting a job whose `.slurmjob.running` file still exists (used by the restart logic).

## Multi-node jobs

For multi-node jobs (`SLURM_NODES > 1`), the script determines the master node from the job allocation (`SLURM_JOB_NODELIST`), exports `MASTER_NODE` and `MASTER_PORT` (default `9973`, see `MASTER_PORT` in [train.mk](../train.mk)) and sets `TOKENIZERS_PARALLELISM=False`. The training command then uses `--node_rank ${SLURM_PROCID} --master_ip ${MASTER_NODE} --master_port ${MASTER_PORT}` for communication.

Note that logging from the individual nodes is stored in per-node log directories, see `SLURM_NODE_LOGDIR` in [env.mk](../env.mk) (`${PWD}/log/job${SLURM_JOBID}/node${SLURM_PROCID}`), e.g. for the GPU energy and usage monitors on LUMI.

## Partitions per host

The included host environments set the partitions, time limits and GPU types for the CSC systems:

| host | GPU partition | GPU | max GPU time | CPU partition |
|---|---|---|---|---|
| LUMI | `standard-g` | `gpu` (AMD MI250X) | `2-00:00:00` | `standard` |
| PUHTI | `gpu` | `gpu:v100` | `3-00:00:00` | `small` |
| MAHTI | `gpumedium` | `gpu:a100` | `1-12:00:00` | `small` |
| ROI-HU | `gpumedium`/`gpularge` | `gpu:gh200` | `1-12:00:00` | `medium` |

See the [environment documentation](env.md) for how to add a new host.