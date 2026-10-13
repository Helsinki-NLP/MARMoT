# RFC-EVAL-YAML — Shared inference configuration derived from train.yaml

**Status:** Draft — compatibility specification (13 October 2026)  
**Reference converter:** `bin/make_inference_yaml.py`  
**Current downstream planner:** `bin/plan_eval3_inference.py`  
**Build interface:** `make <MODEL> mk-eval3-yaml`  
**Related:** RFC-EVAL-ARTIFACTS; RFC-EVAL-SELECTION; planned RFC-EVAL-RUNS / checkpoint resolution

## 1. Scope and decision

Eval3 derives **one model-wide** `evaluation/configs/inference.yaml` from a model's original `train.yaml`. The immediate aim is to replace eval2's repeated **single-task inference YAMLs** without changing the effective HPO decoding configuration used in completed evaluations.

**Current-round requirement:** derive a single, reusable inference configuration whose effective settings agree with the two supplied, already evaluated HPO configurations. The justified departures are a combined task/vocabulary inventory, preservation of original training weights, removal of obsolete helper annotations, and omission of per-execution selectors. The converter must not introduce new inference settings during the filename migration.

Potential changes to generation length, tokenizer flags, timing reports, typing conventions or checkpoint provenance are presented only **after the normative specification** (§11), as topics for future evaluation rounds. Changing a decoding condition can require fresh inference and must not be described as a mere artifact rename.

The shared YAML is a **model configuration**, not a runnable job definition. It must not choose a dataset, one active task, checkpoint, source file, or hypothesis output. The current inference planner selects a task and derives dataset inputs and output paths, but does **not yet** resolve a checkpoint or invoke MAMMOTH. Runtime integration is separate; this RFC does not imply that existing translations are reproduced merely by regenerating configuration files.

Normative **MUST**, **SHOULD**, and **MAY** apply to the compatibility profile unless otherwise noted.

## 2. Evidence: the actual evaluated configurations

The supplied `yamls.tgz` contains the following:

| Case | Model family | Training tasks | Evidence |
|---|---|---:|---|
| HPO PyTorch | `hpo/small-4p+d-Aenc-Ldec-20k` | 313 | `train.yaml`, evaluated `evaluation/configs/mt_eng-mlt.yaml`, existing shared `evaluation/configs/inference.yaml` |
| HPO XTransformers | `hpo-xtransformers/docmt-4pivots` | 280 | `train.yaml`, evaluated `evaluation/configs/mt_eng-mlt.yaml` |
| Developer's example | General MAMMOTH template | 1 | `template/inf.yaml.templ` |

The two HPO `mt_eng-mlt.yaml` files are the **observed status quo** supplied for this RFC. They are not identical to the developer's generic template, and they should not be retroactively reinterpreted as if they had its settings. These configurations establish *recorded* settings; reproducing inference runtime behavior additionally requires the actual MAMMOTH code, checkpoint and invocation.

### 2.1. Comparison: evaluated HPO YAMLs, developer template, and current eval3

The two HPO columns are values **read from the supplied `mt_eng-mlt.yaml` files**. *Absent* means no YAML key was present; it does not establish a runtime default. The RFC column specifies the output of the **current HPO-compatible `make_inference_yaml.py`**, while the last column records what the **actual `plan_eval3_inference.py` writes**. In that last column, *no override* means the planner does not set the field or rewrite the shared YAML; it only points to it. This must not be mistaken for verified runtime parameter inheritance, because the planner does not invoke MAMMOTH yet.

