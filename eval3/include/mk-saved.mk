##################################
# RETURNING THE SCORES
##################################

# these sense the directory layout difference

list-sacre-all:
>       @set -u; \
>       for a in $(MODEL_ALIASES); do \
>         eval "model_dir=\$${MODEL_$$a}"; \
>         if [ -d "$$model_dir/evaluation" ]; then \
>           score_dir="$$model_dir/evaluation/inf_scores"; \
>         else \
>           score_dir="$$model_dir/inf_scores"; \
>         fi; \
>         echo "===== $$a ====="; \
>         if [ -d "$$score_dir" ]; then \
>           find "$$score_dir" -maxdepth 1 -type f \
>             \( -name '*.sacre' -o -name '*.0ssacre' \) \
>             -printf '%f\n' | sort; \
>         else \
>           echo "(no inf_scores directory)"; \
>         fi; \
>         echo; \
>       done

sacre-tsv-all:
>       @set -eu; \
>       for a in $(MODEL_ALIASES); do \
>         eval "model_dir=\$${MODEL_$$a}"; \
>         if [ -d "$$model_dir/evaluation" ]; then \
>           score_dir="$$model_dir/evaluation/inf_scores"; \
>           report_dir="$$model_dir/evaluation/reports"; \
>         else \
>           score_dir="$$model_dir/inf_scores"; \
>           report_dir="$$model_dir/eval3"; \
>         fi; \
>         tsv_file="$$report_dir/sacre.tsv"; \
>         if [ ! -d "$$score_dir" ]; then \
>           echo "WARNING: no inf_scores for $$a: $$score_dir" >&2; \
>           continue; \
>         fi; \
>         mkdir -p "$$report_dir"; \
>         echo "Writing $$tsv_file"; \
>         python3 "$(SELFDIR)/bin/summarize_sacre.py" \
>           "$$score_dir" \
>           --kind mt \
>           --tsv \
>           --model "$$a" \
>           > "$$tsv_file"; \
>         echo "Completed writing $$tsv_file"; \
>       done

list-tsv-all:
> @set -eu; \
> for a in $(MODEL_ALIASES); do \
>   eval "model_dir=\$${MODEL_$$a}"; \
>   if [ -d "$$model_dir/evaluation" ]; then \
>     tsv_file="$$model_dir/evaluation/reports/sacre.tsv"; \
>   else \
>     tsv_file="$$model_dir/eval3/sacre.tsv"; \
>   fi; \
>   if [ -f "$$tsv_file" ]; then \
>     printf '%-24s %s\n' "$$a" "$$tsv_file"; \
>   else \
>     printf '%-24s %s\n' "$$a" "(missing: $$tsv_file)"; \
>   fi; \
> done

