# Extra FLAN datasets

Two Python scripts that download additional FLAN-style (instruction-tuning) NLP datasets and convert them to TSV files under `extra_tsv/`.

## Usage

```bash
python3 fetch_flan_extra_tsv.py     # Tier-1/Tier-2 datasets (robust downloader)
python3 fetch_flan_extra_tsv2.py    # additional datasets via Hugging Face
```

## Output

```text
extra_tsv/
    wikilarge/eng/train.tsv  (dev.tsv, test.tsv)
    wiki_split/eng/...
    ...
```

Each dataset/language gets `train.tsv`, `dev.tsv` and `test.tsv` with the task inputs on one side and the outputs on the other. There is no makefile here; the scripts are run directly (the second script uses `datasets` and `langcodes`, the first relies on `urllib`).