| Setting / structure | Evaluated HPO PyTorch | Evaluated HPO XTransformers | Developer's `inf.yaml.templ` | **Current RFC / `make_inference_yaml.py`** | **Actual `plan_eval3_inference.py`** |
|---|---|---|---|---|---|
| `max_length` | **1024** | **1024** | 512 | Retain `train.yaml` value (1024 in both supplied models) | No override |
| `model_dtype` | `bf16` | `bf16` | `bf16` | Retain original value | No override |
| `use_hf_tokenizer` | Absent | Absent | Boolean `true` | Preserve presence/absence; do not insert | No override |
| `report_time` | Absent | Absent | Boolean `true` | Preserve presence/absence; do not insert | No override |
| `beam_size` | **4** | **4** | 5 | **Set integer 4 universally** | No override |
| `batch_size` / `batch_type` | `32` / `sents` | `32` / `sents` | `32` / `sents` | Set `32` / `sents` | No override |
| `gpu` / `world_size` / `gpu_ranks` | `0` / `1` / `[0]` | `0` / `1` / `[0]` | `0` / `1` / `[0]` | Set `0` / `1` / `[0]` | No override |
| `seed` | 42 | 42 | 42 | Set integer 42 | No override |
| Task `introduce_at_training_step` | String `'0'` | Integer `0` | Integer `0` | PyTorch: string `'0'`; XTransformers: retain training value | No override |
| Task `weight` | String `'1'` imposed by eval2 | Integer `1` | Integer `1` | **Require; preserve training value and type** (integer `1` in both supplied models) | Does not use weight |
| `tasks` mapping | One: `mt_eng-mlt` | One: `mt_eng-mlt` | One: `eng-spa` | **All training tasks** (313 / 280) | Reads tasks; may select subset via `--tasks-file` |
| `src_vocab` / `tgt_vocab` | Vocabularies for selected pair | Vocabularies for selected pair | Vocabularies for selected pair | Union across every task | No override |
| Top-level `task_id` / `_expanded_task` | Both present | Both present | `task_id` present | **Absent**; no selected task in common YAML | Per-case `TASK_ID` Bash variable |
| `model`, `src`, `output` | Not in HPO YAMLs | Not in HPO YAMLs | Execution fields present / placeholders | **Absent** from shared YAML | Emits `INFER_SRC` and `INFER_HYP`; checkpoint not supplied |
| Reference / dataset | Outside inference YAML | Outside inference YAML | Source path only | Outside shared YAML | Emits `INFER_REF`, `TESTSET`, language IDs |
| `_train_config` | Present | Present, but recorded path may be stale | Absent | Set to supplied training YAML path | No override |
| Legacy per-task helper fields | 3 fields | 5 fields | Absent | Delete the five known helpers | Does not generate them |

**What the table establishes.** In the two supplied models, the current converter produces the historical **inference-time numeric and decoding values** while retaining all tasks, preserving their original weights, and omitting old one-task selectors. The planner does not contradict those values because it never assigns them. In particular, it does *not* implement the developer template's `max_length: 512`, `beam_size: 5`, `use_hf_tokenizer: true` or `report_time: true`.

The PyTorch HPO file used a string `'1'` for `weight`, although its training task has integer `1`. Keeping the training scalar is intentional and is the only material task-field change in this example besides dropping legacy helpers. The original training files also use `beam_size: 1`; the shared inference converter sets 4, just as the evaluated HPO YAMLs did.

### 2.2. Precise interface to `plan_eval3_inference.py`

The current planner reads `evaluation/configs/inference.yaml`; it **does not generate, patch, or execute that YAML**. For each selected task and test set it writes a sourceable Bash definition, together with a tab-separated `inf_plan.out` manifest. The definition exports:

```bash
EVAL_BASE=...                 # derived from the Bash definition's own filename
TASK_ID=...                   # task key from inference.yaml
TESTSET=...                   # canonical test-set identifier
TESTSET_SOURCE_LANGUAGE=...
TESTSET_TARGET_LANGUAGE=...
INFER_SRC=...                 # selected test-set source file
INFER_REF=...                 # corresponding reference file
INFER_HYP=...                 # new-standard hypothesis filename
INFERENCE_YAML=...           # path to the shared configuration
```

The planner obtains task-language pairs from `src_tgt`, maps them to dataset-specific language identifiers, and checks the availability of source/reference files (optionally their line counts). It does **not** parse task-type prefixes to determine decoding, require a task's weight to be positive, override a shared-YAML inference parameter, choose a checkpoint, set the MAMMOTH `model` argument, or invoke `translate.py`.

| Boundary | Normative RFC position | Current planner | Assessment |
|---|---|---|---|
| Shared model configuration | Contains all training tasks; selects none | Reads that configuration without changing it | **Agrees** |
| Task selection | Done per execution, outside common YAML | Defines `TASK_ID` per case; optional task-list selection | **Agrees** |
| Decoding and device configuration | HPO settings above | Specifies no overrides, exports `INFERENCE_YAML` | **No conflict; runtime use unverified** |
| Evaluation data and filename | Resolved downstream | Defines source, reference and canonical hypothesis path | **Agrees** |
| Exact checkpoint and MAMMOTH invocation | Execution-layer responsibility | Not implemented in the Bash definitions | **Incomplete, not contradictory** |

**Compatibility limit:** the planner's absence of decoding overrides is not proof that its eventual runner will use all YAML settings. End-to-end equivalence with completed HPO translations can only be checked after connecting and testing the actual MAMMOTH invocation and identifying the historical checkpoint. This does **not** justify changing the historical parameters in the present migration.

