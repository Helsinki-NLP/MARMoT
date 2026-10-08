# OPUS data (opus_get)

Generic downloader for [OPUS](https://opus.nlpl.eu) corpora using the `opus_get` tool. Produces gzip-compressed parallel files named `<corpus>/<langpair>.<src>.gz` / `<corpus>/<langpair>.<trg>.gz` (moses format).

The default corpus is `OpenSubtitles`; any OPUS corpus can be fetched by name, and optional release versions are supported.

## Usage

```bash
make SRC=deu TRG=fin all                       # fetch deu-fin from OpenSubtitles
make CORPUS=OpenLegal SRC=eng TRG=fin all      # any other OPUS corpus
make LANGPAIR=deu-fin RELEASE=v2024 all        # specific release
make opensubs                                  # all OELLM pairs in OpenSubtitles2024
make hplt                                      # HPLT release v3 pairs with English
make hplt2                                     # remaining HPLT release v2 pairs
```

## Targets & variables

| target | purpose |
|---|---|
| `all` | download `${CORPUS}/${LANGPAIR}` (default target) |
| `opensubs` | loop over all OELLM pairs available in OpenSubtitles (release `v2024`), detected via `opus_get -l` |
| `hplt` | download `HPLT` pairs (v3 language list) between each language and `eng` |
| `hplt2` | download the remaining `HPLT` pairs from release v2 |

| variable | default | description |
|---|---|---|
| `CORPUS` | `OpenSubtitles` | OPUS corpus name |
| `LANGPAIR` | `${SRC}-${TRG}` | language pair |
| `SRC`, `TRG` | from `LANGPAIR` | source/target language (ISO 639-3) |
| `RELEASE` | (unset = latest) | OPUS release tag, passed as `-r` to `opus_get` |

Language codes are converted to ISO 639-2 with `iso639` for `opus_get`, and filenames use the 3-letter codes. The `opensubs` target needs the `HPLT`/`OpenSubtitles` data and the `opus_get` command on `PATH`.