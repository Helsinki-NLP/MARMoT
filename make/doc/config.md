# MARMoT Experiment Makefiles - Configuration Reference

This page lists the most important configuration variables of the makefiles, their defaults and where they are defined. All variables are defined with `?=`, which means you can simply overwrite them in your own makefile **before** including `../make/marmot.mk`. Variables set afterwards (or derived variables computed from them) will not be updated.

The defaults are defined in [config.mk](../config.mk) and the included modules [config/tasks.mk](../config/tasks.mk), [config/data.mk](../config/data.mk), [config/vocab.mk](../config/vocab.mk), [config/model.mk](../config/model.mk), [config/training.mk](../config/training.mk) and [config/inference.mk](../config/inference.mk). Environment-specific defaults can be found in [env.mk](../env.mk), the SLURM-related ones in [slurm.mk](../slurm.mk).

## Output locations

| variable | default | description |
|---|---|---|
| `EXPERIMENT_DIR` | `${PWD}` | the directory make is run from; SLURM jobs are started from here |
| `MODEL_NAME` | `mammoth` | name of the experiment / model |
| `MODEL_DIR` | `${EXPERIMENT_DIR}/${MODEL_NAME}` | directory for config, logs and checkpoints |
| `MODEL_PATH` | `${MODEL_DIR}/model` | checkpoint path (`save_model`) |
| `MODEL_META` | `${MODEL_PATH}_checkpoint_metadata.json` | metadata file; if it exists, training is continued from the existing checkpoint |
| `EVAL_DIR` | `${MODEL_DIR}/eval` | directory for evaluation configs, translations and scores |
| `TRAIN_STAGE` | `train` | name of the training stage; used for config and SLURM file names |
| `TRAIN_CONFIGFILE` | `${MODEL_DIR}/${TRAIN_STAGE}.yaml` | generated training config |
| `INFERENCE_CONFIGFILE` | `${EVAL_DIR}/inference_${TASK_ID}.${TESTDATA_NAME}.yaml` | generated inference config for the current task |

## Transformer backend

| variable | default | description |
|---|---|---|
| `TRANSFORMER_BACKEND` | `pytorch` | backend used by MAMMOTH, either `pytorch` or `x-transformers` |

## Tasks

| variable | default | description |
|---|---|---|
| `TASKS` | `fin-eng` | space-separated list of `source-target` language pairs |
| `TASK_IDS` | `task${NR}_${TASK}` for each task | unique task IDs, one per task (you can use several tasks with the same language pair by giving distinct IDs) |
| `TASK_LANGPAIRS` | `${TASKS}` | language pair used for each task |
| `TASK_NRS` | `1 ... n` | 1-based task numbers, derived from `TASKS` |
| `TASK` / `TASK_ID` / `TASK_NR` | - | selectors for the *current task* (used by `eval-task`, `print-task-progress`, ...); `TASK_NR` defaults to the last task |
| `LANGPAIR` / `SRCLANG` / `TRGLANG` | from the current task | languages of the current task |

## GPU allocation

| variable | default | description |
|---|---|---|
| `TASK_GPUS` | automatic | GPU assignment per task, format `<node>:<gpu>`; only needs to cover the first tasks |
| `NR_OF_NODES` | derived from the GPU assignments | number of node ranks used (SLURM `--nodes`); if set, the automatic GPU assignment rotates over at most this many nodes |
| `MAX_GPUS_PER_NODE` | host-specific | number of GPUs on one node (set in `env/<host>.mk`) |

The automatic assignment places one task per GPU on node 0, then continues on the next node once all GPUs of a node are filled. The `rotating_gpu_assignment` helper function in [utilities.mk](../utilities.mk) can be used to generate such lists programmatically, e.g. `$(call rotating_gpu_assignment,0,2,12)`.

## Task-specific values

The following variables take space-separated lists with *one value per task*. If fewer values than tasks are given, the remaining tasks fall back to their defaults.

