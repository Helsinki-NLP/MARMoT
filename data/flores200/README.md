# FLORES-200 dev/test sets

Downloads the [FLORES-200](https://github.com/facebookresearch/flores) machine-translation benchmark (the `dev` and `devtest` sets for 200 languages) into this directory.

## Usage

```bash
make devtest   # or: make all
```

This fetches `flores200.tar.gz` (from the official download link), unpacks it, moves the contents (`dev/`, `devtest/` and the related files) into the current directory and cleans up the archive and the intermediate directory.

## Note

The FLORES data is the **default test data** for the experiment makefiles: [`make/config/data.mk`](../../make/config/data.mk) uses `TESTDATA := flores200/devtest` whenever `${DATA_DIR}/flores200/devtest` exists (and `flores200/dev` as dev data), falling back to Tatoeba otherwise. The per-language files are named like `devtest.eng`, `devtest.deu`, ...