# RFC-EVAL-YAML — Deriving `inference.yaml` from `train.yaml`

**Status:** Draft · **Scope:** Current HPO-compatible evaluation round  
**Implementation:** `bin/make_inference_yaml.py` · **Make target:** `mk-eval3-yaml`

## 1. Baseline: configurations already used for inference

Two `evaluation/configs/mt_eng-mlt.yaml` files in `yamls.tgz` document completed HPO evaluations: an XTransformers model (`hpo-xtransformers/docmt-4pivots`) and a PyTorch model (`hpo/small-4p+d-Aenc-Ldec-20k`). The developer's `template/inf.yaml.templ` is a separate example, **not** evidence of how those evaluations were run.

**Decision for this evaluation round:** use the **evaluated PyTorch HPO configuration** as the reference practice for decoding and inference execution settings. Do not change these settings while migrating to a single model-wide `inference.yaml`. The shared file contains *all* training tasks and their vocabularies. It preserves training-only task information under explicitly non-operational names: `weight` becomes `_training_weight`, and `introduce_at_training_step` becomes `_training_introduce_at_training_step`. Both values and YAML scalar types are preserved. Neither original field appears in the generated task mapping, which does not select a task or a particular inference run.

### Comparison

*Absent* means the key is not present; it does not imply `false` or another runtime default. Values in quotes indicate YAML strings rather than integers.

| Field | Evaluated XTransformers HPO | Developer's PyTorch template | **Evaluated PyTorch HPO (RFC baseline)** |
|---|---|---|---|
| `tasks` | One task: `mt_eng-mlt` | One task: `eng-spa` | One task: `mt_eng-mlt` |
| `task_id` | `mt_XX.eng-XX.mlt` | `eng-spa` | `mt_XX.eng-XX.mlt` |
| Task `weight` | `1` | `1` | `'1'` (forced by eval2) |
| Task `introduce_at_training_step` | `0` | `0` | `'0'` |
| Task `node_gpu` | `'0:0'` | `'0:0'` | `'0:0'` |
| Task sharing groups | `['eng']` / `['mlt']` | `['eng']` / `['spa']` | `['all']` / `['mlt']` |
| Task `transforms` | `[]` | Absent | `[]` |
| `src_vocab`, `tgt_vocab` | Selected language pair | Selected language pair | Selected language pair |
| Model architecture | XTransformers-specific parameters | Mostly unspecified | PyTorch-specific parameters |
| `model_dtype` | `bf16` | `bf16` | `bf16` |
| `max_length` | **1024** | **512** | **1024** |
| `use_hf_tokenizer` | Absent | `true` | Absent |
| `beam_size` | **4** | **5** | **4** |
| `batch_size` | `32` | `32` | `32` |
| `batch_type` | `sents` | `sents` | `sents` |
| `gpu` | `0` | `0` | `0` |
| `world_size` | `1` | `1` | `1` |
| `gpu_ranks` | `[0]` | `[0]` | `[0]` |
| `report_time` | Absent | `true` | Absent |
| `seed` | `42` | `42` | `42` |
| `model`, `src`, `output` | Absent | Execution fields (two blank) | Absent |
| `_train_config` | Present | Absent | Present |

The `weight` and `introduce_at_training_step` rows report **historical file contents**; their spelling and scalar types are not part of the decoding baseline. The shared eval3 YAML instead carries their original training values as `_training_weight` and `_training_introduce_at_training_step`. The XTransformers model has its own architecture parameters; the RFC does **not** replace them with PyTorch architecture parameters. The PyTorch practice is the baseline for **common inference settings**, while each model retains its own architecture.

## 2. Training-time parameters omitted from inference

The converter drops the following **46 top-level training-only fields if present**. All 46 occur in the supplied PyTorch training YAML and are absent from its evaluated inference YAML. The XTransformers training YAML contains 40 of them, all likewise removed. The developer's template is not generated from a training YAML and simply does not specify these settings.

