#!/usr/bin/env python3
"""Optimize node:gpu assignments for modular encoder-decoder training.

Each task in the train yaml declares encoder/decoder sharing groups, which we
treat as component sets (namespaced: "enc:<group>", "dec:<group>").  Tasks
assigned to the same GPU must co-reside all of their components there; likewise
for all GPUs of a compute node.

Objectives, lexicographically:
  1. minimize  max over GPUs of |union of components of tasks on that GPU|
  2. minimize  max over nodes of |union of components of tasks on that node|

Tasks are strictly balanced: every GPU hosts floor(T/G) or ceil(T/G) tasks.

Solved exactly with OR-Tools CP-SAT (two lexicographic phases) using canonical
first-use symmetry breaking (GPUs interchangeable in phase 1; nodes and
within-node GPUs in phase 2).  A scipy/HiGHS MILP is available as
--backend scipy fallback; --greedy-only runs just the fast heuristic.
"""

import argparse
import math
import random
import re
import sys
import time
from collections import Counter, defaultdict

import yaml

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


# --------------------------------------------------------------------------
# problem extraction
# --------------------------------------------------------------------------

def load_tasks(path):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    tasks = cfg.get("tasks") or {}
    if not tasks:
        sys.exit(f"no tasks found in {path}")
    comp_of = {}
    for name, t in tasks.items():
        enc = [f"enc:{g}" for g in (t.get("enc_sharing_group") or [])]
        dec = [f"dec:{g}" for g in (t.get("dec_sharing_group") or [])]
        comp_of[name] = sorted(set(enc + dec))
    return cfg, comp_of


def warn_duplicate_tasks(path):
    """yaml silently collapses duplicate task keys; flag them."""
    counts = Counter()
    in_tasks = False
    task_re = re.compile(r"^  (\S+):\s*$")
    sec_re = re.compile(r"^([A-Za-z_]\w*):")
    with open(path) as f:
        for line in f:
            if line.rstrip("\n") == "tasks:":
                in_tasks = True
                continue
            if in_tasks and sec_re.match(line):
                break
            m = task_re.match(line.rstrip("\n"))
            if m:
                counts[m.group(1)] += 1
    dups = {k: v for k, v in counts.items() if v > 1}
    if dups:
        print("WARNING: duplicate task names in yaml (later definition wins, "
              "all copies get the same assignment):")
        for k, v in sorted(dups.items()):
            print(f"  {k}: defined {v} times")
    return counts