| variable | default | description |
|---|---|---|
| `TASK_GPUS` | `0:0` (rotating) | GPU assignment per task |
| `TASK_WEIGHTS` | `1.0` | weight for data sampling per task |
| `TASK_TRAINSTEPS` | `0` | training step at which the task is introduced |
| `TASK_TRANSFORMS` | `filtertoolong` | data transformations per task (e.g. `denoising,filtertoolong`) |
| `TASK_ENCODERS` | `${SRCLANG}` | encoder sharing classes per task |
| `TASK_DECODERS` | `${TRGLANG}` | decoder sharing classes per task |
| `TASK_SRCPREFIXES` / `TASK_TRGPREFIXES` | `>>${TRGLANG}<<` / `<<${SRCLANG}>>` | source/target prefixes when `ADD_LANGUAGE_TOKEN=true` |

The non-list versions `TASK_GPU`, `TASK_TRAINSTEP`, `TASK_TRANSFORM`, `TASK_ENCODER`, `TASK_DECODER`, `TASK_SRCPREFIX`, `TASK_TRGPREFIX` refer to the currently selected task. In `TASK_ENCODERS`/`TASK_DECODERS` the placeholders `{lang}`, `{langgroup}` and `{task}` can be used.

## Data

| variable | default | description |
|---|---|---|
| `DATA_DIR` | `${PROJECT_DIR}/data` | home directory of the data files |
| `TRAINDATA` | `tatoeba/train` | relative path of the training data directory |
| `TRAINDATA_NAME` | `tatoeba-test-v2023-09-26` | name of the training data set |
| `DEVDATA` / `DEVDATA_NAME` | `flores200/dev` / `flores200-dev` if it exists, else `tatoeba/dev5K` / `tatoeba-test-v2023-09-26` | validation data |
| `TESTDATA` / `TESTDATA_NAME` | `flores200/devtest` / `flores200-devtest` if it exists, else `tatoeba/test` / `tatoeba-test-v2023-09-26` | test data |
| `TRAINDATA_DIR` / `DEVDATA_DIR` / `TESTDATA_DIR` | `${DATA_DIR}/...` | data directories for the current task |
| `TASK_TRAINDATA` / `TASK_DEVDATA` / `TASK_TESTDATA` | - | per-task data directories (relative to `DATA_DIR`) |
| `TASK_TRAINDATA_SRCS` / `TASK_TRAINDATA_TRGS` | - | per-task training data files |
| `TASK_DEVDATA_SRCS` / `TASK_DEVDATA_TRGS` | - | per-task validation data files |
| `TASK_TESTDATA_SRCS` / `TASK_TESTDATA_TRGS` | - | per-task test data files |
| `TRAINDATA_BASENAME` / `DEVDATA_BASENAME` / `TESTDATA_BASENAME` | `*${SORTED_LANGPAIR}*` | file name patterns (see [data configuration](data.md)) |
| `TASK_*_BASENAMES` | - | per-task file name patterns |
| `TRAINDATA_SRC` / `TRAINDATA_TRG` | auto-detected | actual source/target training files of the current task |
| `DEVDATA_SRC` / `DEVDATA_TRG`, `TESTDATA_SRC` / `TESTDATA_TRG` | auto-detected | validation/test files of the current task |
| `TESTDATA_OUTPUT` | `${EVAL_DIR}/${TASK_ID}.${TESTDATA_NAME}.${SRCLANG}.${TRGLANG}` | output file for translations |

More details on the data lookup can be found in the [data configuration documentation](data.md).

## Vocabularies

| variable | default | description |
|---|---|---|
| `VOCAB` | `tatoeba` | name of the tokenizer directory |
| `VOCAB_DIR` | `${PROJECT_DIR}/tokenizer/${VOCAB}` | home directory of the HF tokenizers |
| `VOCAB_SIZE` | `32000` | vocabulary size |
| `VOCAB_SRC_SIZE` / `VOCAB_TRG_SIZE` | `${VOCAB_SIZE}` | source/target vocabulary sizes |
| `VOCAB_SRC_DIR` / `VOCAB_TRG_DIR` | `${VOCAB_DIR}` | source/target tokenizer directories |
| `VOCAB_SRC_FILE` / `VOCAB_TRG_FILE` | `${VOCAB_DIR}/${LANG}/${VOCAB_SIZE}/tokenizer.json` | full tokenizer paths |

The layout `${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json` is assumed for the tokenizer files.

## Model architecture

