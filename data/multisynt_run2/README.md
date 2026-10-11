# MultiSynth doc-level MT data (Nemotron-CC English, run 2)

Same pipeline as [`multisynt`](../multisynt/README.md) but for the **second run** of the Nemotron-CC English translation (500 shards `00000`–`00499` of the `nemotron-cc-english-run2` corpus, `OELLM-synthetic/maxidl/...`).

**Splits** — shards 000–498 → `train`, shard 499 → `dev` (last 2000 documents) and `test` (first 2000 documents):

```text
train/len1024/nemotron-cc-english-run2-train-train-000-498.fin.gz
dev/len1024/nemotron-cc-english-run2-train-train-499-tail2000.fin.gz
test/len1024/nemotron-cc-english-run2-train-train-499-head2000.fin.gz
textpredict/train|dev|test/...1.gz  ...2.gz
```

* `FILEBASE` is `nemotron-cc-english-run2-train-train-` (note the doubled `train-`).
* `OELLM_LANGS` here is `bul ces est fin gle ron swe tur ukr`.

## Usage

Same targets as [`multisynt`](../multisynt): `make all`, `all-mt`, `all-textpredict`, `all-oellm-mt` (SLURM jobs for the OELLM languages), `all-oellm-predict`, `all-4096`, plus:

```bash
make devtest        # dev + test splits only
make all-mt-trg     # target-side MT data only (used by all-oellm-mt)
make all-mt-src     # source-side (English) MT data
make fetch-all      # fetch all 500 jsonl shards
make count-lines    # / count-broken
```

`HPC_PROJECT` defaults to `project_462000964`. See the [`multisynt` README](../multisynt/README.md) for the detailed recipe and caveats.