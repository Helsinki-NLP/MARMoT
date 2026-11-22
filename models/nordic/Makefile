

MODEL_STATS := $(patsubst %/Makefile,%/stats,$(wildcard */Makefile))

.PHONY: all
all: ${MODEL_STATS}
	find . -name stats -type d | sed 's/^.\///;s/\/stats//' | sort > models.txt
	find . -wholename '*/stats/*.txt' | xargs git add
	git add models.txt
	git pull
	git commit -am 'updated validation statistics'
	git push

PHONY: monitor
monitor:
	while true; do \
	  ${MAKE} all; \
	  sleep 3600; \
	done


.PHONY: ${MODEL_STATS}
${MODEL_STATS}:
	-${MAKE} -s -C $(dir $@) print-train-stats print-valid-stats print-eval-stats


MODEL_CONFIGS := $(addsuffix .backup,$(wildcard */mammoth/train.yaml))

PHONY: refresh-configfiles
refresh-configfiles: ${MODEL_CONFIGS}

${MODEL_CONFIGS}: %.backup: %
	mv $< $@
	${MAKE} -C $(patsubst %/mammoth/train.yaml,%,$<) -j8 train-config
