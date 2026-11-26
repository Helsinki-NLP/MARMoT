# Eval3 development notes and eval4 handover

## Value already delivered

Eval3 represents a major engineering effort. Its strengths are automated evaluation across many architectures, backend selection, task expansion and shared-vocabulary handling, resumable inference and scoring, explicit model registration and snapshot audits, canonical artifact names, a common training-to-inference YAML conversion, migration tools, normalized TSV results, coverage checks and exploratory visualizations. The RFCs provide a useful common language for future implementations. Preserve the existing results and the ability to reproduce them while simplifying scheduling.

Complexity arose in part because environment assumptions, artifact contracts and scheduling ideas were not initially simple, stable and jointly committed specifications. Requirements changed as new models, tokenizer sharing, datasets and layouts appeared. Some older interfaces survived while newer ones were added. This is a reason to consolidate contracts and tests, not to discard the working infrastructure.

## Current limitations and proposed priorities

| Area | Observed limitation | Proposed improvement (not implemented here) |
|---|---|---|
| Scheduling | Normal eval3 submits separate jobs per model; inference within a model is effectively sequential and does not scale simply by adding independent workers. | Model-independent workers claiming durable individual tasks; bounded concurrency, leases, retries, resource-aware batching. |
| Queue overhead | Separate 10-minute `small` continuations between phases; queue congestion can delay progress even when work is small. | Persistent/reusable workers or reconciliation without a separate queued continuation for each phase. |
| Priorities | No supported task-level priority policy in routine workflow. | Explicit priority, fairness, starvation prevention and auditable ordering. |
| Selection | Hard-wired proxy whitelist; policy changes can be hidden by cached plans. | Shared versioned `eval.yaml` with schema, validation, deterministic expansion and policy hash; agree before implementation. |
| YAML proliferation | One YAML per task plus combined YAML migration support. | Prefer a single canonical inference config and task selector when backend compatibility is proven. |
| Dataset extension | Download and integration process not exercised recently; benchmark registry spread across code. | Versioned dataset registry, alignment checks, immutable split/revision metadata, integration tests. |
| Metrics | BLEU/chrF active; TER and COMET not integrated. Size-based score validity. | Metric-specific versioned completion/provenance, explicit rescoring and profile support. |
| Analysis | Views and comparison commands exist, but cohort selection, scientific contrasts and validation are manual. | Reproducible analysis recipes and coverage-matched comparisons; keep scientific interpretation separate from scheduling. |
| Archives | Status now consults archives for missing plans and planned artifacts; inference and scoring still require loose files. | Archive manifest/index, freshness validation, scoring/restore policy, distinguish absent from archived. |
| Snapshot identity | Timestamps and line counts are heuristics; a valid-looking file can belong to another checkpoint. | Immutable snapshot identifiers, dataset/config hashes and per-output provenance. |
| Portability | Paths, Slurm accounts, container bindings and backend roots are scattered. | One validated site configuration and explicit environment preflight. |
| Migration | Directory and filename migrations are separate; legacy references remain. | Tested idempotent migration with explicit compatibility matrix and rollback. |

## Concrete issues found in this snapshot

These are static-review findings, not changes to the implementation. Prioritize reproducing them on a disposable fixture before fixing.

