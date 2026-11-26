# Eval3 survival guide

This is the exceptional-workflow companion to [README.md](README.md). Do not treat repair commands as routine steps. Before changing an evaluation, identify its model directory, current plan, snapshot, job IDs, owners and archive state. Stop or wait for all affected producers, including dependent continuations and shared workers. Preserve evidence and a backup; never delete training checkpoints merely because evaluation is incomplete.

## i. Incomplete or premature models

Run `make inspect-training-status`, `make inspect-not-ready`, `make inspect-training-review` and `make inspect-evaluate-now`. The inspector's NO means active training or no best checkpoint; REVIEW means uncertain termination; YES means eligible, not necessarily complete or scientifically adequate. `KEEP_EXCLUDED` means already absent from the ready list; `REMOVE_FROM_READY` recommends exclusion, not deletion. `REEVALUATE_NOW` means the first hypothesis is at or before training end plus the margin, or predates the best checkpoint. `KEEP_EVALUATION` only means no detected timing problem. The older `make stale-hypotheses` compares loose files only.

The audit is heuristic: job IDs can collide across clusters, pending training without logs can be missed, file timestamps can be copied or changed, and log evidence may be incomplete. A timeout can leave a valid snapshot. Check training logs and Slurm accounting when uncertain. The default margin can be overridden with `TRAINING_STATUS_MARGIN=3600` (seconds). Never use a recommendation as an automatic deletion instruction.

To exclude models, back up `models.ready`, review `make models-ready-preview`, then `make models-ready`. For a deliberate manual exclusion, edit the list after coordination; automatic refresh can re-add it. `models.dropped` is not a persistent exclusion policy in the inspected registration code. Manual aliases are independent. Registration changes do not cancel existing jobs.

For stale hypotheses, quarantine affected hypotheses and corresponding scores outside the active evaluation tree after stopping jobs; preserve their original names, checkpoint evidence and plan. Also quarantine stale summary TSVs and archives if they could be mistaken for current results. A fresh plan alone does not regenerate line-count-complete hypotheses or large score files. No automatic safe stale-output deletion target is supplied. Verify the new checkpoint, then replan and run only affected models.

## ii. Archiving and restoration

Archive only quiescent models after checking TSV completeness. The commands operate on `<HPO_ROOT>/<alias>/mammoth/evaluation`. To use another collection, explicitly set `HPO_ROOT` to its real root. Example:

```sh
make evaluation-archive MODEL=ALIAS DRY_RUN=1
make evaluation-archive MODEL=ALIAS
# Only after independent verification and backup:
make evaluation-archive MODEL=ALIAS DELETE_ORIGINALS=1
# To restore absent directories:
make evaluation-restore MODEL=ALIAS
```

`evaluation-archive-dir EVAL_DIR=/absolute/path/.../mammoth/evaluation` is the explicit-path variant, still constrained to HPO_ROOT. `evaluation-archive-all DRY_RUN=1` previews all matching directories; omit dry run only after reviewing the scope. The default is to keep originals. Existing archives are verified, not automatically refreshed; if files changed, verification may fail. Preserve old archives before arranging replacement. The implementation verifies gzip integrity and compares tar contents to the source, but this is not a substitute for a separate backup, nor a transaction across all four directories. Never run while producers can change files. Restoration skips existing directories; it does not merge partially restored trees. Inspect archive member paths before restoring an untrusted archive.

Deleting originals removes the loose plan, hypotheses, scores and configs. `make status` now reads `plan.out` from the tasks archive if the live plan is missing and looks up missing planned hypotheses and SacreBLEU results in their corresponding archives. It supports `.tar.gz`, `.tgz` and `.tar`, combines live and archived names without double-counting, and warns on unreadable archives. It opens artifact archives only when planned names are missing and does not extract files. Archived results with matching names may be counted even if stale; status does not validate their contents or freshness.

Ordinary replanning and scoring may still schedule work again because they do not consult these archives. `sacre-tsv-all` retains valid TSVs when loose scores are absent; it does not read archives. The training inspector separately reads `hypotheses.tar*` for timing; `.tgz` naming is not included in that glob. Restore before resuming or recomputing scores; do not let missing loose files masquerade as missing scientific results.

## iii. Migrate eval2 to eval3

There are two distinct migrations: directory layout and artifact names. Back up and stop jobs first. Do not run normal setup on an unmigrated tree, because it can create an `evaluation/` directory and block the directory migration.

