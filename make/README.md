
# MARMoT Experiment Makefiles

A collection of makefile targets and configurations that support the setup of various experiments with MAMMOTH and shared environments / resources.

* `marmot.mk`: top-level makefile that includes all makefiles below
* `env.mk`: essential environment variables and directories
* `config.mk`: configuration defaults and targets for generating MAMMOTH config files
* `train.mk`: targets for generating / starting SLURM training jobs
* `eval.mk`: targets evaluating models and printing score overviews
* `slurm.mk`: targets for creating and submitting SLURM scripts


## Quickstart

Simply include the top-level makefile in your own work directory and overwrite the default values to match your own experimental setup. Create your top-level makefile with your own task definitions, e.g., for training a model with tasks to translate between English and German or French (in both directions) with default settings (assuming that the [environment](doc/env.md) is set up and all [data files exist](doc/data.md) and can be found):


```make
#-*-makefile-*-

# define tasks
TASKS := eng-deu eng-fra deu-eng fra-eng

# include common configuration and make targets
include ../../../make/marmot.mk
```

Check other default settings like model architecture in [config.mk](config.mk). More about task specifications and model configuration can be found in the [task configuration documentation](doc/tasks.md). The setup requires MAMMOTH in a working [system environment](doc/env.md) (currently examples for LUMI and PUHTI are included in the repository) and [shared data-sets](doc/data.md). If all is set up correctly, you can start a training SLURM job by running:

```
make train
```

The model will be created in a sub-directory called `mammoth`. You can change the name using the variable `MODEL_NAME`. Logfiles will be stored in `mammoth/train.*.out` and `mammoth/train.*.err`. For some reasons, multi-node SLURM jobs submitted with `make train` crash with some errors about communication on LUMI. In those cases, create the SLURM script first and then submit from command-line:

```
make train-slurm
sbatch mammoth/train.slurm
```

All settings need to be specified before including the marmot-makefiles. Otherwise, the system will assume default values. The train targets should be smart enough to set the SLURM jobs correctly to assume multi-node or single-node training, based on the GPU assignments done through `TASK_GPUS`. Tasks can be allocated to the same GPU.



### Monitoring progress

Progress can be monitored with the logfiles. There are also some convenient makefile targets that print validation scores:

```
make print-validation-scores
make print-validation-diffs
```

The first command will print BLEU scores from each validation step for each task in a TAB-separated table. The second command does the same but prints BLEU-score differences for each validation step and the previous step.

The output can be modified using variables that specify the score to be shown (`PRINT_METRIC`) and the validation steps to be shown (`SELECT_LAST_VALID`, `SELECT_FIRST_VALID`, `SELECT_FIRST_LAST_VALID`), e.g. to show perplexity scores of the last 3 validation steps, run:

```
make PRINT_METRIC=perplexity SELECT_LAST_VALID=3 print-validation-scores
```

This also works for `make print-validation-diffs`.



### Evaluating models

All tasks can be evaluated using:

```
make eval
```

This will create configuration files for each task and submit SLURM jobs to translate and evaluate the default test set (flores200-devset in the current setup). Make sure that the test set exists in the directory specified in `config.mk`. A single task can also be evaluated by selecting the task by its task-number (position in the `TASKS` variable):

```
make TASK_NR=2 eval-task
```

The resulting scores an be printed using the reporting target, including a comparison to the best OPUS-MT model score from the OPUS-MT Dashboard:


```
make print-evaluation-scores
```




## Issues and To-Do's

* make it work on other compute environments
* improve data settings and documentation
* lot's of other missing features

Use at your own risk!