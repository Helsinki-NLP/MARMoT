# Eval3 operator cheatsheet

Run from `MARMoT/eval3` on the login node. Replace `ALIAS` with a real alias from `make list`. A star in `make help` means frequently useful, not shell syntax.

| Goal | Command | Effect |
|---|---|---|
| See commands | `make help` | Read only |
| Audit snapshots | `make inspect-training-status` | Read only; queries Slurm |
| Find new/stale evaluations | `make inspect-evaluate-now` | Recommendation, not submission |
| Compare registration | `make inspect-ready-mismatch` | Read only |
| Preview ready list | `make models-ready-preview` | Read only |
| Refresh ready list | `make models-ready` | Replaces list |
| Find model paths | `make list` | Read only |
| Check progress | `make status` | Loose files and plan |
| Check jobs | `make squeue` | Slurm query |
| Accept tasks | `make ALIAS mk-tasks-force` | May replace selection |
| Plan | `make ALIAS mk-calls` | Generated artifacts |
| Start evaluation | `make ALIAS infer-score` | Submits jobs |
| Start fresh model | `make ALIAS mk-infer-score-force` | Accepts tasks and submits |
| Resume | `make ALIAS continue-eval` | Replans and may submit |
| Score only as needed | `make ALIAS score-if-needed` | May submit scoring |
| Start all | `make infer-score-all` | All registered aliases; review first |
| Convert scores | `make sacre-tsv-all` | Per-model TSVs |
| Verify TSVs | `make list-tsv-all` | Read only |
| Preview archive | `make evaluation-archive MODEL=ALIAS DRY_RUN=1` | No packing/deletion |
| Pack one | `make evaluation-archive MODEL=ALIAS` | Keeps originals |

## Quick routine

```sh
make inspect-ready-mismatch
make inspect-evaluate-now
make models-ready-preview
make models-ready
make list
make status
# For each newly eligible model, after checking the snapshot:
make ALIAS mk-tasks-force
make ALIAS mk-calls
make status
make ALIAS infer-score
make squeue
# Later:
make status
module load cray-python
make sacre-tsv-all
make list-tsv-all
```

Do not repeat task acceptance for a curated selection. A completed model need not be submitted again. For a 170-task proxy model, 131 tests is the usual observed count; inspect unexpectedly small or different plans before running.

## Where to look

Relative to `<collection>/<alias>/mammoth`:

| File or directory | Meaning |
|---|---|
| `train.yaml`, `model_best*`, `train.*.out/err` | Training inputs and evidence |
| `evaluation/inf_tasks.txt.input`, `inf_tasks.txt` | Proposed and accepted tasks |
| `evaluation/testing.out`, `testing.err` | Planning diagnostics |
| `evaluation/tasks/plan.out`, `calls*.out`, `*.inf` | Planned cases, remaining calls, durable tasks |
| `evaluation/configs/` | Inference YAMLs |
| `evaluation/hypotheses/`, `scores/` | Outputs and metric files |
| `evaluation/logs/`, `flags/` | Job diagnostics and state |
| `evaluation/reports/sacre.tsv` | Per-model normalized scores |

## Stop before doing these

Resetting plans, changing proxy selection, replacing training YAMLs, moving artifacts, restoring archives or deleting original directories all require a quiescent affected model. Check actual jobs (including other users and continuations), not only flags. `make ALIAS reset-plan` preserves hypotheses and scores; it does not invalidate stale outputs. See [SURVIVAL-GUIDE.md](SURVIVAL-GUIDE.md).
