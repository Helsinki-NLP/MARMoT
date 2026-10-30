# RFC: Eval3 Shared-Filesystem Inference Worker and Scheduler

**Status:** Descriptive RFC for the current eval3 implementation  
**Implementation:** `bin/eval3_worker.py`, `bin/eval3_worker.slurm`, `include/mk-queue.mk`, `bin/plan_eval3_inference.py`  
**Scope:** model-independent GPU inference scheduling on LUMI using a shared filesystem and Slurm

## 1. Purpose

Eval3 inference separates **what must be inferred** from **which GPU worker performs it**. Each model owns a durable set of one-output inference task definitions. A small central scheduler advertises unfinished tasks through hard links on the shared filesystem. Model-independent Slurm workers claim those links, run Mammoth inference, validate the result, and publish a canonical hypothesis without overwriting an existing valid result.

The design intentionally avoids a database, daemon, registry, job array, lease server, heartbeat service, and model-specific worker script. The shared filesystem supplies the atomic primitives needed for arbitration and publication; Slurm supplies worker identity and authoritative process-lifetime information.

The durable truths are:

1. the model-local `.inf` task definition; and
2. a valid canonical `.hyp` file.

The central `queue/` and `claims/` directories are reconstructible scheduler state.

## 2. Design goals

The implementation is designed to provide the following properties.

- **One inference task produces one canonical hypothesis.**
- **Workers are model-independent.** A worker learns the model, Mammoth tree, configuration, source, reference, and output from the claimed `.inf` file.
- **No central scheduler process is required.** Workers coordinate through filesystem operations.
- **No two workers normally execute the same advertised task.** A fixed hard-link destination is the claim arbitration point.
- **A canonical hypothesis is never overwritten.** Publication is a no-overwrite hard-link operation.
- **Incomplete or malformed output is never published.** Output is written under an attempt-specific temporary name and validated first.
- **Worker death does not permanently lose a task.** Stale claims can be recovered using filesystem state plus Slurm state.
- **Deterministic inference failure does not cause a tight retry loop in one worker.** A worker defers any task that it has itself failed.
- **Worker capacity can replenish itself.** A running allocation may submit one successor while it is still running.
- **The scheduler has little persistent state.** There is deliberately no owner database, renewal table, heartbeat file, or `failed/` directory.

## 3. Components and state

### 3.1 Model-local durable state

For each model, the planner creates permanent task definitions under:

```text
<model>/evaluation/tasks/*.inf
```

The canonical hypothesis is under:

```text
<model>/evaluation/hypotheses/*.hyp
```

Inference configuration and per-inference logs remain model-local, for example:

```text
<model>/evaluation/configs/<task>.yaml
<model>/evaluation/logs/job<jobid>.<artifact>.err
```

Task and hypothesis artifact basenames follow the eval3 artifact RFC. A task definition has the same evaluation-case basename as its hypothesis, with `.inf` instead of `.hyp`, for example:

```text
zero_ces-slk.flores200.ces.slk.inf
zero_ces-slk.flores200.ces.slk.hyp
```

### 3.2 Shared scheduler state

The default scheduler root is:

```text
/scratch/project_462001509/members/tiedeman/MARMoT/models/eval3scheduler/
```

It contains only:

```text
queue/      waiting tasks
claims/     tasks owned by workers, including transient anonymous claims
logs/       Slurm worker stdout/stderr
```

`queue/` and `claims/` must be on the same filesystem. In the current implementation the permanent `.inf` task and the final hypothesis must also be on that filesystem because enqueueing, claiming, requeueing, and publication use hard links or same-filesystem rename operations.

The scheduler does not copy task contents. Queue and claim entries are hard links to the permanent model-local `.inf` inode.

## 4. Task specification

A `.inf` file is a trusted generated Bash assignment file. The worker sources it in a restricted Bash process and requires these fields:

```bash
TASK_ID=...
INFER_SRC=...
INFER_REF=...
INFER_HYP=...
INFERENCE_YAML=...
MODEL=...
MAMMOTH=...
```

The planner also currently writes:

```bash
LOGDIR=...
INFER_LOG=...
```

`TASK_ID` is the Mammoth training-task identity passed to `translate.py --task_id`. It is not reconstructed from the artifact filename. `INFERENCE_YAML` is the RFC-conformant one-task inference configuration. `INFER_HYP` names exactly one canonical result.

