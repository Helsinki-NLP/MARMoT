
# MARMoT Experiment Makefiles - Data Configuration


Essential data directories are set in [env.mk](../env.mk)

* `DATA_DIR`: home directory of data files (train, dev and test), default is `${PROJECT_DIR}/data`
* `VOCAB_DIR`: home directory of HF tokenizers / vocabulary files, default is `${PROJECT_DIR}/tokenizer/tatoeba`
* `TRAINDATA_DIR`: home of the training data, default is `${DATA_DIR}/tatoeba/train`
* `TRAINDATA_NAME`: name of the training data, default is `tatoeba-test-v2023-09-26`
* `DEVDATA_DIR`: home of the validation data
* `DEVDATA_NAME`: name of the validation data
* `TESTDATA_DIR`: home of the test data
* `TESTDATA_NAME`: name of the test data


Default values for validation and test data depend on the availability of the data. If the directory `${DATA_DIR}/flores200/dev` exists then those data files will be used for validation (with the name `flores200-dev`). Otherwise, it will be set to `${DATA_DIR}/tatoeba/dev5K` with the name `tatoeba-test-v2023-09-26`). Note that non-existing validation files will not be added to the generated configuration file.

Similarly, the test data directory is set to `${DATA_DIR}/flores200/devtest` (with the data set name `flores200-devtest`) if it exists. Otherwise, `${DATA_DIR}/tatoeba/test` will be used with the name `tatoeba-test-v2023-09-26`).


## Task-specific data

The makefiles will by default search for task-specific data in the directories specified above. The logic for doing this is implemented in the [config.mk](../config.mk) file (see the "data sets" section). The system assumes that datasets follow the naming standards in OPUS data sets with their "moses"-style release packages. The general pattern for finding source and target language files is

* `DATA_SRC = ${XXXDATA_DIR}/*${SORTED_LANGPAIR}.${SRCLANG}.gz`: source language file
* `DATA_TRG = ${XXXDATA_DIR}/*${SORTED_LANGPAIR}.${TRGLANG}.gz`: target language file

Both files need to be aligned (same rows indicate aligned text segments). The `XXXDATA_DIR` corresponds to the directories for training, validation and test data, respectively. `SORTED_LANGPAIR` refers to the language pair of the task but with alphabetically sorted language IDs.

An exception are the Flores200 data sets. For those, we assume the following file pattern:

* `${XXXDATA_DIR}/${SRCLANG}_*)`
* `${XXXDATA_DIR}/${TRGLANG}_*)`

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
