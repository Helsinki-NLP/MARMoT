# Text prediction data (from translated JSONL)

Builds *next-sentence prediction* data from a single shard of machine-translated JSONL data (the same `object.pouta.csc.fi` shards used by the doc-level MT pipelines). For every sentence the pair (sentence, next sentence) is extracted with [`tools/jsonl_to_textpredict.py`](../../tools/jsonl_to_textpredict.py) (with `-s` to split into sentences).

## Output

```text
eng/nemotron-cc-english-run1-train-00.eng-eng.in.gz    # sentence
eng/nemotron-cc-english-run1-train-00.eng-eng.out.gz   # next sentence
```

## Usage

```bash
make all        # default: LANGID=eng, FILEID=00
make LANGID=fin FILEID=01 all
```

## Variables

| variable | default | description |
|---|---|---|
| `DATASET` | `OELLM-synthetic/maxidl/nemotron-cc-english-run1` | corpus on `object.pouta.csc.fi` |
| `FILEBASE` | `nemotron-cc-english-run1-train-` | shard file-name prefix |
| `LANGID` | `eng` | language of the translated data |
| `FILEID` | `00` | shard id |
| `CONVERT_PARAMS` | `-s` | extra options for the conversion script (e.g. `-m <max line length>`) |

The `word`/`-W`/`-M` options of `jsonl_to_textpredict.py` are documented in the script itself.