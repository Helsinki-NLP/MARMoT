#!/usr/bin/env python3
"""Checked eval2 -> eval3 filename migration (legacy expansion preserved)."""
# Dataset and locale tables lifted from archived eval2/bin/inf_plan.py.
import re
from dataclasses import dataclass

TRIPLES = [('bos', 'bos_Latn', ['bs_??']), ('bul', 'bul_Cyrl', ['bg_BG']), ('cat', 'cat_Latn', ['ca_ES']), ('ces', 'ces_Latn', ['cs_CZ']), ('dan', 'dan_Latn', ['da_DK']), ('deu', 'deu_Latn', ['de_DE']), ('ell', 'ell_Grek', ['el_GR']), ('est', 'ekk_Latn', ['et_EE']), ('eng', 'eng_Latn', ['en_??']), ('eus', 'eus_Latn', ['eu_??']), ('fin', 'fin_Latn', ['fi_FI']), ('fra', 'fra_Latn', ['fr_CA', 'fr_FR']), ('gle', 'gle_Latn', ['ga_??']), ('glg', 'glg_Latn', ['gl_??']), ('hrv', 'hrv_Latn', ['hr_HR']), ('hun', 'hun_Latn', ['hu_HU']), ('isl', 'isl_Latn', ['is_IS']), ('ita', 'ita_Latn', ['it_IT']), ('kat', 'kat_Geor', ['ka_??']), ('lav', 'lvs_Latn', ['lv_LV']), ('lit', 'lit_Latn', ['lt_LT']), ('mkd', 'mkd_Cyrl', ['mk_??']), ('mlt', 'mlt_Latn', ['mt_??']), ('nld', 'nld_Latn', ['nl_NL']), ('nno', 'nno_Latn', ['nn_??']), ('nob', 'nob_Latn', ['no_NO']), ('pol', 'pol_Latn', ['pl_PL']), ('por', {'default': 'por_Latn', 'flo': 'por_Latn', 'bqt': 'por_Latn', 'bqtpar': 'por_Latn_braz1246'}, ['pt_PT', 'pt_BR']), ('ron', 'ron_Latn', ['ro_RO']), ('slk', 'slk_Latn', ['sk_SK']), ('slv', 'slv_Latn', ['sl_SI']), ('spa', 'spa_Latn', ['es_MX']), ('sqi', 'als_Latn', ['sq_??']), ('srp_Cyrl', 'srp_Cyrl', ['sr_RS']), ('swe', 'swe_Latn', ['sv_SE']), ('tur', 'tur_Latn', ['tr_TR']), ('ukr', 'ukr_Cyrl', ['uk_UA'])]
DATASETS = {'flo': 'flores200', 'bqt': 'bouquet', 'bqtpar': 'bouquetpar', 'wmt': 'wmt24pp'}
LEGACY_TASK_RE = re.compile(r'^(mt|denoise|sentmt|docmt|zero)[0-9]?_([^-]+)-([^-]+)$')

class Inventory:
    def __init__(self):
        self.refs, self.dataset_refs, self.xcodes = {}, {}, {}
        self.x_to_code, self.x_to_locale = {}, {}
        for code, refs, locales in TRIPLES:
            if isinstance(refs, dict):
                self.refs[code] = refs['default']
                self.dataset_refs[code] = dict(refs)
            else:
                self.refs[code] = refs
                self.dataset_refs[code] = dict.fromkeys(('default', 'flo', 'bqt', 'bqtpar', 'wmt'), refs)
            xcodes = []
            for locale in locales:
                variant = locale.rsplit('_', 1)[-1] if '_' in locale else 'XX'
                if not variant or variant == '??' or len(locales) == 1:
                    variant = 'XX'
                xcode = f'{variant}.{code}'
                xcodes.append(xcode)
                self.x_to_code[xcode] = code
                self.x_to_locale[xcode] = locale
            self.xcodes[code] = xcodes

    def expand_legacy(self, lang):
        if '.' in lang:
            return [lang] if lang in self.x_to_code else []
        return list(self.xcodes.get(lang, ()))

    def ref(self, code, dataset):
        refs = self.dataset_refs[code]
        return refs.get(dataset, refs.get('default', self.refs[code]))