The planner stages `.inf` files in a temporary directory. Each task file is flushed and `fsync`ed. Only after the complete planning pass succeeds does `InferenceTaskWriter.commit()` replace the model's `*.inf` task set. The Make target publishes `inference-tasks.done` only after the task set exists. This gives a useful build semaphore, although the replacement of the entire directory contents is not a single filesystem transaction: individual file replacement is atomic, while a crash during `commit()` could interrupt the set-level replacement.

Several localized training variants are allowed to converge on the same evaluation artifact. They are deduplicated only if their complete inference producer specifications are identical. A same-named artifact with differing source, reference, YAML, model, Mammoth tree, or output specification is a planning error.

Denoising tasks, identified structurally by `src_tgt` with identical source and target languages, are excluded from evaluation before task expansion.

## 5. Queue representation

An advertised task has a scheduler filename of the form:

```text
P000100--<24-hex-stable-key>--a000--<task-basename>.inf
```

For example:

```text
P000100--7c4f...e12a--a000--zero_ces-slk.flores200.ces.slk.inf
```

The fields are:

- `P000100`: zero-padded numeric priority; the default priority is 100;
- stable key: the first 24 hexadecimal digits of SHA-256 over the resolved absolute path of the permanent `.inf` file;
- `a000`: scheduler attempt number;
- final component: the original `.inf` basename.

Workers sort queue filenames lexically. This makes priority the first scheduling key. The stable key gives one scheduler identity to a permanent task path without requiring a registry.

### 5.1 Enqueueing

`mk-queue` iterates over the model's durable `.inf` files and calls:

```text
eval3_worker.py --base <scheduler> enqueue <task.inf>
```

Before advertising a task, `enqueue()`:

1. resolves the permanent task path;
2. verifies that it is an `.inf` file;
3. verifies same-filesystem compatibility;
4. sources and validates the required task fields;
5. checks whether the canonical hypothesis is already valid;
6. checks whether the stable task key already appears in `queue/` or `claims/`; and
7. creates the initial `a000` queue hard link.

Thus queue construction is idempotent with respect to completed, queued, and claimed work.

Queue construction or reconstruction is intended to run while workers are stopped. It is not a transactional reconciliation protocol for concurrent queue rebuilding.

## 6. Claiming and worker assignment

A worker has two pieces of Slurm identity:

```text
J = SLURM_JOB_ID
R = SLURM_RESTART_COUNT, default 0
```

A task is claimed with three filesystem operations:

```text
link(queue/T, claims/T)
unlink(queue/T)
rename(claims/T, claims/T.job-J.r-R)
```

The first operation is the arbitration point. Every competing worker tries to create the same fixed anonymous destination `claims/T`. Hard-link creation is atomic: one worker succeeds and the others receive `EEXIST` or observe that the queue entry has disappeared.

The queue advertisement is removed before the anonymous claim is renamed to an owned claim. The normal named state is therefore:

```text
claims/P......--aNNN--task.inf.job-<jobid>.r<restart>
```

The anonymous `claims/T` state is intentionally short-lived but important. It represents a claim whose worker won arbitration but has not yet recorded its Slurm identity.

There is no static assignment of models or language pairs to workers. Assignment is exactly the successful claim operation. Once claimed, the hard-linked `.inf` inode tells the worker everything needed to run that inference.

## 7. Claim lifetime, recovery, and renewal

### 7.1 There is no lease-renewal protocol

The current implementation deliberately has **no heartbeat and no periodic claim renewal**. A named claim does not expire merely because its timestamp is old. Its ownership is tied to the Slurm job recorded in its filename.

This is an important distinction from lease-based queues. The filesystem timestamp is a conservative grace gate, not an ownership lease.

The default recovery grace is 300 seconds.

### 7.2 Anonymous claim recovery

An anonymous claim has no owner identity. If its inode `ctime` is at least the recovery grace, recovery treats the interrupted three-operation claim transaction as stale and requeues it at the next attempt number.

If the old queue advertisement still exists and is the same inode, recovery first removes that advertisement while retaining the anonymous claim as the exclusive name, then requeues it.

### 7.3 Named claim recovery

For a named claim, age alone is insufficient. After the grace period, recovery asks Slurm about the recorded owner:

1. `squeue` is checked first;
2. if the job is not active there, `sacct -X` is queried using the exact numeric `JobIDRaw`;
3. the claim is recoverable only when the exact owner is positively classified as terminal.

Recognized terminal states include `COMPLETED`, `FAILED`, `TIMEOUT`, `OUT_OF_MEMORY`, `NODE_FAIL`, `CANCELLED`, `PREEMPTED`, and related terminal Slurm states.

