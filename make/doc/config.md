
# MARMoT Experiment Makefiles - Task Configuration


```make
#-*-makefile-*-


## set tasks and GPU assignments

TASKS     := eng-deu eng-fra deu-eng fra-eng deu-fra fra-deu
TASK_GPUS := 0:0 0:1 0:2 0:3 0:4 0:5

## include common configuration and make targets
## and set environment (if different from standard)

MAMMOTH_DIR := /path/to/mammoth
include ../make/marmot.mk
```