def evaluation_language(inv, code, xcode, dataset):
    # The old Bouquet Brazilian Portuguese input is por_Latn_braz1246.
    if dataset in ('bqt', 'bqtpar') and code == 'por' and inv.ref(code, dataset).endswith('_braz1246'):
        return 'por_BR'
    # The two French and Portuguese WMT24++ locales were explicit
    # in legacy extended xcodes. Single-locale xcodes (XX) stay generic,
    # consistently with the RFC's swe.fra_FR example.
    if dataset == 'wmt':
        variant = xcode.split('.', 1)[0]
        if variant != 'XX':
            return f'{code}_{variant}'
    return code


@dataclass(frozen=True)
class Case:
    task: str
    dataset: str
    tag: str
    src: str
    tgt: str
    source_xcode: str
    target_xcode: str
    oldbase: str
    newbase: str


def make_case(inv, task, prefix, src, tgt, source_xcode, target_xcode, tag):
    legacy_expanded_task = f'{prefix}_{source_xcode}-{target_xcode}' if prefix else ''
    oldbase = f'{legacy_expanded_task}.{tag}' if prefix else ''
    src_eval = evaluation_language(inv, src, source_xcode, tag)
    tgt_eval = evaluation_language(inv, tgt, target_xcode, tag)
    newbase = f'{task}.{DATASETS[tag]}.{src_eval}.{tgt_eval}'
    return Case(task, DATASETS[tag], tag, src_eval, tgt_eval,
                source_xcode, target_xcode, oldbase, newbase)


def legacy_cases(inv, task):
    # Exact legacy task-name parsing and localized expansion, including
    # the optional numeric suffix of the legacy task prefix.
    m = LEGACY_TASK_RE.match(task)
    if not m:
        raise ValueError(f'{task!r} cannot be parsed by legacy inf_plan.py; manual migration required')
    prefix, srcspec, tgtspec = m.groups()
    source_codes = inv.expand_legacy(srcspec)
    target_codes = inv.expand_legacy(tgtspec)
    if not source_codes or not target_codes:
        raise ValueError(f'{task!r} has no legacy locale expansion')
    for sx in source_codes:
        for tx in target_codes:
            src, tgt = inv.x_to_code[sx], inv.x_to_code[tx]
            for tag in DATASETS:
                yield make_case(inv, task, prefix, src, tgt, sx, tx, tag)


def new_cases(inv, task, taskconfig):
    pair = taskconfig.get('src_tgt')
    if not isinstance(pair, str) or pair.count('-') != 1:
        raise ValueError(f'{task!r} has no valid src_tgt: {pair!r}')
    src, tgt = pair.split('-', 1)
    if src not in inv.xcodes or tgt not in inv.xcodes:
        raise ValueError(f'{task!r} has no dataset mapping for src_tgt={pair!r}')
    # Generic-language datasets have one case per training task.
    for tag in ('flo', 'bqt', 'bqtpar'):
        yield make_case(inv, task, '', src, tgt, inv.xcodes[src][0], inv.xcodes[tgt][0], tag)
    # WMT24++ has distinct locale-specific files.
    for sx in inv.xcodes[src]:
        for tx in inv.xcodes[tgt]:
            yield make_case(inv, task, '', src, tgt, sx, tx, 'wmt')