## 3. Mechanical derivation: common configuration

Invocation:

```bash
python bin/make_inference_yaml.py "$TRAINCONFIG" "$CFGDIR/inference.yaml" \
  --mammoth-type "$MAMMOTH_TYPE"
```

The converter MUST:

1. Validate a nonempty `tasks` mapping, both vocabulary mappings, task identifiers, `src_tgt`, and an explicit non-null `weight` in **each** task.
2. Copy `train.yaml`, deleting only the enumerated top-level training keys in §4, the per-task paths and helpers in §5, and the global execution selectors in §7.
3. Keep **every task under its exact training task key**. No task selection, task-prefix interpretation, name expansion or dataset-specific language refinement occurs in this stage.
4. Keep every task's original `src_tgt`, sharing groups and `weight`, including its YAML scalar type. A task with weight zero remains in the configuration.
5. Clear task transforms, assign `node_gpu: '0:0'`, and apply the historical backend-specific `introduce_at_training_step` behavior (§5).
6. Keep the union of vocabularies referenced by all tasks (§6).
7. Set only the proven common HPO inference overrides (§8). In particular, **do not overwrite** `max_length`, `model_dtype`, `use_hf_tokenizer`, or `report_time`.
8. Add `_train_config` pointing to the input training YAML path.
9. Write the resulting YAML to a unique temporary file in the destination directory, then atomically replace the final YAML after validation and successful serialization.

Fields not explicitly removed or overridden are preserved to avoid inadvertently altering the model architecture or backend configuration. YAML comments and layout are not retained by PyYAML.

## 4. Exact top-level training-parameter deletions

The following **46 names** are removed **if present**; category headings are descriptive and do not create wildcard deletion rules.

| Category | Keys |
|---|---|
| Validation and early stopping (7) | `early_stopping`, `valid_timeout`, `valid_decode_timeout`, `valid_max_length`, `valid_batch_size`, `valid_steps`, `valid_metrics` |
| Monitoring and logging (6) | `tensorboard`, `tensorboard_log_dir`, `report_tflops`, `log_model_structure`, `report_every`, `report_training_accuracy` |
| Denoising during training (5) | `denoising_objective`, `mask_ratio`, `mask_length`, `poisson_lambda`, `replace_length` |
| Training sequence limits (4) | `src_seq_length_min`, `tgt_seq_length_min`, `src_seq_length_max`, `tgt_seq_length_max` |
| Optimization/scheduling (18) | `reset_optim`, `train_steps`, `accum_count`, `lookahead_minibatches`, `normalization`, `queue_size`, `optim`, `learning_rate`, `adam_beta1`, `adam_beta2`, `weight_decay`, `max_grad_norm`, `label_smoothing`, `warmup_steps`, `decay_method`, `learning_rate_decay`, `start_decay_steps`, `average_decay` |
| Distributed training (2) | `n_nodes`, `task_distribution_strategy` |
| Checkpoint saving (4) | `save_checkpoint_steps`, `keep_checkpoint`, `save_model`, `save_strategy` |

Other top-level removals (`task_id`, `_expanded_task`, `model`, `src`, `output`) are **not included** in the count of 46; they are execution-specific (§7).

## 5. Exact per-task rewrite

| Field | Compatibility action |
|---|---|
| Task key and `src_tgt` | Preserve exactly |
| **`weight`** | **Require, preserve value and YAML type**, never force to 1 |
| `path_src`, `path_tgt`, `path_valid_src`, `path_valid_tgt` | Remove |
| `enc_sharing_group`, `dec_sharing_group` | Preserve; if absent, add `[]` (eval2 behavior) |
| `transforms` | Set `[]` (legacy inference behavior; revisit task-specific preprocessing later) |
| `node_gpu` | Set string `'0:0'` |
| `introduce_at_training_step` | PyTorch: set string `'0'` to match recorded HPO; XTransformers: retain training value/type as recorded |
| `_template_task`, `_original_train_task`, `_pair_type`, `_src_task_candidates`, `_tgt_task_candidates` | Remove if present; never generate |
| Other fields | Preserve |

The source and target vocabulary codes are read from `src_tgt`, **not parsed out of the task key**. No prefix such as `mt_`, `docmt_`, `zero_` or `denoise_` is given special treatment.

