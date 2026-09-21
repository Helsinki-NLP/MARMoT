.PHONY: refresh-calls calls clean-calls mk-calls mk-calls-force clean-calls clean

calls: $(INF_CALLS) $(PLAN_LOG)
> @echo   "mk-calls.mk:    Logged to $(PLAN_LOG)"; \
> echo    "mk-calls.mk:    Created   $(CFGDIR)/*.yaml"; \
> echo -n "mk-calls.mk:    The number of yaml files is "; \
> find "$(CFGDIR)" -maxdepth 1 -type f -name '*.yaml' | wc -l; \
> echo "mk-calls.mk: ✅ Lines in prepared task files:";\
> wc -l $(TSKDIR)/*.out 2>/dev/null | sed 's/^/mk-calls.mk:    /'
> @echo "mk-calls.mk: ✨ I am happy with the yaml files and the planned inference calls."; \
> echo

clean-calls:
> rm -f $(INF_CALLS) $(SACRE_CALLS) $(COMET_CALLS) $(PLAN_LOG) $(PLAN_ERR)
> @echo "mk-calls.mk: ✨ Cleaning of calls done."; \
> echo

clean: clean-calls 
> rm -f $(CFGDIR)/*.yaml 
> @echo "mk-calls.mk: ✨ Cleaning of inference yaml files done."; \
> echo

mk-calls: calls 
> @true

mk-calls-force: 
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" FORCE_PAIRS=1 $(FIRST_GOAL) calls

$(INF_CALLS): $(PLAN_LOG)
> @test -f "$(INF_CALLS)"

$(PLAN_LOG): $(TRAINCONFIG) $(MAMMOTH_SELECTED) $(PRS_DONE) | $(EVAL_DIRS)
> @set -euo pipefail; \
> echo "mk-calls.mk: 🛠️ Creating tentative testing tasks..."; \
> export MAMMOTH="$$(cat "$(MAMMOTH_SELECTED)")"; \
> export LOGDIR="$(LOGDIR)"; \
> export SCRDIR="$(SCRDIR)"; \
> export MODEL="$(MODEL)"; \
> export TRAINCONFIG="$(TRAINCONFIG)"; \
> export TSKDIR="$(TSKDIR)"; \
> export CFGDIR="$(CFGDIR)"; \
> export HYPDIR="$(HYPDIR)"; \
> export DATADIR="$(DATADIR)"; \
> export ZEROSHOTPAIRS="$(ZEROSHOTPAIRS)"; \
> export SUPERVISEDPAIRS="$(SUPERVISEDPAIRS)"; \
> module load cray-python; \
> if "$(VIEW_PYTHON)" "$(SELFDIR)/bin/inf_plan.py" \
>      >"$(PLAN_ERR)" 2>&1 \
>    && grep -Fq 'All stages of planning completed' "$(PLAN_ERR)"; then \
>   mv "$(PLAN_ERR)" "$(PLAN_LOG)"; \
> else \
>   rm -f "$(PLAN_LOG)"; \
>   echo "mk-calls.mk: ❌ Planning failed."; \
>   echo "mk-calls.mk:    The last 20 lines from $(PLAN_ERR):"; \
>   echo -----------------------------------; \
>   tail -20 "$(PLAN_ERR)"; \
>   echo -----------------------------------; \
>   exit 1; \
> fi


