# Evaluation Makefile fragments

This directory contains the GNU Make fragments used by the `eval2` model-evaluation workflow. They prepare a model, select evaluation language pairs, generate inference and scoring calls, create SLURM jobs, submit those jobs, and continue the pipeline until no work remains.

These files are **not standalone Makefiles**. The parent [`../Makefile`](../Makefile) defines the configuration and derived paths, selects a model, and includes the fragments in workflow order:

```make
include $(SELFDIR)/include/mk-basic.mk
include $(SELFDIR)/include/mk-pairs.mk
include $(SELFDIR)/include/mk-calls.mk
include $(SELFDIR)/include/mk-slurm.mk
include $(SELFDIR)/include/mk-infer.mk
include $(SELFDIR)/include/mk-score.mk
include $(SELFDIR)/include/mk-contr.mk
```

Run targets through the parent Makefile from `SELFDIR`; do not invoke an individual fragment with `make -f`.

## Files

| File | Responsibility |
| --- | --- |
| `mk-model.mk` | Declares model aliases and maps each alias to its model directory. |
| `mk-basic.mk` | Validates model inputs, inspects checkpoints, selects the compatible Mammoth installation, creates output directories, and provisions scoring/plotting virtual environments. |
| `mk-pairs.mk` | Derives proposed supervised and zero-shot language pairs and requires the user to accept or edit them unless force mode is used. |
| `mk-calls.mk` | Runs the inference planner and creates per-task YAML files plus inference and scoring call lists. |
| `mk-slurm.mk` | Expands the templates in `../template`, calculates resources, creates submission commands, and prevents conflicting jobs. |
| `mk-infer.mk` | Checks inference planning, submits the inference job, and optionally schedules a continuation job. |
| `mk-score.mk` | Checks scoring planning, submits the SacreBLEU job, and schedules a continuation job. COMET is currently a placeholder. |
| `mk-contr.mk` | Replans after a job completes and dispatches the next required stage; it can also continue all declared models. |

## Requirements

The workflow is designed for the CSC/LUMI environment and assumes:

- GNU Make and Bash; the parent Makefile uses `.RECIPEPREFIX := >` and Bash recipes;
- SLURM commands such as `sbatch`, `squeue`, and `srun`;
- environment modules, including `cray-python`;
- Singularity and a readable `.sif` image;
- the Mammoth source/installations configured by `MAMMOTHDEF` and `MAMMOTH64`;
- helper programs under `$(SELFDIR)/bin`, notably `inf_pairs.py`, `inf_plan.py`, `slurm_wrapper.sh`, and `inspect-model-files.py`; and
- the SLURM templates and distributor in `../template` and `../slurm_distr.sh`.

Paths, project IDs, partitions, container images, and model aliases are installation-specific. Review the configuration block in `../Makefile` and `mk-model.mk` before use on another account or cluster.

## Selecting a model

Known models are declared as `MODEL_<alias>` variables in `mk-model.mk` and listed in `MODEL_ALIASES`. Put the alias first on the command line:

```console
make list
make docmt4denhalfbase mk-basic
make docmt4denhalfbase mk-pairs
```

An alias in a later goal position is rejected, and more than one alias cannot be used in the same invocation. An unlisted model can be addressed directly:

```console
make MODELDIR=/scratch/project/path/to/model mk-basic
```

For alias-based commands, `FIRST_GOAL` retains the alias so recursive and continuation invocations keep the same model context.

## Typical workflow

### 1. Prepare the model

```console
make <alias> mk-basic
```

This stage checks `MODELDIR`, `TESTINGDIR`, `DATADIR`, and `train.yaml`; creates `inf_out`, `inf_logs`, and `inf_scores`; inspects `.pt` checkpoints; selects a Mammoth installation; and ensures the SacreBLEU environment exists. Run initial preparation outside a SLURM allocation.

Useful inspection and maintenance targets include:

```console
make <alias> inspect-model-summary
make <alias> which-mammoth
make <alias> clean-mammoth
make <alias> clean-basic
make venvs
```

### 2. Review language-pair proposals

```console
make <alias> mk-pairs
```

The first run generates:

- `inf_zeroshot.txt.input`
- `inf_supervised.txt.input`

Copy or edit these proposals into the corresponding selection files:

- `inf_zeroshot.txt`
- `inf_supervised.txt`

Then rerun `mk-pairs`. To accept both generated proposals without manual review, use:

```console
make <alias> mk-pairs-force
```

The `-force` targets overwrite the selection files when their generated proposals differ, so use them only when automatic acceptance is intended.

### 3. Plan calls

```console
make <alias> mk-calls
```

The planner reads the training configuration and selected pairs, writes task YAML files under `inf_out`, and produces call lists such as:

```text
inf_out/calls.out
inf_out/calls.sacre.out
inf_out/calls.comet.out
```

Planning succeeds only when `inf_plan.py` emits its completion marker. Its captured diagnostic output is retained as `testing.yaml.err` on failure and renamed to `testing.yaml.out` on success.