def dataset_paths(inv, case, root):
    from pathlib import Path
    root = Path(root)
    src_code = inv.x_to_code[case.source_xcode]
    tgt_code = inv.x_to_code[case.target_xcode]
    tag = case.tag
    if tag == 'flo':
        directory = root / 'flores_plus' / 'devtest'
        return directory / (inv.ref(src_code, tag) + '.txt'), directory / (inv.ref(tgt_code, tag) + '.txt')
    if tag in ('bqt', 'bqtpar'):
        directory = root / ('bouquet' if tag == 'bqt' else 'bouquet_par') / 'test'
        return directory / (inv.ref(src_code, tag) + '.txt'), directory / (inv.ref(tgt_code, tag) + '.txt')
    src_locale = inv.x_to_locale[case.source_xcode]
    tgt_locale = inv.x_to_locale[case.target_xcode]
    directory = root / 'wmt24pp' / 'train'
    if src_code == 'eng':
        pair_dir = directory / f'en-{tgt_locale}'
        return pair_dir / 'source.en.txt', pair_dir / 'reference.target.txt'
    if tgt_code == 'eng':
        pair_dir = directory / f'en-{src_locale}'
        return pair_dir / 'reference.target.txt', pair_dir / 'source.en.txt'
    return (directory / f'en-{src_locale}' / 'reference.target.txt',
            directory / f'en-{tgt_locale}' / 'reference.target.txt')

import argparse
from collections import defaultdict, Counter
import hashlib
import os
from pathlib import Path
import shlex
import sys

import yaml

# Exact legacy extension names from inf_plan.py plus historic .0s variants.
# Extra legacy variants are recognized only for migration; weight stays in YAML.
EXTENSIONS = (
    ('hypotheses', '.0shyp', '.hyp'),
    ('hypotheses', '.hyp', '.hyp'),
    ('scores', '.0ssacre', '.sacre'),
    ('scores', '.sacre', '.sacre'),
    ('scores', '.0scomet', '.comet'),
    ('scores', '.comet', '.comet'),
)


