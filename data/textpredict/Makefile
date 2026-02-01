


DATASET  := OELLM-synthetic/maxidl/nemotron-cc-english-run1
FILEBASE := nemotron-cc-english-run1-train-
LANGID   := eng
FILEID   := 00


LANGID2 := $(shell iso639 -2 -n ${LANGID})


## conversion script, adjust parameters if necessary:
## -s ...... split into sentences (each line will be one sentence)
## -m XX ... maximum line length of XX characters (default = 256)
## -M XX ... maximum length of a string of XX characters (default = 1024)

CONVERT_SCRIPT := python3 ../../tools/jsonl_to_textpredict.py
CONVERT_PARAMS := -s

all: ${LANGID}/${FILEBASE}${FILEID}.${LANGID}-${LANGID}.in.gz


.INTERMIEDIATE: ${LANGID}/${FILEBASE}${FILEID}.jsonl.gz

${LANGID}/${FILEBASE}${FILEID}.jsonl.gz:
	mkdir -p $(dir $@)
	wget -q -O $@ https://object.pouta.csc.fi/${DATASET}/translated/jsonl/$@

${FILEBASE}${FILEID}.${LANGID}-${LANGID}.in.gz: ${LANGID}/${FILEBASE}${FILEID}.jsonl.gz
	${CONVERT_SCRIPT} ${CONVERT_PARAMS} -l ${LANGID2} -i $< -S $@ -T $(@:.in.gz=.out.gz)
