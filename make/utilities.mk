

## pos function: get the position of a word in a word list
##
## lookup function: fetch the word in a word list that appears at the same position
##                  as a given word (key) in another word list
##
## from https://stackoverflow.com/questions/9674711/makefile-find-a-position-of-word-in-a-variable#37483527

_pos      = $(if $(findstring $1,$2),$(call _pos,$1,$(wordlist 2,$(words $2),$2),x $3),$3)
pos       = $(words $(call _pos,$1,$2))
lookup    = $(word $(call pos,$1,$2),$3)

## lookup function that returns the same string if not found
lookup_with_fallback = $(word $(call pos,$1,$1 $2),$1 $3)



## reverse language pair string

reverse = $(lastword $(subst -, ,$(1)))-$(firstword $(subst -, ,$(1)))



## matching a space

space := $(subst ,, )


## some pre-defined subset of languages
## and a mapping from languages to language-groups
## (OpenEuroLLM languages only)


LANGUAGES ?= 	bos bul cat ces dan deu ell eng \
		est eus fin fra gle glg hrv hun \
		isl ita kat lav lit mkd mlt nld \
		nno nob pol por ron slk slv spa \
		sqi srp_Cyrl swe tur ukr

LANGUAGE2GROUP ?= zls zls roa zlw gmq gmw grk gmw \
		urj euq urj roa cel roa zls urj \
		gmq roa ccs bat bat zls sem gmw \
		gmq gmq zlw roa roa zlw zls roa \
		mul zls gmq trk zle


## look up the language group for a given language ID
## (LANGUAGE2GROUP needs to match the list of language IDs in LANGUAGES)
## NOTE: this falls back to immediate language group parent from ISO standard
##       this requires the langgroup tool!



ifneq ($(shell which langgroup 2>/dev/null),)
  langgroup = $(call lookup,$1,$1 $(LANGUAGES),$(shell langgroup -p -n $1 2>/dev/null) $(LANGUAGE2GROUP))
else
  langgroup = $(call lookup_with_fallback,$1,$1 $(LANGUAGES),$1 $(LANGUAGE2GROUP))
endif




## assign GPUs over a number of nodes
## use like $(call rotating_gpu_assignment,$start,$nr_nodes,$nr_tasks) with
## $start = start node number
## $nr_nodes = number of nodes to be used
## $nr_tasks = number of tasks

rotating_gpu_assignment = $(shell \
	n=$1; g=0; \
	l=$$(( $$n + $2 )); \
	tasks=($2); \
	for i in `seq 0 $$(( $3-1 ))`; do \
	  echo "$$n:$$g"; \
	  ((g++)); \
	  if [ $$g -eq ${MAX_GPUS_PER_NODE} ]; then \
	    ((n++)); \
	    g=0; \
	  fi; \
	  if [ $$n -eq $$l ]; then \
	     n=$1; \
	  fi \
	done )


