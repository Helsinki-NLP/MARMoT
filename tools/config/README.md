# MARMoT GPU Assignment Optimizer

Tool to compute optimal `node_gpu` assignments for tasks in a MARMoT training YAML (e.g., `train.yaml`) across a given number of compute nodes and GPUs per node. Assignments satisfy strict load balance and are optimized lexicographically: (1) minimize maximum distinct components per GPU, (2) minimize maximum distinct components per node. Components are namespaced as `enc:X` vs `dec:X`.

## Requirements

- Python 3.8+
- `pyyaml`, `ortools` (required for CP-SAT). `scipy` optional (MILP fallback).
- Input YAML in the MARMoT training format with `tasks` mapping (each task has `enc_sharing_group` and/or `dec_sharing_group`).

## Install

```bash
pip install -r requirements.txt
```

Requirements include: `pyyaml`, `ortools`, `scipy` (optional but available).

## Usage

```bash
python3 optimize_gpu_assignment.py train.yaml --nodes 6 --gpus-per-node 8 --output train_optimized.yaml
```

Key flags:
- `--nodes`, `--gpus-per-node` (defaults: infer from YAML `n_nodes`/`gpu_ranks` or 1/1)
- `--output` (default `optimized.yaml`)
- `--time-limit` (per-phase CP-SAT, seconds; default 600)
- `--phase2-time-limit` (separate phase-2 budget; default same as `--time-limit`)
- `--backend {auto,cpsat,scipy}` (default auto)
- `--greedy-only` (fast heuristic only, no exact proof)
- `--seed` (default 42)
- `--hint-rounds` (initial GPU-level local-search rounds; default 2000)
- `--ls-rounds` (phase-2 polish local-search rounds; default 5000)
- `--ls-seeds` (polish seeds count; default 12)
- `--ls-kicks` (kicks per stall in local search; default 5)
- `--workers`, `--no-symmetry`, `--log`

The script rewrites only `node_gpu` fields in the output YAML (preserving original formatting where possible). It reports baseline metrics, greedy+LS, phase 1 (max/GPU, CP-SAT), phase-2 hint polish, phase 2 (max/node), final metrics, and per-GPU layout. Duplicate task names are warned (later definition wins).

## Notes

- Universal components present in every task (e.g., `enc:all`) are excluded from the solver objective (constant) and added back in reporting.
- Symmetry-breaking (canonical first-use) reduces search space for many-GPU setups.
- Local search uses pairwise swaps with random kicks; the phase-2 polish runs under the proven phase-1 GPU cap to quickly reach near-optimal node maxima. The final assignment is the lexicographically best of the solver result and the polished hint.
- If CP-SAT doesn't improve on the hint but the hint value == the solver's best bound, the node objective is provably optimal.
- Topology-agnostic: you can optimize for a different setup (e.g., `--nodes 4 --gpus-per-node 8`) regardless of the original YAML's topology; baseline comparison is skipped if the original layout doesn't map cleanly to the target topology.