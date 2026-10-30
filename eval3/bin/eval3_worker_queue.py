#!/usr/bin/env python3
"""Small shared-filesystem inference worker for eval3.

Scheduler state is deliberately only:

    <base>/queue/      waiting hard links to permanent model *.inf files
    <base>/claims/     claimed hard links
    <base>/logs/       Slurm worker stdout/stderr and scheduler diagnostics

A queue entry is claimed in three filesystem operations:

    link(queue/T, claims/T)                 # anonymous exclusive claim
    unlink(queue/T)                         # stop advertising the task
    rename(claims/T, claims/T.job-J.r-R)    # identify the Slurm owner

The first link is the arbitration point: claims/T has one fixed name, so only
one worker can create it.  The anonymous state normally lasts milliseconds.
If a worker dies in that window, recovery uses the inode ctime and a generous
grace period before repairing it.

A normal named claim is recovered only when it is old enough *and* Slurm
positively reports its owner as terminal.  Recovery increments the attempt
number encoded in the scheduler filename.

Inference writes only to an attempt-specific temporary hypothesis containing
the Slurm job id.  After validation, link(tmp, final) publishes without ever
overwriting an existing canonical hypothesis.  The temporary file is then
removed.

The permanent model task definition and a valid canonical .hyp are the durable
truth.  queue/ and claims/ are disposable scheduler state.
"""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

DEFAULT_BASE = Path('/scratch/project_462001509/members/tiedeman/MARMoT/models/eval3scheduler')
REQUIRED = (
    'TASK_ID', 'INFER_SRC', 'INFER_REF', 'INFER_HYP',
    'INFERENCE_YAML', 'MODEL', 'MAMMOTH',
)
TERMINAL_STATES = {
    'BOOT_FAIL', 'CANCELLED', 'COMPLETED', 'DEADLINE', 'FAILED', 'NODE_FAIL',
    'OUT_OF_MEMORY', 'PREEMPTED', 'REVOKED', 'TIMEOUT',
}
# P000100--<stable task hash>--a000--<original basename>.inf
QUEUE_RE = re.compile(
    r'^P(?P<priority>\d{6})--(?P<key>[0-9a-f]{24})--a(?P<attempt>\d{3,})--(?P<base>.+\.inf)$'
)
# Same scheduler name followed by owner.  Restart distinguishes Slurm requeues.
CLAIM_RE = re.compile(
    r'^(?P<queue>.+\.inf)\.job-(?P<job>\d+)\.r(?P<restart>\d+)$'
)


def log(message: str) -> None:
    print(f'eval3_worker: {time.strftime("%Y-%m-%dT%H:%M:%S")} {message}', flush=True)


def setup(base: Path) -> dict[str, Path]:
    dirs = {name: base / name for name in ('queue', 'claims', 'logs')}
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    dev = dirs['queue'].stat().st_dev
    if dirs['claims'].stat().st_dev != dev:
        raise RuntimeError('queue/ and claims/ must be on the same filesystem')
    return dirs