| Category | Fields removed |
|---|---|
| Validation (7) | `early_stopping`, `valid_timeout`, `valid_decode_timeout`, `valid_max_length`, `valid_batch_size`, `valid_steps`, `valid_metrics` |
| Logging and training monitoring (6) | `tensorboard`, `tensorboard_log_dir`, `report_tflops`, `log_model_structure`, `report_every`, `report_training_accuracy` |
| Denoising training (5) | `denoising_objective`, `mask_ratio`, `mask_length`, `poisson_lambda`, `replace_length` |
| Training sequence filters (4) | `src_seq_length_min`, `tgt_seq_length_min`, `src_seq_length_max`, `tgt_seq_length_max` |
| Optimization and scheduling (18) | `reset_optim`, `train_steps`, `accum_count`, `lookahead_minibatches`, `normalization`, `queue_size`, `optim`, `learning_rate`, `adam_beta1`, `adam_beta2`, `weight_decay`, `max_grad_norm`, `label_smoothing`, `warmup_steps`, `decay_method`, `learning_rate_decay`, `start_decay_steps`, `average_decay` |
| Distributed training (2) | `n_nodes`, `task_distribution_strategy` |
| Checkpoint saving (4) | `save_checkpoint_steps`, `keep_checkpoint`, `save_model`, `save_strategy` |

Within each task, remove the training and validation corpus paths: `path_src`, `path_tgt`, `path_valid_src`, `path_valid_tgt`. These must not determine evaluation data selection.

The original per-task controls `weight` and `introduce_at_training_step` are **renamed, not dropped**. Their provenance mapping is defined in §3.

## 3. Training configuration retained in PyTorch practice

The evaluated PyTorch HPO inference configuration **inherits the following top-level values unchanged** from its `train.yaml`:

- **Architecture:** `enc_layers`, `dec_layers`, `model_dim`, `heads`, `dropout`, `attn_dropout`, `ff_dropout`, `ff_activation`, `rotary_pos_emb`, `post_emb_norm`, `add_language_tokens`.
- **Model representation and length:** `model_dtype: bf16`, `max_length: 1024`.
- **Vocabulary contents:** the paths in `src_vocab` and `tgt_vocab`, selecting only the languages needed for the evaluated task.
- **Task information:** `src_tgt`, `enc_sharing_group`, and `dec_sharing_group` retain the original values. The task name is also retained.

Other model-specific fields are retained rather than removed by name. For example, the XTransformers HPO inference YAML retains `head_dim` and `x_transformers_opts` from its own training configuration.

### Training-only task metadata in the shared YAML

| Field in `train.yaml` | Field in `inference.yaml` | Requirement |
|---|---|---|
| `weight` | `_training_weight` | Required; preserve exact value and YAML type |
| `introduce_at_training_step` | `_training_introduce_at_training_step` | Rename when present; otherwise omit |

For example, the task fragment

```yaml
tasks:
  mt_eng-mlt:
    src_tgt: eng-mlt
    weight: 0
    introduce_at_training_step: 12000
```

becomes, as far as these fields are concerned:

```yaml
tasks:
  mt_eng-mlt:
    src_tgt: eng-mlt
    _training_weight: 0
    _training_introduce_at_training_step: 12000
```

These private metadata keys do not request task sampling or training-step scheduling during translation. If the source already contains either destination metadata key, conversion should fail on ambiguity rather than overwrite it silently.

**Shared eval3 configuration:** keep *every* training task under its original name, and retain the union of their required `src_vocab` and `tgt_vocab` entries instead of only one pair. For each task, **rename** the required training `weight` field to `_training_weight`, retaining its original value and YAML scalar type (including zero). If `introduce_at_training_step` exists, **rename** it to `_training_introduce_at_training_step`, likewise retaining its original value and type; do not insert it when absent. The old field names MUST NOT remain in `inference.yaml`. These underscore-prefixed fields preserve provenance; they are **not inputs to the inference task scheduler or decoder**. Historical PyTorch HPO generation instead wrote `weight: '1'` and `introduce_at_training_step: '0'` irrespective of original scalar types.

## 4. Values introduced or replaced for inference

The following settings implement the evaluated PyTorch HPO practice; they are also consistent with the evaluated XTransformers configuration.

| Setting | Inference value | Treatment |
|---|---|---|
| `beam_size` | `4` | Override training value (which was `1` in both samples) |
| `batch_size` | `32` | Override training batch size |
| `batch_type` | `sents` | Override training `tokens` |
| `gpu` | `0` | Introduce as inference device |
| `world_size` | `1` | Override training world size |
| `gpu_ranks` | `[0]` | Override training GPU ranks |
| `seed` | `42` | Write explicitly (same as both sampled training YAMLs) |
| Task `node_gpu` | `'0:0'` | Override training placement |
| Task `transforms` | `[]` | Clear training transforms |
| `_train_config` | Original `train.yaml` pathname | Introduce for debugging and provenance |

