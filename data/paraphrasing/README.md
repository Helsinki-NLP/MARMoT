# Paraphrasing data

Paraphrase corpora in the repo's standard same-language-pair format (`<set>1.gz` / `<set>2.gz`: paraphrase on one side, alternative on the other). Five sub-datasets:

| sub-dataset | source | how | output |
|---|---|---|---|
| **Opusparcus** | [Kielipankki](https://www.kielipankki.fi/download/opusparcus/) | `make -C opusparcus all` | `opusparcus/{train,dev,test}/opusparcus.{deu,eng,fin,fra,rus,swe}{1,2}.gz` |
| **ParaBank2** | Hugging Face `redis/langcache-sentencepairs-v3` (config `parabank2`) | `python3 parabank2/download.py` | `parabank2/parabank2_tsv/*.tsv` |
| **ParaNMT** | [paranmt](https://github.com/nextgenusfs/paranmt) | `python3 paranmt/download.py` | `paranmt/paranmt_tsv/*.tsv` |
| **PAWS-X** | Hugging Face `google-research-datasets/paws-x` | `python3 pawsx/download.py` | `pawsx/pawsx_tsv/*.tsv` |
| **TaPaCo** | [zenodo.org/records/3707949](https://zenodo.org/records/3707949) | `make -C tapaco tapaco_v1.0.zip` | downloads the zip (no conversion) |

### Opusparcus

Six languages (de, en, fi, fr, ru, sv); downloads the per-language zips, and for each of `train`/`dev`/`test` converts the TSV into gz files (detokenized with `detokenize.py`, max `MAXLINES = 1000000` lines).

### ParaBank2 / ParaNMT / PAWS-X

Plain Python download scripts (using the Hugging Face `datasets` library; ParaNMT additionally detokenizes with `sacremoses`). They dump TSV files into `*_tsv/` directories; run them in the respective sub-directory.

### TaPaCo

Only downloads `tapaco_v1.0.zip` from Zenodo — conversion is left to the user.

See also [SemAntoNeg](https://github.com/Helsinki-NLP/SemAntoNeg) and the [MWE paraphrasing resources](https://unidive.lisn.upsaclay.fr/doku.php?id=outcomes:language-resources) linked in the original README.