- `mk-calls.mk`: `reset-plan` has a semicolon after `INF_TASKS_DONE` in its rm list; the following script paths appear as a separate shell command. `reset-replan` touches `RESET_PLAN_DONE`, which is not defined in the inspected Makefiles. Bulk reset uses the same recipe. Fix and test preservation of accepted tasks, hypotheses and scores.
- `mk-score.mk`: `mk-score-force` has a questionable command boundary in its recursive Make recipe. `mk-comet` is a placeholder. `mk-contr.mk` can select COMET even though it is not implemented, and has a branch to missing `mk-viz`. Define an explicit terminal state for the active metric set.
- `mk-model.mk`: `EX_MANUAL_MODEL_ALIASES` is defined but `MODEL_ALIASES` uses `MANUAL_MODEL_ALIASES`. `CONTINUE_MODELS` defaults to all aliases despite a comment suggesting an explicit list. Clarify registration and bulk scope; detect duplicate aliases and unresolved roots.
- `mk-paths.mk` uses `evaluation/tsv`, whereas `mk-saved.mk` writes `evaluation/reports/sacre.tsv`. The migration moves old reports into `tsv`. Align report paths with the RFC and readers; avoid losing old summaries.
- `status.py` counts names in the current plan, not hypothesis line validity or score content. It now reads archived plans when the live plan is absent and supplements missing live hypothesis and SacreBLEU names from `.tar.gz`, `.tgz` or `.tar` archives without double-counting or extracting files. Archive freshness is not verified; unreadable archives produce warnings. An archive manifest or index could reduce repeated compressed-archive scanning. `inspect_training_status.py` separately scans `hypotheses.tar*`, not arbitrary `.tgz` names. Keep readiness, progress and archival state separate.
- Planner language resolution now handles shared vocab IDs by falling back to task names, but relies on naming conventions and the language inventory. The selected-task validation catches unresolved MT/zero tasks, not missing dataset files. Test G32 and `mul`, both shared sides, locale aliases and genuine denoising.
- Some declared names have no recipe (`view-help`, `mk-pairs-tasks`, `refresh-calls`, `tasks-clear`); legacy plot commands reference `compare.py`, absent from this archive, and legacy metric targets read `inf_scores`. Some non-static targets require a model even if conceptually global. The updated help distinguishes these rather than changing target dispatch.
- `infer-score-all` reports individual failures but does not necessarily return nonzero for them. Improve bulk exit semantics and dry-run/selection controls. Do not assume registration means a model needs submission.
- The planner's fallback to train-raw.yaml is not shared by Make prerequisites and other consumers. Establish a single validated configuration resolver.
- `sacre-tsv-all` may delete an existing TSV if summarization fails or produces no rows; preserve last-known-good reports and report failure explicitly.

## Proposed shared eval.yaml discussion

The maintainer reports Slack discussion of shared evaluation configuration; the discussion itself and an agreed schema are not included in this archive. Do not present a speculative YAML example as a standard. Agree the semantics first: benchmark IDs and revisions, task/direction selectors, proxy vs full policy, locale mapping, metrics/profiles, expected coverage, exclusions, priorities, snapshot selection and provenance. Decide which settings are site-specific versus scientific policy. Validate the config and produce a deterministic expanded plan before submission. Version the policy with the results. Keep the existing proxy reproducible as a named policy.

## Eval4 transition and compatibility

The supplied eval3 already contains a fine-grained experimental inference queue (`mk-queue`, `eval3_worker.py`, `eval3_worker.slurm`), durable `.inf` files, and a separate scoring planner. These are useful foundations, not evidence that a complete eval4 service is ready. The ordinary eval3 path remains per-model. The queue/claims device check is already present; the future shared scheduler must define which directories and atomic operations require a common filesystem. Test device IDs, permissions, concurrent claims, stale leases, restart, failure recovery and container visibility. Avoid concurrent producers for one artifact.

Artifact compatibility is the goal: preserve original task IDs, canonical benchmark and language IDs, hypothesis and score names, YAML semantics and result tables as specified in the existing RFCs. Do not promise compatibility of old flags, generated Slurm scripts, queue records or partially written artifacts. Define an explicit acceptance test: eval4 discovers existing complete outputs without recomputation, detects incomplete/stale ones, and produces equivalent artifacts on a representative PyTorch and shared-tokenizer model. Include legacy x-transformers if supported. Agree archive handling before bulk transition.

Suggested sequence: freeze eval3 policy; finish or stop all jobs; inventory and verify outputs; retain reports and backups; configure the shared same-device directory; pilot eval4 with isolated work; compare results and failure behavior; then transfer ownership of production outputs. Rollback must not allow two schedulers to write concurrently.

## Documentation release verification

The handover is based on the supplied November 2026 archive and the maintainer's operational context. The original handover preserved existing Markdown files and executable code, changing only the Makefile help recipe and adding new guides. The subsequent archive-aware `status.py` update has been reported working by the maintainer; this documentation revision records that change without further software modifications. No live Slurm submissions, dataset downloads, archive deletion or migration were performed. The repository URL, current Slack decisions, live permissions, exact eval4 setup and scientific benchmark revisions require confirmation from the team. The help was rendered locally; operational commands were inspected statically, not certified by execution on LUMI.