If Slurm state is unavailable or ambiguous, recovery holds the claim rather than guessing that the worker is dead.

A special case handles Slurm restart of the same job. If a current job with restart count `R2` sees a claim belonging to the same job with `R1 < R2`, the old claim is considered superseded and may be recovered without waiting for the ordinary grace condition.

### 7.4 Recovery checks for completed work

Before requeueing a stale named claim, recovery reads its task and checks the canonical hypothesis. If the final hypothesis is already valid, recovery removes the claim as completed. Otherwise it requeues the task at the next attempt number.

Recovery is run by the Slurm wrapper before entering the container, and the worker also invokes recovery at startup and whenever the queue appears empty.

## 8. Attempts, Slurm restarts, trials, and failure

The scheduler maintains two different counters and they must not be confused.

### 8.1 Scheduler attempt number

The `aNNN` component belongs to the task:

```text
a000 -> a001 -> a002 -> ...
```

It is incremented whenever a claim is returned to the queue after inference failure or stale-claim recovery. It therefore counts scheduler-level retries/recoveries of that task identity.

### 8.2 Slurm restart number

The `.rR` component belongs to the worker allocation:

```text
.job-123456.r0
.job-123456.r1
```

It is `SLURM_RESTART_COUNT`. It distinguishes successive incarnations of the same Slurm job and allows a later incarnation to recover a claim left by an earlier one.

### 8.3 Current failure policy

If `translate.py` exits nonzero or produces an invalid temporary hypothesis:

1. the temporary hypothesis is removed;
2. the model-local stderr log is retained;
3. the claim is requeued with `aNNN+1`; and
4. the current worker records the task's stable key in a local `failed_keys` set.

That worker will not claim the same task again during the same allocation. Another worker may claim it immediately, and a later allocation may retry it.

This prevents the earlier failure mode in which one deterministic bad task was claimed, failed, requeued, and reclaimed dozens of times by the same worker.

### 8.4 There is currently no global trial limit

The attempt counter is recorded, but the current implementation does **not** declare a task permanently failed after N attempts. There is no `failed/` directory and no terminal task-failure record. Therefore a persistently bad task can continue to be retried by successive workers and its `aNNN` number can continue to increase.

This is a deliberate description of the current code, not a claim that unlimited retries are ideal. Section 15 discusses whether a bounded trial policy should be added.

## 9. Pre-execution checks and canonical completion

The system tests completion at several boundaries rather than trusting the presence of a filename.

`valid_hyp()` requires all of the following:

- source exists and is a regular file;
- reference exists and is a regular file;
- hypothesis exists and is a regular file;
- hypothesis size is nonzero;
- no hypothesis line contains a NUL byte;
- every hypothesis line is strict UTF-8;
- the hypothesis contains at least one line; and
- hypothesis, source, and reference have identical line counts.

This predicate is used:

- before enqueueing, to avoid advertising completed work;
- after claiming, to discard a task that became complete meanwhile;
- after `translate.py`, before publication;
- after a publication collision, to accept another valid writer's result; and
- during stale-claim recovery, to distinguish completed work from work that must be retried.

An existing **invalid** canonical hypothesis is not silently repaired or overwritten. The worker refuses to overwrite it and raises an error. This makes corruption visible and preserves the no-overwrite invariant.

## 10. Running inference

For a named claim, the worker constructs an attempt-specific output beside the canonical hypothesis:

```text
<canonical>.hyp.tmp.job-<J>.r<R>
```

It removes any stale attempt file with exactly that worker identity and invokes:

```text
python -u <MAMMOTH>/translate.py \
    --config <INFERENCE_YAML> \
    --model <MODEL> \
    --task_id <TASK_ID> \
    --src <INFER_SRC> \
    --output <attempt-path>
```

The reference is not passed to Mammoth translation; it is part of the task because validation requires its cardinality and later scoring uses it.

Inference stderr is appended to the model-local log. `INFER_LOG`, when present, takes precedence and may contain a literal `${SLURM_JOB_ID}` placeholder. Each invocation adds a header containing job id, restart count, and timestamp.

## 11. Atomic validated publication

`translate.py` never writes directly to the canonical `.hyp` path.

After successful process exit, the worker validates the temporary output with `valid_hyp()` and `fsync`s the temporary file. It then publishes with:

```text
link(attempt, canonical)
```

This hard-link creation is atomic and does not replace an existing path.

There are three outcomes:

