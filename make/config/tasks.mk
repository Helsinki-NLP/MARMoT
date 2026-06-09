
##-----------------------------------------------------------------------------
## if no TASKS are defined: try to get the tasks from the TASK_IDS
## --> assumes that the task follows an underscore like in "task_fin-eng"
##-----------------------------------------------------------------------------

ifeq (${TASKS},)
ifdef TASK_IDS
  TASKS := $(shell echo ${TASK_IDS} | tr " " "\n" | sed 's/^[^_]*_//')
endif
endif

TASKS          ?= fin-eng
TASK_NRS       := $(shell seq $(words ${TASKS}))
TASK_IDS       ?= $(foreach t,${TASK_NRS},task$t_$(word $t,${TASKS}))
# TASK_IDS     ?= $(patsubst %,task_%,${TASKS})
TASK_TYPES     ?= $(notdir $(subst _,/,$(TASK_IDS)))
TASK_LANGPAIRS ?= ${TASKS}


## select a task as the current one

TASK_NR       ?= $(words $(TASKS))
TASK          := $(word ${TASK_NR},$(TASKS))
TASK_LANGPAIR ?= $(word ${TASK_NR},$(TASK_LANGPAIRS))


## languages for the task data

LANGPAIR ?= $(word ${TASK_NR},$(TASKS))
SRCLANG  ?= $(firstword $(subst -, ,${LANGPAIR}))
TRGLANG  ?= $(lastword  $(subst -, ,${LANGPAIR}))



##-----------------------------------------------------------------------------
## GPU assignments: simply distribute one task per GPU/Node
## - skip re-assigning the initial GPU assignments if they exist (in TASK_GPUS)
## - if NR_OF_NODES is set: rotate over available nodes
##-----------------------------------------------------------------------------

## don't allocate more nodes than what we can fill with tasks
ifndef NR_OF_NODES
  NR_OF_NODES ?= $(shell if [ $(words ${TASKS}) -gt ${MAX_GPUS_PER_NODE} ]; then \
			  echo $$(( $(words ${TASKS}) / ${MAX_GPUS_PER_NODE} )); \
			 else echo 1; fi )
  export NR_OF_NODES
endif

ifndef TASK_GPU_ASSIGNMENTS
  export TASK_GPU_ASSIGNMENTS := $(shell \
	n=0; g=0; \
	tasks=(${TASKS}); \
	gpus=(${TASK_GPUS}); \
	for i in `seq $(words ${TASKS})`; do \
	  t=$${tasks[$$i-1]}; \
	  a=$${gpus[$$i-1]}; \
	  if [ "$$a" != "" ]; then \
	    echo $$a; \
	  else \
	    echo "$$n:$$g"; \
	    ((g++)); \
	    if [ $$g -eq ${MAX_GPUS_PER_NODE} ]; then \
	      ((n++)); \
	      g=0; \
	    fi; \
	    if [ "${NR_OF_NODES}" != "" ]; then \
	       if [ $$n -eq ${NR_OF_NODES} ]; then \
	         n=0; \
	       fi \
	    fi; \
	  fi \
	done )
endif


## TODO: do we still need this? (this is mostly for reporting target in train.mk, is it?)
##       is it enough to set MULTIPLE_JOBS_PER_GPU?
##
## find tasks allocated for each GPU (those calls are very expensive and slow down make!)
## - ALLOCATED_GPUS: all GPUs that have a task assigned
## - GPU_TASK_PAIRS: GPU-task pairs (format = gpu/task)
## - GPU_TASKID_PAIRS: GPU-taskid pairs (format = gpu/taskid)
## - GPU_TASKS: all tasks for each GPU in the same order as ALLOCATED_GPUS
##              (tasks merged with ':' if there is more than one per GPU)
## - GPU_TASK_IDS: same as above but with task_ids

ALLOCATED_GPUS := $(sort ${TASK_GPU_ASSIGNMENTS})