Predefined architectures can be selected with `MODEL_ARCHITECTURE` (`transformer-tiny`, `transformer-small`, `transformer-base`, `transformer-deepenc`, `transformer-deepdec`, `transformer-deep`, `transformer-big`, `transformer-xl`, `transformer-xxl`). The main model parameters:

| variable | default | description |
|---|---|---|
| `MODEL_ARCHITECTURE` | `transformer-base` | preset that sets the parameters below |
| `ENCODER_LAYERS` | `6` | encoder layer groups, e.g. `3,6` for 3 language-specific + 6 shared layers |
| `DECODER_LAYERS` | `6` | decoder layer groups |
| `MODEL_DIMENSION` | `512` (presets differ) | transformer model dimension |
| `MODEL_DTYPE` | `bf16` (`fp32` on PUHTI) | parameter precision / dtype |
| `DROPOUT_RATE` | `0.1` | dropout rate |
| `ADD_LANGUAGE_TOKEN` | `false` | add `>>target<<` / `<<source>>` language tokens (uses the `prefix` transform) |
| `TRF_HEADS` | `8` | number of attention heads (`heads`) |
| `TRF_ROTARY_POS_EMBEDDINGS` | `true` | use rotary positional embeddings |
| `TRF_POST_EMB_NORM` | `true` | apply (RMS)Norm after token embedding |
| `TRF_ATTN_DROPOUT` / `TRF_FF_DROPOUT` | `0.1` / `0.1` | attention / feed-forward dropout |
| `TRF_FF_ACTIVATION` | `swiglu` | feed-forward activation (`swiglu` or `gelu`) |

The `XTRF_*` variables (`XTRF_FLASH_ATTENTION`, `XTRF_PRE_NORM`, `XTRF_LAYERNORM_BIAS`, `XTRF_USE_ABS_POS_EMB`, `XTRF_TIE_EMBEDDINGS`, ...) configure the x-transformers backend and inherit their defaults from the `TRF_*` variables where applicable.

## Training

| variable | default | description |
|---|---|---|
| `BATCH_TYPE` | `tokens` | type of training batch unit |
| `BATCH_SIZE` | `8192` (`4096` on PUHTI, `32768` for the `transformer-tiny`/`transformer-small` presets) | batch size **per GPU** |
| `MIN_SRCSEQ_LENGTH` / `MIN_TRGSEQ_LENGTH` | `1` / `1` | minimum sequence lengths |
| `MAX_SEQ_LENGTH` | `1024` | default maximum sequence length |
| `MAX_SRCSEQ_LENGTH` / `MAX_TRGSEQ_LENGTH` | `${MAX_SEQ_LENGTH}` | maximum source/target lengths |
| `VALID_BATCH` | `16` | validation batch size (sentences) |
| `VALID_MAX_LENGTH` | `${MAX_SEQ_LENGTH}` | maximum length for validation |
| `VALID_TIMEOUT` / `VALID_DECODE_TIMEOUT` | `300` / `60` | validation timeouts (seconds) |
| `GRADIENT_ACCUM` | `20` | gradient accumulation (number of batches), written as `accum_count` |
| `LOOK_AHEAD` | `80` | batch look-ahead for length sorting |
| `QUEUE_SIZE` | `120` | data loader queue size |
| `VALID_FREQ` | `2500` | validation frequency (steps) |
| `VALID_METRICS` | `bleu,chrf` | validation metrics |
| `SAVE_FREQ` | `2500` | checkpoint saving frequency (steps) |
| `KEEP_CHECKPOINTS` | `1` | number of checkpoints to keep |
| `REPORT_FREQ` | `500` | progress reporting frequency (steps) |
| `REPORT_TFLOPS` | `true` | report TFLOPS |
| `TENSORBOARD` | `true` | enable TensorBoard logging |
| `TENSORBOARD_DIR` | `${EXPERIMENT_DIR}/tb_logs` | TensorBoard log directory |
| `TRAINING_STEPS` | `250000` | number of training steps |
| `EARLY_STOPPING` | `5` | stop after this many validation steps without improvement |
| `OPTIMIZER` | `adamw` | optimizer |
| `LEARNING_RATE` | `0.0003` | learning rate |
| `ADAM_BETA1` / `ADAM_BETA2` | `0.9` / `0.95` | Adam betas |
| `WEIGHT_DECAY` | `0.01` | weight decay |
| `MAX_GRAD_NORM` | `1.0` | maximum gradient norm |
| `LABEL_SMOOTHING` | `0.1` | label smoothing |
| `WARMUP_STEPS` | `1000` | number of warmup steps |
| `DECAY_METHOD` | `linear_warmup` | learning rate decay method |
| `LR_DECAY` | `0.5` | learning rate decay factor |
| `DECAY_START` | `10000` | step at which decay starts |
| `AVERAGE_DECAY` | `0` | model averaging decay |
| `RANDOM_SEED` | `42` | random seed |
| `RESET_OPTIMIZER` | `none` | optimizer reset when continuing training |
| `PRETRAINED_MODEL` | - | path to a pretrained model to initialize from (`train_from`) |
| `MASTER_PORT` | `9973` | port for distributed training communication |
| `TRAIN_RESTARTS` | `0` | maximum number of automatic SLURM restarts for training jobs |

