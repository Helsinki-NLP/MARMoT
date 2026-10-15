#!/bin/bash
#SBATCH --job-name=eval3-inf-worker
#SBATCH --account=project_462001509
#SBATCH --partition=small-g
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus-per-task=1
#SBATCH --cpus-per-task=7
#SBATCH --mem=60G
#SBATCH --output=/scratch/project_462001509/members/tiedeman/MARMoT/models/eval3scheduler/logs/infjob%j.out
#SBATCH --error=/scratch/project_462001509/members/tiedeman/MARMoT/models/eval3scheduler/logs/infjob%j.err

# Model-independent eval3 inference worker for LUMI.
#
# Resource/container defaults intentionally follow eval2/3 slurm_inf.templ:
#   small-g, 1 task, 1 GPU, 7 CPUs, 60 GiB, project_462001509,
#   lumi-multitorch Singularity image, shared Mammoth venv, project scratch
#   bindings, and the established inference NCCL settings.
#
# Scheduler state remains only queue/, claims/, logs/.  Each worker submits at
# most one successor, normally after 1/3 of its allocation if queue work remains.
set -euo pipefail

ACCOUNT=${EVAL3_ACCOUNT:-project_462001509}
DISKPROJECT=${EVAL3_DISKPROJECT:-project_462001087}
SCHED=${EVAL3_SCHEDULER:-/scratch/project_462001509/members/tiedeman/MARMoT/models/eval3scheduler}
EVAL3_CODE=${EVAL3_CODE:-/scratch/project_462001087/members/aylijyra/dev/MARMoT/eval3/bin}
WORKER=${EVAL3_WORKER:-$EVAL3_CODE/eval3_worker.py}
SIF=${EVAL3_SIF:-/appl/local/laifs/containers/lumi-multitorch-u24r70f21m50t210-20260513_121430/lumi-multitorch-full-u24r70f21m50t210-20260513_121430.sif}
ACTIVATE=${EVAL3_ACTIVATE:-/scratch/project_462001509/shared/mammoth-shared/.venv/bin/activate}
RECOVERY_GRACE=${EVAL3_RECOVERY_GRACE:-300}
STOP_RESERVE=${EVAL3_STOP_RESERVE:-900}
POLL_SECONDS=${EVAL3_POLL_SECONDS:-15}
SUCCESSOR_DIVISOR=${EVAL3_SUCCESSOR_DIVISOR:-3}
DISABLE_SUCCESSOR=${EVAL3_DISABLE_SUCCESSOR:-0}
# Must be a persistent path, not Slurm's temporary spool copy.
SCRIPT=${EVAL3_SLURM_SCRIPT:-$EVAL3_CODE/eval3_worker.slurm}

[[ -f "$WORKER" ]] || { echo "ERROR: worker not found: $WORKER" >&2; exit 2; }
[[ -r "$SIF" ]] || {
    echo "ERROR: SIF image not readable on compute node: $SIF" >&2
    echo "Try: find -L /appl/local/laifs/containers -maxdepth 3 -type f -name '*.sif'" >&2
    exit 2
}
[[ -f "$ACTIVATE" ]] || { echo "ERROR: activation script not found: $ACTIVATE" >&2; exit 2; }
[[ -r "$SCRIPT" ]] || { echo "ERROR: worker Slurm script not readable: $SCRIPT" >&2; exit 2; }
[[ "$DISABLE_SUCCESSOR" == 0 || "$DISABLE_SUCCESSOR" == 1 ]] || {
    echo "ERROR: EVAL3_DISABLE_SUCCESSOR must be 0 or 1, got $DISABLE_SUCCESSOR" >&2
    exit 2
}
[[ "$SUCCESSOR_DIVISOR" =~ ^[1-9][0-9]*$ ]] || {
    echo "ERROR: bad EVAL3_SUCCESSOR_DIVISOR=$SUCCESSOR_DIVISOR" >&2
    exit 2
}
mkdir -p "$SCHED"/{queue,claims,logs}

