# Synthetic corpora (OPUS legacy)

Downloads synthetic MT training data from the legacy OPUS API for an arbitrary language pair and converts it into the standard gzip-compressed bitext format.

## Usage

```bash
make fin-eng          # Wiki/v1syn fin-eng (convenience target)
make eng-fin          # Wikipedia/v1syn eng-fin
make all              # default: CORPUS=Wiki VERSION=v1syn SRC=fin TRG=eng
make CORPUS=Wiki SRC=deu TRG=eng all
```

The data is fetched from `https://opus.nlpl.eu/legacy/synthetic/download.php?f=...` and stored as

```text
<corpus>/<langpair>.<src>.gz
<corpus>/<langpair>.<trg>.gz
```

## Variables

| variable | default | description |
|---|---|---|
| `CORPUS` | `Wiki` | synthetic corpus (e.g. `Wiki`, `Wikipedia`) |
| `VERSION` | `v1syn` | synthetic data version |
| `SRC`, `TRG` | `fin`, `eng` | language pair (ISO 639-3) |

Requires the `iso639` tool (for the ISO 639-2 codes used in the OPUS download URLs).