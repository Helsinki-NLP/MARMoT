# Shared eval3 inference queue.
#
# Durable task definitions live under each model:
#     $(TSKDIR)/*.inf
# Each task names exactly one canonical hypothesis (INFER_HYP).  The complete
# task set is advertised by:
#     $(INF_TASKS_DONE)
# The central queue contains hard links to those task definitions.
# Queueing is idempotent: eval3_worker.py skips a task if its canonical
# hypothesis is already valid or if that task is already queued/claimed.

EVAL3_WORKER ?= $(SELFDIR)/bin/eval3_worker.py
EVAL3_WORKER_SLURM ?= $(SELFDIR)/bin/eval3_worker.slurm
EVAL3_DEVG_TIME ?= 00:30:00

.PHONY: eval3-scheduler-dirs mk-inf-tasks require-inf-tasks mk-queue queue-infer submit-inf-worker submit-inf-worker-dev-g test-eval3-worker

eval3-scheduler-dirs:
> @set -euo pipefail; \
> mkdir -p "$(EVAL3_QUEUE)" "$(EVAL3_CLAIMS)" "$(EVAL3_LOGS)"; \
> qdev="$$(stat -c %d "$(EVAL3_QUEUE)")"; \
> cdev="$$(stat -c %d "$(EVAL3_CLAIMS)")"; \
> if [ "$$qdev" != "$$cdev" ]; then \
>   echo "mk-queue.mk: ❌ queue and claims are not on the same filesystem" >&2; \
>   exit 1; \
> fi