The PyTorch HPO file's forced `weight: '1'` is **not carried forward**: it loses the training exposure information when weights differ. For the supplied PyTorch sample, training weight `1` becomes inference weight `1` (integer), the only intended task-value difference other than removed debug fields.

## 6. Vocabulary union

Let `T` be the training configuration and let `s(t)` and `d(t)` be the two strings in `T.tasks[t].src_tgt`. Define:

```text
S = { s(t) : t in T.tasks }
D = { d(t) : t in T.tasks }
```

The converter keeps `T.src_vocab` restricted to `S` and `T.tgt_vocab` restricted to `D`; referenced vocabulary paths are unchanged. Missing required vocabularies are errors. This generalizes eval2's one-source/one-target vocabulary submaps to one shared configuration. Source and target vocabulary maps remain distinct even if their keys overlap.

## 7. Boundary between model-wide YAML and execution

The shared YAML **MUST NOT** select a particular task. It includes the `tasks:` mapping containing all training tasks, but excludes top-level `task_id` and `_expanded_task`.

It also excludes job-specific `model`, `src`, and `output`. These values are supplied by per-task inference Bash definitions or an equivalent supported MAMMOTH invocation interface. Evaluation reference files, test-set identities, language/locale refinements, hypothesis filenames and scoring details likewise belong downstream.

`_train_config` **is retained** to help debug provenance and inspect the original training configuration. It records the path supplied to the converter; this is not a content hash, and moving a model may invalidate the recorded path.

**Checkpoint policy:** a checkpoint cannot be proved final from this derived YAML. For historical HPO evaluations, preserve the actual checkpoint identity if logs/commands permit; do not infer it retrospectively from file names. A future planner SHOULD resolve and record whether the selected checkpoint is final, best, last available, or explicitly overridden, based on checkpoint metadata and training-completion evidence. The label `model_best*` alone does not prove finality. The shared YAML must not invent or embed a checkpoint selection.

## 8. HPO-compatible inference-time overrides

These **seven** top-level values are mechanically set for both backends:

```yaml
beam_size: 4
batch_size: 32
batch_type: sents
gpu: 0
world_size: 1
gpu_ranks: [0]
seed: 42
```

This matches the two supplied HPO `mt_eng-mlt.yaml` files. Seed 42 is a repeatable project convention, not a universally standardized or guaranteed fully deterministic GPU seed. Beam width 4 is the established HPO evaluation setting and the universal choice for this migration round.

**Preserve from `train.yaml` rather than force values:**

```yaml
max_length: 1024     # observed in both training files, not an unconditional override
model_dtype: bf16    # observed in both training files, not an unconditional override
```

If a new model has different training values, this compatibility converter keeps them and reports that difference only through the generated YAML; the evaluation planner should record the actual decoding configuration. This is a deliberate conservative policy, **not** a decision that every future evaluation must inherit the training limit.

**Do not inject** the following fields simply because the developer's template includes them:

```yaml
# use_hf_tokenizer: true
# report_time: true
```

Both are absent from the supplied training and HPO YAMLs. Their absence must be preserved in the compatibility round; whether the runtime nevertheless uses a Hugging Face tokenizer or reports times is a separate backend-default/runtime question. If present explicitly in a future `train.yaml`, this converter leaves them unchanged.

## 9. Publication and Make integration

Canonical command:

```bash
make <MODEL> mk-eval3-yaml
```

Implementation command:

```bash
python bin/make_inference_yaml.py "$TRAINCONFIG" "$CFGDIR/inference.yaml" \
    --mammoth-type "$MAMMOTH_TYPE"
```

`train.yaml` is never overwritten. If input validation fails, the existing inference file must remain unchanged. The converter serializes YAML into a unique file in the destination directory, then replaces the final path atomically with `os.replace()`.

The Make target currently depends on the training YAML and converter script. Both observed backends have the same top-level overrides but different `introduce_at_training_step` typing, so the selected `MAMMOTH_TYPE` must be tracked or regeneration explicitly forced when it changes. Existing Make files may not yet track variable changes as file dependencies.

This conversion neither schedules inference nor proves that a particular backend supports execution from a multi-task shared YAML. The execution interface must be validated separately.

## 10. Compatibility conformance criteria

The two supplied HPO YAMLs are regression fixtures. For the corresponding training configurations, the converter must:

