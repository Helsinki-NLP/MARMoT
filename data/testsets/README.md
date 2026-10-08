# Test sets (NTREX, WMT, OpenSubtitles2024-multiset)

Test and evaluation data used for evaluating the trained models. Four independent sub-directories:

## [`ntrex/`](ntrex/README.md) — NTREX-128

The [NTREX-128](https://github.com/MicrosoftTranslator/NTREX) test set (128 languages), cloned from GitHub and converted into the standard flat-file format:

```bash
make -C ntrex all
# -> newstest2019.<lang>.gz for every language in NTREX-128
```

## [`wmt/`](wmt/README.md) — WMT dev sets

The [WMT24 GeneralMT dev sets](https://data.statmt.org/wmt24/general-mt/) (XML files), extracted into per-language-pair plain-text test sets:

```bash
make -C wmt all
# -> <testsets>/<testsets>.<langpair3>.<lang3>.gz
```

## [`wmt24pp/`](wmt24pp/README.md) — WMT24++

The [WMT24++](https://huggingface.co/datasets/google/wmt24pp) benchmark (multi-sentence examples, English-centric), converted into flat text files and next-sentence-prediction data:

```bash
make -C wmt24pp all          # extract all 56 language pairs
make -C wmt24pp LANGPAIR=en-fi_FI all
make -C wmt24pp predict      # text prediction (next sentence) data
```

## [`OpenSubtitles2024-multiset/`](OpenSubtitles2024-multiset/README.md) — OpenSubtitles2024 multiset

Per-language files built from the OpenSubtitles2024 *multiset* movie "linksets" (35 languages, ISO 639-3 file names — one line per aligned subtitle sentence):

```bash
make -C OpenSubtitles2024-multiset all
# -> opensubs2024-multiset.<lang3> for each of the 35 languages
```

Note: it needs the `linkset/` source directory (see the [sub-directory README](OpenSubtitles2024-multiset/README.md)).
