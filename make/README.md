# MARMoT Experiment Makefiles

A collection of makefile targets and configurations that support the setup and execution of experiments with MAMMOTH on SLURM-based HPC clusters, including shared environments and resources (currently CSC systems: LUMI, PUHTI, MAHTI and ROI-HU).

## Makefiles

| file | description |
|---|---|
| `marmot.mk` | top-level makefile, includes all makefiles below |
| `env.mk` | essential environment variables and directories; loads host-specific configuration from `env/` |
| `env/*.mk` | host-specific configurations (`lumi.mk`, `puhti.mk`, `mahti.mk`, `roihu.mk`) |
| `utilities.mk` | helper functions (`pos`, `lookup`, `langgroup`, `rotating_gpu_assignment`, ...) |
| `config.mk` | configuration defaults and targets for generating MAMMOTH config files; includes `config/*.mk` |
| `config/*.mk` | defaults for tasks, data, vocabularies, model architecture, training and inference |
| `train.mk` | targets for generating / starting training jobs and for printing training and validation statistics |
| `eval.mk` | targets for evaluating models and printing score overviews |
| `slurm.mk` | targets for creating, submitting and stopping SLURM scripts |

## Documentation

* [Environment configuration](doc/env.md)
* [Task configuration](doc/tasks.md)
* [Data configuration](doc/data.md)
* [SLURM configuration](doc/slurm.md)
* [Configuration reference](doc/config.md) (all variables and defaults)
* [Tutorial: multilingual experiments like `models/hpo`](doc/tutorial.md)

## Quickstart

Clone the repository and create your own experiment directory:

```bash
git clone https://github.com/Helsinki-NLP/MARMoT.git
cd MARMoT
git checkout sandbox
mkdir my_experiment
cd my_experiment
```

Create a makefile within your experiment directory with your own task definitions, e.g. for training a model with tasks to translate between English and German or French (in both directions) with default settings (assuming that the [environment](doc/env.md) is set up and all [data files exist and can be found](doc/data.md)):

```make
#-*-makefile-*-

## define tasks
TASKS := eng-deu eng-fra deu-eng fra-eng

## include common configuration and make targets
include ../make/marmot.mk
```

All settings need to be specified *before* including the marmot makefiles; otherwise the system will use default values. Check the other default settings like model architecture in [config.mk](config.mk) or in the [configuration reference](doc/config.md). More about task specifications and model configuration can be found in the [task configuration documentation](doc/tasks.md). The setup requires MAMMOTH in a working [system environment](doc/env.md) (currently examples for LUMI, PUHTI, MAHTI and ROI-HU are included in the repository) and [shared data-sets](doc/data.md).

If all is set up correctly, you can start a training SLURM job by running:

```
make -j8 train
```

This will generate the model configuration file (`mammoth/train.yaml`), create the SLURM script (`mammoth/train.slurm`) and submit it. The model will be created in a sub-directory called `mammoth`; you can change that name using the variable `MODEL_NAME`. Logfiles will be stored in `mammoth/train.*.out` and `mammoth/train.*.err`. The submission is recorded in `mammoth/train.slurmjob` (`.running` while it is being executed, `.done` after it finished).


The train targets should be smart enough to set up the SLURM jobs correctly for multi-node or single-node training, based on the GPU assignments done through `TASK_GPUS`. Tasks can also be allocated to the same GPU.

## Main targets

| target | purpose |
|---|---|
| `make train` | generate the training config and SLURM script, then submit the training job |
| `make train-slurm` | only generate the training config and SLURM script (`mammoth/train.slurm`), do not submit |
| `make train-config` | only generate the training config file (`mammoth/train.yaml`) |
| `make stop` / `make trainstop` | cancel the submitted training job (`scancel`) |
| `make memory-profile` | run the MAMMOTH memory profiler with the current training config |
| `make eval` | submit *one* SLURM job that evaluates all tasks on the default test set |
| `make eval-jobs` | submit *one SLURM job per task* for evaluation |
| `make TASK_NR=2 eval-task` | evaluate a single task (select by `TASK_NR`, `TASK` or `TASK_ID`) |
| `make eval/newstest2013` | evaluate on a specific test set (see list of test sets below) |
| `make print-evaluation-scores` | print the evaluation score table |
| `make print-eval-score-comparison` | score table with a comparison to the OPUS-MT dashboard |
| `make print-eval-stats` | write the evaluation score tables to `${MODEL_DIR}/stats/` |

