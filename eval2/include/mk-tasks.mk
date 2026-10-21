.PHONY: mk-tasks mk-tasks-force tasks-clear

$(SELFDIR)/bin/inf_tasks.py:
> @test -f "$(SELFDIR)/bin/inf_tasks.py" || { \
>   echo "mk-tasks.mk: ❌ Missing $(SELFDIR)/bin/inf_tasks.py" >&2; \
>   exit 1; \
> }

$(TASKS_INPUT_DONE): $(TRAINCONFIG) $(VIEW_PYTHON) $(SELFDIR)/bin/inf_tasks.py | $(BAS_DONE)
> @set -euo pipefail; \
> echo "mk-tasks.mk: 🛠️ Building $(TASKSINPUT)..."; \
> module load cray-python; \
> $(VIEW_PYTHON) "$(SELFDIR)/bin/inf_tasks.py" \
>   "$(TRAINCONFIG)" "$(TASKSINPUT)"; \
> touch "$@"

$(TASKSINPUT): $(TASKS_INPUT_DONE)
> @test -f "$@"

$(TASKS): $(TASKSINPUT) | $(BAS_DONE)
> @if [ "$(FORCE_PAIRS)" = 1 ]; then \
>   if [ ! -e "$@" ] || ! cmp -s "$<" "$@"; then \
>     cp -p "$<" "$@"; \
>   else \
>     touch "$@"; \
>   fi; \
>   echo "mk-tasks.mk: ✅ Accepted proposed tasks: $@"; \
> else \
>   echo "mk-tasks.mk: ❌ Missing task selection: $@" >&2; \
>   echo "mk-tasks.mk:    Read suggestions from: $<" >&2; \
>   exit 1; \
> fi

$(PRS_DONE): $(TASKS) | $(BAS_DONE)
> @echo "mk-tasks.mk: ✅ Task selection exists:"; \
> wc -l "$(TASKS)" | sed 's/^/mk-tasks.mk:    /'; \
> touch "$@"

mk-tasks: $(PRS_DONE)

mk-tasks-force:
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" \
>   FORCE_PAIRS=1 $(FIRST_GOAL) mk-tasks