1. **Link succeeds.** This attempt becomes the canonical hypothesis.
2. **Canonical path already exists and is valid.** Another valid result has won; the current attempt is accepted as redundant and removed.
3. **Canonical path already exists but is invalid.** The worker refuses to overwrite it and reports an error.

After successful or accepted publication, the temporary name is removed and the claim is deleted.

This is a first-valid-writer-wins protocol with no destructive replacement of canonical output.

## 12. Worker loop and walltime discipline

The Slurm wrapper determines the actual allocation `StartTime` and `EndTime` with `scontrol` and exports the end time as `EVAL3_DEADLINE_EPOCH`.

The Python worker normally uses:

```text
reserve = 900 seconds
poll    = 15 seconds
```

Before claiming a new task it checks the remaining allocation time. If fewer than `reserve` seconds remain, it stops claiming and exits cleanly. An inference already running is not interrupted by this reserve rule.

If no task can be claimed, the worker performs recovery, tries to claim again, and then sleeps for the polling interval. A smoke worker may set polling to zero so that it exits as soon as the isolated queue is empty.

The reserve is a **claim admission rule**, not a prediction that an inference will finish within the remaining walltime.

## 13. Slurm execution environment

The production wrapper currently requests one LUMI GPU worker:

```text
partition       small-g
walltime        02:00:00
nodes           1
ntasks          1
gpus-per-task   1
cpus-per-task   7
memory          60G
account         project_462001509
```

Host-side recovery uses `cray-python`, because it needs access to Slurm commands. Inference runs through `srun` in the configured LUMI multitorch Singularity image, activates the shared Mammoth virtual environment, binds the two project scratch trees, and exports the established NCCL settings.

The `dev-g` smoke target uses the same worker/container/code path but overrides the partition and walltime, disables successor submission, and sets polling to zero. It is explicitly refused against the default production scheduler so that a smoke test must use an isolated scheduler root.

## 14. Successor submission and worker population

A production worker can submit at most one successor. This is not a Slurm dependency chain: the successor is an ordinary independent `sbatch`, so parent and successor may overlap.

### 14.1 Submission time

The wrapper derives the actual allocation duration from Slurm and computes:

```text
successor_time = start + allocation_duration / EVAL3_SUCCESSOR_DIVISOR
```

The default divisor is 3. For a two-hour allocation, the nominal successor point is therefore about 40 minutes after the allocation starts.

This produces a chain such as:

```text
A -> B -> C -> D
```

rather than branching. With two-hour jobs and forty-minute spacing, approximately three generations may overlap in steady state while the queue remains nonempty.

### 14.2 When a successor is submitted

At the timer point, the wrapper submits a successor only if `queue/*.inf` currently contains work.

A local `mkdir` lock arbitrates between the timer and the normal-exit fallback. A local submitted marker records that this allocation has already created its successor. These files live under `SLURM_TMPDIR` (or `/tmp`) and are local coordination state, not persistent scheduler state.

Before `sbatch`, inherited Slurm job identity variables and `EVAL3_DEADLINE_EPOCH` are unset. The persistent worker script path and eval3 configuration are exported to the new job.

### 14.3 Exit fallback

If the worker exits cleanly before the timer has produced a successor, the wrapper makes one final successor decision. It submits only if queued work remains.

If the worker process itself exits with an error, the fallback is suppressed. This prevents a deterministic setup or inference failure from generating a rapid chain of replacement allocations.

If the timer has already awakened, shutdown waits for its submit/marker transaction to finish rather than killing it in the middle of `sbatch` bookkeeping.

## 15. State machine summary

A normal task follows:

```text
permanent model task
        |
        | enqueue if final HYP is not valid
        v
queue/...--a000--task.inf
        |
        | atomic hard-link arbitration
        v
claims/...--a000--task.inf             anonymous transient claim
        |
        | queue unlink + owner rename
        v
claims/...--a000--task.inf.job-J.rR    named claim
        |
        | translate to temporary output
        v
artifact.hyp.tmp.job-J.rR
        |
        | validate + fsync + hard-link publish
        v
artifact.hyp                           canonical durable completion
        |
        `-- claim removed
```

A failed attempt follows:

```text
claim aNNN
   |
   | translate/process/validation failure
   v
remove temporary output
retain stderr log
   |
   v
queue a(NNN+1)
```

A dead worker follows:

```text
named claim
   |
   | grace elapsed + Slurm positively terminal
   +--------------------------+
   |                          |