# LUMI host-side Python.  Inference itself uses the shared venv in Singularity.
module load cray-python

# Keep the established LUMI inference NCCL settings from slurm_inf.templ.
export NCCL_SOCKET_IFNAME=hsn0,hsn1,hsn2,hsn3
export NCCL_NET_GDR_LEVEL=PHB
export NCCL_DEBUG=INFO

echo "eval3 worker job:       $SLURM_JOB_ID"
echo "scheduler:              $SCHED"
echo "account/disk project:   $ACCOUNT / $DISKPROJECT"
echo "container:              $SIF"
echo "inference environment:  $ACTIVATE"
echo "successor disabled:     $DISABLE_SUCCESSOR"
echo "Memory-related Slurm environment before srun:" >&2
env | LC_ALL=C sort | grep '^SLURM_MEM_' >&2 || true

# Use the actual Slurm allocation rather than assuming the #SBATCH walltime.
job_record=$(scontrol show job "$SLURM_JOB_ID" -o 2>/dev/null || true)
start_string=$(sed -n 's/.* StartTime=\([^ ]*\).*/\1/p' <<<"$job_record")
end_string=$(sed -n 's/.* EndTime=\([^ ]*\).*/\1/p' <<<"$job_record")
start_epoch=$(date -d "$start_string" +%s 2>/dev/null || true)
end_epoch=$(date -d "$end_string" +%s 2>/dev/null || true)
if [[ ! "$start_epoch" =~ ^[0-9]+$ || ! "$end_epoch" =~ ^[0-9]+$ || "$end_epoch" -le "$start_epoch" ]]; then
    echo "ERROR: cannot determine Slurm StartTime/EndTime for $SLURM_JOB_ID" >&2
    exit 2
fi
export EVAL3_DEADLINE_EPOCH=$end_epoch

allocation_seconds=$((end_epoch - start_epoch))
successor_epoch=$((start_epoch + allocation_seconds / SUCCESSOR_DIVISOR))
now_epoch=$(date +%s)
successor_delay=$((successor_epoch - now_epoch))
(( successor_delay < 0 )) && successor_delay=0

# Local coordination only.  This is not scheduler state.
local_state=${SLURM_TMPDIR:-/tmp}
SUCCESSOR_LOCK="$local_state/eval3-successor-${SLURM_JOB_ID}.lock"
SUCCESSOR_MARKER="$local_state/eval3-successor-${SLURM_JOB_ID}.submitted"
SUCCESSOR_TIMER_DUE="$local_state/eval3-successor-${SLURM_JOB_ID}.timer-due"

queue_has_work() {
    compgen -G "$SCHED/queue/*.inf" >/dev/null
}

submit_successor() {
    local why=$1

    # Timer and normal-exit fallback can race; mkdir is the arbitration point.
    if ! mkdir "$SUCCESSOR_LOCK" 2>/dev/null; then
        return 0
    fi
    if [[ -e "$SUCCESSOR_MARKER" ]]; then
        rmdir "$SUCCESSOR_LOCK" 2>/dev/null || true
        return 0
    fi
    if ! queue_has_work; then
        echo "No queued tasks at $why; not submitting a successor"
        rmdir "$SUCCESSOR_LOCK" 2>/dev/null || true
        return 0
    fi

    echo "Queued tasks remain at $why; submitting successor of job $SLURM_JOB_ID"
    local new_job
    if new_job=$(
        export EVAL3_ACCOUNT="$ACCOUNT" EVAL3_DISKPROJECT="$DISKPROJECT"
        export EVAL3_SCHEDULER="$SCHED" EVAL3_CODE EVAL3_WORKER="$WORKER"
        export EVAL3_SIF="$SIF" EVAL3_ACTIVATE="$ACTIVATE"
        export EVAL3_RECOVERY_GRACE="$RECOVERY_GRACE"
        export EVAL3_STOP_RESERVE="$STOP_RESERVE" EVAL3_POLL_SECONDS="$POLL_SECONDS"
        export EVAL3_SUCCESSOR_DIVISOR="$SUCCESSOR_DIVISOR"
        export EVAL3_SLURM_SCRIPT="$SCRIPT"
        unset SLURM_JOB_ID SLURM_JOBID SLURM_RESTART_COUNT
        unset SLURM_ARRAY_JOB_ID SLURM_ARRAY_TASK_ID SLURM_STEP_ID
        unset EVAL3_DEADLINE_EPOCH
        sbatch --parsable --export=ALL \
            --output="$SCHED/logs/infjob%j.out" \
            --error="$SCHED/logs/infjob%j.err" \
            "$SCRIPT"
    ); then
        printf '%s\n' "$new_job" >"$SUCCESSOR_MARKER"
        echo "Submitted successor job $new_job"
        rmdir "$SUCCESSOR_LOCK" 2>/dev/null || true
        return 0
    fi

    echo "Successor submission failed at $why" >&2
    rmdir "$SUCCESSOR_LOCK" 2>/dev/null || true
    return 1
}