def fingerprint(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.digest()


def equivalent_hypotheses(a, b):
    """Strict byte equality; no assumption from matching names or scores."""
    if a.stat().st_size != b.stat().st_size:
        return False
    return fingerprint(a) == fingerprint(b)


def quoted(*items):
    return ' '.join(shlex.quote(str(item)) for item in items)


def verify_command(a, b):
    # Recheck at execution time. `cmp` compares the COMPLETE hypothesis files.
    return f'cmp -s -- {quoted(a, b)}'


def preferred_source(dst, pairs):
    """Choose a deterministic representative, preferring matching locales."""
    def rank(pair):
        oldname = pair[1].name
        penalty = 0
        # bouquetpar with por_BR should prefer the BR rather than PT alias.
        if '.por_BR.' in dst.name and 'BR.por' not in oldname:
            penalty += 1
        return (penalty, oldname)
    return sorted(pairs, key=rank)


def main():
    p = argparse.ArgumentParser(description='Generate CHECKED mv commands for existing eval2 artifacts. Does not execute them.')
    p.add_argument('inference_yaml', type=Path)
    p.add_argument('--hyp-dir', required=True, type=Path, help='existing hypotheses directory')
    p.add_argument('--score-dir', required=True, type=Path, help='existing scores directory')
    p.add_argument('--tasks-file', type=Path, help='optional explicit training-task selection')
    p.add_argument('--out', type=Path, help='write checked shell script (default: stdout)')
    p.add_argument('--deduplicate-identical', action='store_true',
                   help='deprecated compatibility option; hypothesis collision checks are now automatic')
    p.add_argument('--keep-equivalent-aliases', action='store_true',
                   help='keep duplicate legacy hypotheses and superseded scores instead of removing them')
    args = p.parse_args()
    for field in ('inference_yaml', 'hyp_dir', 'score_dir', 'tasks_file', 'out'):
        path = getattr(args, field)
        if path is not None:
            setattr(args, field, path.resolve())
    with args.inference_yaml.open(encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    tasks = cfg.get('tasks') if isinstance(cfg, dict) else None
    if not isinstance(tasks, dict) or not tasks:
        p.error('missing tasks mapping in inference YAML')
    if args.tasks_file:
        selected = set(line.strip() for line in args.tasks_file.read_text().splitlines()
                       if line.strip() and not line.lstrip().startswith('#'))
        unknown = selected - tasks.keys()
        if unknown:
            p.error('tasks missing from inference YAML: ' + ', '.join(sorted(unknown)))
    else:
        selected = set(tasks)
    inv = Inventory()
    buckets = defaultdict(list)
    seen_old = set()
    selected_count = Counter()
    unsupported = []
    for task in sorted(selected):
        if any(char in task for char in ('/', '\\', '\n', '\r', '\t', '\0')):
            p.error(f'unsafe task name for filename scheme: {task!r}')
        try:
            cases = list(legacy_cases(inv, task))
        except ValueError as exc:
            unsupported.append(str(exc))
            continue
        # Every legacy case has exactly one target basename (whether or not the file exists).
        assert all(case.newbase.startswith(task + '.') for case in cases)
        for case in cases:
            for kind, oldext, newext in EXTENSIONS:
                base_dir = args.hyp_dir if kind == 'hypotheses' else args.score_dir
                src = base_dir / (case.oldbase + oldext)
                dst = base_dir / (case.newbase + newext)
                if not src.is_file():
                    continue
                if src in seen_old:
                    p.error(f'legacy filename reused by different tasks: {src}')
                seen_old.add(src)
                selected_count[task] += 1
                buckets[dst].append((task, src))
    if unsupported:
        print('WARNING: task names not recognized by eval2 inf_plan.py (no legacy artifacts can be inferred):', file=sys.stderr)
        for msg in unsupported:
            print('  ' + msg, file=sys.stderr)
    errors = []
    commands = []
    aliases = []
    collision_groups = 0
    hyp_duplicate_count = 0
    score_duplicate_count = 0
    for dst, pairs in sorted(buckets.items(), key=lambda item: str(item[0])):
        pairs = preferred_source(dst, pairs)
        if dst.exists() and not dst.is_file():
            errors.append(f'destination exists but is not a regular file: {dst}')
            continue
        is_hyp = dst.suffix == '.hyp'
        canonical = dst if dst.exists() else pairs[0][1]
        if len(pairs) > 1 or dst.exists():
            collision_groups += 1
        if is_hyp:
            # BOTH collisions of old names and an existing new-name output
            # must have precisely identical hypothesis content.
            nonidentical = [src for _, src in pairs
                            if src != canonical and not equivalent_hypotheses(canonical, src)]
            if nonidentical:
                errors.append(f'NON-IDENTICAL HYPOTHESES map to {dst}:\n  '
                              + '\n  '.join([str(canonical), *(str(s) for s in nonidentical)]))
                continue
            if len(pairs) > 1 or dst.exists():
                print(f'IDENTICAL HYPOTHESES: {len(pairs)} legacy source(s) for {dst}'
                      f'{" (canonical already exists)" if dst.exists() else ""}', file=sys.stderr)
        elif len(pairs) > 1 or dst.exists():
            print(f'SCORES TO RECOMPUTE: {len(pairs)} legacy score source(s) for {dst}'
                  f'{" (canonical already exists)" if dst.exists() else ""}; '
                  'score contents NOT compared', file=sys.stderr)
        if not dst.exists():
            task, src = pairs[0]
            commands.append((task, src, dst))
            rest = pairs[1:]
        else:
            rest = pairs
        for _, alias in rest:
            aliases.append((alias, dst, canonical, is_hyp))
            if is_hyp:
                hyp_duplicate_count += 1
            else:
                score_duplicate_count += 1
    # Self-integrity checks: every old file is accounted for; every target
    # starts with exact opaque task ID; no two moves can target same destination.
    assert len(seen_old) == sum(selected_count.values())
    assert len(seen_old) == sum(len(pairs) for pairs in buckets.values())
    if not errors:
        assert len(seen_old) == len(commands) + len(aliases)
    if not errors:
        move_counts = Counter(task for task, _, _ in commands)
        alias_files = {src for src, _, _, _ in aliases}
        alias_counts = Counter(task for pairs in buckets.values()
                               for task, src in pairs if src in alias_files)
        for task in selected:
            assert selected_count[task] == move_counts[task] + alias_counts[task], (
                f'per-task migration count mismatch for {task}')
    assert len({dst for _, _, dst in commands}) == len(commands)
    assert all(dst.name.startswith(task + '.') for task, _, dst in commands)
    # Each task count is derived from existing files only: it cannot be
    # required to be equal ACROSS tasks (not every task has been evaluated).
    if errors:
        for err in errors:
            print('ERROR: ' + err, file=sys.stderr)
        sys.exit('Refusing to emit a partial/unsafe rename plan; no files changed.')
    lines = ['#!/usr/bin/env bash', 'set -euo pipefail',
             '# Generated eval2 -> eval3 migration plan.',
             '# No files are modified by the planner itself.',
             '# Hypothesis collisions require byte-identical content.',
             '# Score collisions are permitted: scores MUST BE RECOMPUTED.',
             '# Do not execute while inference/scoring jobs are writing files.',
             '',
             '# Preflight every source, destination, and hypothesis collision.',
             ]
    for task, src, dst in commands:
        lines.append(f'test -f {quoted(src)} && test ! -e {quoted(dst)} || '
                     f'{{ echo {quoted("Migration preflight failed: " + str(src) + " -> " + str(dst))} >&2; exit 1; }}')
    for alias, dst, canonical, is_hyp in aliases:
        lines.append(f'test -f {quoted(alias)} && test -f {quoted(canonical)} || '
                     f'{{ echo {quoted("Migration preflight missing source: " + str(alias))} >&2; exit 1; }}')
        if is_hyp:
            lines.append(verify_command(canonical, alias) + ' || '
                         f'{{ echo {quoted("Hypothesis collision differs: " + str(alias) + " vs " + str(canonical))} >&2; exit 1; }}')
    lines += ['', '# Publish one filename per evaluation case; never overwrite a destination.']
    for task, src, dst in commands:
        lines.append(f'mv -n -- {quoted(src, dst)}')
    if aliases:
        if args.keep_equivalent_aliases:
            lines += ['', '# Legacy aliases deliberately retained:']
            for alias, dst, _, is_hyp in aliases:
                lines.append(f'# {"hypothesis" if is_hyp else "superseded score"}: {quoted(alias)} -> {quoted(dst)}')
        else:
            lines += ['', '# Clean up verified hypothesis duplicates and superseded legacy scores.']
            for alias, dst, _, is_hyp in aliases:
                if is_hyp:
                    # Recheck against the published output before removing.
                    lines.append(verify_command(dst, alias) + ' || '
                                 f'{{ echo {quoted("Refusing to delete changed hypotheses: " + str(alias))} >&2; exit 1; }}')
                lines.append(f'rm -- {quoted(alias)}')
    body = '\n'.join(lines) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(body, encoding='utf-8')
        args.out.chmod(0o755)
    else:
        sys.stdout.write(body)
    print(f'Integrity OK: {len(selected)} selected tasks; {len(seen_old)} existing legacy files; '
          f'{len(commands)} canonical renames; {hyp_duplicate_count} byte-identical hypothesis aliases; '
          f'{score_duplicate_count} unchecked score aliases; {collision_groups} collision groups',
          file=sys.stderr)
    print('IMPORTANT: migrated .sacre/.comet score outputs are historical and MUST be recomputed.',
          file=sys.stderr)
    alias_files = {src for src, _, _, _ in aliases}
    for task in sorted(selected_count):
        count = sum(t == task for t, _, _ in commands)
        aliascount = sum(t == task for pairs in buckets.values() for t, src in pairs
                         if src in alias_files)
        print(f'  {task}: {selected_count[task]} found, {count} moves, {aliascount} aliases', file=sys.stderr)
    if not seen_old:
        print('WARNING: no legacy hypothesis/score files found; no moves emitted', file=sys.stderr)

if __name__ == '__main__':
    try:
        main()
    except (OSError, yaml.YAMLError, ValueError) as e:
        sys.exit(f'ERROR: {e}')
