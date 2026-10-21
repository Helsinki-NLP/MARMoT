##################################
# RETURNING THE SCORES
##################################
#
# Targets in this file:
#
#   make list-sacre-all
#       Lists the SacreBLEU score files for every configured model.
#
#   make sacre-tsv-all
#       Reads the SacreBLEU score files for every configured model and
#       writes one summary TSV file per model.
#
#   make list-tsv-all
#       Shows the location of the generated sacre.tsv for every model,
#       and reports models for which the TSV has not yet been generated.
#
#
# Directory layouts
# -----------------
#
# Current eval3 layout:
#
#   <model>/evaluation/scores/*.sacre
#   <model>/evaluation/reports/sacre.tsv
#
# Legacy layout:
#
#   <model>/inf_scores/*.sacre
#   <model>/eval3/sacre.tsv
#
#
# Model aliases
# -------------
#
# MODEL_ALIASES contains aliases such as:
#
#   Enc12Dec12H8D512-2p-GAenc-Ldec-320k
#
# and the corresponding Make variable is, for example:
#
#   MODEL_Enc12Dec12H8D512-2p-GAenc-Ldec-320k
#
# We must NOT try to dereference this as a shell variable.  In shell
# parameter expansion, '-' has special meaning, so something such as
#
#   ${MODEL_Enc12Dec12H8D512-2p-GAenc-Ldec-320k}
#
# is not a safe shell variable reference.
#
# Instead, Make expands $(MODEL_$(a)) here while constructing MODEL_SPECS.
# Each resulting alias|directory pair is single-quoted, so the '|' is
# passed to the shell as an ordinary character rather than interpreted
# as a pipeline operator.
#
# Example shell word:
#
#   'Enc12...-320k|/scratch/.../Enc12...-320k/mammoth'
#
# The shell loop then separates the alias and directory using ordinary
# POSIX parameter expansion.

MODEL_SPECS := $(foreach a,$(MODEL_ALIASES),'$(a)|$(MODEL_$(a))')


##################################
# LIST SACRE SCORE FILES
##################################
#
# List the score files belonging to every configured model.
#
# For the current layout the scores are under evaluation/scores.
# For old model directories without evaluation/, fall back to inf_scores.
#
# This target does not create or modify anything.  It is useful for
# checking that MODEL_ALIASES resolves to the expected model directories
# before running sacre-tsv-all.

list-sacre-all:
>	@set -eu; \
>	for spec in $(MODEL_SPECS); do \
>	  a="$${spec%%|*}"; \
>	  model_dir="$${spec#*|}"; \
>	  if [ -d "$$model_dir/evaluation" ]; then \
>	    score_dir="$$model_dir/evaluation/scores"; \
>	  else \
>	    score_dir="$$model_dir/inf_scores"; \
>	  fi; \
>	  echo "===== $$a ====="; \
>	  echo "score directory: $$score_dir"; \
>	  if [ -d "$$score_dir" ]; then \
>	    find "$$score_dir" -maxdepth 1 -type f \
>	      \( -name '*.sacre' -o -name '*.0ssacre' \) \
>	      -printf '%f\n' | sort; \
>	  else \
>	    echo "(no score directory)"; \
>	  fi; \
>	  echo; \
>	done


##################################
# CREATE SACRE TSV SUMMARIES
##################################
#
# Produce one sacre.tsv for every configured model.
#
# Current layout:
#
#   input:
#       <model>/evaluation/scores/*.sacre
#
#   output:
#       <model>/evaluation/reports/sacre.tsv
#
# Legacy layout:
#
#   input:
#       <model>/inf_scores/*.sacre
#
#   output:
#       <model>/eval3/sacre.tsv
#
# summarize_sacre.py reads the score directory and writes TSV to stdout.
# stdout is redirected to the model-specific sacre.tsv.
#
# Models without a score directory are skipped with a warning.

##################################
# CREATE SACRE TSV SUMMARIES
##################################
#
# Generate one sacre.tsv per model from the eval3 *.sacre files.
#
# Current eval3 layout:
#
#   input:
#       <model>/evaluation/scores/*.sacre
#
#   output:
#       <model>/evaluation/reports/sacre.tsv
#
# Legacy layout:
#
#   input:
#       <model>/inf_scores/*.sacre
#
#   output:
#       <model>/eval3/sacre.tsv
#
# The output is first written to a temporary file in the same directory.
# A valid temporary file is atomically renamed to sacre.tsv.
#
# A TSV is valid only when it contains the header plus at least one
# actual data row.
#
# If no *.sacre files currently exist:
#
#   - an existing TSV containing data is retained;
#   - an absent or header-only TSV is removed.
#
# This is intentional: the individual score files may have been deleted
# after a valid summary TSV was produced.
#
# If *.sacre files do exist, however, they are authoritative and the TSV
# is regenerated.  If summarization produces no data rows, the invalid
# TSV is removed.
#
# shopt -s nullglob makes "$score_dir"/*.sacre expand to an empty array
# when no files match, rather than leaving the literal "*.sacre" string.

