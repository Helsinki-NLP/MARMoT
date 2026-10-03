# mk-calls (FORCE_PAIRS=1) (ensures the calls.out)
#   |
#   |   status-infer
#   |    | 
#   |    |  clean-inf-lock
#   |    |     | (ensure no process is running; no $INF_FLAG exists)
#   |    V     V
#   |   mk-infer
#   |    |  (run $INF_SBATCH)
#   V    V
# mk-infer-force

.PHONY: mk-infer mk-infer-force status-infer infer infer-score 
.PHONY: dev-g-smoke dev-g-smoke-force dev-g-smoke-submit

# dev-g-smoke        normaali planning; pysähtyy, jos pair-valintoja ei ole
# dev-g-smoke-force  hyväksyy ehdotukset ja ajaa sitten saman smoketestin

# Normal inference: one GPU, bounded walltime, no call-count cap.
INF_MIN_MINUTES          ?= 15
INF_MAX_MINUTES          ?= 120
INF_STARTUP_MINUTES      ?= 3
INF_EST_CALL_MINUTES     ?= 4
INF_STOP_RESERVE_MINUTES ?= 12
INF_TIMINGS              := $(TSKDIR)/inference-times.tsv

EVAL_PARTITION           ?= small-g
EVAL_SLURM_PROFILE       ?= auto

DEVG_SMOKE_CALLS ?= 1
# Empty: use the normal dev-g planner estimate.
# Set explicitly for a multi-call dev-g probe.
DEVG_SMOKE_TIME ?=

DEVG_TSKDIR   := $(TSKDIR)/dev-g-smoke
DEVG_CALLS    := $(DEVG_TSKDIR)/calls.out
DEVG_PLAN_LOG := $(DEVG_TSKDIR)/calls.ready

