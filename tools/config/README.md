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

## Companion scripts: analysis & weight rebalancing

Three standalone scripts for inspecting and adjusting an existing configuration. They need Python 3.8+ and only `pyyaml` (no `ortools`/`scipy`). All of them share the optimizer's component model: `enc:X` and `dec:X` are different components, the set on a GPU is the union of the components of the tasks placed on it (a component used by several tasks on one GPU counts once), and a compute node's set is the union over its GPUs.

### `sum_task_weights.py`

Sums the task weights per compute node and per GPU.

```bash
./sum_task_weights.py train-weights.yaml
./sum_task_weights.py train-weights.yaml --json         # machine-readable output
./sum_task_weights.py train-weights.yaml --precision 4  # decimal places (default 2)
```

Prints a `node × gpu` matrix of summed weights, a per-node summary (task count, total, share of the grand total) and a balance line (min/max/mean per GPU plus the max/min ratio). Weights are added with `decimal.Decimal`, because the YAML carries ~20 fractional digits. Tasks with a missing or malformed `weight`/`node_gpu` are skipped and reported on stderr; a missing or invalid file is a one-line error, not a traceback.

For `train-weights.yaml`: 584 tasks, grand total 60,904,021.74, GPU weights 203,745–3,329,858 (max/min ratio 16.34).

### `rebalance_gpu_weights.py`

Shifts `node_gpu` assignments to equalize the total weight per GPU **without increasing the maximum number of components on any GPU**.

```bash
./rebalance_gpu_weights.py train-weights.yaml            # → train-weights_rebalanced.yaml
./rebalance_gpu_weights.py train-weights.yaml --dry-run  # report only, write nothing
./rebalance_gpu_weights.py train-weights.yaml --strict   # no GPU may raise its own count
./rebalance_gpu_weights.py train-weights.yaml --limit 8  # custom component cap
```

- **Objective**: minimize the variance of the total weight per GPU (the mean is fixed), by greedy single-task moves with O(1) analytic deltas, followed by pairwise swaps between a heavy and a light GPU whenever a single move is blocked by the component cap.
- **Component constraint**: every GPU must end up with at most `--limit` components (default: the peak per-GPU component count of the input), which is exactly the requirement that the maximum number of components per GPU does not increase. `--strict` additionally forbids any individual GPU from increasing its own component count (the stricter reading; expect a less perfect weight balance).
- **Output**: only the `node_gpu` lines inside the `tasks:` block are rewritten - everything else is preserved byte for byte. The written file is re-parsed afterwards and every task's placement, weight and component set is verified before success is reported.
- **Flags**: `-o/--output` (default `<input>_rebalanced.yaml`, may be the input file itself), `--dry-run`, `--limit N`, `--strict`, `--precision N`, `--max-passes` (safety cap, default 500), `--verbose` (list every moved task). Runs in ~12 s for 584 tasks on 64 GPUs.

Result on `train-weights.yaml` (418 of 584 tasks moved, peak components 10 → 10):

| metric                |       before |        after |
|-----------------------|-------------:|-------------:|
| max GPU weight        | 3,329,858.32 | 970,555.79 (−70.9%) |
| min GPU weight        |   203,745.21 | 949,898.46 (+366%) |
| stdev of GPU weight   |   635,353.91 |     2,468.31 (−99.6%) |
| max/min ratio         |        16.34 |         1.02 |
| max components per GPU|           10 |           10 |
| tasks moved           |            — |  418 / 584   |

Cross-checking the result with `./sum_task_weights.py train-weights_rebalanced.yaml` shows the unchanged grand total (60,904,021.74) and a max/min ratio of 1.02.

### `sum_components.py`

Summarizes the components hosted on each GPU and each compute node.

```bash
./sum_components.py train-weights.yaml
./sum_components.py train-weights.yaml --verbose
```

- **Per GPU**: task count, enc/dec split and distinct component total for every `node:gpu`, with min/median/max across GPUs and the replication factor (per-GPU placements vs. distinct components).
- **Per compute node**: the union over the node's GPUs (a component sitting on several GPUs of one node counts once), with the sum of the per-GPU totals next to it to show how much duplication exists inside the node.
- **Universal components**: those present on every GPU / every node (in `train-weights.yaml` only `enc:all` is on all 64 GPUs).
- **`--verbose`**: component names per GPU and per node, plus a per-component spread table (tasks / GPUs / nodes, rarest first).

For `train-weights.yaml`: 53 distinct components (16 enc, 37 dec); per GPU min 4 / median 7 / max 10; per node min 14 / median 17.5 / max 31 (node 6 is the outlier with 31 of the 53). On `train-weights_rebalanced.yaml` the per-GPU maximum is still 10, while node unions widen (e.g. node 3: 15 → 32), since weight balancing deliberately spreads components across nodes.

### Typical workflow

```bash
./sum_task_weights.py train-weights.yaml            # inspect the weight imbalance
./rebalance_gpu_weights.py train-weights.yaml       # write train-weights_rebalanced.yaml
./sum_components.py train-weights_rebalanced.yaml   # inspect the resulting component layout
./sum_task_weights.py train-weights_rebalanced.yaml # verify the new balance
```