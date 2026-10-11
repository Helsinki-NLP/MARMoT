# Definition modelling datasets

Data for *definition modelling* (predicting a dictionary definition from a word, or the reverse). Two sub-datasets with makefiles, plus an external dataset:

| dataset | source | make target | outputs |
|---|---|---|---|
| **3D-EX** | [github.com/F-Almeman/3D-EX](https://github.com/F-Almeman/3D-EX) | `make 3d-ex-data` | `3D-EX/train|dev|test/3d_ex.eng1.gz` / `3d_ex.eng2.gz` |
| **CoDWoE** | [codwoe.atilf.fr](https://codwoe.atilf.fr) | `make -C CoDWoE all` | `CoDWoE/train|dev/codwoe.{eng,fra,rus}{1,2}.gz` |
| **Dore** | [huggingface.co/datasets/multidefmod/dore](https://huggingface.co/datasets/multidefmod/dore) | – (download manually) | – |

The converted files follow the same-name-pair convention used elsewhere in the repo: stream `1` contains `word:example` (word + colon, then the usage example), stream `2` contains the definition.

## 3D-EX usage

```bash
make 3d-ex-data
```

clones the repository, downloads the complete-dataset CSVs (from Google Drive), converts them with [`3D-EX_to_tsv.py`](3D-EX_to_tsv.py) into tab-separated files and builds the train/dev/test gz files. The `*_valid.tsv` files become `dev/` and `*_test.tsv` become `test/`; everything else (excluding the CoDWoE CSV) becomes `train/`.

## CoDWoE usage

```bash
make -C CoDWoE all
```

downloads `full_dataset.zip`, converts the complete (train) and trial (dev) CSVs for English, French and Russian with [`codwoe_csv2tsv.py`](CoDWoE/codwoe_csv2tsv.py) and writes the same `eng1.gz`/`eng2.gz`-style files.