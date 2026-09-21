
from pathlib import Path
import pandas as pd
from huggingface_hub import snapshot_download

REPO = "MichaelR207/MultiSim"
OUT = Path("multisim_tsv")

# Download only the public data directory
data_dir = Path(
    snapshot_download(
        repo_id=REPO,
        repo_type="dataset",
        allow_patterns="data/*.csv",
    )
) / "data"

OUT.mkdir(exist_ok=True)

# Each language directory contains *_train.csv, *_val.csv, *_test.csv
for language_dir in data_dir.iterdir():
    if not language_dir.is_dir():
        continue

    language = language_dir.name

    for split in ["train", "val", "test"]:
        files = list(language_dir.glob(f"*_{split}.csv"))

        if not files:
            continue

        # Combine all available corpora for this language/split
        dfs = [pd.read_csv(f) for f in files]
        df = pd.concat(dfs, ignore_index=True)

        # Use "dev" rather than "val" in the output filename
        output_split = "dev" if split == "val" else split
        output_file = OUT / f"{language}_{output_split}.tsv"

        df.to_csv(output_file, sep="\t", index=False)

        print(f"{output_file}: {len(df):,} examples")