sacre-tsv-all:
>	@set -eu; \
>	shopt -s nullglob; \
>	for spec in $(MODEL_SPECS); do \
>	  a="$${spec%%|*}"; \
>	  model_dir="$${spec#*|}"; \
>	  if [ -d "$$model_dir/evaluation" ]; then \
>	    score_dir="$$model_dir/evaluation/scores"; \
>	    report_dir="$$model_dir/evaluation/reports"; \
>	  else \
>	    score_dir="$$model_dir/inf_scores"; \
>	    report_dir="$$model_dir/eval3"; \
>	  fi; \
>	  tsv_file="$$report_dir/sacre.tsv"; \
>	  if [ ! -d "$$score_dir" ]; then \
>	    if [ -f "$$tsv_file" ] && \
>	       [ "$$(wc -l < "$$tsv_file")" -gt 1 ]; then \
>	      echo "No score directory for $$a; keeping existing TSV with data"; \
>	    else \
>	      echo "No score directory for $$a and no valid TSV; deleting TSV"; \
>	      rm -f "$$tsv_file"; \
>	    fi; \
>	    continue; \
>	  fi; \
>	  sacre_files=("$$score_dir"/*.sacre); \
>	  sacre_count="$${#sacre_files[@]}"; \
>	  if [ "$$sacre_count" -eq 0 ]; then \
>	    if [ -f "$$tsv_file" ] && \
>	       [ "$$(wc -l < "$$tsv_file")" -gt 1 ]; then \
>	      echo "No SacreBLEU files for $$a; keeping existing TSV with data"; \
>	    else \
>	      echo "No SacreBLEU files for $$a and no valid TSV; deleting TSV"; \
>	      rm -f "$$tsv_file"; \
>	    fi; \
>	    continue; \
>	  fi; \
>	  mkdir -p "$$report_dir"; \
>	  tmp_file="$$(mktemp "$$report_dir/.sacre.tsv.tmp.XXXXXX")"; \
>	  echo "Writing $$tsv_file from $$sacre_count score files"; \
>	  if ! python3 "$(SELFDIR)/bin/summarize_sacre.py" \
>	    "$$score_dir" \
>	    --kind mt \
>	    --tsv \
>	    --model "$$a" \
>	    > "$$tmp_file"; then \
>	    echo "ERROR: summarizer failed for $$a; deleting invalid TSV" >&2; \
>	    rm -f "$$tmp_file" "$$tsv_file"; \
>	    continue; \
>	  fi; \
>	  row_count="$$(wc -l < "$$tmp_file")"; \
>	  if [ "$$row_count" -le 1 ]; then \
>	    echo "WARNING: $$sacre_count score files for $$a but no TSV data rows; deleting TSV" >&2; \
>	    rm -f "$$tmp_file" "$$tsv_file"; \
>	    continue; \
>	  fi; \
>	  mv -f "$$tmp_file" "$$tsv_file"; \
>	  echo "Completed $$tsv_file: $$((row_count - 1)) data rows"; \
>	done


##################################
# LIST GENERATED TSV FILES
##################################
#
# Show the expected sacre.tsv for every configured model.
#
# Existing files are printed with their full path.  If a model does not
# yet have a sacre.tsv, "(missing: ...)" is printed instead.
#
# This target does not create or modify files.

list-tsv-all:
>	@set -eu; \
>	for spec in $(MODEL_SPECS); do \
>	  a="$${spec%%|*}"; \
>	  model_dir="$${spec#*|}"; \
>	  if [ -d "$$model_dir/evaluation" ]; then \
>	    tsv_file="$$model_dir/evaluation/reports/sacre.tsv"; \
>	  else \
>	    tsv_file="$$model_dir/eval3/sacre.tsv"; \
>	  fi; \
>	  if [ -f "$$tsv_file" ]; then \
>	    row_count="$$(wc -l < "$$tsv_file")"; \
>	    if [ "$$row_count" -le 1 ]; then \
>	      rm -f "$$tsv_file"; \
>	      printf '%-40s %s\n' "$$a" "(no data)"; \
>	    else \
>	      printf '%-40s %s (%s data rows)\n' \
>	        "$$a" "$$tsv_file" "$$((row_count - 1))"; \
>	    fi; \
>	  else \
>	    printf '%-40s %s\n' "$$a" "(missing)"; \
>	  fi; \
>	done

