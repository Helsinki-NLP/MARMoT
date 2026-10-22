# SLURM job templates - used internally by the eval pipeline

This directory contains templates used to generate model-specific SLURM job scripts for inference, evaluation, and continuation of the evaluation pipeline.

The files in this directory are **templates, not scripts that should normally be submitted directly with `sbatch`**. They contain placeholders such as `**ACCOUNT**`, `**OUTDIR**`, and `**MODELDIR**` that are replaced when the job scripts are generated.

The templates are expanded with `m4`. The line

```bash
changecom()dnl
```

changes the `m4` comment syntax so that lines beginning with `#`, in particular SLURM directives such as

```bash
#SBATCH --partition=small
```

are preserved and expanded correctly.

## Files

| Template | Purpose | Default partition |
|---|---|---|
| `slurm_inf.templ` | Run translation/inference jobs, including GPU jobs | `small-g` |
| `slurm_met.templ` | Compute evaluation metrics such as SacreBLEU | `small` |
| `slurm_cnt.templ` | Continue the evaluation pipeline after an earlier stage | `small` |

The generated scripts are normally managed by the surrounding Makefile infrastructure. Users should generally invoke the corresponding `make` targets rather than expanding or submitting these templates manually.

---

## Template variables

The templates contain values of the form

```text
**VARIABLE**
```

which must be replaced before the generated script is executed.

Frequently used variables include:

| Variable | Meaning |
|---|---|
| `ACCOUNT` | SLURM project/account |
| `DISKPROJECT` | project used for filesystem bindings |
| `SELFDIR` | directory containing the evaluation Makefiles and helper scripts |
| `TSKDIR` | tasks directory for the current model/job |
| `MODELDIR` | model directory; also used as the SLURM working directory |
| `LOGDIR` | directory for SLURM stdout/stderr logs |
| `JOB_NAME` | SLURM job name |
| `MAKESCRIPT` | generated, model-specific version of a template |
| `FLAG` | file indicating that the corresponding stage has been submitted/running |
| `DONE` | completion marker |
| `PARTITION` | selected SLURM partition |
| `SBATCH_LINE` | generated `sbatch` command |
| `ACTIVATE` | environment-activation command or configuration |
| `SIF` | Singularity container image used for inference |

Each generated script checks its required variables before doing any work. If a placeholder has accidentally survived template expansion, the script terminates with an error such as

```text
ERROR: ACCOUNT was not substituted: **ACCOUNT**
```

This is intended to catch incomplete or incorrectly generated job scripts early.

---

# Inference jobs: `slurm_inf.templ`

`slurm_inf.templ` is the GPU template used for model inference.

Its default SLURM resources are

```bash
#SBATCH --partition=small-g
#SBATCH --mem=60G
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=7
```

The total running time, number of tasks, GPUs, and nodes are determined dynamically rather than being fixed in the template:

```text
##SBATCH --time=**TIME**
##SBATCH --ntasks=**NTASKS**
##SBATCH --gpus=**GPUS**
##SBATCH --nodes=**NODES**
```

The doubled `##SBATCH` makes these lines comments. The actual resource request is constructed separately from the calculated workload.

## Two-phase execution

The inference machinery deliberately uses the same generated script in two different contexts.

### Phase 1: determine the resources

When the generated script is run outside SLURM, i.e. when `SLURM_JOBID` is not set, it runs

```bash
bash "${SLURM_DISTR}"
```

where

```bash
SLURM_DISTR="${SELFDIR}/slurm_distr.sh"
```

The distributor examines the inference calls in

```text
${OUTDIR}/calls.out
```

and constructs the model-specific SLURM submission machinery, including the required `sbatch` command.

Conceptually, the process is

```text
calls.out
    |
    v
slurm_distr.sh
    |
    +--> calculate required resources
    |
    +--> generate model-specific SLURM script / sbatch command
```

### Phase 2: execute under SLURM

When the generated script runs as a SLURM job, `SLURM_JOBID` is defined. The script then launches the work through `srun` inside the configured Singularity container:

```text
SLURM allocation
      |
      v
Singularity container
      |
      v
bin/slurm_wrapper.sh
      |
      v
distributed inference calls
```

The wrapper is expected at

```text
${SELFDIR}/bin/slurm_wrapper.sh
```

and the distributor at

```text
${SELFDIR}/slurm_distr.sh
```

The script verifies that both exist before proceeding.

## Singularity container

Inference is executed in the image specified by `SIF`.

Before starting, the compute job checks that the image is readable:

