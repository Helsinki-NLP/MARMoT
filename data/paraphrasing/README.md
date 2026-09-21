
# Usage


```
python download_paraphrase_datasets.py
```

gives

```
paraphrase_tsv/
├── tapaco/
│   ├── ara/
│   ├── deu/
│   ├── eng/
│   ├── ...
│   └── zho/
│
├── opusparcus/
│   ├── deu/
│   ├── eng/
│   ├── fin/
│   ├── fra/
│   ├── rus/
│   └── swe/
│
└── pawsx/
    ├── deu/
    ├── eng/
    ├── fra/
    ├── jpn/
    ├── kor/
    ├── spa/
    └── zho/
```

PawsX includes a label:

```
source    target    label
```

Filter for label = 1 to obtaine actual paraphrases!



OpusParcus with different quality levels:


```
python download_paraphrase_datasets.py \
    --datasets opusparcus \
    --opusparcus-quality 95
```