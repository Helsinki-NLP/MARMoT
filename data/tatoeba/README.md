# Tatoeba Translation Challenge Data

Downloads and splits the [Tatoeba Translation Challenge](https://github.com/Helsinki-NLP/Tatoeba-Challenge) bitexts (release `v2023-09-26`) into `train/`, `dev/` and `test/` directories of gzip-compressed parallel files.

Each language pair is fetched as a `.tar` archive from `https://object.pouta.csc.fi/Tatoeba-Challenge-${RELEASE}` and split into per-pair files `<s>-<t>.<s>.gz` / `<s>-<t>.<t>.gz` (plus `<pair>.corpora.gz` with source-corpus IDs for the training data). Pair names are always sorted alphabetically, e.g. `deu-eng`.

## Usage

```bash
make SRC=deu TRG=eng fetch          # fetch deu-eng (and dev/test splits)
make LANGPAIRS="deu-eng eng-fin" all  # fetch several pairs + dev5K
make oellm                         # fetch all 561 OELLM language pairs
make oellm-eng                     # fetch English-centric OELLM pairs
make PIVOT_LANG=fin oellm-pivot    # fetch Finnish-centric OELLM pairs
make dev5K                         # cap all dev sets at 5000 lines
```

## Targets

| target | purpose |
|---|---|
| `all` | build the pairs in `LANGPAIRS` and then `dev5K` |
| `fetch` | fetch a single pair from `SRC`/`TRG` (no dev5K) |
| `oellm` | all 561 pairs among the OELLM languages (incl. `eng`) |
| `oellm-pivot` | pairs between `PIVOT_LANG` and all OELLM languages |
| `oellm-eng` | `oellm-pivot` with `PIVOT_LANG=eng` |
| `dev5K` | derive `dev5K/` from `dev/` by keeping only the first 5000 lines |
| `tatoeba-highest`, `tatoeba-higher`, `tatoeba-high` | fetch pairs from the corresponding released-bitext resource lists (from the Tatoeba-Challenge repo) |
| `*-zho` variants | like above but only `zho` pairs; then `move-regional`/`merge-regional` |
| `move-regional` | move regional-variant files (e.g. `zh_CN`) into `train/regional/` |
| `merge-regional` | merge regional variants back into the base pairs (used for zho) |

## Variables

| variable | default | description |
|---|---|---|
| `SRC`, `TRG` | `eng`, `fin` | language pair to fetch |
| `LANGPAIRS` | `${SRC}-${TRG}` | space-separated list of pairs |
| `PIVOT_LANG` | `eng` | pivot language for `oellm-pivot` |
| `RELEASE` | `v2023-09-26` | Tatoeba-Challenge release date |

## Notes

* **Macro-languages**: Tatoeba data is organized under macro-language IDs (e.g. `hbs` for Serbo-Croatian); the makefile extracts the individual languages (with their IDs from the archive) where possible, so you get e.g. `bos`, `srp_Cyrl` etc. as separate pairs.
* **Bosnian**: `bos` is converted to `bos_Latn` in the pairs to match the OpenEuroLLM data.
* Some dev/test files contain several language IDs; the makefile splits them using the ID files shipped in the archives.
* The official release lists can be fetched as `released-bitexts-{highest,higher,medium,lower,lowest}.txt`.