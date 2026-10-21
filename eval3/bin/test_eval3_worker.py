#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import multiprocessing as mp
import os
from pathlib import Path
import sys
import tempfile

MODULE = Path(__file__).with_name('eval3_worker.py')
spec = importlib.util.spec_from_file_location('eval3_worker', MODULE)
w = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(w)


def fixture(root: Path):
    dirs = w.setup(root / 'scheduler')
    ev = root / 'model' / 'evaluation'
    for d in ('tasks', 'hypotheses', 'configs'):
        (ev / d).mkdir(parents=True, exist_ok=True)
    src = root / 'src.txt'
    ref = root / 'ref.txt'
    src.write_text('a\nb\n', encoding='utf-8')
    ref.write_text('A\nB\n', encoding='utf-8')
    config = ev / 'configs' / 'inference.yaml'
    config.write_text('tasks: {}\n', encoding='utf-8')
    mammoth = root / 'mammoth'
    mammoth.mkdir()
    (mammoth / 'translate.py').write_text(
        """import argparse\np=argparse.ArgumentParser()\nfor x in ('config','model','task_id','src','output'):\n p.add_argument('--'+x, required=True)\na=p.parse_args()\nopen(a.output,'w',encoding='utf-8').write('A\\nB\\n')\n""",
        encoding='utf-8',
    )
    task = ev / 'tasks' / 'mt_swe-fra.flores200.swe.fra.inf'
    hyp = ev / 'hypotheses' / 'mt_swe-fra.flores200.swe.fra.hyp'
    task.write_text(
        f'TASK_ID=mt_swe-fra\n'
        f'INFER_SRC={src}\n'
        f'INFER_REF={ref}\n'
        f'INFER_HYP={hyp}\n'
        f'INFERENCE_YAML={config}\n'
        f'MODEL={root / "model"}\n'
        f'MAMMOTH={mammoth}\n',
        encoding='utf-8',
    )
    return dirs, task, hyp


def compete(base: str, job: int, result: mp.Queue) -> None:
    dirs = w.setup(Path(base))
    got = w.claim_one(dirs, str(job), 0)
    result.put(got.name if got else None)


def only_queue(dirs):
    xs = list(dirs['queue'].iterdir())
    assert len(xs) == 1, xs
    return xs[0]


