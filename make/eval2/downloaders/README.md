# Downloading evaluation data using downloader scripts

## Preparations

Assume you have $PROJHOME defined as the working directory for this.

Creating the Python virtual environment for downloading scripts:
```
deactivate 2>/dev/null || true
mkdir -p $PROJHOME/venvs
module load cray-python
python3 -m venv $PROJHOME/venvs/eval
source $PROJHOME/venvs/eval/bin/activate
python -m pip install --upgrade pip
python -m pip install datasets huggingface-hub pandas
```  

## Downloading Bouquet

Running the command on LUMI.csc.fi:
```
module load cray-python
cd $DATA
source $PROJHOME/venvs/eval/bin/activate
python dl-bouquet-all.py
```
Example files after downloading:
```
data/bouquet/dev/eng_Latn.txt
data/bouquet/dev/fin_Latn.txt
data/bouquet/test/eng_Latn.txt
data/bouquet/test/fin_Latn.txt
```

## Downloading FLORES+

FLORES+ provides at least the _dev_ and _devtest_splits. In a clean
evaluation setup, one should decide in advance which split is used for
which purpose.  A practical beginner-friendly convention is the
following:

- use _dev_ for small pilot runs, pipeline checks, debugging, and sanity checks,

- use _devtest_ for the main reported evaluation results.

This keeps exploratory work separate from the main benchmark results.


To access FLORES+ through Hugging Face, the user must
1. install the \texttt{datasets} package (see above),
2. log in to Hugging Face at \url{https://huggingface.co/},
3. accept the FLORES+ terms of use, and
4. authenticate locally using the authentication token.

At that point, the user is prompted to enter a Hugging Face access
token. This token is obtained from the Hugging Face account settings
`https://huggingface.co/settings/tokens/new?tokenType=fineGrained`
after you have logged in on the web site.  After creating and copying
(keep the copy somewhere) the accesstoken, the basic workflow is as
follows:
```
python
>>> import huggingface_hub
>>> huggingface_hub.login()
Enter your token (input will not be visible):
Add token as git credential? [y/N]: 
```

Now the files can be downloaded:
```
python dl-flores-all.py
```
This should give files:
```
data/flores_plus/
  dev/
    eng_Latn.txt
    bos_Latn.txt
    bul_Cyrl.txt
    cat_Latn.txt
    ...
  devtest/
    eng_Latn.txt
    bos_Latn.txt
    bul_Cyrl.txt
    cat_Latn.txt
    ...
```

## Downloading WMT24++

WMT24++ is intended as an evaluation resource for multilingual
translation, with a particular focus on English-to-target directions.
It is distributed through Hugging Face, and its README describes it as
human translation and post-edit data for 55 English-to-target language
pairs. Unlike FLORES+, where one can think in terms of
language-centered parallel files, WMT24++ is organized primarily by
\emph{language-pair configuration}. Each pair is stored in its own
JSONL file and exposed on Hugging Face as its own dataset
configuration, such as _en-fi\_FI_ or _en-de\_DE_.  The directory
structure follows this pattern:
```
data/wmt24pp/
  train/
    en-fi_FI/
      source.en.txt
      reference.fi_FI.txt
      reference_original.fi_FI.txt
    en-de_DE/
      source.en.txt
      reference.de_DE.txt
      reference_original.de_DE.txt
    ...
```

Downloading:
```
module load cray-python
source $PROJHOME/venvs/eval/bin/activate
python dl-wmt-all.py
```