```sh
make ALIAS list-eval-files
make ALIAS migrate-eval-dry-run
# Review moves, then:
make ALIAS migrate-eval
make ALIAS mk-eval3-yaml
make ALIAS eval3-migrate-dry > rename-eval3.sh
# Inspect the generated script, then explicitly execute if correct:
bash rename-eval3.sh
```

The first migration stages recognized legacy files, moves them into `evaluation/` and attempts rollback on failure; it refuses existing destination trees, stale staging and suspicious legacy contents/markers. It leaves training YAML and checkpoints in place. The second migration produces a combined inference YAML and a checked rename plan for canonical RFC artifact names. Its dry target can generate the YAML; it does not execute renames. `EVAL3_TASKS_FILE` can limit task IDs; `EVAL3_DEDUPLICATE_IDENTICAL=1` is an opt-in for byte-identical aliases, not general conflict resolution. `make eval3-migrate-all MIGRATE_MODELS="alias1 alias2"` pipes generated plans into Bash and actually renames files. Do not use it as a preview. Verify canonical names, accepted task list, reports location and plan afterwards; old plans may need regeneration.

## iv. Compare models.ready with actual readiness

`make inspect-ready-mismatch` shows discrepancies; `make models-ready-preview` shows proposed replacement. Inspect both before `make models-ready`. The inspector needs an existing ready file: for a genuinely new checkout without one, create an empty file only after verifying the path is absent, e.g. `test -e models.ready || touch models.ready`. A failed or empty refresh preserves the existing list. `make list` shows resolved aliases, not necessarily every line in the file. Duplicate names across roots are ambiguous (resolution prefers NMODELS); resolve collisions before evaluation. The inspector scans PMODELS and NMODELS by default, not the manual x-transformers collection.

## v. Add another model collection

For a one-off model, `make MODELDIR=/absolute/path/to/mammoth mk-calls` works only when backend selection recognizes the path or an appropriate backend override is supplied and verified. For a permanent collection, coordinate updates to root definitions, alias resolution, `TRAINING_STATUS_ROOTS`, backend classification in `mk-paths.mk`, archive root, container bindings and permissions. Changing only the inspector's roots is insufficient: it can recommend aliases that the resolver cannot find. The current `EX_MANUAL_MODEL_ALIASES` list is not the `MANUAL_MODEL_ALIASES` variable used by `MODEL_ALIASES`; verify explicit manual activation. Check `make list` and `which-mammoth` before planning. Avoid duplicate aliases and paths containing whitespace (several recipes use shell word lists).

## vi. Missing train.yaml

`train.yaml` is required by normal Make setup, task selection (`inf_tasks.py`), inference YAML conversion, migration and planning dependencies. Model inspection also reads it for architecture/task metadata where available. The planner itself has a narrow fallback: if its TRAINCONFIG points to missing `train.yaml` and sibling `train-raw.yaml` exists, it uses that file. This does not bypass Make prerequisites or make the other consumers fall back. The training-status audit is log/checkpoint based, so eligibility is not proof that train.yaml exists.

Recover the authoritative config from training records or a verified archive. Compare task IDs, src_tgt, sharing groups, vocab paths and architecture to the checkpoint. If `train-raw.yaml` is verified equivalent for evaluation, arrange a documented copy or symlink to the expected name, or explicitly override TRAINCONFIG where supported. Do not overwrite a valid train.yaml or assume raw and final configs are interchangeable. The supplied `train.yamls.tgz` is a possible recovery source, not proof that every model has a matching file.

## vii. Shared tokenizers and src_tgt

The current planner uses structured `src_tgt` for model vocabulary IDs. When a side is not a recognized language or localized code, it resolves the evaluation language from `mt_SRC-TGT` or `zero_SRC-TGT`, checks agreement on any unshared side, and retains the original IDs for vocabulary selection. Examples: `mt_ita-eng` / `roa-eng` evaluates Italian to English with `roa` source vocabulary; `mt_eng-ita` / `gmw-ita` evaluates English to Italian with `gmw`; `mt_kat-eng` / `ccs-eng` evaluates Georgian to English with `ccs`. The original task ID and sharing groups are retained. Same-language evaluation objectives are skipped after resolution; two distinct languages can share one vocabulary. Unresolved selected MT/zero tasks now fail before output writers open. Missing benchmark files can still reduce the plan.

For affected G32 models, stop old jobs, inspect existing outputs for wrong-language or wrong-snapshot provenance, then use `make ALIAS reset-plan` followed by `make ALIAS mk-calls`. Verify `testing.out`, expected coverage and per-task YAMLs. The fix does not automatically invalidate old hypotheses. Check `src_vocab` and `tgt_vocab` keys against the original config, and benchmark source/reference against actual languages. No full LUMI regression is claimed here.

