# OpenSubtitles2024 multilingual multiset

Builds one file per language from the OpenSubtitles2024 *multiset* "linksets": for every movie, the aligned subtitle sentences of the 35 supported languages are stored under `linkset/<movie>.<lang2>`. This makefile concatenates all movies per language and emits

```text
opensubs2024-multiset.<lang3>     # for each of the 35 languages (ISO 639-3)
```

## Usage

```bash
make all
```

`LANG2` lists the source languages (ISO 639-2 codes, e.g. `ar`, `de`, `en`, ...; `pt_BR`, `zh_Hans`, `zh_Hant` included). `LANG3` converts them to ISO 639-3 via `iso639 -n -3 -k`, and the `linkset` filenames map `Hans`→`CN` and `Hant`→`TW` back to the subtitle-language suffixes.

## Requirements

* the `linkset/` directory with the per-movie aligned files (not fetched by this makefile),
* the `iso639` tool on `PATH`.