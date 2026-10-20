# MARMoT Experiment Makefiles - Task Configuration

The system applies a lot of default values that can be adjusted for specific experiments. All configuration parameters can be seen in the [configuration reference](config.md) and in [config.mk](../config.mk). Important is also to check that the [data files can be found](data.md). Changing default parameters can be done by simply overwriting variables before including the generic make files.

## Selecting tasks

Tasks are defined in the space-separated `TASKS` variable as `source-target` language pairs, e.g. `eng-deu` for translating from English to German. From the task list, the makefiles derive the task numbers `TASK_NRS` (1-based positions) and the task IDs `TASK_IDS`. By default, a task ID is built from the task number and the language pair: `task${NR}_${LANGPAIR}`, e.g. `task1_eng-deu`. You can set your own task IDs (which also allows to have several tasks for the same language pair, e.g. for back-translation data):

* `TASKS`: source-target language pairs (default: `fin-eng`)
* `TASK_IDS`: unique task IDs (default = `task${NR}_${TASK}` for each task in `TASKS`)
* `TASK_LANGPAIRS`: language pair used for the task (default = `${TASKS}`)

Many targets (e.g. `eval-task`, `print-task-progress`, config generation) operate on *the currently selected task*. The current task can be selected by setting any of these variables:

* `TASK_NR`: 1-based position in the `TASKS`/`TASK_IDS` lists (default: the last task)
* `TASK`: language pair, e.g. `eng-deu`
* `TASK_ID`: task ID, e.g. `task_eng-deu` (or whatever you defined in `TASK_IDS`)

For the current task, the language pair and its languages are available as `TASK_LANGPAIR` (defaults to `TASK`), `SRCLANG` and `TRGLANG`.

One simple example is to set task-specific GPU allocations:

```make
#-*-makefile-*-

## set tasks and GPU assignments

TASKS     := eng-deu eng-fra deu-eng fra-eng deu-fra fra-deu
TASK_GPUS := 0:0 1:0 0:1 1:1 0:2 1:2

## include common configuration and make targets
include ../make/marmot.mk
```

## GPU assignments

GPU assignments use the specification `<node>:<rank>` and in the example above distribute the tasks over 2 nodes using 3 GPUs on each node. The makefiles take care of translating this into appropriate SLURM commands with the allocations needed.

The default GPU allocation simply assigns one GPU per task, starting with node 0 and using all available GPUs on each node (= `MAX_GPUS_PER_NODE`, which is set in the host-specific [environment configuration](env.md)). You can also specify the maximum number of nodes to use with the `NR_OF_NODES` variable. In that case, the automatic GPU assignment starts again with assignment `0:0` once that maximum is filled, which gives you multiple tasks per GPU.

`TASK_GPUS` only needs to cover the *first* tasks; all following tasks automatically receive the default assignment (rotating over the nodes). The same applies to the other `TASK_*` variables described below: if fewer values than tasks are given, the remaining tasks fall back to their default values. Note that those special values are assigned to the *initial* tasks, so they need to be the first ones in the list.

You can check the resulting task-to-GPU mapping of your setup with:

```
make task-info
```

or find the task number of a given task ID with:

```
make TASK_ID=task_eng-deu find_tasknr
```

## Model architectures

The default model architecture is a base transformer with 6 encoder layers and 6 decoder layers, and both encoders and decoders use completely language-specific components. There are also a number of predefined architectures available via `MODEL_ARCHITECTURE` (`transformer-tiny`, `transformer-small`, `transformer-base`, `transformer-deepenc`, `transformer-deepdec`, `transformer-deep`, `transformer-big`, `transformer-xl`, `transformer-xxl`; see [config.mk](../config.mk)). The size of encoders and decoders can be controlled directly by

* `ENCODER_LAYERS`: list of encoder component sizes (default: `6`)
* `DECODER_LAYERS`: list of decoder component sizes (default: `6`)

The default encoder and decoder sharing classes are set by

* `DEFAULT_ENCODER`: list of default encoder component identifiers (default: the source language ID)
* `DEFAULT_DECODER`: list of default decoder component identifiers (default: the target language ID)

To change the architecture to a shared encoder with 9 layers and language-specific decoders of 3 layers you can specify your top-level makefile like this:

```make
#-*-makefile-*-

TASKS := eng-deu eng-fra deu-eng fra-eng deu-fra fra-deu

ENCODER_LAYERS  := 9
DECODER_LAYERS  := 3
DEFAULT_ENCODER := "shared"


## include common configuration and make targets
include ../make/marmot.mk
```

After that, you can simply run the top-level targets like `make train` to create the SLURM script and submit it.

For more advanced architectures with multiple components and layer sharing you need to define individual layer sharing classes using the variables `TASK_ENCODERS` and `TASK_DECODERS`. Each task needs its own encoder and/or decoder specification in that case, with one list entry per layer group. For example, creating a model with 3 language-specific layers followed by 6 shared layers you can specify your experiment in this way:

