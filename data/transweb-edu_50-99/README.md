# FineWeb-Edu (350BT) doc-level MT data (shards 00050–00099)

Continuation of the [`transweb-edu`](../transweb-edu/README.md) pipeline for shards `00050`–`00099` of the same FineWeb-Edu (350BT) corpus.

* **Output**: `train/len1024/fineweb-edu_350BT_50-99.{eng,trg}.gz` (training data only — this shard range has **no dev/test splits**).
* **Languages** (`OELLM_LANGS`): `ces fin ukr`.
* **Targets**: `all`, `all-mt`, `all-textpredict`, `all-oellm-mt`, `all-oellm-predict`, `all-4096`, `convert`, `fetch`.
* `FILEBASE = fineweb-edu_350BT_`, `HPC_PROJECT = project_462000964`.

See the [`multisynt` README](../multisynt/README.md) for the pipeline details and caveats.