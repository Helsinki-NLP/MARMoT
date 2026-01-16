
# MARMoT Experiment Makefiles - Task Configuration


The system applies a lot of default values that can be adjusted for specific experiments. All configuration parameters can be seen in [../config.mk](config.mk). Important is also to check that [data files can be found](data.md). Changing default parameters can be done by simply overwriting variables before including the generic make files. One simple example is to set task-specific GPU allocations:


```make
#-*-makefile-*-

## set tasks and GPU assignments

TASKS     := eng-deu eng-fra deu-eng fra-eng deu-fra fra-deu
TASK_GPUS := 0:0 1:0 0:1 1:1 0:2 1:2

## include common configuration and make targets
include ../../../make/marmot.mk
```

GPU assignments use the specification as `<node>:<rank>` and in the example above to distribute the tasks over 2 nodes using 3 GPUs on each node. The makefiles take care of translating this into appropriate SLURM commands with the allocations needed. The default GPU allocation would simply assign one GPU per task starting with node 0 and using all available GPUs on each node. One can also specify the maximum number of nodes that you want to allocate using the `NR_OF_NODES` variable. In that case, the automatic GPU assignment will start again with assignment `0:0` once that maximum is reached and filled. In that case, you would get multiple tasks per GPU.



## Model architectures


The default model architecture is a base transformer with 6 encoder layers and 6 decoder layers and both, encoders and decoders will use completely language-specific components. This behaviour can be changed in various ways. For example, the size of encoders and decoders can be controlled by

* `ENCODER_LAYERS`: list of encoder component sizes (default: `6`)
* `DECODER_LAYERS`: list of decoder component sizes (default: `6`)


The default encoder and decoder sharing classes are set by

* `DEFAULT_ENCODER`: list of default encoder component identifiers (default: the source language ID)
* `DEFAULT_DECODER`: list of default decoder component identifiers (default: the target language ID)

To change the architecture to a shared encoder with 9 layers and language-specific decoders of 3 layers you can specify your top-level makefile like this:

```make
#-*-makefile-*-

TASKS := eng-deu eng-fra deu-eng fra-eng deu-fra fra-deu

ENCODER_LAYERS  := 6
DECODER_LAYERS  := 3
DEFAULT_ENCODER := "shared"


## include common configuration and make targets
include ../../../make/marmot.mk
```

After that, you can simply run the top-level targets like `make train` to create the SLURM script and submit it.


For more advanced architectures with multiple components and layer sharing you would need to define individual layer sharing classes using the variables `TASK_ENCODERS` and `TASK_DECODERS`. For example, creating a model with 3 language-specific layers followed by 6 shared layers you can specify your experiment in this way:


```make
#-*-makefile-*-

ENCODER_LAYERS  := 3,6
DECODER_LAYERS  := 3

TASKS           :=  eng-deu   eng-fra   deu-eng   fra-eng   deu-fra   fra-deu
TASK_ENCODERS   := "eng,all" "eng,all" "deu,all" "fra,all" "deu,all" "fra,all"


## include common configuration and make targets
include ../../../make/marmot.mk
```

Note, that you need an encoder specification for each task in that case.

There is many other model architecture parameters that can be adjusted by setting the appropriate variables. Have a look into the `model architecture` section in [config.mk](../config.mk).



## Other task specific configuration


The following variables require space-separated lists with one values per task. It is possible to only specify a smaller number of values than the number of tasks. In that case, the initial tasks will be assigned with the values specified here and other tasks will obtain the default values. That can be useful for adding some special GPU assignments and sampling weights only for a small number of tasks. But those need to be the initial ones!

* `TASK_GPUS`: GPU assignments
* `TASK_WEIGHTS`: weight for data sampling (default: 1.0)
* `TASK_TRANSFORMS`: transformations to apply to the data (default = `filtertoolong`)
* `TASK_TRAINSTEPS`: step number when to introduce a task (default = 0)
* `TASK_ENCODERS`: encoder sharing classes
* `TASK_ENCODERS`: decoder sharing classes
* `TASK_TRAINDATA_SRCS`: source language training data
* `TASK_TRAINDATA_TRGS`: target language training data



## Vocabularies

Tokenizers and vocabularies are now quite hard-coded and taken directly from the `VOCAB_DIR`. This needs to be adjusted if the setup does not match your environment.

* `VOCAB_SIZE`: voabulary size (default = 32000)
* `VOCAB_FILE`: location of the HF tokenizer file (default = `${VOCAB_DIR}/${LANGID}/${VOCAB_SIZE}/tokenizer.json`)

