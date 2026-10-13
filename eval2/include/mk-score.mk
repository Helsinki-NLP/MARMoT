# -----------------------------------------------------------------------------
# Metric command planning and submission
# -----------------------------------------------------------------------------

# mk-calls (FORCE_PAIRS=1) (ensures the calls.out)
#   |
#   |   status-score
#   |    | 
#   |    |  clean-met-lock
#   |    |     | (ensure no process is running; no $MET_FLAG exists)
#   |    V     V
#   |   mk-score
#   |    |  (run $MET_SBATCH)
#   V    V
# mk-score-force

.PHONY: mk-score mk-score-force status-score score 

status-score: clean-met-lock | mk-calls 
> @set -euo pipefail; \
> echo "mk-score.mk: ✅ Checking the status of scoring planning:"; \
> if [ ! -e "$(SACRE_CALLS)" ]; then \
>   echo "mk-score.mk: ❌ calls missing: $(SACRE_CALLS)"; \
>   exit 1; \
> fi; \
> echo "mk-score.mk:        calls: $(SACRE_CALLS)"; \
> if [ ! -s "$(SACRE_CALLS)" ]; then \
>   echo "mk-score.mk: ✅ No remaining sacrebleu calls to submit"; \
>   exit 0; \
> fi; \
> n="$$(grep -c 'sacrebleu' "$(SACRE_CALLS)" || true)"; \
> echo "mk-score.mk:   The number of sacrebleu commands: $$n"; \
> for f in \
>   "$(MET_TEMPLATE)" "$(MET_SCRIPT)" "$(MET_SBATCH)" "$(CNT_TEMPLATE)" "$(CNT_SCRIPT)"; \
> do \
>   if [ ! -e "$$f" ]; then \
>     echo "mk-score.mk: ❌ Missing required file: $$f"; \
>     exit 1; \
>   fi; \
> done; \
> echo "mk-score.mk: metric template: $(MET_TEMPLATE)"; \
> echo "mk-score.mk:   metric script: $(MET_SCRIPT)"; \
> echo "mk-score.mk:   metric sbatch: $(MET_SBATCH)"; \
> echo "mk-score.mk:  cont' template: $(CNT_TEMPLATE)"; \
> echo "mk-score.mk:    cont' script: $(CNT_SCRIPT)"; \
> sed 's/^/mk-score.mk:    /' "$(MET_SBATCH)"; \
> echo "mk-score.mk: ✨ I am happy with slurm run preparations."

score: $(SACRE_CALLS) $(MET_SCRIPT) $(MET_SBATCH) $(CNT_SCRIPT) | status-score
> @set -euo pipefail; \
> rm -f "$(MET_DONE)"; \
> cat "$(MET_SBATCH)"; \
> score_out="$$(bash -c 'unset "$${!SLURM_@}"; exec bash "$$1"' _ "$(MET_SBATCH)")"; \
> echo "$$score_out"; \
> score_job="$$(printf '%s\n' "$$score_out" | awk '{print $$NF}')"; \
> test -n "$$score_job"; \
> printf '%s\n' "$$score_job" > "$(MET_FLAG)"; \
> echo "mk-score.mk: ✅ Submitted scoring job $$score_job"; \
> cnt_job="$$(bash -c 'unset "$${!SLURM_@}"; exec sbatch --parsable --dependency=afterany:"$$1" "$$2"' _ "$$score_job" "$(CNT_SCRIPT)")"; \
> test -n "$$cnt_job"; \
> printf '%s\n' "$$cnt_job" > "$(CNT_FLAG)"; \
> rm -f "$(CNT_DONE)"; \
> echo "mk-score.mk: ✅ Submitted continuation job $$cnt_job after scoring $$score_job"


mk-score-force: 
> @$(MAKE) --no-print-directory -C "$(SELFDIR)" MODELDIR="$(MODELDIR)"; \
>   MODEL="$(MODEL)" FORCE_PAIRS=1 $(FIRST_GOAL) mk-score

mk-score: score
> @true

mk-comet:
> @echo "mk-comet.mk: ✅ COMET evaluation functionality is not currently implemented"
