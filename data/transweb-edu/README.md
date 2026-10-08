# FineWeb-Edu (350BT) doc-level MT data (shards 00000–00049)

Doc-level MT training data built from the **FineWeb-Edu** sample (350BT, `OELLM-synthetic/fineweb-edu/350BT` on `object.pouta.csc.fi`), machine-translated into the OpenEuroLLM languages. The pipeline is identical to [`multisynt`](../multisynt/README.md): fetch JSONL + plain-text per shard, convert with [`tools/multisynt_to_docbitext.py`](../../tools/multisynt_to_docbitext.py) (`-l len1024`), split into train/dev/test and derive text-prediction pairs.

**Shards** `00000`–`00049`: 00–48 → `train`, 49 → `dev` (tail 2000) + `test` (head 2000).

## Usage

```bash
make all                  # MT + text-prediction data (default TRG=fin)
make all-mt               # / all-oellm-mt (SLURM jobs, all OELLM languages)
make all-textpredict      # / all-oellm-predict
make all-4096             # LENGTH=4096 variant via SLURM
make convert | fetch | fetch-all | count-lines | count-broken
```

Output follows the same layout as multisynt, e.g.

```text
train/len1024/fineweb-edu_350BT_00-48.fin.gz
dev/len1024/fineweb-edu_350BT_49-tail2000.fin.gz
test/len1024/fineweb-edu_350BT_49-head2000.fin.gz
```

`FILEBASE` is `fineweb-edu_350BT_` and `HPC_PROJECT` defaults to `project_462000964`. See the [`multisynt` README](../multisynt/README.md) for the details, requirements and caveats.