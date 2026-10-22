#!/usr/bin/env python3
"""Plan eval3 score definitions from plan_eval3_inference.py's inf_plan.out TSV.

Each score Bash file is a sourceable definition; no metric is executed yet.
"""
import argparse
import csv
from pathlib import Path
import re
import shlex
import sys

FIELDS = ('basename', 'task', 'dataset', 'source_language', 'target_language',
          'source', 'reference', 'hypothesis', 'inference_script')


def quote(s):
    return shlex.quote(str(s))


def definition(row, sacre, comet, scorer):
    return '\n'.join([
        '#!/usr/bin/env bash',
        '# Generated eval3 scoring case definition (source or execute).',
        'export EVAL_BASE="${BASH_SOURCE[0]##*/}"',
        'export EVAL_BASE="${EVAL_BASE%.score.sh}"',
        f'export TASK_ID={quote(row["task"])}',
        f'export TESTSET={quote(row["dataset"])}',
        f'export TESTSET_SOURCE_LANGUAGE={quote(row["source_language"])}',
        f'export TESTSET_TARGET_LANGUAGE={quote(row["target_language"])}',
        f'export SCORE_SRC={quote(row["source"])}',
        f'export SCORE_REF={quote(row["reference"])}',
        f'export SCORE_HYP={quote(row["hypothesis"])}',
        f'export SCORE_SACRE={quote(sacre)}',
        f'export SCORE_COMET={quote(comet)}',
        f'export COMET_PROFILE={quote(scorer)}',
        '',
        '# Score commands and validated atomic publication will be added separately.',
        '',
    ])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('inf_plan', type=Path, help='TSV produced by plan_eval3_inference.py')
    p.add_argument('--score-dir', type=Path, required=True)
    p.add_argument('--out-dir', type=Path, required=True)
    p.add_argument('--comet-profile', default='', help='immutable registered COMET scorer identifier; omit to disable COMET')
    args = p.parse_args()
    for field in ('inf_plan', 'score_dir', 'out_dir'):
        setattr(args, field, getattr(args, field).resolve())
    if args.comet_profile and not re.fullmatch(r'[A-Za-z0-9_-]+', args.comet_profile):
        p.error('COMET profile must contain only letters, digits, underscores and hyphens')
    with args.inf_plan.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        if not set(FIELDS).issubset(reader.fieldnames or []):
            p.error('inf_plan.out is missing required columns')
        rows = list(reader)
    seen = set()
    outputs = []
    for row in rows:
        name = row['basename']
        expected = '.'.join(row[field] for field in ('task', 'dataset', 'source_language', 'target_language'))
        if name != expected or '/' in name or '\\' in name:
            p.error(f'inconsistent or unsafe basename: {name!r}, expected {expected!r}')
        if name in seen:
            p.error(f'duplicate basename: {name}')
        seen.add(name)
        sacre = args.score_dir / (name + '.sacre')
        comet = (args.score_dir / (name + '.comet.' + args.comet_profile + '.json')) if args.comet_profile else ''
        script = args.out_dir / (name + '.score.sh')
        content = definition(row, sacre, comet, args.comet_profile)
        if script.exists() and script.read_text(encoding='utf-8') != content:
            p.error(f'score definition already exists with different content: {script}')
        outputs.append((row, sacre, comet, script, content))
    args.score_dir.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for _, _, _, script, content in outputs:
        script.write_text(content, encoding='utf-8')
        script.chmod(0o755)
    plan = args.out_dir / 'score_plan.out'
    columns = ('basename', 'source', 'reference', 'hypothesis', 'sacre', 'comet', 'script')
    with plan.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
        writer.writeheader()
        for row, sacre, comet, script, _ in outputs:
            writer.writerow(dict(zip(columns, (row['basename'], row['source'], row['reference'],
                                               row['hypothesis'], sacre, comet, script))))
    print(f'Wrote {plan} and {len(outputs)} scoring definitions', file=sys.stderr)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, csv.Error) as e:
        sys.exit(f'ERROR: {e}')