**Do not introduce** `use_hf_tokenizer` or `report_time` when absent from `train.yaml`. **Do not override** its `max_length` or `model_dtype`. Beam size **4** applies to both model implementations in this round. **Do not expose** training-time `weight` or `introduce_at_training_step` under their operational names: rename them to the `_training_...` metadata fields specified in §3. This changes only their representation in the shared YAML, not the established decoding parameters.

The shared `inference.yaml` must contain the `tasks` mapping, **not** a globally selected `task_id`. Remove any global `task_id`, `_expanded_task`, `model`, `src`, or `output`; the latter fields belong to the actual inference execution. Also remove the obsolete per-task helper fields `_template_task`, `_original_train_task`, `_pair_type`, `_src_task_candidates`, and `_tgt_task_candidates` if present.

`plan_eval3_inference.py` selects evaluation cases and defines their source, reference and hypothesis paths. It does not override the above decoding settings or yet execute MAMMOTH. Thus the generated task definition is not by itself evidence of a completed inference run.

**Training metadata rule:** For every task, `train.yaml` MUST contain a non-null `weight`. The converter MUST produce `_training_weight` with the **same value and YAML type**, then omit `weight`. If `introduce_at_training_step` is present, it MUST produce `_training_introduce_at_training_step` with the **same value and YAML type**, then omit `introduce_at_training_step`; if absent, both the source field and its metadata counterpart remain absent. The converter MUST NOT coerce values, fabricate defaults, or silently overwrite an existing `_training_weight` or `_training_introduce_at_training_step` field. In the inspected PyTorch inference path, translation constructs the selected task using fixed operational values (`weight=1.0`, `introduce_at_training_step=0`) independent of these training records. The underscore-prefixed fields document training rather than request those runtime values.

The conversion is invoked with:

```bash
make <MODEL> mk-eval3-yaml
```

The generated shared configuration is `evaluation/configs/inference.yaml`. It does not replace the original `train.yaml` or the historical single-task HPO YAMLs.

## 5. Discussion only — questions for later evaluation rounds

**This section is not an RFC requirement and is not implemented by the current converter.** It identifies points requiring review before changing inference behavior. In particular, changing a decoding parameter can invalidate comparisons with completed HPO translations.

- **Fields essential to retain from training.** Model architecture, parameter-sharing groups, vocabulary mappings, `add_language_tokens`, and tokenizer/model representation settings must remain consistent with the trained checkpoint. A silent change could prevent loading the model or change tokenization. The observed inherited `model_dtype` and architecture settings are therefore important; any newly introduced preprocessing or tokenizer flag needs backend-specific confirmation.
- **`max_length`: 1024 versus 512.** Both HPO files inherit `1024`; the developer template uses `512`. It is unclear whether a smaller limit is desirable or whether both implementations interpret the limit identically. Neither question justifies changing completed evaluations retroactively.
- **`use_hf_tokenizer`: absent versus `true`.** The developer recommends `true`, but neither HPO file specifies the key. Its runtime default and interaction with the stored tokenizer paths should be checked before adding it; *absent* cannot be equated with *false*.
- **`report_time`: absent versus `true`.** The developer enables timing. The HPO files do not. Enabling it may be useful for future timing and token-throughput studies, but the existing runs' actual logging behavior must be established independently.
- **Training-only task metadata in inference YAML.** The PyTorch HPO YAML contains the strings `weight: '1'` and `introduce_at_training_step: '0'`, although the developer's template and the XTransformers HPO use numeric values. In the inspected MAMMOTH PyTorch translation entry point (`mammoth/bin/translate.py`), `TaskSpecs` is constructed with `weight=1.0` and `introduce_at_training_step=0` independently of the task's YAML values. The shared YAML therefore carries the original training values only as `_training_weight` and `_training_introduce_at_training_step`, without reproducing historical string conversions. This is a metadata-schema change, not a requested inference-behavior change. The local MAMMOTH revision and its handling of unrecognized underscore-prefixed keys should be checked if strict execution equivalence is required.
- **Cleared `transforms` and omitted data filters.** These match the HPO MT practice, but may be inappropriate for denoising or other tasks whose inference requires preprocessing. The intended semantics of `transforms`, `src_seq_length_*`, and `tgt_seq_length_*` warrant separate inspection for those tasks.
- **Checkpoint identity.** Neither the historical HPO YAMLs nor the shared `inference.yaml` proves that a particular checkpoint is *final*. The inference runner should eventually record the exact checkpoint and evidence of training completion; a filename alone is insufficient.

No change discussed here is required to rename or reuse the existing evaluated HPO artifacts.