# Build the model-local durable inference tasks.  The semaphore is a real Make
# target, so changes to the selected tasks, training config, Mammoth selection,
# or planner invalidate it.  The planner stages the complete *.inf set and
# commits it only after successful planning; Make publishes the semaphore last.
$(INF_TASKS_DONE): $(TRAINCONFIG) $(MAMMOTH_SELECTED) $(PRS_DONE) $(TASKS) $(SELFDIR)/bin/plan_eval3_inference.py | $(EVAL_DIRS)
> @set -euo pipefail; \
> echo "mk-queue.mk: 🛠️ Building model-local one-hypothesis inference tasks"; \
> rm -f "$@" "$(PLAN_LOG)"; \
> $(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODELDIR_CLEAN)" "$(PLAN_LOG)"; \
> shopt -s nullglob; \
> tasks=("$(TSKDIR)"/*.inf); \
> if [ "$${#tasks[@]}" -eq 0 ]; then \
>   echo "mk-queue.mk: ❌ Planner completed but produced no .inf tasks in $(TSKDIR)" >&2; \
>   exit 1; \
> fi; \
> tmp="$@.tmp.$$"; \
> printf 'tasks=%d\n' "$${#tasks[@]}" >"$$tmp"; \
> mv "$$tmp" "$@"; \
> echo "mk-queue.mk: ✅ Published $@ ($${#tasks[@]} tasks)"

mk-inf-tasks: $(INF_TASKS_DONE)
> @true

# Verify the semaphore and task set.  The worker itself revalidates every task
# and its hypothesis when enqueueing/claiming, so this target only checks the
# model-level build invariant.
require-inf-tasks: mk-inf-tasks
> @set -euo pipefail; \
> test -f "$(INF_TASKS_DONE)" || { \
>   echo "mk-queue.mk: ❌ Missing inference-task semaphore: $(INF_TASKS_DONE)" >&2; exit 1; }; \
> shopt -s nullglob; \
> tasks=("$(TSKDIR)"/*.inf); \
> [ "$${#tasks[@]}" -gt 0 ] || { \
>   echo "mk-queue.mk: ❌ Semaphore exists but no .inf tasks were found in $(TSKDIR)" >&2; exit 1; }; \
> echo "mk-queue.mk: ✅ Found $${#tasks[@]} model-local inference tasks"

mk-queue: eval3-scheduler-dirs require-inf-tasks
> @set -euo pipefail; \
> shopt -s nullglob; \
> tasks=("$(TSKDIR)"/*.inf); \
> echo "mk-queue.mk: 🛠️ Adding $${#tasks[@]} tasks to $(EVAL3_QUEUE)"; \
> module load cray-python; \
> for task in "$${tasks[@]}"; do \
>   python3 "$(EVAL3_WORKER)" --base "$(EVAL3_SCHEDULER)" enqueue "$$task"; \
> done; \
> echo "mk-queue.mk: ✅ Model tasks reconciled with the shared inference queue"

queue-infer: mk-queue
> @true


# Submit a model-independent production worker.  Queue population is a separate
# model-specific operation (mk-queue), so this target intentionally has no model
# prerequisite.
submit-inf-worker: eval3-scheduler-dirs
> @set -euo pipefail; \
> test -r "$(EVAL3_WORKER_SLURM)" || { echo "mk-queue.mk: missing $(EVAL3_WORKER_SLURM)" >&2; exit 1; }; \
> job="$$(EVAL3_SCHEDULER="$(EVAL3_SCHEDULER)" EVAL3_CODE="$(SELFDIR)/bin" EVAL3_WORKER="$(EVAL3_WORKER)" EVAL3_SLURM_SCRIPT="$(EVAL3_WORKER_SLURM)" EVAL3_SIF="$(SIF)" EVAL3_ACTIVATE="$(INF_ACTIVATE)" EVAL3_ACCOUNT="$(JOBPROJECT)" EVAL3_DISKPROJECT="$(DISKPROJECT)" sbatch --parsable --export=ALL --output="$(EVAL3_LOGS)/infjob%j.out" --error="$(EVAL3_LOGS)/infjob%j.err" "$(EVAL3_WORKER_SLURM)")"; \
> echo "mk-queue.mk: submitted eval3 inference worker $$job"

# Safe integration smoke test: same worker/container/code path, but dev-g,
# short walltime, and no self-submitted successor.  Point EVAL3_SCHEDULER at an
# isolated smoke scheduler when using this target.
submit-inf-worker-dev-g: eval3-scheduler-dirs
> @set -euo pipefail; \
> test -r "$(EVAL3_WORKER_SLURM)" || { echo "mk-queue.mk: missing $(EVAL3_WORKER_SLURM)" >&2; exit 1; }; \
> if [ "$(EVAL3_SCHEDULER)" = "/scratch/$(JOBPROJECT)/members/tiedeman/MARMoT/models/eval3scheduler" ]; then echo "mk-queue.mk: refusing dev-g smoke test on production scheduler; set EVAL3_SCHEDULER=.../eval3scheduler-smoke-$$USER" >&2; exit 2; fi; \
> job="$$(EVAL3_DISABLE_SUCCESSOR=1 EVAL3_POLL_SECONDS=0 EVAL3_SCHEDULER="$(EVAL3_SCHEDULER)" EVAL3_CODE="$(SELFDIR)/bin" EVAL3_WORKER="$(EVAL3_WORKER)" EVAL3_SLURM_SCRIPT="$(EVAL3_WORKER_SLURM)" EVAL3_SIF="$(SIF)" EVAL3_ACTIVATE="$(INF_ACTIVATE)" EVAL3_ACCOUNT="$(JOBPROJECT)" EVAL3_DISKPROJECT="$(DISKPROJECT)" sbatch --parsable --partition=dev-g --time="$(EVAL3_DEVG_TIME)" --export=ALL --output="$(EVAL3_LOGS)/infjob%j.out" --error="$(EVAL3_LOGS)/infjob%j.err" "$(EVAL3_WORKER_SLURM)")"; \
> echo "mk-queue.mk: submitted dev-g eval3 smoke worker $$job"

test-eval3-worker:
> @module load cray-python; python3 "$(SELFDIR)/bin/test_eval3_worker.py"