status-infer: clean-inf-lock | mk-calls 
> @echo "mk-infer.mk: ✅ Checking the status of inference planning:"; \
> if  [ -e "$(INF_CALLS)" ];    then \
>   echo "mk-infer.mk:        calls: $(INF_CALLS)"; \
> else \
>   echo "mk-infer.mk: ❌     calls: $(INF_CALLS) missing";  exit 1; fi; \
> if [ ! -s "$(INF_CALLS)" ]; then \
>   echo "mk-infer.mk: ❌ Found no inference commands in $(INF_CALLS) to submit"; \
>   exit 0; \
> fi; \
> echo -n "mk-infer.mk:   The number of inference calls: "; \
> egrep 'python' "$(INF_CALLS)" | wc -l; \
> if  [ -e "$(INF_TEMPLATE)" ]; then echo "mk-infer.mk:     template: $(INF_TEMPLATE)"; else \
>   echo "mk-infer.mk: ❌  template: $(INF_TEMPLATE) missing"; exit 1; fi; \
> if  [ -e "$(INF_SCRIPT)" ];   then echo "mk-infer.mk:       script: $(INF_SCRIPT)";   else \
>   echo "mk-infer.mk: ❌    script: $(INF_SCRIPT) missing"; exit 1; fi; \
> if  [ -e "$(INF_SBATCH)" ];   then echo "mk-infer.mk:       sbatch: $(INF_SBATCH)";   else \
>   echo "mk-infer.mk: ❌    script: $(INF_SBATCH) missing"; exit 1; fi; \
> cat "$(INF_SBATCH)" | sed 's/^/mk-infer.mk: /'; \
> if  [ -e "$(CNT_TEMPLATE)" ]; then echo "mk-infer.mk:     continuation template: $(CNT_TEMPLATE)"; else \
>   echo "mk-infer.mk: ❌  template: $(CNT_TEMPLATE) missing"; exit 1; fi; \
> if  [ -e "$(CNT_SCRIPT)" ];   then echo "mk-infer.mk:       continuation script: $(CNT_SCRIPT)";   else \
>   echo "mk-infer.mk: ❌    script: $(CNT_SCRIPT) missing"; exit 1; fi; \
> if  [ -e "$(INF_FLAG)" ];     then \
>     job=$$(sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p; /^[0-9][0-9]*$$/p' "$(INF_FLAG)" | head -n1); \
>     squeue -j "$$job" -o "%.18i %.40j %.10T %.12M %.12l %.30R"; \
> fi; \
> echo "mk-infer.mk: ✨ I am happy with slurm run preparations."; \
> echo

infer: $(INF_CALLS) $(INF_SCRIPT) $(INF_SBATCH) $(CNT_SCRIPT) | status-infer
> @set -euo pipefail; \
> cat "$(INF_SBATCH)"; \
> infer_out="$$(bash -c 'unset "$${!SLURM_@}"; exec bash "$$1"' _ "$(INF_SBATCH)")"; \
> echo "$$infer_out"; \
> infer_job="$$(printf '%s\n' "$$infer_out" | awk '{print $$NF}')"; \
> test -n "$$infer_job"; \
> printf '%s\n' "$$infer_job" > "$(INF_FLAG)"; \
> rm -f "$(INF_DONE)"; \
> echo "mk-infer.mk: ✅ Submitted inference job $$infer_job"

# Submit only a tiny, independent smoke-test job to dev-g.
dev-g-smoke: $(INF_CALLS)
> @set -euo pipefail; \
> test "$(DEVG_SMOKE_CALLS)" -ge 1; \
> mkdir -p "$(DEVG_TSKDIR)"; \
> awk -v limit="$(DEVG_SMOKE_CALLS)" \
>   '/^(python|if)/ { print; if (++n >= limit) exit }' \
>   "$(INF_CALLS)" > "$(DEVG_CALLS)"; \
> test -s "$(DEVG_CALLS)"; \
> n_calls="$$(wc -l < "$(DEVG_CALLS)")"; \
> echo "mk-infer.mk: 🧪 Submitting $$n_calls smoke inference call(s) to dev-g"; \
> $(MAKE) --no-print-directory -C "$(SELFDIR)" \
>   MODELDIR="$(MODELDIR)" MODEL="$(MODEL)" \
>   TSKDIR="$(DEVG_TSKDIR)" FLGDIR="$(FLGDIR)/dev-g-smoke" \
>   INF_CALLS="$(DEVG_CALLS)" SKIP_CALL_PLANNING=1 \
>   EVAL_PARTITION=dev-g EVAL_SLURM_PROFILE=dev-g \
>   dev-g-smoke-submit

# This deliberately avoids `infer`, whose status prerequisite reruns mk-calls
# and pair selection.  The smoke call list already exists.
dev-g-smoke-submit: $(INF_SCRIPT) $(INF_SBATCH)
> @set -euo pipefail; \
> echo "mk-infer.mk: Generated smoke submission:"; \
> cat "$(INF_SBATCH)"; \
> infer_out="$$(bash -c 'unset "$${!SLURM_@}"; exec bash "$$1"' _ "$(INF_SBATCH)")"; \
> echo "$$infer_out"; \
> infer_job="$$(printf '%s\n' "$$infer_out" | awk '{print $$NF}')"; \
> test -n "$$infer_job"; \
> mkdir -p "$(FLGDIR)"; \
> printf '%s\n' "$$infer_job" > "$(INF_FLAG)"; \
> rm -f "$(INF_DONE)"; \
> echo "mk-infer.mk: ✅ Submitted dev-g smoke job $$infer_job"

# Accept proposed pairs, build the normal call plan, then submit one call to dev-g.
dev-g-smoke-force:
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" \
>   FORCE_PAIRS=1 "$(FIRST_GOAL)" dev-g-smoke

infer-score: infer $(INF_FLAG)
> @set -euo pipefail; \
> infer_job="$$(cat "$(INF_FLAG)")"; \
> test -n "$$infer_job"; \
> cnt_job="$$(bash -c 'unset "$${!SLURM_@}"; exec sbatch --parsable --dependency=afterany:"$$1" "$$2"' _ "$$infer_job" "$(CNT_SCRIPT)")"; \
> echo "mk-control.mk: ✅ Submitted continuation job $$cnt_job after inference"

mk-infer-force: 
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODELDIR)" \
>   MODEL="$(MODEL)" FORCE_PAIRS=1 $(FIRST_GOAL) infer

mk-infer-score-force: 
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODELDIR)" \
>   MODEL="$(MODEL)" FORCE_PAIRS=1 $(FIRST_GOAL) infer-score

mk-infer: infer
> @true

mk-infer-score: infer-score
> @true