### 4. Submit inference and scoring

Common entry points are:

```console
make <alias> mk-infer
make <alias> mk-score
make <alias> mk-infer-score
```

`mk-infer` submits only inference. `mk-score` submits planned SacreBLEU work. `mk-infer-score` submits inference and a small continuation job with an `afterany` dependency; the continuation replans the model and starts scoring when appropriate.

Force variants run pair selection in automatic-acceptance mode:

```console
make <alias> mk-infer-force
make <alias> mk-score-force
make <alias> mk-infer-score-force
```

### 5. Resume or finish a pipeline

```console
make <alias> continue-eval
make <alias> continue-eval-force
make continue-all
make continue-all-force
```

Continuation removes stale planning output, replans the remaining work, counts the call lists, and chooses the next stage in this order:

1. inference;
2. SacreBLEU scoring;
3. COMET scoring;
4. visualization; or
5. completion.

`continue-all` applies this logic to every alias, skipping a model when its recorded inference or scoring job is still queued or running.

## Generated files and state markers

For a model directory `MODELDIR`, the parent Makefile derives the following locations:

| Path | Meaning |
| --- | --- |
| `model-summary.yaml` | Checkpoint inspection summary. |
| `mammoth.selected` | Selected Mammoth installation. |
| `preps.done` | Basic preparation completed. |
| `pairs.done` | Pair selections exist. |
| `inf_out/` | Planned YAML files, call lists, generated SLURM scripts, and submission commands. |
| `inf_logs/` | SLURM stdout and stderr logs. |
| `inf_scores/` | Evaluation scores. |
| `*.submitted` | Recorded job IDs used to detect conflicting or active work. |
| `inference.done`, `metrics.done`, `cnt.done` | Stage termination markers created by generated job scripts. |

The SLURM layer generates:

```text
inf_out/inf.slurm
inf_out/cnt.slurm
inf_out/met.slurm
inf_out/inf.sbatch
inf_out/met.sbatch
```

The `.slurm` files come from the `m4` templates in `../template`. Running the inference or metric script outside SLURM invokes `slurm_distr.sh`, which calculates resources and writes the corresponding `.sbatch` command. Under SLURM, the same generated script executes the planned calls through the wrapper.

## Job locking and continuation semantics

Before creating or submitting work, `clean-inf-lock`, `clean-cnt-lock`, and `clean-met-lock` inspect the relevant `.submitted` marker. If its job ID is still visible to `squeue`, the target stops rather than launching a conflicting job. Otherwise, the stale marker is removed.

Inference and scoring continuations use SLURM's `afterany` dependency. This intentionally runs the continuation step whether the preceding job succeeds or fails, allowing the workflow to inspect and replan residual work. Likewise, the templates create their `*.done` marker from an `EXIT` trap, so a done marker records script termination and is not by itself proof of success. Check the job exit status and logs when diagnosing failures.

## Cleaning and rebuilding

Available cleanup targets include:

```console
make <alias> clean-calls
make <alias> clean-slurm
make <alias> clean-basic
make <alias> clean
```

`clean-calls` removes generated call lists and planner logs. `clean-slurm` removes generated job/submission files. `clean-basic` removes the model summary and Mammoth selection. The generic `clean` target also removes generated YAML files from `inf_out`.

Review a target's recipe before cleaning a model with valuable generated state.

## Extending the fragments

When adding a workflow stage:

1. define its paths and state markers in the parent Makefile;
2. make dependencies explicit so Make can rebuild stale artifacts;
3. add lock checking before job submission;
4. update `mk-contr.mk` if the stage participates in continuation;
5. add required substitutions to the matching template and its `m4` invocation; and
6. test both initial execution and resumption after partial completion.

Recipes use `set -euo pipefail` where failure propagation matters. Preserve that behavior in multi-command recipes, quote filesystem paths, and remember to double shell dollar signs (`$$`) inside Make recipes.

## Current limitations

- COMET evaluation reports that it is not implemented.
- Continuation refers to a visualization stage (`mk-viz`), which must be supplied elsewhere in the complete checkout.
- Model aliases and many filesystem paths are tied to the current LUMI installation.
- Several targets depend on helper scripts and templates outside this directory; copying `include/` alone is insufficient.
- A `*.done` file indicates termination, not necessarily successful completion.

The current fragments also contain several implementation details worth checking before production use:

- the virtual-environment recipes test an empty filename (`[ ! -f "" ]`), so they attempt to rebuild whenever invoked;
- `clean-cnt-lock` removes `INF_FLAG` instead of `CNT_FLAG` after finding a stale continuation marker;
- `status-score` extracts a job ID from `INF_FLAG` while testing `MET_FLAG`;
- the recipes for some `*-force` targets split their recursive `make` command at a semicolon and should be verified before relying on them; and
- the all-model continuation recipes refer to globally expanded flag paths rather than paths derived inside the alias loop.

These observations describe the supplied version. If they are corrected, update this section together with the recipes.
