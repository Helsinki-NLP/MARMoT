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

.PHONY: reset-plan
reset-plan: clean-inf-lock clean-cnt-lock clean-met-lock
> @set -euo pipefail; \
> test -f "$(TASKS)" || { \
>   echo "mk-calls.mk: ❌ Cannot reset planning: missing task selection $(TASKS)" >&2; \
>   echo "mk-calls.mk:    Resolve task selection first." >&2; \
>   exit 2; \
> }; \
> echo "mk-calls.mk: 🧹 Resetting derived planning state for $(MODELDIR)"; \
> echo "mk-calls.mk:    planner log:    $(PLAN_LOG)"; \
> echo "mk-calls.mk:    planner error:  $(PLAN_ERR)"; \
> echo "mk-calls.mk:    task plan:      $(TSKDIR)/plan.out"; \
> echo "mk-calls.mk:    inference:      $(INF_CALLS)"; \
> echo "mk-calls.mk:    sacreBLEU:      $(SACRE_CALLS)"; \
> echo "mk-calls.mk:    COMET:          $(COMET_CALLS)"; \
> rm -f \
>   "$(PLAN_LOG)" \
>   "$(PLAN_ERR)" \
>   "$(TSKDIR)/plan.out" \
>   "$(INF_CALLS)" \
>   "$(SACRE_CALLS)" \
>   "$(COMET_CALLS)" \
>   "$(INF_TASKS_DONE)"; \
>   "$(INF_SCRIPT)" \
>   "$(CNT_SCRIPT)" \
>   "$(MET_SCRIPT)" \
>   "$(INF_SBATCH)" \
>   "$(CNT_SBATCH)" \
>   "$(MET_SBATCH)"; \
> rm -f "$(TSKDIR)"/*.inf; \
> rm -f "$(CFGDIR)"/*.yaml; \
> echo "mk-calls.mk: ✅ Planning state reset."; \
> echo "mk-calls.mk:    Preserved task selection: $(TASKS)"; \
> echo "mk-calls.mk:    Preserved hypotheses: $(HYPDIR)"; \
> echo "mk-calls.mk:    Preserved scores: $(SCRDIR)"

.PHONY: reset-replan

reset-replan: reset-plan
> @$(MAKE) -C "$(SELFDIR)" --no-print-directory "$(FIRST_GOAL)" mk-calls
> @touch "$(RESET_PLAN_DONE)"
> @echo "mk-calls.mk: ✅ Reset and replan completed for $(FIRST_GOAL)"

.PHONY: reset-plan-all

reset-plan-all:
> @set -u; \
> failed=""; \
> for a in $(MODEL_ALIASES); do \
>   echo; \
>   echo "======================================================================"; \
>   echo "Resetting and replanning $$a"; \
>   echo "======================================================================"; \
>   if $(MAKE) -C "$(SELFDIR)" --no-print-directory "$$a" reset-plan \
>      && $(MAKE) -C "$(SELFDIR)" --no-print-directory "$$a" mk-calls; then \
>     echo "mk-calls.mk: ✅ $$a reset and replanned"; \
>   else \
>     echo "mk-calls.mk: ❌ $$a FAILED -- continuing with remaining models"; \
>     failed="$$failed $$a"; \
>   fi; \
> done; \
> echo; \
> if [ -n "$$failed" ]; then \
>   echo "mk-calls.mk: ❌ Reset/replan failures:"; \
>   for a in $$failed; do echo "mk-calls.mk:    $$a"; done; \
>   exit 1; \
> fi; \
> echo "mk-calls.mk: ✅ All models reset and replanned."

mk-calls: calls 
> @true

mk-calls-force: 
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" FORCE_PAIRS=1 $(FIRST_GOAL) calls

$(INF_CALLS): $(PLAN_LOG)
ifeq ($(SKIP_CALL_PLANNING),1)
$(INF_CALLS):
> @test -s "$(INF_CALLS)"
else
$(INF_CALLS): $(PLAN_LOG)
> @test -f "$(INF_CALLS)"
endif

$(PLAN_LOG): $(TRAINCONFIG) $(TRAINCONFIG_SELECTION) \
             $(MAMMOTH_SELECTED) $(PRS_DONE) \
             $(SELFDIR)/bin/plan_eval3_inference.py \
             $(SELFDIR)/bin/make_inference_yaml.py \
             | $(EVAL_DIRS)
> @set -euo pipefail; \
> echo "mk-calls.mk: 🛠️ Creating tentative testing tasks..."; \
> rm -f "$(INF_TASKS_DONE)"; \
> export MAMMOTH="$$(cat "$(MAMMOTH_SELECTED)")"; \
> export LOGDIR="$(LOGDIR)"; \
> export SCRDIR="$(SCRDIR)"; \
> export MODEL="$(MODEL)"; \
> export TRAINCONFIG="$(TRAINCONFIG)"; \
> export TSKDIR="$(TSKDIR)"; \
> export CFGDIR="$(CFGDIR)"; \
> export HYPDIR="$(HYPDIR)"; \
> export DATADIR="$(DATADIR)"; \
> export INFTASKS="$(TASKS)"; \
> export MAMMOTH_TYPE="$(MAMMOTH_TYPE)"; \
> module load cray-python; \
> if "$(VIEW_PYTHON)" "$(SELFDIR)/bin/plan_eval3_inference.py" \
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