def assignment_metrics(assign, comp_of, gpus_per_node, n_nodes, n_gpus):
    """Per-GPU/per-node distinct-component counts and loads."""
    gpu_comps = [set() for _ in range(n_gpus)]
    node_comps = [set() for _ in range(n_nodes)]
    gpu_load = [0] * n_gpus
    for task, g in assign.items():
        gpu_comps[g].update(comp_of[task])
        gpu_load[g] += 1
        node_comps[g // gpus_per_node].update(comp_of[task])
    gpu_counts = [len(s) for s in gpu_comps]
    node_counts = [len(s) for s in node_comps]
    return {
        "gpu_comps": gpu_comps,
        "node_comps": node_comps,
        "gpu_load": gpu_load,
        "gpu_counts": gpu_counts,
        "node_counts": node_counts,
        "max_gpu": max(gpu_counts),
        "max_node": max(node_counts),
    }


# --------------------------------------------------------------------------
# greedy constructive + local search (fast feasible solutions / CP-SAT hints)
# --------------------------------------------------------------------------

def greedy_assignment(comp_of, n_gpus, gpus_per_node, n_nodes):
    tasks = list(comp_of)
    freq = Counter(c for s in comp_of.values() for c in s)
    # rarest-component-first: tasks whose scarcest component is rare go first
    order = sorted(tasks, key=lambda t: (min(freq[c] for c in comp_of[t]),
                                         -len(comp_of[t]), t))
    T = len(tasks)
    lo = T // n_gpus
    hi = math.ceil(T / n_gpus)

    assign = {}
    gpu_comps = [set() for _ in range(n_gpus)]
    gpu_load = [0] * n_gpus

    def feasible(load):
        need = sum(max(0, lo - l) for l in load)
        return need <= (T - sum(load))

    for idx, t in enumerate(order):
        best = None
        for g in range(n_gpus):
            if gpu_load[g] >= hi:
                continue
            new = len(set(comp_of[t]) - gpu_comps[g])
            load2 = gpu_load[:]
            load2[g] += 1
            if not feasible(load2):
                continue
            key = (new, len(gpu_comps[g]), gpu_load[g], g)
            if best is None or key < best[0]:
                best = (key, g)
        g = best[1] if best else max(range(n_gpus), key=lambda gg: -gpu_load[gg])
        assign[t] = g
        gpu_comps[g].update(comp_of[t])
        gpu_load[g] += 1

    # repair any GPU below the floor quota (steal from the most loaded GPU)
    for g in range(n_gpus):
        while gpu_load[g] < lo:
            src = max(range(n_gpus), key=lambda gg: (gpu_load[gg], len(gpu_comps[gg])))
            if gpu_load[src] <= lo:
                break
            t = min((t2 for t2, gg in assign.items() if gg == src),
                    key=lambda t2: len(set(comp_of[t2]) - gpu_comps[g]))
            assign[t] = g
            gpu_comps[src] = set()
            for t2, gg in assign.items():
                if gg == src:
                    gpu_comps[src].update(comp_of[t2])
            gpu_comps[g].update(comp_of[t])
            gpu_load[src] -= 1
            gpu_load[g] += 1
    return assign


def local_search(comp_of, assign, n_gpus, gpus_per_node, n_nodes,
                 max_rounds=500, seed=0, mode="gpu", gpu_cap=None, kicks=5):
    """Iterated first-improvement local search over pairwise task swaps.

    mode="gpu": lexicographic (max_gpu, max_node, sum_gpu).
    mode="node": lexicographic (max_node, sum_node, max_gpu), restricted to
    assignments whose max_gpu stays <= gpu_cap (polishes the phase-2 hint
    under the proven phase-1 cap).  Random kicks escape local optima.
    """
    rng = random.Random(seed)
    tasks = list(comp_of)
    cset = {t: frozenset(comp_of[t]) for t in tasks}
    cap = gpu_cap if gpu_cap is not None else float("inf")

    gpu_tasks = [[] for _ in range(n_gpus)]
    for t in tasks:
        gpu_tasks[assign[t]].append(t)

    def gset(g):
        s = set()
        for t in gpu_tasks[g]:
            s |= cset[t]
        return s

    gpu_comps = [gset(g) for g in range(n_gpus)]
    gpu_counts = [len(s) for s in gpu_comps]

    def recompute_node(n):
        s = set()
        for g in range(n * gpus_per_node, (n + 1) * gpus_per_node):
            s |= gpu_comps[g]
        node_counts[n] = len(s)

    node_counts = [0] * n_nodes
    for n in range(n_nodes):
        recompute_node(n)

    def objective():
        if mode == "node":
            return (max(node_counts), sum(node_counts), max(gpu_counts))
        return (max(gpu_counts), max(node_counts), sum(gpu_counts))

    def snapshot():
        return ([l[:] for l in gpu_tasks], [s.copy() for s in gpu_comps],
                gpu_counts[:], node_counts[:])

    def restore(st):
        gt, gc, gcn, nc = st
        for i in range(n_gpus):
            gpu_tasks[i], gpu_comps[i] = gt[i][:], gc[i].copy()
            gpu_counts[i] = gcn[i]
        for n in range(n_nodes):
            node_counts[n] = nc[n]

    best_state = snapshot()
    best = objective()

    def apply_swap(g1, g2, t1, t2):
        """Swap t1 (on g1) with t2 (on g2); unions recomputed exactly
        (set-difference math would be wrong when components are shared)."""
        gpu_tasks[g1].remove(t1)
        gpu_tasks[g1].append(t2)
        gpu_tasks[g2].remove(t2)
        gpu_tasks[g2].append(t1)
        s1, s2 = gset(g1), gset(g2)
        gpu_comps[g1], gpu_comps[g2] = s1, s2
        gpu_counts[g1], gpu_counts[g2] = len(s1), len(s2)
        recompute_node(g1 // gpus_per_node)
        recompute_node(g2 // gpus_per_node)

    def scan():
        """First-improvement scan; restarts after each accepted swap."""
        nonlocal best, best_state
        pairs = [(a, b) for a in range(n_gpus) for b in range(a + 1, n_gpus)]
        rng.shuffle(pairs)
        for g1, g2 in pairs:
            for t1 in gpu_tasks[g1][:]:
                for t2 in gpu_tasks[g2][:]:
                    apply_swap(g1, g2, t1, t2)
                    if mode == "node" and (gpu_counts[g1] > cap
                                           or gpu_counts[g2] > cap):
                        apply_swap(g1, g2, t2, t1)  # revert
                        continue
                    if objective() < best:
                        best = objective()
                        assign[t1], assign[t2] = g2, g1
                        best_state = snapshot()
                        return True
                    apply_swap(g1, g2, t2, t1)  # revert
        return False

    stall = 0
    for _ in range(max_rounds):
        if scan():
            stall = 0
            continue
        for _ in range(kicks):  # local optimum: random perturbation
            g1, g2 = rng.sample(range(n_gpus), 2)
            if not gpu_tasks[g1] or not gpu_tasks[g2]:
                continue
            t1 = rng.choice(gpu_tasks[g1])
            t2 = rng.choice(gpu_tasks[g2])
            apply_swap(g1, g2, t1, t2)
            if mode == "node" and (gpu_counts[g1] > cap or gpu_counts[g2] > cap):
                apply_swap(g1, g2, t2, t1)  # revert
                continue
            assign[t1], assign[t2] = g2, g1
        stall += 1
        if stall >= 20:
            break
    restore(best_state)
    # rebuild assign from the restored best state (kicks may have moved it)
    for t in list(assign):
        del assign[t]
    for g in range(n_gpus):
        for t in gpu_tasks[g]:
            assign[t] = g
    return assign


def canonicalize(assign, tasks, gpus_per_node):
    """Relabel nodes and within-node GPUs in first-use order; objective
    preserving and satisfying the solver's symmetry-breaking constraints."""
    node_map, gpu_map, out = {}, {}, {}
    for t in tasks:  # tasks in canonical (yaml) order
        n, w = divmod(assign[t], gpus_per_node)
        nn = node_map.setdefault(n, len(node_map))
        key = (nn, w)
        if key not in gpu_map:
            gpu_map[key] = sum(1 for k in gpu_map if k[0] == nn)
        out[t] = nn * gpus_per_node + gpu_map[key]
    return out


# --------------------------------------------------------------------------
# CP-SAT exact solver
# --------------------------------------------------------------------------

def solve_cpsat(comp_of, n_nodes, gpus_per_node, time_limit, seed, log,
                workers, break_symmetry, hint_assign, ls_rounds=5000,
                time_limit2=None, ls_seeds=12, ls_kicks=5):
    from ortools.sat.python import cp_model

    tasks = list(comp_of)
    T = len(tasks)
    n_gpus = n_nodes * gpus_per_node
    lo, rem = divmod(T, n_gpus)
    hi = lo + (1 if rem else 0)

    all_comps = sorted({c for s in comp_of.values() for c in s})
    # universal components sit on every non-empty GPU/node: constant, drop them
    universal = {c for c in all_comps
                 if all(c in s for s in comp_of.values())}
    comps = [c for c in all_comps if c not in universal]
    ck = {c: k for k, c in enumerate(comps)}
    C = len(comps)
    comp_tasks = {c: [i for i, t in enumerate(tasks) if c in comp_of[t]] for c in comps}

    def build(phase, gpu_cap=None):
        """phase 1: full GPU canonical labeling; phase 2: node + within-node."""
        m = cp_model.CpModel()
        x = [[m.NewBoolVar(f"x_{i}_{g}") for g in range(n_gpus)] for i in range(T)]
        for i in range(T):
            m.Add(sum(x[i]) == 1)
        for g in range(n_gpus):
            m.Add(sum(x[i][g] for i in range(T)) >= lo)
            m.Add(sum(x[i][g] for i in range(T)) <= hi)

        if break_symmetry:
            glab = [sum(g * x[i][g] for g in range(n_gpus)) for i in range(T)]
            if phase == 1:
                # w.l.o.g. GPUs are introduced in order of first use
                m.Add(glab[0] == 0)
                for i in range(1, T):
                    m.Add(glab[i] <= glab[i - 1] + 1)
            else:
                # w.l.o.g. nodes introduced in order; within a node, its GPUs
                # introduced in order by first task of that node in yaml order
                nlab = [sum((g // gpus_per_node) * x[i][g]
                            for g in range(n_gpus)) for i in range(T)]
                wlab = [sum((g % gpus_per_node) * x[i][g]
                            for g in range(n_gpus)) for i in range(T)]
                m.Add(nlab[0] == 0)
                m.Add(wlab[0] == 0)
                for i in range(1, T):
                    m.Add(nlab[i] <= nlab[i - 1] + 1)
                    m.Add(wlab[i] <= wlab[i - 1] + 1
                          - gpus_per_node * (nlab[i] - nlab[i - 1]))

        y = [[m.NewBoolVar(f"y_{g}_{k}") for k in range(C)] for g in range(n_gpus)]
        for c in comps:
            k = ck[c]
            for g in range(n_gpus):
                ts = comp_tasks[c]
                for i in ts:
                    m.Add(y[g][k] >= x[i][g])
                if ts:
                    m.Add(y[g][k] <= sum(x[i][g] for i in ts))
                else:
                    m.Add(y[g][k] == 0)
        Mgpu = m.NewIntVar(0, C, "Mgpu")
        for g in range(n_gpus):
            m.Add(sum(y[g]) <= Mgpu)

        z = [[m.NewBoolVar(f"z_{n}_{k}") for k in range(C)] for n in range(n_nodes)]
        for n in range(n_nodes):
            gs = range(n * gpus_per_node, (n + 1) * gpus_per_node)
            for c in comps:
                k = ck[c]
                for i in comp_tasks[c]:
                    for g in gs:
                        m.Add(z[n][k] >= x[i][g])
        Mnode = m.NewIntVar(0, C, "Mnode")
        for n in range(n_nodes):
            m.Add(sum(z[n]) <= Mnode)
        if gpu_cap is not None:
            m.Add(Mgpu <= gpu_cap)
        return m, x, Mgpu, Mnode

    def add_hint(m, x, Mgpu, Mnode, hint):
        hm = assignment_metrics(hint, comp_of, gpus_per_node, n_nodes, n_gpus)
        for i, t in enumerate(tasks):
            for g in range(n_gpus):
                m.AddHint(x[i][g], 1 if hint[t] == g else 0)
        m.AddHint(Mgpu, hm["max_gpu"] - len(universal))
        m.AddHint(Mnode, hm["max_node"] - len(universal))

    def make_solver(tl=None):
        sv = cp_model.CpSolver()
        sv.parameters.max_time_in_seconds = tl if tl is not None else time_limit
        sv.parameters.random_seed = seed
        sv.parameters.num_search_workers = workers
        sv.parameters.log_search_progress = log
        return sv

    n_univ = len(universal)

    # ---- phase 1: minimize max components per GPU
    m1, x1, Mg1, Mn1 = build(1)
    add_hint(m1, x1, Mg1, Mn1, hint_assign)
    m1.Minimize(Mg1)
    s = make_solver()
    t0 = time.time()
    st1 = s.Solve(m1)
    t_phase1 = time.time() - t0
    if st1 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sys.exit(f"phase 1 solve failed: {s.StatusName(st1)}")
    opt_gpu = s.Value(Mg1) + n_univ
    bound_gpu = s.BestObjectiveBound() + n_univ
    print(f"phase 1 (min max/GPU): {s.StatusName(st1)}  value={opt_gpu}  "
          f"bound={bound_gpu:.1f}  ({t_phase1:.1f}s)", flush=True)

    # ---- phase 2 hint polish: local search optimizing the node objective
    # under the proven phase-1 cap, several seeds, best kept
    t0 = time.time()
    p2_hint, p2_key = None, None
    for sd in range(seed, seed + ls_seeds):
        cand = local_search(comp_of, dict(hint_assign), n_gpus, gpus_per_node,
                            n_nodes, max_rounds=ls_rounds, seed=sd,
                            mode="node", gpu_cap=opt_gpu, kicks=ls_kicks)
        cand = canonicalize(cand, tasks, gpus_per_node)
        cm = assignment_metrics(cand, comp_of, gpus_per_node, n_nodes, n_gpus)
        key = (cm["max_node"], cm["max_gpu"])
        if p2_key is None or key < p2_key:
            p2_hint, p2_key = cand, key
    print(f"phase-2 hint (local search, cap={opt_gpu}): max/node={p2_key[0]} "
          f"max/GPU={p2_key[1]}  ({time.time() - t0:.1f}s)", flush=True)

    # ---- phase 2: with max-per-GPU fixed at optimum, minimize max per node
    m2, x2, Mg2, Mn2 = build(2, gpu_cap=opt_gpu - n_univ)
    add_hint(m2, x2, Mg2, Mn2, p2_hint)
    m2.Minimize(Mn2)
    s2 = make_solver(time_limit2)
    t0 = time.time()
    st2 = s2.Solve(m2)
    t_phase2 = time.time() - t0
    if st2 not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sys.exit(f"phase 2 solve failed: {s2.StatusName(st2)}")
    print(f"phase 2 (min max/node): {s2.StatusName(st2)}  "
          f"value={s2.Value(Mn2) + n_univ}  "
          f"bound={s2.BestObjectiveBound() + n_univ:.1f}  ({t_phase2:.1f}s)",
          flush=True)

    assign = {tasks[i]: g for i in range(T) for g in range(n_gpus)
              if s2.Value(x2[i][g]) == 1}
    # keep whichever is lexicographically better: solver result vs polished hint
    am = assignment_metrics(assign, comp_of, gpus_per_node, n_nodes, n_gpus)
    used_hint = (am["max_node"], am["max_gpu"]) > p2_key
    if used_hint:
        assign = p2_hint
        am = assignment_metrics(assign, comp_of, gpus_per_node, n_nodes, n_gpus)
    sol2_val = am["max_node"]
    sol2_bound = s2.BestObjectiveBound() + n_univ
    phase2_proven = (st2 == cp_model.OPTIMAL or (sol2_val <= sol2_bound + 1e-12))
    info = {
        "backend": "cpsat",
        "phase1_status": s.StatusName(st1),
        "phase1_proven_optimal": st1 == cp_model.OPTIMAL,
        "phase1_bound": bound_gpu,
        "opt_max_gpu": opt_gpu,
        "phase1_time": t_phase1,
        "phase2_status": s2.StatusName(st2),
        "phase2_proven_optimal": phase2_proven,
        "phase2_bound": sol2_bound,
        "opt_max_node": sol2_val,
        "phase2_time": t_phase2,
        "phase2_used_hint": used_hint,
    }
    return assign, info


# --------------------------------------------------------------------------
# scipy / HiGHS MILP fallback
# --------------------------------------------------------------------------

def solve_scipy(comp_of, n_nodes, gpus_per_node, time_limit, seed, log):
    import numpy as np
    from scipy.optimize import Bounds, LinearConstraint, milp
    from scipy.sparse import lil_matrix

    tasks = list(comp_of)
    T, N, gpp = len(tasks), n_nodes, gpus_per_node
    G = N * gpp
    lo, rem = divmod(T, G)
    hi = lo + (1 if rem else 0)
    comps = sorted({c for s in comp_of.values() for c in s})
    C = len(comps)
    ck = {c: k for k, c in enumerate(comps)}
    comp_tasks = {c: [i for i, t in enumerate(tasks) if c in comp_of[t]] for c in comps}

    nx, ny, nz = T * G, G * C, N * C
    ix = lambda i, g: i * G + g
    iy = lambda g, k: nx + g * C + k
    iz = lambda n, k: nx + ny + n * C + k
    iMg, iMn = nx + ny + nz, nx + ny + nz + 1
    nvar = nx + ny + nz + 2

    rows, lb, ub = [], [], []

    def add(cells, l, u):
        r = defaultdict(float)
        for j, v in cells:
            r[j] += v
        rows.append(r)
        lb.append(l)
        ub.append(u)

    for i in range(T):
        add([(ix(i, g), 1.0) for g in range(G)], 1.0, 1.0)
    for g in range(G):
        add([(ix(i, g), 1.0) for i in range(T)], float(lo), float(hi))
    glab = lambda i: [(ix(i, g), float(g)) for g in range(G)]
    add(glab(0), 0.0, 0.0)                                 # canonical labeling
    for i in range(1, T):                                  # (full symmetry)
        add(glab(i) + [(j, -1.0) for j, _ in glab(i - 1)], -np.inf, 1.0)
    for c in comps:
        k = ck[c]
        for g in range(G):
            ts = comp_tasks[c]
            for i in ts:                                   # y >= x
                add([(iy(g, k), 1.0), (ix(i, g), -1.0)], 0.0, np.inf)
            if ts:                                         # y <= sum x
                add([(iy(g, k), 1.0)] + [(ix(i, g), -1.0) for i in ts],
                    -np.inf, 0.0)
            else:
                add([(iy(g, k), 1.0)], 0.0, 0.0)
    for g in range(G):                                     # Mgpu >= sum y
        add([(iy(g, k), 1.0) for k in range(C)] + [(iMg, -1.0)], -np.inf, 0.0)
    for n in range(N):
        gs = range(n * gpp, (n + 1) * gpp)
        for c in comps:
            k = ck[c]
            for i in comp_tasks[c]:
                for g in gs:                               # z >= x
                    add([(iz(n, k), 1.0), (ix(i, g), -1.0)], 0.0, np.inf)
    for n in range(N):                                     # Mnode >= sum z
        add([(iz(n, k), 1.0) for k in range(C)] + [(iMn, -1.0)], -np.inf, 0.0)

    A = lil_matrix((len(rows), nvar))
    for r, d in enumerate(rows):
        for j, v in d.items():
            A[r, j] = v
    A = A.tocsr()

    bounds = Bounds(np.zeros(nvar), np.ones(nvar))
    bounds.ub[iMg] = C
    bounds.ub[iMn] = C
    integrality = np.ones(nvar)
    opts = {"time_limit": time_limit, "mip_rel_gap": 0.0,
            "presolve": True, "disp": log}

    def run(obj, extra=None):
        Ause, lbuse, ubuse = A, np.array(lb), np.array(ub)
        if extra is not None:
            Ause = np.vstack([Ause, extra[0]])
            lbuse = np.concatenate([lbuse, extra[1]])
            ubuse = np.concatenate([ubuse, extra[2]])
        c = np.zeros(nvar)
        c[obj] = 1.0
        return milp(c=c, constraints=LinearConstraint(Ause, lbuse, ubuse),
                    bounds=bounds, integrality=integrality, options=opts)

    r1 = run(iMg)
    if not r1.success:
        sys.exit(f"scipy phase 1 failed: {r1.message}")
    opt_gpu = int(round(r1.x[iMg]))
    extra = (np.array([[1.0 if j == iMg else 0.0 for j in range(nvar)]]),
             np.array([-np.inf]), np.array([float(opt_gpu)]))
    r2 = run(iMn, extra)
    if not r2.success:
        sys.exit(f"scipy phase 2 failed: {r2.message}")
    xsol = r2.x[:nx].reshape(T, G)
    assign = {tasks[i]: int(np.argmax(xsol[i])) for i in range(T)}
    info = {
        "backend": "scipy",
        "phase1_status": r1.message,
        "phase1_proven_optimal": r1.status == 0,
        "phase1_bound": opt_gpu,
        "opt_max_gpu": opt_gpu,
        "phase1_time": None,
        "phase2_status": r2.message,
        "phase2_proven_optimal": r2.status == 0,
        "phase2_bound": int(round(r2.x[iMn])),
        "opt_max_node": int(round(r2.x[iMn])),
        "phase2_time": None,
    }
    return assign, info


# --------------------------------------------------------------------------
# reporting + yaml rewrite
# --------------------------------------------------------------------------

def print_report(title, m, gpus_per_node, n_nodes):
    print(f"\n=== {title} ===")
    print(f"max distinct components per GPU : {m['max_gpu']}")
    print(f"max distinct components per node: {m['max_node']}")
    sc = sorted(m['gpu_counts'])
    print(f"components per GPU  (min/median/max): "
          f"{sc[0]}/{sc[len(sc)//2]}/{sc[-1]}")
    print(f"tasks per GPU       (min/max): {min(m['gpu_load'])}/{max(m['gpu_load'])}")
    print("per-node distinct components:",
          " ".join(f"n{n}={c}" for n, c in enumerate(m['node_counts'])))
    print("per-GPU distinct components :",
          " ".join(str(c) for c in m['gpu_counts']))


def rewrite_yaml(path, out_path, assign, gpus_per_node):
    """Update only node_gpu fields, preserving the rest of the file."""
    out_lines = []
    in_tasks = False
    cur_task = None
    task_re = re.compile(r"^  (\S+):\s*$")
    ng_re = re.compile(r'^(\s*node_gpu:\s*)"[^"]*"(\s*)$')
    sec_re = re.compile(r"^([A-Za-z_]\w*):")
    with open(path) as f:
        for line in f:
            stripped = line.rstrip("\n")
            if stripped == "tasks:":
                in_tasks = True
            elif in_tasks and sec_re.match(stripped):
                in_tasks = False
                cur_task = None
            if in_tasks:
                mt = task_re.match(stripped)
                if mt:
                    cur_task = mt.group(1)
                else:
                    mn = ng_re.match(stripped)
                    if mn and cur_task in assign:
                        node, gpu = divmod(assign[cur_task], gpus_per_node)
                        stripped = f'{mn.group(1)}"{node}:{gpu}"'
            out_lines.append(stripped + "\n")
    with open(out_path, "w") as f:
        f.writelines(out_lines)


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("config", help="train yaml file")
    ap.add_argument("--nodes", type=int, default=None,
                    help="number of compute nodes (default: n_nodes from yaml)")
    ap.add_argument("--gpus-per-node", type=int, default=None,
                    help="GPUs per node (default: len(gpu_ranks) from yaml)")
    ap.add_argument("--output", default=None,
                    help="output yaml with rewritten node_gpu (default: <config stem>_opt.yaml)")
    ap.add_argument("--time-limit", type=float, default=600.0,
                    help="per-phase solver time limit in seconds")
    ap.add_argument("--phase2-time-limit", type=float, default=None,
                    help="separate time limit for phase 2 (default: --time-limit)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--backend", choices=["auto", "cpsat", "scipy"], default="auto")
    ap.add_argument("--workers", type=int, default=16,
                    help="CP-SAT parallel workers")
    ap.add_argument("--hint-rounds", type=int, default=2000,
                    help="local-search rounds for the initial (GPU-level) hint")
    ap.add_argument("--ls-rounds", type=int, default=5000,
                    help="max local-search rounds per seed")
    ap.add_argument("--ls-seeds", type=int, default=12,
                    help="number of local-search seeds for the phase-2 hint")
    ap.add_argument("--ls-kicks", type=int, default=5,
                    help="random kicks per stall in local search")
    ap.add_argument("--greedy-only", action="store_true",
                    help="skip the exact solver; emit greedy+local-search solution")
    ap.add_argument("--no-symmetry", action="store_true",
                    help="disable canonical symmetry-breaking constraints")
    ap.add_argument("--log", action="store_true", help="solver logs")
    args = ap.parse_args()

    cfg, comp_of = load_tasks(args.config)
    raw_counts = warn_duplicate_tasks(args.config)
    n_nodes = args.nodes or int(cfg.get("n_nodes", 0))
    gpus_per_node = args.gpus_per_node or len(cfg.get("gpu_ranks", []) or [])
    if not n_nodes or not gpus_per_node:
        sys.exit("could not infer topology; pass --nodes/--gpus-per-node")
    n_gpus = n_nodes * gpus_per_node
    tasks = list(comp_of)
    T = len(tasks)
    lo, hi = T // n_gpus, math.ceil(T / n_gpus)
    if hi < 1: hi = 1
    comps = sorted({c for s in comp_of.values() for c in s})
    print(f"tasks={T} unique ({sum(raw_counts.values())} task blocks in yaml)  "
          f"nodes={n_nodes}  gpus/node={gpus_per_node}  total GPUs={n_gpus}")
    print(f"strict balance: each GPU hosts {lo}-{hi} tasks")
    print(f"components: {len(comps)} distinct "
          f"({sum(1 for c in comps if c.startswith('enc:'))} enc, "
          f"{sum(1 for c in comps if c.startswith('dec:'))} dec)")

    # baseline: current node_gpu values in the yaml (if topology matches)
    baseline = {}
    mapped = 0
    for name, t in cfg["tasks"].items():
        try:
            ngs = str(t.get("node_gpu", "0:0")).split(":")
            n0 = int(ngs[0]); g0 = int(ngs[1]) if len(ngs) > 1 else 0
            if n0 < 0 or n0 >= n_nodes or g0 < 0 or g0 >= gpus_per_node:
                continue
            baseline[name] = n0 * gpus_per_node + g0
            mapped += 1
        except Exception:
            continue
    have_baseline = mapped >= max(1, len(tasks) // 2)
    if have_baseline:
        bm = assignment_metrics(baseline, comp_of, gpus_per_node, n_nodes, n_gpus)
        lbl = "baseline (original layout mapped to target topology)" if (int(cfg.get("n_nodes", 0)) or -1) != n_nodes or len(cfg.get("gpu_ranks", []) or []) != gpus_per_node else "baseline (current train.yaml)"
        print_report(lbl, bm, gpus_per_node, n_nodes)
    else:
        print("baseline: skipped (target topology differs; cannot map most original node_gpu values)")

    # fast heuristic: greedy + local search
    t0 = time.time()
    hint = greedy_assignment(comp_of, n_gpus, gpus_per_node, n_nodes)
    gm = assignment_metrics(hint, comp_of, gpus_per_node, n_nodes, n_gpus)
    print(f"\ngreedy: max/GPU={gm['max_gpu']} max/node={gm['max_node']}  "
          f"({time.time() - t0:.2f}s)")
    t0 = time.time()
    hint = local_search(comp_of, hint, n_gpus, gpus_per_node, n_nodes,
                        max_rounds=args.hint_rounds, seed=args.seed)
    hm = assignment_metrics(hint, comp_of, gpus_per_node, n_nodes, n_gpus)
    print(f"greedy+local-search: max/GPU={hm['max_gpu']} max/node={hm['max_node']}  "
          f"({time.time() - t0:.2f}s)")

    if args.greedy_only:
        hint = canonicalize(hint, tasks, gpus_per_node)
        assign, info = hint, {
            "backend": "greedy+ls (no exact proof)",
            "phase1_status": "greedy+ls",
            "phase1_proven_optimal": False, "phase1_bound": None,
            "opt_max_gpu": hm["max_gpu"],
            "phase1_time": None,
            "phase2_status": "greedy+ls",
            "phase2_proven_optimal": False, "phase2_bound": None,
            "opt_max_node": hm["max_node"],
            "phase2_time": None,
            "phase2_used_hint": False,
        }
    else:
        if args.backend in ("auto", "cpsat"):
            try:
                assign, info = solve_cpsat(
                    comp_of, n_nodes, gpus_per_node, args.time_limit, args.seed,
                    args.log, args.workers, not args.no_symmetry, hint,
                    ls_rounds=args.ls_rounds,
                    time_limit2=args.phase2_time_limit,
                    ls_seeds=args.ls_seeds,
                    ls_kicks=args.ls_kicks)
            except ImportError:
                if args.backend == "cpsat":
                    sys.exit("ortools not installed")
                assign, info = solve_scipy(comp_of, n_nodes, gpus_per_node,
                                           args.time_limit, args.seed, args.log)
        else:
            assign, info = solve_scipy(comp_of, n_nodes, gpus_per_node,
                                       args.time_limit, args.seed, args.log)
        assign = canonicalize(assign, tasks, gpus_per_node)

    om = assignment_metrics(assign, comp_of, gpus_per_node, n_nodes, n_gpus)
    o_by_gpu = defaultdict(list)
    for t, g in assign.items():
        o_by_gpu[g].append(t)
    print_report("optimized", om, gpus_per_node, n_nodes)

    print(f"\nsolver: backend={info['backend']}  "
          f"phase1(Mgpu)={info['phase1_status']}  phase2(Mnode)={info['phase2_status']}")
    if info.get("phase1_time") is not None:
        print(f"timing: phase1={info['phase1_time']:.1f}s  "
              f"phase2={info['phase2_time']:.1f}s")
    if info.get("phase2_used_hint"):
        print("note: final assignment comes from local-search hint "
              "(solver did not improve on it)")
    if info["phase1_bound"] is not None:
        print(f"optimality: max-GPU proven optimal: {info['phase1_proven_optimal']}"
              f" (solver bound {info['phase1_bound']:.2f}), "
              f"max-node proven optimal: {info['phase2_proven_optimal']}"
              f" (solver bound {info['phase2_bound']:.2f})")

    print("\nper-GPU layout (node:gpu -> [tasks] | #components):")
    for g in range(n_gpus):
        node, gpu = divmod(g, gpus_per_node)
        ts = sorted(o_by_gpu[g])
        print(f"  {node}:{gpu}  {len(ts)} tasks  {om['gpu_counts'][g]} comps  "
              f"{', '.join(ts)}")

    out = args.output or re.sub(r"\.ya?ml$", "", args.config) + "_opt.yaml"
    rewrite_yaml(args.config, out, assign, gpus_per_node)
    print(f"\nwrote optimized assignments to {out}")


if __name__ == "__main__":
    main()
