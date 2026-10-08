# Parsing data (MTOP)

The [MTOP](https://huggingface.co/datasets/tasksource/mtop) multilingual task-oriented parsing dataset (intents + slot labels for spoken-language understanding).

```bash
python3 download_mtop.py [--output_dir mtop_tsv]
```

Downloads the dataset from Hugging Face (`tasksource/mtop`), converts the language codes to ISO 639-3 with `langcodes`/`iso639` and writes TSV files (one per language/split) under `mtop_tsv/`. There is no makefile.