### Monitoring progress

Progress can be monitored with the logfiles. There are also some convenient makefile targets that print training progress information and validation scores:

```
make print-training-progress
make print-validation-scores
make print-validation-diffs
```

The first command prints the training progress (steps, loss, etc.) for each task. The second command prints the validation scores for each task and validation step in a TAB-separated table (default metric: BLEU). The third command does the same but prints the score differences between each validation step and the previous one. Both score tables also include an average row.

The output can be modified using variables that specify the score to be shown (`PRINT_METRIC`) and the validation steps to be shown (`PRINT_LAST`, `PRINT_FIRST`, `PRINT_FIRST_LAST`), e.g. to show the perplexity scores of the last 3 validation steps, run:

```
make PRINT_METRIC=perplexity PRINT_LAST=3 print-validation-scores
```

This also works for `make print-validation-diffs`. The progress information can be restricted to a specific task, for example task number 2:

```
make TASK_NR=2 print-task-progress
```

The statistics read from the training logfiles, by default the most recently created `mammoth/train.*.err` file. Use `LAST_LOGFILE=/path/to/logfile` to select a specific one. The same statistics can also be written to plain text files inside `${MODEL_DIR}/stats/` with:

```
make print-train-stats
make print-valid-stats
make print-valid-diffs
```

### Evaluating models

All tasks can be evaluated using:

```
make eval
```

This will create an inference configuration file for each task and submit a SLURM job that translates and evaluates the default test set (by default the Flores-200 devtest set, `${DATA_DIR}/flores200/devtest` with the name `flores200-devtest`, if it exists; otherwise the Tatoeba test set). Make sure that the test set exists in the directory specified in [config.mk](config.mk). A single task can also be evaluated by selecting the task with `TASK_NR` (position in the `TASKS` variable), `TASK` (language pair) or `TASK_ID`:

```
make TASK_NR=2 eval-task
```

One job per task can be submitted with `make eval-jobs`. Evaluation results are stored in `${EVAL_DIR}/eval_${TASK_ID}_${TESTDATA_NAME}` (raw sacrebleu output).

Other test sets can be selected by appending the test set name to the target, e.g.:

```
make eval/newstest2013
make eval-jobs/wmttest2024
make print-eval-scores/newstest2013
```

The available test sets are defined in `TESTSETS` (mostly WMT test sets) and `MULTI_TESTSETS` (multi-parallel sets `wmt24pp` and `ntrex`) in [eval.mk](eval.mk).

The resulting scores can be printed using the reporting targets, including a comparison to the best OPUS-MT model score from the OPUS-MT Dashboard if needed:

```
make print-evaluation-scores
make print-eval-score-comparison
```

Both targets print the score for the metric given by `PRINT_METRIC` (`bleu` by default), which is one of the sacrebleu metrics computed during evaluation, defined in `MT_METRICS` (default: `bleu chrf`). Evaluation of denoising tasks or monolingual tasks is skipped by default; set `SKIP_DENOISING_EVAL_TASKS=0` / `SKIP_SAME_LANGUAGE_EVAL_TASKS=0` to enable it.

## Known issues

* GPU allocation is very simplistic and does not optimize the task distribution according to tasks and training data
* Tokenizer settings and vocabulary selections follow a fixed directory layout (`${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json`) and are not very flexible. It is possible to set individual base directories for the source and target language vocabularies using `VOCAB_SRC_DIR`, `VOCAB_TRG_DIR` and individual size parameters (`VOCAB_SRC_SIZE`, `VOCAB_TRG_SIZE`).
* job failure may not be caught properly and stale `.slurmjob` file may prevent re-submitting the job