ifneq ($(words ${ALLOCATED_GPUS}),$(words ${TASK_IDS}))
  export MULTIPLE_JOBS_PER_GPU := 1
  ifndef GPU_TASK_IDS
    export GPU_TASKID_PAIRS   := $(foreach t,${TASK_IDS},$(call lookup,$t,${TASK_IDS},${TASK_GPU_ASSIGNMENTS})/$t)
    export GPU_LANGPAIR_PAIRS := $(foreach t,${GPU_TASKID_PAIRS},$(dir $t)$(call lookup,$(notdir $t),${TASK_IDS},${TASK_LANGPAIRS}))
    export GPU_LANGPAIRS      := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(sort $(notdir $(filter $g/%,${GPU_LANGPAIR_PAIRS}))))))
    export GPU_TASK_IDS       := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(notdir $(filter $g/%,${GPU_TASKID_PAIRS})))))
  endif
endif



##-----------------------------------------------------------------------------
## set parameters for current task
##-----------------------------------------------------------------------------


# current task specifications - default values

ifeq (${ADD_LANGUAGE_TOKEN},true)
  DEFAULT_TRANSFORM  ?= prefix,filtertoolong
  DEFAULT_SRCPREFIX  ?= >>${TRGLANG}<<
  DEFAULT_TRGPREFIX  ?= <<${SRCLANG}>>
endif

DEFAULT_GPU        ?= 0:0
DEFAULT_TRANSFORM  ?= filtertoolong
DEFAULT_TRAINSTEP  ?= 0
DEFAULT_ENCODER    ?= "${SRCLANG}"
DEFAULT_DECODER    ?= "${TRGLANG}"

ENCODER    ?= ${DEFAULT_ENCODER}
DECODER    ?= ${DEFAULT_DECODER}
TRANSFORM  ?= ${DEFAULT_TRANSFORM}


# current task specifications - selected with TASK_NR or default value

TASK_ID        := $(firstword $(word ${TASK_NR},$(TASK_IDS))             task${TASK_NR}_${TASK})
TASK_TYPE      := $(firstword $(word ${TASK_NR},$(TASK_TYPES))           $(notdir $(subst _,/,$(TASK_ID))))
TASK_GPU       := $(firstword $(word ${TASK_NR},$(TASK_GPU_ASSIGNMENTS)) $(DEFAULT_GPU))
TASK_TRAINSTEP := $(firstword $(word ${TASK_NR},$(TASK_TRAINSTEPS))      $(DEFAULT_TRAINSTEP))
TASK_SRCPREFIX := $(firstword $(word ${TASK_NR},$(TASK_SRCPREFIXES))     $(DEFAULT_SRCPREFIX))
TASK_TRGPREFIX := $(firstword $(word ${TASK_NR},$(TASK_TRGPREFIXES))     $(DEFAULT_TRGPREFIX))
TASK_TRANSFORM := $(firstword $(word ${TASK_NR},$(TASK_TRANSFORMS))      $(TRANSFORM))
TASK_ENCODER   := $(firstword $(word ${TASK_NR},$(TASK_ENCODERS))        $(ENCODER))
TASK_DECODER   := $(firstword $(word ${TASK_NR},$(TASK_DECODERS))        $(DECODER))


## replace variables for {lang} and {langgroup}

ifeq ($(findstring {lang,${TASK_ENCODER}),{lang)
  TASK_ENCODER := $(subst {langgroup},$(call langgroup,${SRCLANG}),$(subst {lang},${SRCLANG},${TASK_ENCODER}))
endif
ifeq ($(findstring {lang,${TASK_DECODER}),{lang)
  TASK_DECODER := $(subst {langgroup},$(call langgroup,${TRGLANG}),$(subst {lang},${TRGLANG},${TASK_DECODER}))
endif


## add language tokens and prefix transform if necessary

ADD_LANGUAGE_TOKEN ?= false

ifneq (${TASK_SRCPREFIX}${TASK_TRGPREFIX},)
ifneq ($(findstring prefix,$(TASK_TRANSFORM)),prefix)
  TASK_TRANSFORM := prefix,${TASK_TRANSFORM}
  ADD_LANGUAGE_TOKEN := true
endif
endif



