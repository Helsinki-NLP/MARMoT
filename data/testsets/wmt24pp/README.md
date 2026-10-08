# WMT24++ benchmark data

The [WMT24++](https://huggingface.co/datasets/google/wmt24pp) benchmark: multi-sentence translation examples (source + target, and a **next-sentence continuation** used to measure document-context awareness), for 56 English-centric language/regional-variant pairs (e.g. `en-fi_FI`, `en-zh_CN`).

## Usage

```bash
make all                            # extract all 56 pairs
make LANGPAIR=en-fi_FI all          # or a single pair
make LANGPAIR=en-fi_FI predict      # next-sentence-prediction data
```

## Output

* the raw `jsonl` files are downloaded from Hugging Face (`google/wmt24pp`) — `<src>-<trg>.jsonl`;
* `extract` converts them with [`tools/wmt24_to_tsv.py`](../../../tools/wmt24_to_tsv.py) into flat text files `<lang>.<iso3>` (e.g. `en.eng`, `fi.fin`, ...); language codes come from `LANGPAIR` with region suffixes stripped for the ISO conversion;
* `predict` builds adjacent-sentence pairs with [`tools/wmt24_to_predict.py`](../../../tools/wmt24_to_predict.py) under `next_sent_predict/wmt24pp_<iso3>-<iso3>.{in,out}.gz` for both the source and target language.

Note: the file names use the `SRC`/`TRG` codes from `LANGPAIR` (e.g. `en-fi_FI` → `en.eng` + `fi_FI.fin` after conversion).