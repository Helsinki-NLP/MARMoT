

MODEL_STATS := $(patsubst %/Makefile,%/stats,$(wildcard */Makefile))

.PHONY: all
all: ${MODEL_STATS}
	find . -name stats -type d | sed 's/^./models/;s/\/stats//' | sort > models.txt

.PHONY: ${MODEL_STATS}
${MODEL_STATS}:
	-${MAKE} -s -C $(dir $@) print-train-stats print-eval-stats
