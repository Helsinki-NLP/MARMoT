#!/usr/bin/env python3

import sys
import yaml

if len(sys.argv) != 3:
    raise SystemExit(f"Usage: {sys.argv[0]} TRAIN_YAML OUTFILE")

train_yaml, outfile = sys.argv[1:]

with open(train_yaml, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

tasks = cfg.get("tasks")
if not isinstance(tasks, dict):
    raise SystemExit("No top-level 'tasks' mapping found")

with open(outfile, "w", encoding="utf-8") as f:
    for task_name in sorted(tasks):
        f.write(task_name + "\n")