def run_tests() -> None:
    # 1. Atomic anonymous link: eight workers, exactly one claim.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, _ = fixture(root)
        assert w.enqueue(task, dirs, 100)
        q: mp.Queue = mp.Queue()
        ps = [mp.Process(target=compete, args=(str(root / 'scheduler'), 900000+i, q)) for i in range(8)]
        for p in ps:
            p.start()
        for p in ps:
            p.join()
            assert p.exitcode == 0
        winners = [q.get() for _ in ps]
        assert sum(x is not None for x in winners) == 1, winners
        assert not list(dirs['queue'].iterdir())
        claims = list(dirs['claims'].iterdir())
        assert len(claims) == 1
        assert '.job-' in claims[0].name

    # 2. Anonymous crash after link but before queue unlink: ctime grace holds it,
    # then recovery removes the old advertisement and returns attempt+1.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, _ = fixture(root)
        assert w.enqueue(task, dirs, 7)
        q0 = only_queue(dirs)
        anon = dirs['claims'] / q0.name
        os.link(q0, anon)
        assert w.recover(dirs, grace=10**9) == 0
        assert anon.exists() and q0.exists()
        assert w.recover(dirs, grace=0) == 1
        q1 = only_queue(dirs)
        assert '--a001--' in q1.name
        assert not list(dirs['claims'].iterdir())

    # 3. Anonymous crash after queue unlink: same ctime recovery path.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, _ = fixture(root)
        assert w.enqueue(task, dirs, 100)
        q0 = only_queue(dirs)
        anon = dirs['claims'] / q0.name
        os.link(q0, anon)
        q0.unlink()
        assert w.recover(dirs, grace=0) == 1
        assert '--a001--' in only_queue(dirs).name

    # 4. Named claim is never stolen on unknown Slurm state; terminal owner is
    # requeued with incremented attempt.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, _ = fixture(root)
        assert w.enqueue(task, dirs, 37)
        claim = w.claim_one(dirs, '900003', 0)
        assert claim is not None
        old = w.slurm_state
        try:
            w.slurm_state = lambda _job: ('unknown', 'accounting delay')
            assert w.recover(dirs, grace=0) == 0
            assert claim.exists()
            w.slurm_state = lambda _job: ('terminal', 'sacct=TIMEOUT')
            assert w.recover(dirs, grace=0) == 1
        finally:
            w.slurm_state = old
        q1 = only_queue(dirs)
        assert q1.name.startswith('P000037--') and '--a001--' in q1.name

    # 5. A later Slurm restart supersedes the previous incarnation even while
    # the allocation's job id itself still appears active.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, _ = fixture(root)
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900004', 0)
        assert claim is not None
        old = w.slurm_state
        try:
            w.slurm_state = lambda _job: ('active', 'RUNNING')
            assert w.recover(dirs, grace=10**9, current_job='900004', current_restart=1) == 1
        finally:
            w.slurm_state = old
        assert '--a001--' in only_queue(dirs).name

    # 6. Successful inference writes tmp.job-ID, validates, links final, removes
    # tmp, and removes the claim.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900005', 0)
        assert claim is not None
        assert w.execute_claim(claim, dirs, '900005', 0, sys.executable)
        assert hyp.read_text(encoding='utf-8') == 'A\nB\n'
        assert not w.attempt_path(hyp, '900005', 0).exists()
        assert not list(dirs['claims'].iterdir())
        assert not list(dirs['queue'].iterdir())
        assert task.exists()

    # 7. If canonical HYP was published before a crash, recovery removes the
    # dead claim rather than rerunning/requeueing it.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900006', 0)
        assert claim is not None
        hyp.write_text('A\nB\n', encoding='utf-8')
        old = w.slurm_state
        try:
            w.slurm_state = lambda _job: ('terminal', 'sacct=COMPLETED')
            assert w.recover(dirs, grace=0) == 1
        finally:
            w.slurm_state = old
        assert hyp.exists()
        assert not list(dirs['claims'].iterdir())
        assert not list(dirs['queue'].iterdir())

    # 8. Translation failure removes tmp, keeps stderr, and returns attempt+1.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        (root / 'mammoth' / 'translate.py').write_text('raise SystemExit(9)\n', encoding='utf-8')
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900007', 0)
        assert claim is not None
        assert not w.execute_claim(claim, dirs, '900007', 0, sys.executable)
        assert not hyp.exists()
        assert not w.attempt_path(hyp, '900007', 0).exists()
        assert '--a001--' in only_queue(dirs).name
        logs = root / 'model' / 'evaluation' / 'logs'
        assert (logs / 'job900007.mt_swe-fra.flores200.swe.fra.err').is_file()

    # 9. Inference stderr naming follows eval2/3, including legacy .0shyp,
    # while an explicit INFER_LOG can preserve an exact planner-selected name.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        final = root / 'model' / 'evaluation' / 'hypotheses' / 'zero_XX.foo-XX.bar.wmt.0shyp'
        env = {'INFER_HYP': str(final)}
        assert w.inference_log_path(env, '900008') == (
            root / 'model' / 'evaluation' / 'logs' / 'job900008.zero_XX.foo-XX.bar.wmt.err'
        )
        env['INFER_LOG'] = str(root / 'logs' / 'job${SLURM_JOB_ID}.exact.err')
        assert w.inference_log_path(env, '900008') == root / 'logs' / 'job900008.exact.err'

    # 10. A valid canonical hypothesis is completion truth: enqueue does not
    # advertise it again.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        hyp.write_text('A\nB\n', encoding='utf-8')
        assert w.valid_hyp(hyp, w.task_env(task))
        assert not w.enqueue(task, dirs, 100)
        assert not list(dirs['queue'].iterdir())

    # 11. Recheck canonical HYP after claiming.  If it appeared after queueing,
    # do not run translate.py again.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900009', 0)
        assert claim is not None
        hyp.write_text('A\nB\n', encoding='utf-8')
        (root / 'mammoth' / 'translate.py').write_text(
            "raise RuntimeError('translate must not run')\n", encoding='utf-8'
        )
        assert w.execute_claim(claim, dirs, '900009', 0, sys.executable)
        assert hyp.read_text(encoding='utf-8') == 'A\nB\n'
        assert not list(dirs['claims'].iterdir())

    # 12. A successful translate process with the wrong number of lines is not
    # publishable.  The canonical HYP stays absent and the task is requeued.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        (root / 'mammoth' / 'translate.py').write_text(
            "import sys\nopen(sys.argv[sys.argv.index('--output')+1], 'w').write('only one\\n')\n",
            encoding='utf-8',
        )
        assert w.enqueue(task, dirs, 100)
        claim = w.claim_one(dirs, '900010', 0)
        assert claim is not None
        assert not w.execute_claim(claim, dirs, '900010', 0, sys.executable)
        assert not hyp.exists()
        assert '--a001--' in only_queue(dirs).name

    # 13. A worker that fails a task once must not immediately reclaim the
    # same requeued task.  It may be retried by another/later worker.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        dirs, task, hyp = fixture(root)
        (root / 'mammoth' / 'translate.py').write_text(
            "raise SystemExit(9)\n", encoding='utf-8'
        )
        assert w.enqueue(task, dirs, 100)
        old_job = os.environ.get('SLURM_JOB_ID')
        old_restart = os.environ.get('SLURM_RESTART_COUNT')
        old_deadline = os.environ.get('EVAL3_DEADLINE_EPOCH')
        try:
            os.environ['SLURM_JOB_ID'] = '900011'
            os.environ['SLURM_RESTART_COUNT'] = '0'
            os.environ.pop('EVAL3_DEADLINE_EPOCH', None)
            assert w.run_worker(dirs, reserve=0, poll=0, grace=300, python=sys.executable) == 0
        finally:
            if old_job is None:
                os.environ.pop('SLURM_JOB_ID', None)
            else:
                os.environ['SLURM_JOB_ID'] = old_job
            if old_restart is None:
                os.environ.pop('SLURM_RESTART_COUNT', None)
            else:
                os.environ['SLURM_RESTART_COUNT'] = old_restart
            if old_deadline is None:
                os.environ.pop('EVAL3_DEADLINE_EPOCH', None)
            else:
                os.environ['EVAL3_DEADLINE_EPOCH'] = old_deadline
        assert not hyp.exists()
        q1 = only_queue(dirs)
        assert '--a001--' in q1.name
        assert not list(dirs['claims'].iterdir())

    print('PASS: claims, recovery, publication, HYP guards, and no same-worker retry storm')


if __name__ == '__main__':
    run_tests()
