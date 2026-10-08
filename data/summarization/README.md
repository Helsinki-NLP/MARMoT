# Summarization data

Summarization corpora (document → summary). The top-level makefile concatenates the per-dataset files into one multilingual corpus; per-dataset download/convert makefiles live in the sub-directories.

## Top-level makefile

For each language, combines **all** sub-dataset files (per split) into a single file pair:

```bash
make all
# -> {train,dev,test}/summarization.<lang>1.gz   (source documents)
# -> {train,dev,test}/summarization.<lang>2.gz   (summaries)
```

`LANGUAGES` is auto-detected from the files matched by `*/${DATASPLIT}/*1.gz`; the cross-lingual subsets of CrossSum are skipped because they do not fit the same-language pattern.

## Sub-datasets

| sub-dataset | source | how | output |
|---|---|---|---|
| **SamSum** | Hugging Face `samsum` | `make -C samsum all` | `samsum/{train,dev,test}/samsum.eng{1,2}.gz` |
| **WikiLingua** | Hugging Face `wiki_lingua` | `make -C WikiLingua all` | `WikiLingua/{train,dev,test}/wikilingua.<lang>{1,2}.gz` |
| **XLSum** | Hugging Face `csebuetnlp/xlsum` | `make -C XLSum all` | `XLSum/{train,dev,test}/xlsum.<lang>{1,2}.gz` |
| **CrossSum** | Hugging Face (`cross_sum`) | `make -C CrossSum all` | `CrossSum/{train,dev,test}/CrossSum.<langpair>.<ext>.gz` (see below) |
| **MLSum** | Hugging Face `mlsum` | `python3 MLSum/download_mlsum.py` | `MLSum/mlsum_tsv/*.tsv` (no makefile) |

### SamSum

English dialogue summarization; `download_samsum.py` writes `samsum_tsv/<split>.tsv`, the makefile converts columns 2/3 (dialogue/summary) into `samsum.eng1.gz`/`samsum.eng2.gz`.

### WikiLingua / XLSum

Multi-language summarization (WikiLingua: article + summary in 19 languages; XLSum: article + summary in 44 languages). `LANGUAGES` is auto-detected from the downloaded `*_tsv/` directories.

### CrossSum

Cross-lingual summarization between English and French, including the monolingual pairs (`english-english`, `french-french`). `download_cross_sum.py --pairs <pairs>` fetches the TSVs; the makefile converts the four language-pair combinations for each split. (`LANGPAIRS := english-french french-english english-english french-french`.)

Cross-lingual pairs produce files named with the language code (`CrossSum.english-french.fra.gz`), monolingual pairs with a direction suffix (`CrossSum.english-english.eng2.gz`).

### MLSum

German and Spanish summarization; only a download script is provided.