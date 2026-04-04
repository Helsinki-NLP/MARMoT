

## pos function: get the position of a word in a word list
##
## lookup function: fetch the word in a word list that appears at the same position
##                  as a given word (key) in another word list
##
## from https://stackoverflow.com/questions/9674711/makefile-find-a-position-of-word-in-a-variable#37483527

_pos      = $(if $(findstring $1,$2),$(call _pos,$1,$(wordlist 2,$(words $2),$2),x $3),$3)
pos       = $(words $(call _pos,$1,$2))
lookup    = $(word $(call pos,$1,$2),$3)
lookup_with_fallback = $(firstword $(word $(call pos,$1,$2),$3) $1)



## reverse language pair string

reverse = $(lastword $(subst -, ,$(1)))-$(firstword $(subst -, ,$(1)))



## matching a space

space := $(subst ,, )
