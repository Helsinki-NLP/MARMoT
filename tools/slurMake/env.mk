#-*-makefile-*-

SHELL  := /bin/bash
PWD    := $(shell pwd | xargs realpath)
WHOAMI := $(shell whoami)


## host specific configuration:
## - try to find some know hosts in HOSTNAME
## - LUMI is used as default

ifndef HPC_HOST
  ifeq ($(findstring puhti,${HOSTNAME}),puhti)
    HPC_HOST := puhti
  else ifeq ($(findstring mahti,${HOSTNAME}),mahti)
    HPC_HOST := mahti
  else
    HPC_HOST := lumi
  endif
endif


## include host-specific configuration

MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include ${MAKEFILE_DIR}env/${HPC_HOST}.mk


## some default values (in case those variables are not set yet)

HPC_PROJECT      ?= project_2001194
MAX_MEM_PER_GPU  ?= 32
MAX_CPUS_PER_GPU ?= 10