def task_env(path: Path) -> dict[str, str]:
    """Source a trusted generated Bash assignment file."""
    proc = subprocess.run(
        ['bash', '--noprofile', '--norc', '-c', 'set -a; source "$1"; env -0', '_', str(path)],
        env={'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(
            f'cannot source {path}: {proc.stderr.decode(errors="replace").strip()}'
        )
    env: dict[str, str] = {}
    for item in proc.stdout.split(b'\0'):
        if item and b'=' in item:
            key, value = item.split(b'=', 1)
            env[key.decode(errors='surrogateescape')] = value.decode(errors='surrogateescape')
    missing = [key for key in REQUIRED if not env.get(key)]
    if missing:
        raise ValueError(f'{path}: missing task variables: {", ".join(missing)}')
    return env


def stable_key(task: Path) -> str:
    """Stable identity of a model-specific task definition."""
    absolute = str(task.resolve(strict=True))
    return hashlib.sha256(absolute.encode()).hexdigest()[:24]


def parse_queue_name(name: str) -> re.Match[str] | None:
    return QUEUE_RE.match(name)


def next_queue_name(name: str) -> str:
    m = parse_queue_name(name)
    if not m:
        raise ValueError(f'malformed scheduler task name: {name}')
    attempt = int(m.group('attempt')) + 1
    width = max(3, len(m.group('attempt')))
    return (
        f'P{m.group("priority")}--{m.group("key")}--'
        f'a{attempt:0{width}d}--{m.group("base")}'
    )


def count_lines(path: Path) -> int:
    with path.open('rb') as stream:
        return sum(1 for _ in stream)


def valid_hyp(path: Path, env: dict[str, str]) -> bool:
    """Require UTF-8, nonempty output, and matching source/reference cardinality."""
    src = Path(env['INFER_SRC'])
    ref = Path(env['INFER_REF'])
    if not (src.is_file() and ref.is_file() and path.is_file()):
        return False
    try:
        if path.stat().st_size == 0:
            return False
        n_hyp = 0
        with path.open('rb') as stream:
            for raw in stream:
                if b'\0' in raw:
                    return False
                raw.decode('utf-8', errors='strict')
                n_hyp += 1
        return n_hyp > 0 and n_hyp == count_lines(src) == count_lines(ref)
    except (OSError, UnicodeError):
        return False


def enqueue(task: Path, dirs: dict[str, Path], priority: int = 100) -> bool:
    """Create the initial a000 queue hard link for an unfinished task.

    Queue construction/reconstruction must not run concurrently with workers.
    The worker protocol itself never recreates an a000 advertisement.
    """
    task = task.resolve(strict=True)
    if task.suffix != '.inf':
        raise ValueError(f'not an .inf task: {task}')
    if task.stat().st_dev != dirs['queue'].stat().st_dev:
        raise RuntimeError(f'task and scheduler are on different filesystems: {task}')
    env = task_env(task)
    if valid_hyp(Path(env['INFER_HYP']), env):
        return False
    key = stable_key(task)
    # Do not advertise a task already represented in queue/ or claims/.
    marker = f'--{key}--'
    if any(marker in p.name for p in dirs['queue'].iterdir()):
        return False
    if any(marker in p.name for p in dirs['claims'].iterdir()):
        return False
    target = dirs['queue'] / f'P{priority:06d}--{key}--a000--{task.name}'
    try:
        os.link(task, target, follow_symlinks=False)
        return True
    except FileExistsError:
        return False


def worker_identity() -> tuple[str, int]:
    job = os.environ.get('SLURM_JOB_ID', '')
    if not job.isdecimal():
        raise RuntimeError('worker requires SLURM_JOB_ID')
    restart_text = os.environ.get('SLURM_RESTART_COUNT', '0')
    restart = int(restart_text) if restart_text.isdecimal() else 0
    return job, restart


def claim_one(dirs: dict[str, Path], job: str, restart: int) -> Path | None:
    """Claim the first queue entry using anonymous-link arbitration."""
    try:
        entries = sorted(
            p for p in dirs['queue'].iterdir()
            if p.is_file() and parse_queue_name(p.name)
        )
    except FileNotFoundError:
        return None

    for queue_path in entries:
        anonymous = dirs['claims'] / queue_path.name
        try:
            # Fixed anonymous destination is the exclusive arbitration point.
            os.link(queue_path, anonymous, follow_symlinks=False)
        except (FileExistsError, FileNotFoundError):
            continue

        try:
            # Stop advertising before the anonymous name disappears.
            queue_path.unlink()
        except FileNotFoundError:
            # We cannot prove that our queue transaction completed.  Leave the
            # anonymous link for ctime-based recovery rather than guessing.
            log(f'CLAIM HOLD {anonymous.name}: queue entry disappeared unexpectedly')
            return None

        owned = dirs['claims'] / f'{anonymous.name}.job-{job}.r{restart}'
        try:
            os.rename(anonymous, owned)
        except Exception:
            # Keep anonymous state: startup recovery can repair it after grace.
            raise
        log(f'CLAIMED {owned.name}')
        return owned
    return None


def normalize_state(state: str) -> str:
    return state.strip().split()[0].split('+')[0].upper() if state.strip() else ''


def slurm_state(job: str) -> tuple[str, str]:
    """Return active, terminal, or unknown; missing from squeue is not death."""
    if not shutil.which('squeue') or not shutil.which('sacct'):
        return 'unknown', 'squeue/sacct unavailable'

    sq = subprocess.run(
        ['squeue', '-h', '-j', job, '-o', '%T'],
        text=True, capture_output=True, check=False,
    )
    if sq.returncode != 0:
        return 'unknown', f'squeue failed: {sq.stderr.strip()}'
    states = [normalize_state(x) for x in sq.stdout.splitlines() if x.strip()]
    if states:
        return 'active', 'squeue=' + ','.join(states)

    # JobIDRaw lets us compare the numeric SLURM_JOB_ID directly, including
    # array elements, without depending on array-name formatting.
    ac = subprocess.run(
        ['sacct', '-n', '-X', '-j', job, '--format=JobIDRaw,State', '--parsable2'],
        text=True, capture_output=True, check=False,
    )
    if ac.returncode != 0:
        return 'unknown', f'sacct failed: {ac.stderr.strip()}'
    exact: list[str] = []
    for line in ac.stdout.splitlines():
        fields = line.strip().split('|')
        if len(fields) >= 2 and fields[0] == job:
            exact.append(normalize_state(fields[1]))
    if not exact:
        return 'unknown', f'no exact sacct record for job {job}'
    if all(state in TERMINAL_STATES for state in exact):
        return 'terminal', 'sacct=' + ','.join(exact)
    return 'unknown', 'sacct=' + ','.join(exact)


def requeue_claim(claim: Path, dirs: dict[str, Path], queue_name: str) -> Path:
    """Return a claim to queue with its attempt number incremented."""
    new_name = next_queue_name(queue_name)
    target = dirs['queue'] / new_name
    if target.exists():
        # A duplicate target should only be acceptable if it is the same task.
        if not os.path.samefile(claim, target):
            raise RuntimeError(f'requeue target contains a different inode: {target}')
        claim.unlink()
    else:
        os.rename(claim, target)
    log(f'REQUEUED {queue_name} -> {new_name}')
    return target


def recover(dirs: dict[str, Path], grace: int, current_job: str | None = None,
            current_restart: int = 0) -> int:
    """Recover stale anonymous claims and claims whose Slurm owner is dead."""
    now = time.time()
    repaired = 0

    # Anonymous claim names are exactly queue names.  ctime is inode ctime:
    # link()/unlink() update it.  It is used only as a conservative grace gate
    # for the millisecond-sized transaction that has no owner id yet.
    for claim in sorted(dirs['claims'].iterdir()):
        if not claim.is_file() or not parse_queue_name(claim.name):
            continue
        try:
            age = now - claim.stat().st_ctime
        except FileNotFoundError:
            continue
        if age < grace:
            continue
        old_queue = dirs['queue'] / claim.name
        if old_queue.exists():
            try:
                if not os.path.samefile(claim, old_queue):
                    log(f'RECOVERY HOLD {claim.name}: queue path is a different inode')
                    continue
                # Hide the old advertisement first.  The anonymous claim stays
                # in place as the exclusive lock until it is renamed to a+1.
                old_queue.unlink()
            except FileNotFoundError:
                pass
        try:
            requeue_claim(claim, dirs, claim.name)
            repaired += 1
        except FileNotFoundError:
            pass

    # Named claims have a Slurm owner.  Age merely delays investigation; only
    # a terminal Slurm state (or a later restart of this same job) permits it.
    for claim in sorted(dirs['claims'].iterdir()):
        if not claim.is_file():
            continue
        m = CLAIM_RE.match(claim.name)
        if not m or not parse_queue_name(m.group('queue')):
            continue
        try:
            age = now - claim.stat().st_ctime
        except FileNotFoundError:
            continue
        owner_job = m.group('job')
        owner_restart = int(m.group('restart'))
        superseded = (
            current_job is not None
            and owner_job == current_job
            and owner_restart < current_restart
        )
        if age < grace and not superseded:
            continue
        if superseded:
            classification, detail = 'terminal', 'superseded by later Slurm restart'
        else:
            classification, detail = slurm_state(owner_job)
        if classification != 'terminal':
            if classification == 'unknown':
                log(f'RECOVERY HOLD {claim.name}: owner not proven dead ({detail})')
            continue

        try:
            env = task_env(claim)
            final = Path(env['INFER_HYP'])
            if valid_hyp(final, env):
                claim.unlink()
                log(f'RECOVERED completed claim {claim.name}: {final}')
            else:
                requeue_claim(claim, dirs, m.group('queue'))
            repaired += 1
        except FileNotFoundError:
            pass
        except Exception as exc:
            log(f'RECOVERY HOLD {claim.name}: {exc}')
    return repaired


def attempt_path(final: Path, job: str, restart: int) -> Path:
    """Attempt output beside the final, carrying the Slurm worker identity."""
    return final.with_name(f'{final.name}.tmp.job-{job}.r{restart}')


def inference_log_path(env: dict[str, str], job: str) -> Path:
    """Return the model-local per-inference stderr path used by eval2/3.

    An optional INFER_LOG in the task definition wins.  It may contain the
    literal ${SLURM_JOB_ID}.  Otherwise derive evaluation/logs/jobJ.BASE.err
    from INFER_HYP, stripping the legacy .hyp or .0shyp suffix.
    """
    explicit = env.get('INFER_LOG', '')
    if explicit:
        explicit = explicit.replace('${SLURM_JOB_ID}', job).replace('$SLURM_JOB_ID', job)
        return Path(explicit)

    final = Path(env['INFER_HYP'])
    name = final.name
    if name.endswith('.0shyp'):
        base = name[:-len('.0shyp')]
    elif name.endswith('.hyp'):
        base = name[:-len('.hyp')]
    else:
        base = name
    logdir = Path(env.get('LOGDIR', str(final.parent.parent / 'logs')))
    return logdir / f'job{job}.{base}.err'


def run_translation(claim: Path, env: dict[str, str], attempt: Path,
                    python: str, dirs: dict[str, Path], job: str, restart: int) -> Path:
    attempt.unlink(missing_ok=True)
    stderr = inference_log_path(env, job)
    stderr.parent.mkdir(parents=True, exist_ok=True)
    command = [
        python, '-u', str(Path(env['MAMMOTH']) / 'translate.py'),
        '--config', env['INFERENCE_YAML'],
        '--model', env['MODEL'],
        '--task_id', env['TASK_ID'],
        '--src', env['INFER_SRC'],
        '--output', str(attempt),
    ]
    log('RUN ' + ' '.join(command))
    with stderr.open('ab') as err:
        err.write(
            f'\n=== job={job} restart={restart} time={time.strftime("%Y-%m-%dT%H:%M:%S")} ===\n'.encode()
        )
        err.flush()
        proc = subprocess.run(command, stderr=err, check=False)
    if proc.returncode:
        raise RuntimeError(f'translate.py exited {proc.returncode}; stderr={stderr}')
    if not valid_hyp(attempt, env):
        raise RuntimeError(f'invalid inference attempt: {attempt}; stderr={stderr}')
    # Make file contents durable before publishing the directory entry.
    with attempt.open('rb') as stream:
        os.fsync(stream.fileno())
    return stderr


def publish(attempt: Path, final: Path, env: dict[str, str]) -> None:
    """First valid writer wins; never replace an existing canonical hypothesis."""
    try:
        os.link(attempt, final, follow_symlinks=False)
        log(f'PUBLISHED {final}')
    except FileExistsError:
        if not valid_hyp(final, env):
            raise RuntimeError(f'canonical hypothesis exists but is invalid: {final}')
        log(f'canonical hypothesis already valid: {final}')
    # User-requested protocol: after successful/accepted publication, remove tmp.
    attempt.unlink(missing_ok=True)


def execute_claim(claim: Path, dirs: dict[str, Path], job: str, restart: int,
                  python: str) -> bool:
    """Execute one named claim.  Return True on completion, False on retry."""
    m = CLAIM_RE.match(claim.name)
    if not m:
        raise ValueError(f'not a named claim: {claim}')
    env = task_env(claim)
    final = Path(env['INFER_HYP'])
    if valid_hyp(final, env):
        claim.unlink(missing_ok=True)
        log(f'ALREADY COMPLETE {final}')
        return True
    if final.exists():
        raise RuntimeError(f'canonical hypothesis exists but is invalid; refusing overwrite: {final}')
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.parent.stat().st_dev != claim.stat().st_dev:
        raise RuntimeError(f'claim and hypothesis must share a filesystem: {claim} vs {final}')

    attempt = attempt_path(final, job, restart)
    try:
        run_translation(claim, env, attempt, python, dirs, job, restart)
        publish(attempt, final, env)
        claim.unlink(missing_ok=True)
        return True
    except Exception as exc:
        # Do not publish a failed/invalid attempt.  Remove it as requested; the
        # model-local inference stderr log remains.  Requeue with incremented attempt.
        attempt.unlink(missing_ok=True)
        log(f'FAILED {claim.name}: {exc}')
        try:
            requeue_claim(claim, dirs, m.group('queue'))
        except FileNotFoundError:
            pass
        return False


def run_worker(dirs: dict[str, Path], reserve: int, poll: int, grace: int,
               python: str) -> int:
    job, restart = worker_identity()
    recover(dirs, grace, current_job=job, current_restart=restart)

    deadline_text = os.environ.get('EVAL3_DEADLINE_EPOCH', '')
    deadline = int(deadline_text) if deadline_text.isdecimal() else 0
    while True:
        if deadline and deadline - time.time() < reserve:
            log(f'STOP: less than {reserve}s remain; no new task will be claimed')
            return 0

        claim = claim_one(dirs, job, restart)
        if claim is None:
            # Recovery is useful when the queue appears empty: a dead worker may
            # be holding the only remaining task.
            recover(dirs, grace, current_job=job, current_restart=restart)
            claim = claim_one(dirs, job, restart)
            if claim is None:
                if poll <= 0:
                    return 0
                time.sleep(poll)
                continue
        execute_claim(claim, dirs, job, restart, python)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('setup')

    p_enq = sub.add_parser('enqueue')
    p_enq.add_argument('task', type=Path)
    p_enq.add_argument('--priority', type=int, default=100)

    p_rec = sub.add_parser('recover')
    p_rec.add_argument('--grace', type=int, default=300)
    p_rec.add_argument('--current-job')
    p_rec.add_argument('--current-restart', type=int, default=0)

    p_run = sub.add_parser('run')
    p_run.add_argument('--reserve', type=int, default=900)
    p_run.add_argument('--poll', type=int, default=15)
    p_run.add_argument('--grace', type=int, default=300)
    p_run.add_argument('--python', default=sys.executable)

    args = parser.parse_args()
    dirs = setup(args.base)
    if args.command == 'setup':
        return 0
    if args.command == 'enqueue':
        changed = enqueue(args.task, dirs, args.priority)
        log(('ENQUEUED ' if changed else 'NOT ENQUEUED ') + str(args.task))
        return 0
    if args.command == 'recover':
        n = recover(dirs, args.grace, args.current_job, args.current_restart)
        log(f'RECOVERY repaired={n}')
        return 0
    if args.command == 'run':
        return run_worker(dirs, args.reserve, args.poll, args.grace, args.python)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
