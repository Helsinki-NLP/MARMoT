## GPU assignments: simply distribute one task per GPU/Node
## - skip the initial GPU assignments if they exist (in TASK_GPUS)
## - if NR_OF_NODES is set: rotate over available nodes

## don't allocate more nodes than what we can fill with tasks
NR_OF_NODES ?= $(shell 	if [ $(words ${TASKS}) -gt ${MAX_GPUS_PER_NODE} ]; then \
			  echo $$(( $(words ${TASKS}) / ${MAX_GPUS_PER_NODE} )); \
			else echo 1; fi )
export NR_OF_NODES

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


## find tasks allocated for each GPU
## - ALLOCATED_GPUS: all GPUs that have a task assigned
## - GPU_TASK_PAIRS: GPU-task pairs (format = gpu/task)
## - GPU_TASKID_PAIRS: GPU-taskid pairs (format = gpu/taskid)
## - GPU_TASKS: all tasks for each GPU in the same order as ALLOCATED_GPUS
##              (tasks merged with ':' if there is more than one per GPU)
## - GPU_TASK_IDS: same as above but with task_ids

ALLOCATED_GPUS := $(sort ${TASK_GPU_ASSIGNMENTS})

ifneq ($(words ${ALLOCATED_GPUS}),$(words ${TASK_IDS}))
  export MULTIPLE_JOBS_PER_GPU := 1
  export GPU_TASKID_PAIRS   := $(foreach t,${TASK_IDS},$(call lookup,$t,${TASK_IDS},${TASK_GPU_ASSIGNMENTS})/$t)
  export GPU_LANGPAIR_PAIRS := $(foreach t,${GPU_TASKID_PAIRS},$(dir $t)$(call lookup,$(notdir $t),${TASK_IDS},${TASK_LANGPAIRS}))
  export GPU_LANGPAIRS      := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(sort $(notdir $(filter $g/%,${GPU_LANGPAIR_PAIRS}))))))
  export GPU_TASK_IDS       := $(strip $(foreach g,${ALLOCATED_GPUS},$(subst ${space},:,$(notdir $(filter $g/%,${GPU_TASKID_PAIRS})))))
endif