1. Generate 313 PyTorch / 280 XTransformers tasks under the original names, with the required source/target vocabulary unions.
2. Match **every ordinary top-level setting** from the respective HPO `mt_eng-mlt.yaml` after excluding the expected differences in selected-task structure, vocabularies, job selectors, and `_train_config` path.
3. Match each HPO `mt_eng-mlt` task's operational fields, **except** preserve `weight` as in training and delete obsolete helper annotations.
4. Preserve `max_length: 1024`, `model_dtype: bf16`, beam 4, seed 42, batch 32, and absence of `use_hf_tokenizer` / `report_time` in both archived samples.
5. Preserve weight values/types for all tasks and reject missing/null weights (including zero as a valid weight).
6. Remove the 46 enumerated top-level training parameters, training data paths, single-job selectors, and five legacy per-task helper fields.
7. Fail without damaging an existing target YAML when validation fails.

These tests establish **YAML compatibility with historical HPO configs**, not equivalence of generated translations without executing the corresponding models and inference code. A downstream planner that merely exports paths does not by itself establish inference-runtime parity.

## 11. Discussion: limitations and possible changes for future rounds (non-normative)

The normative compatibility specification ends in §10. The following are **discussion points, not changes required or implemented in this migration**. A new, named evaluation profile should be defined and tested before changing any of the following:

| Topic | Historical compromise | Future recommendation and required decision |
|---|---|---|
| Output length | `max_length` inherited as 1024 in both HPO models | Decide whether 512 is suitable, verify whether it means generated tokens or total sequence length per backend, and label/re-run comparisons when changing it |
| Hugging Face tokenizer | No explicit `use_hf_tokenizer` | Inspect both backend parsers and runtime logs; only then decide whether explicitly setting boolean `true` preserves or changes behavior |
| Inference timing | No explicit `report_time` | Prefer boolean `true` for future profiling **if supported**, with tested logging and token/time measurement semantics; do not mislabel archived runs |
| Model dtype | Inherited `bf16` | Check device/backend support, numerical behavior and checkpoint expectations before enforcing globally |
| Task step value | PyTorch string `'0'`, XTransformers integer `0` | Prefer integer `0` after confirming both inference parsers handle the change, or keep backend-specific typing in a documented compatibility adapter |
| Training weight | PyTorch historical `'1'` erased exposure | Already improved: preserve required original numeric value/type; evaluate any runner reliance on a fixed weight separately |
| Beam size | 4 in supplied HPO runs; developer template 5 | Keep **4** as the universal project default; any future departure is a new named decoding profile |
| Checkpoint | Historical run selection external to YAML | Add an explicit checkpoint-resolution/verification record, distinguish *final* from *best* and *latest*, never infer finality from YAML alone |
| Reuse and reproducibility | Output paths may hide runtime choices | Include checkpoint identity, backend/code version, actual decoding settings, source content identity and tokenizer in downstream run provenance |

Future variants should have an explicit profile identity (for example a profile version in run metadata), not silently replace the compatibility behavior for already-scored HPO artifacts. Changes to tokenization, generation length, checkpoint or beam may change hypotheses; **renaming files cannot make such evaluations equivalent**.

### 11.1. Problems to resolve separately

1. **Execution still needs validation.** The current planner only writes Bash variable definitions; it does not yet inject `task_id` into the MAMMOTH invocation, choose a model checkpoint, or execute translation. Before relying on the shared YAML to reproduce past runs, test one known task with both backends against the previously used invocation.
2. **Checkpoint identity is external.** A `model_best*` name does not establish that a checkpoint is the final training state. Existing files can be renamed without proving this, but future execution must record the exact selected checkpoint and how it was identified.
3. **One historical provenance path appears stale.** The XTransformers HPO `mt_eng-mlt.yaml` records an `_train_config` path under a different model directory from the archived `train.yaml`. This supports regenerating `_train_config` from the actual converter input and treating historical paths as debugging clues rather than cryptographic identities.
4. **Omitted options have unknown runtime defaults.** The absence of `use_hf_tokenizer` and `report_time` in HPO YAMLs cannot establish whether tokenization or timing reporting was disabled; determine this from the relevant MAMMOTH code and run logs before setting explicit booleans.
5. **Compatibility is model-specific.** Inheriting `max_length` preserves the supplied HPO configurations, but a new model trained with another limit will inherit that other limit. This is deliberate for migration, not a standardization of all future evaluations.
6. **Scalar types differ between old files.** PyTorch used `'0'` for `introduce_at_training_step` and forced `'1'` for `weight`. The compatibility converter retains the first convention but corrects the second. Verify that evaluation runners do not depend on the discarded string-typed weight before re-inferencing historical configurations.

None of these concerns requires changing historical hypothesis files or introducing new decoding parameters during the present filename migration.