valid canonical HYP      no valid HYP
   |                          |
remove claim             requeue a+1
```

An interrupted anonymous claim follows:

```text
anonymous claim
   |
   | inode ctime older than grace
   v
requeue a+1
```

## 16. Important invariants

The implementation relies on the following invariants.

1. **Permanent `.inf` files are immutable while advertised.** Queue and claim names are hard links to their inodes.
2. **Task files are trusted.** They are sourced as Bash; this is not a sandbox for untrusted input.
3. **Queue construction is separate from worker execution.** Reconstructing the queue concurrently with workers is outside the intended protocol.
4. **One `.inf` names one canonical `.hyp`.** The output path is part of the durable task definition.
5. **Canonical hypotheses are immutable completion records.** Workers never overwrite them.
6. **Presence is not completion.** A hypothesis must satisfy `valid_hyp()`.
7. **Missing Slurm information is not proof of death.** Recovery prefers holding a claim to stealing work from a possibly live worker.
8. **Age is not a lease for named claims.** Slurm state is authoritative.
9. **Attempt number and Slurm restart count describe different phenomena.** Neither should be substituted for the other.
10. **A worker that fails a task does not immediately retry it.** The exclusion is local to that worker allocation, not global.

## 17. Failure semantics and crash windows

The design reduces distributed coordination to a small number of filesystem transitions, but it cannot make every multi-operation transition atomic as a whole.

### 17.1 Claim transaction

`link -> unlink -> rename` is three operations. The anonymous claim state exists specifically so that crashes between these operations are recoverable. If the worker cannot prove that queue removal completed, it leaves the anonymous claim rather than guessing.

### 17.2 Requeue transaction

Requeue increments the attempt and moves the claim back into `queue/`. The current implementation checks for an existing target and then uses `os.rename()` when absent. This is adequate under the intended single-representation invariant, but the check-plus-rename sequence is not itself a no-overwrite primitive if an unexpected concurrent actor creates the target between those operations.

### 17.3 Publication

Publication has the strongest atomicity property in the design because `link(attempt, final)` is itself the no-overwrite arbitration operation. The canonical output is never exposed partially by the worker.

### 17.4 Successor bookkeeping

There is an unavoidable small process/node-failure window after a successful `sbatch` and before the local submitted marker is written. The design prevents ordinary timer/exit races but cannot make Slurm submission and local marker creation one distributed transaction.

## 18. Observability

There are two intentionally different log scopes.

Scheduler/worker logs are central:

```text
<scheduler>/logs/infjob<jobid>.out
<scheduler>/logs/infjob<jobid>.err
```

Mammoth inference stderr is model-local:

```text
<model>/evaluation/logs/job<jobid>.<artifact>.err
```

Useful worker events include:

```text
ENQUEUED
NOT ENQUEUED
CLAIMED
RUN
PUBLISHED
ALREADY COMPLETE
FAILED
REQUEUED
DEFER
RECOVERY HOLD
RECOVERED
STOP
```

The queue filename itself also exposes priority and retry count without a database query.

## 19. Testing strategy

The implementation has local regression tests for claim arbitration, recovery, publication guards, hypothesis validation, and prevention of same-worker retry storms. Planner tests cover RFC artifact naming, safe localized deduplication, exclusion of denoising tasks, and parity with the RFC YAML conversion.

The LUMI `dev-g` smoke test is deliberately separate. It should use an isolated scheduler and one real `.inf` task. It exercises the remaining integration boundary: Slurm, the shared filesystem, hard links, the Singularity image, scratch bindings, the Mammoth environment, ROCm/GPU execution, and the real `translate.py` invocation. Success is checked by equal source/reference/hypothesis line counts, disappearance of the temporary output and claim, existence of the canonical hypothesis, and the expected central and model-local logs.

## 20. Reflective discussion

The main strength of this scheduler is that its coordination model is small enough to reason about directly. It does not attempt to reproduce a general batch scheduler inside Slurm. Slurm owns compute allocations and job lifetime; the shared filesystem owns task arbitration and durable publication; model directories own task definitions and results. The boundary between these responsibilities is relatively sharp.

Hard links are doing three distinct jobs. First, they let the queue refer to a task without copying or translating its contents. Second, creation of a fixed claim link provides an atomic compare-and-acquire operation. Third, creation of the canonical hypothesis link provides atomic first-writer publication. This economy is attractive on a single reliable shared filesystem, but it is also the principal portability constraint: the design assumes hard-link semantics and common filesystem devices across the relevant paths.

The absence of lease renewal is also a deliberate simplification. A conventional distributed queue often needs heartbeat timestamps because it has no external authority that can say whether a worker still exists. Here Slurm already supplies that authority. A named claim can therefore remain valid for hours without being periodically touched. The five-minute age gate merely avoids investigating fresh claims, while actual reclamation requires positive evidence of owner termination. This reduces write traffic and eliminates a class of heartbeat races. Anonymous claims are the exception because they have not yet acquired an owner identity; conservative ctime recovery is the price of keeping the claim transaction minimal.

Attempts are currently diagnostic and operational rather than punitive. Incrementing `aNNN` records that the task has been through another failed or recovered execution, while the worker-local failed-key set prevents a single allocation from spinning on deterministic failure. The design does not yet answer the policy question "how many trials are enough?" A global limit such as three or five attempts could protect GPU capacity from permanently broken tasks, but implementing it cleanly requires deciding what durable terminal failure means. Adding only a numeric cutoff without a durable failure record would make tasks silently disappear. A future bounded-retry extension should therefore probably introduce an explicit, inspectable terminal-failure artifact or report, even if the scheduler continues to avoid a general database.

The successor chain is intentionally approximate capacity control rather than a precise autoscaler. It is simple, decentralized, and avoids job dependencies. The one-third rule creates overlap so that queueing delay for a successor need not leave the pipeline empty. However, the current successor test sees only `queue/`, not work held in `claims/`. If the queue is momentarily empty because all remaining tasks are claimed, a worker may decide not to create a successor; a later owner failure could then leave recoverable work with no worker alive to recover it. Similarly, workers poll an empty queue until their reserve window, which can spend GPU allocation on waiting. These are acceptable simplifications for the current workload, but they are the clearest places to revisit if liveness or utilization becomes more important.

There is also a useful asymmetry between conservative recovery and aggressive throughput. Recovery refuses to steal a named claim unless Slurm positively proves the owner terminal. That can delay work when accounting information is unavailable, but it strongly reduces duplicate inference. Conversely, once a task has explicitly failed, it is immediately returned to the shared queue for another worker. If repeated deterministic failures become common, a bounded global trial policy would make this asymmetry more balanced.

The canonical hypothesis is intentionally treated almost like a commit record. A valid `.hyp` makes queue state irrelevant: enqueue skips it, execution discards a redundant claim, and recovery closes a stale claim. This makes scheduler state disposable and reconstruction practical. The strict refusal to overwrite an invalid canonical file follows the same philosophy: corruption should require explicit operator action rather than being silently hidden by a later worker.

The current task format is likewise intentionally plain. A generated Bash assignment file is easy to inspect, hard-link, source, and reproduce, and it keeps each inference self-describing. Its weakness is trust: sourcing is appropriate only because these files are generated inside the controlled eval3 pipeline. If task definitions ever become externally supplied, the format should move to a non-executable serialization format rather than attempting to harden Bash sourcing incrementally.

Finally, the implementation benefits from distinguishing **mechanism** from **policy**. The mechanisms are now fairly stable: immutable task definitions, hard-link queueing, exclusive claims, Slurm-backed recovery, attempt-specific output, validation, and no-overwrite publication. Policies remain adjustable: priority, recovery grace, reserve time, polling interval, successor spacing, and eventually maximum trials. Keeping these policy choices outside the core correctness protocol should make the eval3 worker easier to evolve without destabilizing its central invariants.

## 21. Current limitations and likely next refinements

The following are known properties of the current implementation rather than hidden assumptions:

- there is no global maximum-attempt/final-failure policy;
- there is no heartbeat or lease renewal, by design;
- successor decisions inspect queued work, not claimed work;
- empty-queue polling can consume GPU allocation;
- queue reconstruction is not designed to race with active workers;
- the task format is trusted executable Bash assignments;
- task-set commit is atomic per file, not as one directory-wide transaction;
- requeue uses a check followed by `rename`, rather than a single no-overwrite transition;
- Slurm `scontrol` time parsing, `sacct` identity handling, compute-node `sbatch`, container bindings, and hard-link behavior remain platform assumptions that the LUMI smoke test is intended to exercise;
- a successful `sbatch` followed by immediate node/process death before the local successor marker is an unavoidable small bookkeeping window.

None of these invalidate the central protocol. They identify where additional machinery would buy a concrete property, and therefore provide a basis for deciding whether the added complexity is justified by observed failures rather than by hypothetical ones.