```bash
[[ -r "${SIF}" ]]
```

The relevant project scratch directories are bound into the container:

```text
/scratch/${DISKPROJECT}
/scratch/${ACCOUNT}
```

This setup is currently tailored to the LUMI environment.

## NCCL configuration

The inference template also sets LUMI-specific NCCL networking variables:

```bash
NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
NCCL_NET_GDR_LEVEL=PHB
NCCL_DEBUG=INFO
```

These settings are passed explicitly into the Singularity environment.

---

# Metric jobs: `slurm_met.templ`

`slurm_met.templ` is used for metric computation after inference.

It uses CPU nodes by default:

```bash
#SBATCH --partition=small
#SBATCH --cpus-per-task=1
```

The workload is described in

```text
${OUTDIR}/calls.sacre.out
```

and is distributed using the same generic helpers as inference:

```text
${SELFDIR}/slurm_distr.sh
${SELFDIR}/bin/slurm_wrapper.sh
```

As with inference, the template has two modes.

Outside a SLURM allocation it runs

```bash
bash "${SLURM_DISTR}"
```

to prepare the model-specific job.

Inside a SLURM allocation it runs

```bash
srun "${SLURM_WRAPPER}"
```

to execute the metric calls.

The time, number of tasks, and number of nodes are calculated from the workload rather than being permanently fixed in the template.

---

# Continuation jobs: `slurm_cnt.templ`

`slurm_cnt.templ` provides a small CPU job for advancing the pipeline after a previous stage.

Its default resource request is deliberately modest:

```bash
#SBATCH --partition=small
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --time=00:10:00
#SBATCH --ntasks=1
```

The main command is

```bash
make -C "${SELFDIR}" "${FIRST_GOAL}" continue-eval
```

Thus the continuation job returns control to the Makefile infrastructure and asks it to start with `FIRST_GOAL` and then continue the evaluation pipeline.

This makes it possible to chain stages without keeping an interactive shell running.

---

# Status files

The templates use two filesystem markers:

```text
FLAG
DONE
```

`FLAG` represents an active/submitted stage, while `DONE` is created when the generated script exits.

The templates install an `EXIT` trap similar to

```bash
trap 'rm -f "${FLAG}"; touch "${DONE}"' EXIT
```

so that the running/submitted flag is removed and the completion marker is created when the script terminates.

**Note:** because this is an `EXIT` trap, `DONE` currently means that the script has *terminated*, not necessarily that every command completed successfully. Scripts use

```bash
set -euo pipefail
```

so failures normally terminate the job immediately, but the `EXIT` trap still runs afterward. Code that needs to distinguish successful completion from failure should therefore also inspect the SLURM/job exit status or corresponding logs.

---

# Log files

The generated jobs write SLURM output and errors under `LOGDIR`.

Inference:

```text
infjob<jobid>.out
infjob<jobid>.err
```

Metric computation:

```text
sacrebleu<jobid>.out
sacrebleu<jobid>.err
```

Continuation jobs:

```text
cnt<jobid>.out
cnt<jobid>.err
```

Here `<jobid>` is the SLURM job ID (`%j`).

---

# Expected helper files

The templates are part of a larger evaluation framework and expect at least the following helper scripts:

```text
slurm_distr.sh
bin/slurm_wrapper.sh
```

Depending on the stage, they also expect a generated call list such as

```text
<OUTDIR>/calls.out
<OUTDIR>/calls.sacre.out
```

Users normally do not need to invoke these files directly. The corresponding Makefile targets create and consume them as part of the evaluation workflow.

---

# For developers

When adding a new placeholder to a template:

1. add the corresponding `export` statement;
2. add the variable to the template's substitution check;
3. ensure that the Makefile or template-generation code supplies its value; and
4. test the generated script, not only the `.templ` source.

For example:

```bash
export NEW_VARIABLE=**NEW_VARIABLE**
```

should be accompanied by `NEW_VARIABLE` in the validation loop:

```bash
for var in ... NEW_VARIABLE; do
    ...
done
```

This ensures that accidentally unexpanded templates fail immediately instead of producing a malformed SLURM job.

## Portability

These templates currently contain several assumptions specific to CSC/LUMI, notably:

- the `small` and `small-g` partitions;
- Singularity;
- `/scratch/<project>` filesystem paths;
- LUMI HSN interfaces `hsn0`–`hsn3`; and
- the current GPU/NCCL configuration.

Adapting the framework to another SLURM cluster will therefore normally require changes to the resource defaults, container execution, filesystem bindings, and network configuration.
