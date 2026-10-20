# Question answering data

Three multilingual question-answering datasets, each with a download script that pulls the data from Hugging Face and converts it to TSV files (language codes mapped to ISO 639-3):

| dataset | HF dataset | script | languages |
|---|---|---|---|
| **Mintaka** | `AmazonScience/mintaka` | `Mintaka/download_mintaka.py` | en, de, es, fr, hi, pt, ... |
| **MultiNativeQA** | `QCRI/MultiNativQA` | `MultiNativeQA/download_multinativqa.py` | Arabic, English, French, Hindi, Spanish |
| **TyDiQA** | `khalidalt/tydiqa-goldp` | `TyDiQA/download_tydiqa.py` | 11 typologically diverse languages |

## Usage

```bash
cd Mintaka && python3 download_mintaka.py
# -> TSV files under *_tsv/ (questions/contexts/answers)
```

There are no makefiles; run the scripts inside the respective sub-directory. The scripts support `--output_dir` to set the destination.