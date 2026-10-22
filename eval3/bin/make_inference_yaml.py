#!/usr/bin/env python3
"""Derive a single eval3 inference.yaml using the observed HPO inference profile.

The output preserves historical HPO inference settings (including train.yaml's
max_length and model_dtype), except that all tasks/vocabularies are combined,
training weights are required and retained as _training_weight, and optional
training-introduction steps as _training_introduce_at_training_step; obsolete
eval2 annotations and run-specific selectors are omitted.

Usage:
    python bin/make_inference_yaml.py TRAIN_YAML INFERENCE_YAML \
      --mammoth-type {pytorch,xtransformers}
"""
from __future__ import annotations

import argparse
import copy
import os
from pathlib import Path
import sys
import tempfile

import yaml

# Exact train-only top-level deletion list inherited from eval2/inf_plan.py.
DROP_TOP_LEVEL_KEYS = (
    'early_stopping', 'valid_timeout', 'valid_decode_timeout', 'valid_max_length',
    'tensorboard', 'tensorboard_log_dir', 'report_tflops', 'denoising_objective',
    'mask_ratio', 'mask_length', 'poisson_lambda', 'replace_length',
    'reset_optim', 'src_seq_length_min', 'tgt_seq_length_min',
    'src_seq_length_max', 'tgt_seq_length_max', 'train_steps', 'accum_count',
    'lookahead_minibatches', 'normalization', 'queue_size', 'valid_batch_size',
    'optim', 'learning_rate', 'adam_beta1', 'adam_beta2', 'weight_decay',
    'max_grad_norm', 'label_smoothing', 'warmup_steps', 'decay_method',
    'learning_rate_decay', 'start_decay_steps', 'average_decay', 'n_nodes',
    'task_distribution_strategy', 'valid_steps', 'valid_metrics',
    'save_checkpoint_steps', 'keep_checkpoint', 'log_model_structure',
    'report_every', 'report_training_accuracy', 'save_model', 'save_strategy',
)
DROP_TASK_PATHS = ('path_src', 'path_tgt', 'path_valid_src', 'path_valid_tgt')
# These existed only for eval2 expansion/debugging, not for MAMMOTH inference.
DROP_TASK_HELPERS = (
    '_template_task', '_original_train_task', '_pair_type',
    '_src_task_candidates', '_tgt_task_candidates',
)
# Execution-time values must be supplied by an inference job, not by this file.
DROP_RUN_KEYS = ('task_id', '_expanded_task', 'model', 'src', 'output')


def convert(config: dict, train_path: str | Path) -> dict:
    """Return the model-wide HPO-compatible inference configuration."""
    if not isinstance(config, dict) or not isinstance(config.get('tasks'), dict) or not config['tasks']:
        raise ValueError('train.yaml requires a nonempty tasks mapping')
    if not isinstance(config.get('src_vocab'), dict) or not isinstance(config.get('tgt_vocab'), dict):
        raise ValueError('train.yaml requires src_vocab and tgt_vocab mappings')

    result = copy.deepcopy(config)
    for key in DROP_TOP_LEVEL_KEYS + DROP_RUN_KEYS:
        result.pop(key, None)

    used_src, used_tgt = set(), set()
    rewritten = {}
    for task_id, original in config['tasks'].items():
        if not isinstance(task_id, str) or not task_id or not isinstance(original, dict):
            raise ValueError(f'invalid task definition: {task_id!r}')
        pair = original.get('src_tgt')
        if not isinstance(pair, str) or pair.count('-') != 1:
            raise ValueError(f'task {task_id!r}: src_tgt must be SOURCE-TARGET')
        source, target = pair.split('-', 1)
        if not source or not target or source not in config['src_vocab'] or target not in config['tgt_vocab']:
            raise ValueError(f'task {task_id!r}: missing vocabulary for {pair!r}')
        if 'weight' not in original or original['weight'] is None:
            raise ValueError(f'task {task_id!r}: weight must be present and non-null')
        for metadata_key in ('_training_weight', '_training_introduce_at_training_step'):
            if metadata_key in original:
                raise ValueError(f'task {task_id!r}: training metadata key {metadata_key!r} already exists')
        used_src.add(source)
        used_tgt.add(target)

        task = copy.deepcopy(original)
        # These values describe *training*, not translate.py runtime settings.
        # Move them without changing the original YAML scalar values or types.
        task['_training_weight'] = task.pop('weight')
        if 'introduce_at_training_step' in task:
            task['_training_introduce_at_training_step'] = task.pop('introduce_at_training_step')
        for key in DROP_TASK_PATHS + DROP_TASK_HELPERS:
            task.pop(key, None)
        task['src_tgt'] = pair
        task['enc_sharing_group'] = copy.deepcopy(original.get('enc_sharing_group', []))
        task['dec_sharing_group'] = copy.deepcopy(original.get('dec_sharing_group', []))
        task['transforms'] = []
        task['node_gpu'] = '0:0'
        rewritten[task_id] = task

    result['tasks'] = rewritten
    result['src_vocab'] = {k: v for k, v in config['src_vocab'].items() if k in used_src}
    result['tgt_vocab'] = {k: v for k, v in config['tgt_vocab'].items() if k in used_tgt}

    # Shared HPO/eval2 effective inference settings observed in both archived
    # mt_eng-mlt.yaml files. Keep train.yaml's max_length, model_dtype,
    # use_hf_tokenizer and report_time unchanged/absent, just as HPO did.
    result['beam_size'] = 4
    result['batch_size'] = 32
    result['batch_type'] = 'sents'
    result['gpu'] = 0
    result['world_size'] = 1
    result['gpu_ranks'] = [0]
    result['seed'] = 42
    result['_train_config'] = str(train_path)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('train_yaml', type=Path)
    ap.add_argument('inference_yaml', type=Path)
    args = ap.parse_args()
    if args.train_yaml.resolve() == args.inference_yaml.resolve():
        ap.error('input and output YAML paths must be different')

    with args.train_yaml.open(encoding='utf-8') as handle:
        cfg = yaml.safe_load(handle)
    out = convert(cfg, args.train_yaml)
    args.inference_yaml.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=args.inference_yaml.name + '.tmp.', dir=args.inference_yaml.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            yaml.safe_dump(out, handle, sort_keys=False, allow_unicode=True)
        os.replace(tmp, args.inference_yaml)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f'Wrote {args.inference_yaml}: {len(out["tasks"])} tasks; '
          f'{len(out["src_vocab"])} source / {len(out["tgt_vocab"])} target vocabularies',
          file=sys.stderr)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, yaml.YAMLError) as exc:
        sys.exit(f'ERROR: {exc}')
