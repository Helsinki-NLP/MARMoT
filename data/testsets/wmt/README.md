# WMT24 General MT dev/test sets

The [WMT24 general machine translation dev sets](https://data.statmt.org/wmt24/general-mt/), downloaded as a zip of XML files and converted to plain text:

```bash
make all          # download, convert everything, clean up
make convert      # convert a single TESTSET/LANGPAIR
make LANGPAIR=deu-eng TESTSET=<set> convert
```

* XML files are converted with `wmt_devsets/xml/extract.py`.
* Output files are named `<TESTSET>/<TESTSET>.<langpair3>.<lang3>.gz` using ISO 639-3 codes (converted with `iso639`), e.g. `wmt24_GeneralMT-devsets/...eng.gz`.
* The downloaded `wmt_devsets/` directory is deleted by `make all` after conversion (target `cleanup`).