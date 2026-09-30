from pathlib import Path
import csv
import shutil
import urllib.request
import zipfile

from sacremoses import MosesDetokenizer


# ============================================================
# Configuration
# ============================================================

OUTPUT_DIR = Path("paranmt_tsv")
DOWNLOAD_DIR = Path("paranmt_downloads")

LANG = "eng"

# Official ParaNMT-5M processed archive.
FILE_ID = "19NQ87gEFYu3zOIp_VNYQZgmnwRuSIyJd"

ZIP_NAME = "para-nmt-5m-processed.zip"

ZIP_PATH = DOWNLOAD_DIR / ZIP_NAME
EXTRACT_DIR = DOWNLOAD_DIR / "para-nmt-5m-processed"


# ============================================================
# Download
# ============================================================

def download_google_drive(file_id, output_path):

    if output_path.exists():
        print(f"Already downloaded: {output_path}")
        return

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    url = (
        "https://drive.usercontent.google.com/"
        f"download?id={file_id}&export=download&confirm=t"
    )

    print("Downloading ParaNMT-5M...")

    with urllib.request.urlopen(url) as response:
        with open(output_path, "wb") as f:
            shutil.copyfileobj(response, f)

    print(f"Saved: {output_path}")


# ============================================================
# Extract
# ============================================================

def extract_zip(zip_path, output_dir):

    if output_dir.exists():
        existing = list(
            output_dir.rglob(
                "para-nmt-5m-processed.txt"
            )
        )

        if existing:
            print(
                f"Already extracted: {existing[0]}"
            )
            return existing[0]

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        f"Extracting {zip_path}..."
    )

    with zipfile.ZipFile(zip_path) as z:
        z.extractall(output_dir)

    files = list(
        output_dir.rglob(
            "para-nmt-5m-processed.txt"
        )
    )

    if not files:
        raise RuntimeError(
            "Could not find "
            "'para-nmt-5m-processed.txt' "
            "after extracting the archive."
        )

    return files[0]


# ============================================================
# Moses detokenizer
# ============================================================

detokenizer = MosesDetokenizer(
    lang="en"
)


def detokenize(text):
    """
    Detokenize a Moses-tokenized sentence.

    XML entities are also unescaped, matching the normal
    Moses detokenization behavior.
    """

    tokens = text.strip().split()

    if not tokens:
        return ""

    return detokenizer.detokenize(
        tokens,
        return_str=True,
        unescape=True,
    )


# ============================================================
# Convert to TSV
# ============================================================

def convert_to_tsv(
    input_path,
    output_path,
):

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    count = 0

    print(
        f"Converting {input_path}"
    )

    with open(
        input_path,
        "r",
        encoding="utf-8",
    ) as src, open(
        output_path,
        "w",
        encoding="utf-8",
        newline="",
    ) as dst:

        writer = csv.writer(
            dst,
            delimiter="\t",
            lineterminator="\n",
        )

        writer.writerow(
            [
                "source",
                "target",
            ]
        )

        for line in src:

            line = line.rstrip(
                "\r\n"
            )

            if not line:
                continue

            parts = line.split(
                "\t"
            )

            if len(parts) < 2:
                continue

            source = detokenize(
                parts[0]
            )

            target = detokenize(
                parts[1]
            )

            if not source or not target:
                continue

            writer.writerow(
                [
                    source,
                    target,
                ]
            )

            count += 1

            if count % 100000 == 0:
                print(
                    f"Processed {count:,} pairs..."
                )

    print(
        f"Wrote {count:,} pairs"
    )

    print(
        f"Output: {output_path}"
    )


# ============================================================
# Main
# ============================================================

def main():

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    download_google_drive(
        FILE_ID,
        ZIP_PATH,
    )

    # --------------------------------------------------------
    # Extract
    # --------------------------------------------------------

    data_file = extract_zip(
        ZIP_PATH,
        EXTRACT_DIR,
    )

    # --------------------------------------------------------
    # Convert + Moses detokenize
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / LANG
        / "train.tsv"
    )

    convert_to_tsv(
        data_file,
        output_path,
    )


if __name__ == "__main__":
    main()