## viii. Add testsets

There is no generic dataset plug-in registry yet. Start with a versioned benchmark and a small aligned sample. Review `downloaders/`, `TRIPLES`, `TESTSET_NAMES`, `DATASET_LANGUAGE_OVERRIDES`, `dataset_ref`, `dataset_language_id`, `emit_tasks`, and proxy pairs in the planner. Define stable canonical benchmark IDs and artifact naming per RFC, locale mapping, split, reference alignment and source/reference paths. Extend migration and result readers/views if their registries require it. Add tests for missing files, locale collapse, zero-shot alignment and expected counts. Pilot one model with isolated outputs, then compare against known results. This is development work, not a current Make command. The download path has not been exercised recently; check upstream dataset changes.

## ix. Add metrics

Current SacreBLEU commands request `-m bleu chrf`; TER is off. Adding a metric requires a versioned scorer configuration, output naming/format, completion criteria, TSV parser and view support. Check `plan_eval3_inference.py`, `summarize_sacre.py`, scoring templates and the RFC. Do not assume adding `ter` to the command updates existing scores: the >500-byte completion check may skip them. Preserve old metrics and plan explicit rescoring. Verify with a small known example before bulk use.

## x. COMET

The planner writes `calls.comet.out` for complete hypotheses, but `mk-comet` only prints a not-implemented message. The separate `plan_eval3_scoring.py` has an optional COMET profile mechanism; it is not an integrated replacement for the routine Make scoring workflow. Do not interpret generated calls as completed COMET evaluation. Reinstatement needs an agreed model/version/profile, GPU environment, source/reference/hypothesis alignment, output schema, scheduling, validation and reporting. Avoid running arbitrary old calls without inspecting them and the model license. Until then, BLEU and chrF are the operational metrics.

## xi. Mixed storage devices

Normal eval3 per-model jobs use absolute paths and can operate across mounted projects/devices; the current setup separates JOBPROJECT and DISKPROJECT. Each job/container must see all required paths with appropriate permissions. Check actual device IDs with `stat -c '%d %n' /path1 /path2` and verify from compute nodes, not only login nodes. Local atomic replacements require the temporary file and destination to share a filesystem. The shared queue already checks queue and claims device IDs. Do not infer that arbitrary cross-device atomic renames or links work. Eval4 is planned to require a shared directory on the same device for its scheduling operations; exact scope must be agreed and tested.

## xii. Switch to eval4

Eval4 is under construction. There is no verified eval4 installation or cutover command in this archive. The intended compatibility is at the artifact level, not necessarily flags, queue entries or scripts. Finish or explicitly stop eval3 work, including continuations and experimental workers. Inventory outstanding work, checkpoint identity, accepted tasks, proxy policy, canonical artifacts and archives. Preserve validated TSVs and a backup. Establish a shared same-device scheduler directory with permissions and container visibility, agree the eval4 configuration, and pilot a single model against existing artifacts before enabling workers. Never run both schedulers on the same outputs. See [DEVELOPMENT-NOTES.md](DEVELOPMENT-NOTES.md).

## Additional repair notes

`make ALIAS reset-plan` is intended to preserve hypotheses, scores and accepted tasks while deleting generated plans/YAMLs and `.inf` files. It has a suspicious shell statement boundary after the first rm list, so it may fail partway (generated script paths are then treated as a command). `reset-replan` also references an undefined `RESET_PLAN_DONE` in this snapshot. Do not rely on either wrapper as transactional. Inspect the actual files after failure; with jobs stopped, `make ALIAS clean-calls` then `make ALIAS mk-calls` is a narrower way to regenerate the plan. The planner replaces the `.inf` set on success. `reset-plan-all` uses the problematic reset target; avoid bulk use until repaired. `mk-score-force` has a questionable recursive recipe; use explicit task acceptance/planning and score instead. `status-infer` and `status-score` are not purely read-only (they may plan and clean flags). `mk-viz`, `view-help`, `mk-pairs-tasks`, `refresh-calls` and `tasks-clear` are missing or only declared; do not depend on them.

If a command fails, inspect `evaluation/testing.err`, Slurm stderr/stdout and flags; verify paths, backend, accepted tasks and dataset files. Do not remove flags blindly: a missing flag is not proof that no job is running. If a plan unexpectedly contains only a few tests, diagnose task resolution, proxy policy and data availability before submitting more jobs.
