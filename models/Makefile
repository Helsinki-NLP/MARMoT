

MODEL_STATS := $(patsubst %/Makefile,%/stats,$(wildcard */Makefile))

.PHONY: all
all: ${MODEL_STATS}
	find . -maxdepth 1 -mindepth 1 -type d | sed 's/^.\///' | sort > models.txt

.PHONY: ${MODEL_STATS}
${MODEL_STATS}:
	-${MAKE} -C $(dir $@) print-train-stats print-eval-stats