```make
#-*-makefile-*-

ENCODER_LAYERS  := 3,6
DECODER_LAYERS  := 3

TASKS           :=  eng-deu   eng-fra   deu-eng   fra-eng   deu-fra   fra-deu
TASK_ENCODERS   := "eng,all" "eng,all" "deu,all" "fra,all" "deu,all" "fra,all"


## include common configuration and make targets
include ../make/marmot.mk
```

In encoder/decoder specifications you can also use the placeholders `{lang}` (the language ID of the source/target language), `{langgroup}` (the language group from the `LANGUAGES`/`LANGUAGE2GROUP` mapping in `utilities.mk`) and `{task}` (the task type, i.e. the prefix of the task ID up to the first underscore). For example `"{langgroup}-{lang}"` or `"{task}-{lang}"`.

There are many other model architecture parameters that can be adjusted by setting the appropriate variables. Have a look into the `model architecture` section in [config.mk](../config.mk) or in the [configuration reference](config.md).

## Other task-specific configuration

The following variables require space-separated lists with one value per task. As explained above, it is possible to only specify a smaller number of values than the number of tasks; in that case the initial tasks will be assigned the values specified here and all other tasks will obtain the default values:

* `TASK_GPUS`: GPU assignments (`<node>:<gpu>`, default = `0:0` rotating over nodes)
* `TASK_WEIGHTS`: weight for data sampling (default: 1.0)
* `TASK_TRANSFORMS`: transformations to apply to the data (default = `filtertoolong`)
* `TASK_TRAINSTEPS`: training step when to introduce a task (default = 0)
* `TASK_ENCODERS`: encoder sharing classes (default = `${SRCLANG}`)
* `TASK_DECODERS`: decoder sharing classes (default = `${TRGLANG}`)
* `TASK_SRCPREFIXES` / `TASK_TRGPREFIXES`: source/target prefixes added to the data (used together with `ADD_LANGUAGE_TOKEN`, see below)
* `TASK_TRAINDATA_SRCS` / `TASK_TRAINDATA_TRGS`: source/target language training data files
* `TASK_TRAINDATA` / `TASK_DEVDATA` / `TASK_TESTDATA`: per-task data *directories* (relative to `DATA_DIR`)
* `TASK_DEVDATA_SRCS` / `TASK_DEVDATA_TRGS`: source/target language validation data files
* `TASK_TESTDATA_SRCS` / `TASK_TESTDATA_TRGS`: source/target language test data files
* `TASK_TRAINDATA_BASENAMES` / `TASK_DEVDATA_BASENAMES` / `TASK_TESTDATA_BASENAMES`: per-task file name patterns (see [data configuration](data.md))

### Language tokens for multilingual models

If `ADD_LANGUAGE_TOKEN=true`, language tokens are added to the source and target side using the `prefix` transform. The default prefixes are `>>${TRGLANG}<<` on the source side (`>>target<<`) and `<<${SRCLANG}>>` on the target side (`<<source>>`), but they can be adapted per task with `TASK_SRCPREFIXES` and `TASK_TRGPREFIXES`.

### Denoising tasks

Monolingual (`denoising`) tasks can be added by giving the same language for source and target, e.g. `eng-eng`, and setting the transform `denoising` (in addition to `filtertoolong`). For those tasks the makefiles automatically use different file extensions for the source and target files (`eng1.gz` / `eng2.gz`) so that source and target data are not mixed up. Denoising tasks are skipped by default in evaluation; see `SKIP_DENOISING_EVAL_TASKS` in [eval.mk](../eval.mk). Validation is enabled for them unless `SKIP_DENOISING_VALID_TASKS=1` is set (similarly `SKIP_SAME_LANGUAGE_VALID_TASKS` for other monolingual tasks; both default to `0` in [config.mk](../config.mk)).

## Vocabularies

Tokenizers and vocabularies are taken directly from the `VOCAB_DIR` and follow a fixed directory layout: one tokenizer per language and vocabulary size in `${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json`. The main variables are:

* `VOCAB`: name of the tokenizer directory (default = `tatoeba`)
* `VOCAB_DIR`: home directory of the HF tokenizers / vocabulary files (default = `${PROJECT_DIR}/tokenizer/${VOCAB}`)
* `VOCAB_SIZE`: vocabulary size (default = 32000)
* `VOCAB_SRC_SIZE` / `VOCAB_TRG_SIZE`: vocabulary size of the source/target tokenizers (default = `VOCAB_SIZE`)
* `VOCAB_SRC_DIR` / `VOCAB_TRG_DIR`: source/target tokenizer directories (default = `VOCAB_DIR`)
* `VOCAB_SRC_FILE` / `VOCAB_TRG_FILE`: full path to the source/target tokenizer file (default as in the layout above)

The makefiles automatically collect the unique set of source and target languages over all tasks for the `src_vocab` and `tgt_vocab` sections of the generated configuration. Adjust the variables to match your environment if the default layout does not apply.