successor_timer_pid=
if [[ "$DISABLE_SUCCESSOR" -eq 0 ]]; then
    (
        sleep "$successor_delay"
        : >"$SUCCESSOR_TIMER_DUE"
        submit_successor "one-third point"
    ) &
    successor_timer_pid=$!
else
    echo "Successor submission disabled for this allocation"
fi

# Recovery needs host Slurm commands (squeue/sacct), so do it before entering
# Singularity.  The Python worker is stdlib-only; cray-python supplies python3.
restart=${SLURM_RESTART_COUNT:-0}
python3 "$WORKER" --base "$SCHED" recover \
    --grace "$RECOVERY_GRACE" \
    --current-job "$SLURM_JOB_ID" \
    --current-restart "$restart"

echo "Launching eval3 inference worker under srun/Singularity..."
set +e
srun /usr/bin/singularity exec \
    --env NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME}" \
    --env NCCL_NET_GDR_LEVEL="${NCCL_NET_GDR_LEVEL}" \
    --env NCCL_DEBUG="${NCCL_DEBUG}" \
    --env EVAL3_DEADLINE_EPOCH="${EVAL3_DEADLINE_EPOCH}" \
    --env SLURM_RESTART_COUNT="$restart" \
    -B "/scratch/${DISKPROJECT}:/scratch/${DISKPROJECT}:rw" \
    -B "/scratch/${ACCOUNT}:/scratch/${ACCOUNT}:rw" \
    -B "$EVAL3_CODE:$EVAL3_CODE:ro" \
    "$SIF" /bin/bash -c '
        set -euo pipefail
        source "$1"
        exec python3 "$2" --base "$3" run \
            --reserve "$4" --poll "$5" --grace "$6"
    ' _ "$ACTIVATE" "$WORKER" "$SCHED" \
      "$STOP_RESERVE" "$POLL_SECONDS" "$RECOVERY_GRACE"
worker_rc=$?
set -e

# If the timer is still sleeping, the exit fallback can decide immediately.
# Once the timer is due, let its sbatch/marker transaction finish atomically.
if [[ -n "$successor_timer_pid" ]]; then
    if kill -0 "$successor_timer_pid" 2>/dev/null; then
        if [[ -e "$SUCCESSOR_TIMER_DUE" ]]; then
            wait "$successor_timer_pid" 2>/dev/null || true
        else
            kill "$successor_timer_pid" 2>/dev/null || true
            wait "$successor_timer_pid" 2>/dev/null || true
        fi
    else
        wait "$successor_timer_pid" 2>/dev/null || true
    fi
fi

# Deterministic setup/inference failure must not create a rapid resubmission
# chain.  Only a clean worker exit gets the fallback opportunity.
if [[ "$DISABLE_SUCCESSOR" -eq 0 && "$worker_rc" -eq 0 && ! -e "$SUCCESSOR_MARKER" ]]; then
    submit_successor "worker exit" || true
fi

exit "$worker_rc"
