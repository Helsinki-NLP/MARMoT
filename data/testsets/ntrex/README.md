# NTREX-128 test set

The [NTREX-128](https://github.com/MicrosoftTranslator/NTREX) machine-translation test set (Newstest2019, 128 languages).

```bash
make all
```

* clones `https://github.com/MicrosoftTranslator/NTREX.git`,
* copies the `NTREX-128` files to this directory, renaming them `newstest2019.<lang>.gz` (dashes in language codes, e.g. `en-ZH`, become underscores),
* removes the cloned repository afterwards.