### Task sampling

* `TASK_DISTRIBUTION`: sampling strategy (default `weighted_sampling`)
* `USE_DATASIZE_AS_TASK_WEIGHT=1`: sample proportional to the training data size (`TRAINDATA_SIZE`, requires the size files, see [data configuration](data.md))
* `TASK_WEIGHTS` / `SAMPLING_WEIGHT`: per-task / default sampling weight
* `TASK_WEIGHT_FACTORS` / `SAMPLING_FACTOR`: multiplicative factors
* `TASK_WEIGHT_TEMPS` / `SAMPLING_TEMP`: temperature for weight scaling `w^(1/T)`
* `TRAINDATA_SIZE`: total size (bytes) of the current task's training files

## Inference / decoding

| variable | default | description |
|---|---|---|
| `DECODING_BEAM_SIZE` | `4` | beam size |
| `DECODING_BATCH_SIZE` | `32` | decoding batch size |
| `DECODING_BATCH_TYPE` | `sents` | decoding batch unit |

## Evaluation and reporting

| variable | default | description |
|---|---|---|
| `MT_METRICS` | `bleu chrf` | sacrebleu metrics used in evaluation |
| `PRINT_METRIC` | `bleu` | metric shown by the reporting targets (`bleu`, `chrf`, `perplexity`, ...) |
| `PRINT_LAST` / `PRINT_FIRST` / `PRINT_FIRST_LAST` | - | restrict the reported validation steps |
| `EVAL_TASKS` | all task IDs | tasks to evaluate (space-separated task IDs) |
| `SKIP_DENOISING_EVAL_TASKS` / `SKIP_SAME_LANGUAGE_EVAL_TASKS` | `1` / `1` | skip denoising / monolingual tasks during evaluation; set to `0` to enable |
| `EVAL_NR_OF_NODES` / `EVAL_GPUS_PER_NODE` | `1` / `1` | SLURM resources for evaluation jobs |
| `EVAL_CPUS_PER_TASK` / `EVAL_MEM_PER_NODE` | `${MAX_CPUS_PER_GPU}` / `${MAX_MEM_PER_GPU}G` | CPUs/memory for evaluation jobs |
| `EVAL_TASK_WALLTIME` / `EVAL_TASKS_WALLTIME` | `00:30:00` / `24:00:00` | walltime for single-task / all-task evaluation |
| `EVAL_SLURM_TASKS` / `EVAL_PARALLEL_JOBS` | `1` / `1` | SLURM tasks and parallel make jobs during evaluation |
| `EVAL_MAX_LENGTH` | `1024` | maximum sequence length used during decoding (length filter removed) |

The available test sets for the `eval/<testset>` targets are defined in `TESTSETS` (WMT sets) and `MULTI_TESTSETS` (`wmt24pp`, `ntrex`) in [eval.mk](../eval.mk).

## Makefile-generated configuration

The targets above generate MAMMOTH configuration files ([training](train.mk)/[inference](eval.mk)) with task sections (`config-add-task`), vocabulary sections (`config-add-srcvocabs` / `config-add-trgvocabs`), model architecture, transformer, training, checkpoint and denoising parameters. The main targets that trigger this are `train-config`, `inference-config`, `train-slurm` and `eval-slurm`; see the [README](../README.md) for the top-level workflow.