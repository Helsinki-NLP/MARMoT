# MARMoT Experiment Makefiles - Data Configuration

The essential data directories are set in [data.mk](../config/data.mk) (included through [config.mk](../config.mk)) and use the base directory from the [environment configuration](env.md):

* `DATA_DIR`: home directory of data files (train, dev and test), default = `${PROJECT_DIR}/data`

## Default data sets

The names of the default train, dev and test data sets are defined with the following variables (each a relative path inside `DATA_DIR` and a name used to tag generated files):

* `TRAINDATA`: relative path of the training data directory (default = `tatoeba/train`)
* `TRAINDATA_NAME`: name of the training data set (default = `tatoeba-test-v2023-09-26`)
* `DEVDATA`: relative path of the validation data directory (default = `flores200/dev` if `DATA_DIR/flores200/dev` exists, otherwise `tatoeba/dev5K`)
* `DEVDATA_NAME`: name of the validation data set (default = `flores200-dev`, otherwise `tatoeba-test-v2023-09-26`)
* `TESTDATA`: relative path of the test data directory (default = `flores200/devtest` if it exists, otherwise `tatoeba/test`)
* `TESTDATA_NAME`: name of the test data set (default = `flores200-devtest`, otherwise `tatoeba-test-v2023-09-26`)

The full data directories used for the current task are:

* `TRAINDATA_DIR` = `${DATA_DIR}/${TRAINDATA}`
* `DEVDATA_DIR` = `${DATA_DIR}/${DEVDATA}`
* `TESTDATA_DIR` = `${DATA_DIR}/${TESTDATA}`

Note that only existing validation/test files are added to the generated configuration files. Validation data can be skipped for denoising and other monolingual task types with `SKIP_DENOISING_VALID_TASKS` and `SKIP_SAME_LANGUAGE_VALID_TASKS` (both `0` by default, i.e. validation is enabled).

## Looking up data files

The makefiles search for task-specific data in the directories above. The logic for this is implemented in the [data.mk](../config/data.mk) file (see the "data sets" section) and works as follows: for each data type, a search pattern is built from a *basename* and an *extension*.

* Basenames (default: `*${SORTED_LANGPAIR}*`, i.e. the alphabetically sorted language pair of the task, e.g. `*deu-eng*` for an `eng-deu` task). Additional fallback patterns are tried in order: `*${REVERSE_LANGPAIR}*` and finally `*`.
* Extensions (default: `${SRCLANG}.gz` for source and `${TRGLANG}.gz` for target files), e.g. `eng.gz` / `deu.gz`.

The general pattern for finding source and target language files is therefore

* source: `${XXXDATA_DIR}/*${SORTED_LANGPAIR}*.${SRCLANG}.gz`
* target: `${XXXDATA_DIR}/*${SORTED_LANGPAIR}*.${TRGLANG}.gz`

where `${XXXDATA_DIR}` corresponds to the training, validation or test data directory, respectively. For validation and test data, an additional pattern `${XXXDATA_DIR}/${SRCLANG}*` / `${XXXDATA_DIR}/${TRGLANG}*` is tried, which covers the Flores-200 file naming convention (`eng_Latn`, `deu_Latn`, ...). Both files must be aligned (the same row numbers indicate aligned text segments).

For monolingual tasks (typically `denoising` tasks with the same source and target language, e.g. `eng-eng`) the extensions are `${SRCLANG}1.gz` and `${TRGLANG}2.gz` so that input and output files can be distinguished.

### Basename placeholders

The default basename pattern can be overwritten with `TRAINDATA_BASENAME`, `DEVDATA_BASENAME` and `TESTDATA_BASENAME` (or per task with `TASK_TRAINDATA_BASENAMES`, `TASK_DEVDATA_BASENAMES` and `TASK_TESTDATA_BASENAMES`). Basenames may contain the placeholders `{langpair}` (the task's language pair, e.g. `eng-deu`), `{sorted_langpair}` (the alphabetically sorted pair, e.g. `deu-eng`) and `{reverse_langpair}` (the reverse of the sorted pair).

## Task-specific data

Task-specific training data can also be given in the top-level makefile by specifying files with the variables `TASK_TRAINDATA_SRCS` and `TASK_TRAINDATA_TRGS`, for example:

```make
#-*-makefile-*-

# define tasks
TASKS := eng-deu eng-fra

TASK_TRAINDATA_SRCS := /path/to/eng-deu.eng /path/to/eng-fra.eng
TASK_TRAINDATA_TRGS := /path/to/eng-deu.deu /path/to/eng-fra.fra


# include common configuration and make targets
include ../make/marmot.mk
```

Similarly, one can also specify task-specific validation data (with `TASK_DEVDATA_SRCS` and `TASK_DEVDATA_TRGS`) and task-specific test data (with `TASK_TESTDATA_SRCS` and `TASK_TESTDATA_TRGS`). Per-task data *directories* can be selected with `TASK_TRAINDATA`, `TASK_DEVDATA` and `TASK_TESTDATA` (relative to `DATA_DIR`, overriding the default `TRAINDATA` / `DEVDATA` / `TESTDATA` for the corresponding task).

## Output files

During evaluation, translations are written to

* `TESTDATA_OUTPUT`: `${EVAL_DIR}/${TASK_ID}.${TESTDATA_NAME}.${SRCLANG}.${TRGLANG}`

and the corresponding inference configuration to

* `INFERENCE_CONFIGFILE`: `${EVAL_DIR}/inference_${TASK_ID}.${TESTDATA_NAME}.yaml`

## Data size statistics

The makefiles can compute size statistics (lines, words, bytes) for the training data files with:

```
make make-train-datasize-files
```

The result is stored in `${TRAINDATA_SRC}.size` and `${TRAINDATA_TRG}.size`. These statistics are also used for sampling weights when `USE_DATASIZE_AS_TASK_WEIGHT=1` is set (see the [configuration reference](config.md)).