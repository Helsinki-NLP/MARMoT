# Setting the layout of the output directories

# Training configuration and checkpoints ==>  $(MODELDIR_CLEAN)
# Model inspection summary, Mammoth selection, pair files, evaluation markers => $(EVALROOT)

TRAINCONFIG := $(MODELDIR_CLEAN)/train.yaml
EVALDIR     := $(MODELDIR_CLEAN)/evaluation

# Infer the rough Mammoth implementation type from the model collection.
MAMMOTH_TYPE := unknown
ifneq ($(filter $(XMODELS)/%,$(MODELDIR_CLEAN)),)
  MAMMOTH_TYPE := xtransformers
endif
ifneq ($(filter $(PMODELS)/%,$(MODELDIR_CLEAN)),)
  MAMMOTH_TYPE := pytorch
endif

# Select the layout
# ifneq ($(wildcard $(EVALDIR)/.),)
  # new layout
  EVALROOT    := $(EVALDIR)
  FLGDIR      := $(EVALROOT)/flags
  TSKDIR      := $(EVALROOT)/tasks
  CFGDIR      := $(EVALROOT)/configs
  HYPDIR      := $(EVALROOT)/hypotheses
  LOGDIR      := $(EVALROOT)/logs
  SCRDIR      := $(EVALROOT)/scores
  TSVDIR      := $(EVALROOT)/tsv
  PLAN_LOG    := $(EVALROOT)/testing.out
  PLAN_ERR    := $(EVALROOT)/testing.err
# else
#  # old layout
#  EVALROOT    := $(MODELDIR_CLEAN)
#  FLGDIR      := $(EVALROOT)
#  TSKDIR      := $(EVALROOT)/inf_out
#  CFGDIR      := $(EVALROOT)/inf_out
#  HYPDIR      := $(EVALROOT)/inf_out
#  LOGDIR      := $(EVALROOT)/inf_logs
#  SCRDIR      := $(EVALROOT)/inf_scores
#  TSVDIR      := $(EVALROOT)/eval3
#  PLAN_LOG    := $(EVALROOT)/testing.yaml.out
#  PLAN_ERR    := $(EVALROOT)/testing.yaml.err
# endif
EVAL_DIRS := $(sort $(FLGDIR) $(TSKDIR) $(CFGDIR) $(HYPDIR) $(LOGDIR) $(SCRDIR))
EVAL_DIRS_TO_CREATE := $(sort $(filter-out \
                     $(MODELDIR) $(MODELDIR_CLEAN),$(EVAL_DIRS)))

ZEROSHOTPAIRSINPUT    := $(EVALROOT)/inf_zeroshot.txt.input
ZEROSHOTPAIRS         := $(EVALROOT)/inf_zeroshot.txt
SUPERVISEDPAIRSINPUT  := $(EVALROOT)/inf_supervised.txt.input
SUPERVISEDPAIRS       := $(EVALROOT)/inf_supervised.txt
MODEL_SUMMARY         := $(EVALROOT)/model-summary.yaml
MAMMOTH_SELECTED      := $(EVALROOT)/mammoth.selected

# Keep all completion markers together.
PAIR_INPUTS_DONE := $(FLGDIR)/pairs_input.done
BAS_DONE         := $(FLGDIR)/preps.done
PRS_DONE         := $(FLGDIR)/pairs.done
INF_DONE         := $(FLGDIR)/inference.done
CNT_DONE         := $(FLGDIR)/cnt.done
MET_DONE         := $(FLGDIR)/metrics.done
INF_FLAG         := $(FLGDIR)/inference.submitted
CNT_FLAG         := $(FLGDIR)/cnt.submitted
MET_FLAG         := $(FLGDIR)/metrics.submitted

SACRE_TSV        := $(TSVDIR)/sacre.tsv

INF_CALLS   := $(TSKDIR)/calls.out
SACRE_CALLS := $(TSKDIR)/calls.sacre.out
COMET_CALLS := $(TSKDIR)/calls.comet.out
INF_SCRIPT  := $(TSKDIR)/inf.slurm
CNT_SCRIPT  := $(TSKDIR)/cnt.slurm
MET_SCRIPT  := $(TSKDIR)/met.slurm
INF_SBATCH  := $(TSKDIR)/inf.sbatch
MET_SBATCH  := $(TSKDIR)/met.sbatch

.PHONY: list-eval-files
list-eval-files:
> @set -euo pipefail; \
> model_dir="$(MODELDIR_CLEAN)"; \
> eval_root="$(EVALROOT)"; \
> rel() { \
>   case "$$1" in \
>     "$$model_dir") printf '.\n' ;; \
>     "$$model_dir"/*) printf '%s\n' "$${1#"$${model_dir}"/}" ;; \
>     *) printf '%s\n' "$$1" ;; \
>   esac; \
> }; \
> count_files() { \
>   if [ -d "$$1" ]; then \
>     find "$$1" -maxdepth 1 -type f -name "$$2" -print | wc -l; \
>   else \
>     printf '0\n'; \
>   fi; \
> }; \
> show_file() { \
>   if [ -f "$$1" ]; then \
>     printf '  %-52s %s\n' "$$(rel "$$1")" "$$2"; \
>   else \
>     printf '  %-52s %s\n' "(not found)" "$$2"; \
>   fi; \
> }; \
> show_optf() { \
>   if [ -f "$$1" ]; then \
>     printf '  %-52s %s\n' "$$(rel "$$1")" "$$2"; \
>   fi; \
> }; \
> show_lines() { \
>   if [ -f "$$1" ]; then \
>     lines="$$(wc -l < "$$1")"; \
>     printf '  %-52s %s (%s lines)\n' "$$(rel "$$1")" "$$2" "$$lines"; \
>   fi; \
> }; \
> model_base="$$(basename "$$model_dir")"; \
> if [ "$$model_base" = mammoth ]; then \
>   model_name="$$(basename "$$(dirname "$$model_dir")")"; \
> else \
>   model_name="$$model_base"; \
> fi; \
> echo "Model:            $$model_name"; \
> echo "Model directory:  $$model_dir"; \
> if [ "$$eval_root" = "$$model_dir" ]; then \
>   echo "Evaluation layout: legacy (files are directly under the model directory)"; \
> else \
>   echo "Evaluation layout: new (root: $$(rel "$$eval_root"))"; \
> fi; \
> echo; \
> echo "Named evaluation files"; \
> show_file "$(MODEL_SUMMARY)"          "checkpoint architecture summary"; \
> show_file "$(MAMMOTH_SELECTED)"       "> selected Mammoth implementation"; \
> show_file "$(BAS_DONE)"               "  > basic setup completion marker"; \
> \
> show_file "$(ZEROSHOTPAIRSINPUT)"     "input zero-shot pair selection"; \
> show_file "$(SUPERVISEDPAIRSINPUT)"   "input supervised pair selection"; \
> show_file "$(PAIR_INPUTS_DONE)"       "> pair-input preparation completion marker"; \
> show_file "$(ZEROSHOTPAIRS)"          "  > selected zero-shot pairs — REQUIRED for re-planning"; \
> show_file "$(SUPERVISEDPAIRS)"        "  > selected supervised pairs — REQUIRED for re-planning"; \
> show_file "$(PRS_DONE)"               "    > pair-selection completion marker"; \
> \
> show_lines "$(TSKDIR)/plan.out"       "planned evaluation runs"; \
> show_lines "$(INF_CALLS)"             "> translation commands still required"; \
> show_lines "$(SACRE_CALLS)"           "> SacreBLEU commands still required"; \
> show_lines "$(COMET_CALLS)"           "> COMET commands still required"; \
> show_file "$(PLAN_LOG)"               "  > successful planner completion log"; \
> show_optf "$(PLAN_ERR)"               "  > planner error log, if planning failed"; \
> \
> show_file "$(INF_SCRIPT)"             "inference Slurm script"; \
> show_file "$(INF_SBATCH)"             "> inference submission command"; \
> show_optf "$(INF_FLAG)"               "  > inference job submission marker"; \
> show_file "$(INF_DONE)"               "    > inference completion marker"; \
> \
> show_file "$(CNT_SCRIPT)"             "counting-stage Slurm script"; \
> show_optf "$(CNT_FLAG)"               "> counting-stage submission marker"; \
> show_file "$(CNT_DONE)"               "  > counting-stage completion marker"; \
> \
> show_file "$(MET_SCRIPT)"             "metrics Slurm script"; \
> show_file "$(MET_SBATCH)"             "> metrics submission command"; \
> show_optf "$(MET_FLAG)"               "  > metrics job submission marker"; \
> show_file "$(MET_DONE)"               "    > metrics completion marker (for Sacrebleu + COMET)"; \
> \
> show_file "$(SACRE_TSV)"              "> derived SacreBLEU TSV summary for comparison tools"; \
> echo; \
> echo "Task-specific evaluation files"; \
> yaml_all="$$(count_files "$(CFGDIR)" '*.yaml')"; \
> yaml_zs="$$(count_files "$(CFGDIR)" '*.0shot.yaml')"; \
> printf '  %-52s %s files (%s zero-shot): inference configurations\n' \
>   "$$(rel "$(CFGDIR)")/*.yaml" "$$yaml_all" "$$yaml_zs"; \
> hyp="$$(count_files "$(HYPDIR)" '*.hyp')"; \
> zhyp="$$(count_files "$(HYPDIR)" '*.0shyp')"; \
> printf '  %-52s %s supervised, %s zero-shot: translations\n' \
>   "$$(rel "$(HYPDIR)")/{*.hyp,*.0shyp}" "$$hyp" "$$zhyp"; \
> sacre="$$(count_files "$(SCRDIR)" '*.sacre')"; \
> zsacre="$$(count_files "$(SCRDIR)" '*.0ssacre')"; \
> printf '  %-52s %s supervised, %s zero-shot: SacreBLEU results\n' \
>   "$$(rel "$(SCRDIR)")/{*.sacre,*.0ssacre}" "$$sacre" "$$zsacre"; \
> comet="$$(count_files "$(SCRDIR)" '*.comet')"; \
> zcomet="$$(count_files "$(SCRDIR)" '*.0scomet')"; \
> printf '  %-52s %s supervised, %s zero-shot: COMET results\n' \
>   "$$(rel "$(SCRDIR)")/{*.comet,*.0scomet}" "$$comet" "$$zcomet"; \
> logrel="$$(rel "$(LOGDIR)")"; \
> show_log_pair() { \
>   stem="$$1"; description="$$2"; \
>   outs="$$(count_files "$(LOGDIR)" "$${stem}*.out")"; \
>   errs="$$(count_files "$(LOGDIR)" "$${stem}*.err")"; \
>   total=$$((outs + errs)); \
>   if [ "$$total" -gt 0 ]; then \
>     printf '  %-52s %s stdout, %s stderr: %s\n' \
>       "$$logrel/$${stem}<jobid>.{out,err}" \
>       "$$outs" "$$errs" "$$description"; \
>   fi; \
> }; \
> task_errs="$$(count_files "$(LOGDIR)" 'job*.*.err')"; \
> plain_job_outs="$$(find "$(LOGDIR)" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | awk '/^job[0-9]+\.out$$/ { n++ } END { print n+0 }')"; \
> plain_job_errs="$$(find "$(LOGDIR)" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null | awk '/^job[0-9]+\.err$$/ { n++ } END { print n+0 }')"; \
> if [ "$$task_errs" -gt 0 ]; then \
>   printf '  %-52s %s files: per-task inference stderr; retained across retries\n' \
>     "$$logrel/job<jobid>.<kind>_<pair>.<dataset>.err" "$$task_errs"; \
>   for kind in docmt sentmt mt; do \
>     n="$$(count_files "$(LOGDIR)" "job*.$${kind}_*.err")"; \
>     if [ "$$n" -gt 0 ]; then \
>       printf '    %-50s %s task stderr files\n' "$$kind" "$$n"; \
>     fi; \
>   done; \
> fi; \
> show_log_pair infjob \
>   'Slurm batch logs for distributed inference and its dispatcher'; \
> show_log_pair cnt \
>   'Slurm batch logs for the cnt pipeline stage'; \
> show_log_pair sacrebleu \
>   'Slurm batch logs for SacreBLEU scoring submissions'; \
> if [ "$$((plain_job_outs + plain_job_errs))" -gt 0 ]; then \
>   printf '  %-52s %s stdout, %s stderr: legacy generic Slurm job logs\n' \
>     "$$logrel/job<jobid>.{out,err}" "$$plain_job_outs" "$$plain_job_errs"; \
> fi

.PHONY: migrate-eval-dry-run migrate-eval migrate-eval-layout
MIGRATE ?= 0
migrate-eval-dry-run: MIGRATE := 0
migrate-eval-dry-run: migrate-eval-layout
migrate-eval: MIGRATE := 1
migrate-eval: migrate-eval-layout
migrate-eval-layout:
> @set -euo pipefail; \
> shopt -s nullglob dotglob; \
> oldroot="$(MODELDIR_CLEAN)"; \
> finalroot="$$oldroot/evaluation"; \
> migrate="$(MIGRATE)"; \
> die() { echo "mk-paths.mk: ❌ $$*" >&2; exit 1; }; \
> plan=0; \
> moved_src=(); \
> moved_dst=(); \
> legacy_out="$$oldroot/inf_out"; \
> legacy_out_existed=0; \
> [ -d "$$legacy_out" ] && legacy_out_existed=1; \
> for b in inf_supervised.txt inf_zeroshot.txt; do \
>   if [ -e "$$oldroot/pairs.done" ] && [ ! -f "$$oldroot/$$b" ]; then \
>     die "pairs.done exists but required pair list is missing: $$oldroot/$$b"; \
>   fi; \
> done; \
> rollback() { \
>   status=$$?; \
>   if [ "$$migrate" = 1 ]; then \
>     echo "mk-paths.mk: ⚠️ Migration failed; restoring moved files..." >&2; \
>     [ "$$legacy_out_existed" = 0 ] || mkdir -p "$$legacy_out"; \
>     for ((i=$${#moved_src[@]} - 1; i >= 0; i--)); do \
>       src="$${moved_src[i]}"; \
>       dst="$${moved_dst[i]}"; \
>       if [ -e "$$dst" ] && [ ! -e "$$src" ]; then \
>         mkdir -p "$$(dirname "$$src")"; \
>         mv -- "$$dst" "$$src" || true; \
>       fi; \
>     done; \
>   fi; \
>   exit "$$status"; \
> }; \
> plan_move() { \
>   src="$$1"; \
>   dst="$$2"; \
>   description="$$3"; \
>   [ -e "$$src" ] || return 0; \
>   if [ "$$migrate" = 1 ]; then \
>     mkdir -p "$$(dirname "$$dst")"; \
>     mv -- "$$src" "$$dst"; \
>     moved_src+=("$$src"); \
>     moved_dst+=("$$dst"); \
>     printf '  moved  %s  # %s\n' "$$src" "$$description"; \
>   else \
>     printf '  mkdir -p %q\n' "$$(dirname "$$dst")"; \
>     printf '  mv -- %q %q  # %s\n' "$$src" "$$dst" "$$description"; \
>   fi; \
>   plan=$$((plan + 1)); \
> }; \
> plan_glob() { \
>   from="$$1"; \
>   pattern="$$2"; \
>   todir="$$3"; \
>   description="$$4"; \
>   for src in "$$from"/$$pattern; do \
>     [ -e "$$src" ] || continue; \
>     plan_move "$$src" "$$todir/$$(basename "$$src")" "$$description"; \
>   done; \
> }; \
> [[ -d "$$oldroot" ]] || die "model directory does not exist: $$oldroot"; \
> [[ ! -e "$$finalroot" ]] || die "new layout already exists: $$finalroot"; \
> stale_staging=( "$$oldroot"/.evaluation.migration.* ); \
> [ "$${#stale_staging[@]}" -eq 0 ] || \
>   die "stale staging directory exists: $${stale_staging[*]}"; \
> active=(); \
> for f in \
>   "$$oldroot/inference.submitted" \
>   "$$oldroot/cnt.submitted" \
>   "$$oldroot/metrics.submitted" \
>   "$$oldroot/comet.submitted" \
>   "$$oldroot/viz.submitted" \
>   "$$oldroot/inference-planning.lock" \
>   "$$oldroot/metrics-planning.lock"; do \
>   [ -e "$$f" ] && active+=("$$(basename "$$f")"); \
> done; \
> [ "$${#active[@]}" -eq 0 ] || \
>   die "refusing migration while work may be active: $${active[*]}"; \
> if [ -d "$$legacy_out" ]; then \
>   unknown=(); \
>   for f in "$$legacy_out"/*; do \
>     b="$$(basename "$$f")"; \
>     case "$$b" in \
>       *.yaml|*.hyp|*.0shyp|plan.out|calls.out|calls.sacre.out|calls.comet.out|\
>       inf.slurm|cnt.slurm|met.slurm|inf.sbatch|cnt.sbatch|met.sbatch|cmt.sbatch|\
>       extraction_complete) ;; \
>       *) unknown+=("$$b") ;; \
>     esac; \
>   done; \
>   [ "$${#unknown[@]}" -eq 0 ] || { \
>     printf 'mk-paths.mk: ❌ Unrecognised legacy inf_out files:\n' >&2; \
>     printf '  %s\n' "$${unknown[@]}" >&2; \
>     exit 1; \
>   }; \
> fi; \
> if [ "$$migrate" = 1 ]; then \
>   newroot="$$(mktemp -d "$$oldroot/.evaluation.migration.XXXXXX")"; \
>   trap rollback ERR INT TERM; \
>   echo "Evaluation-layout migration"; \
>   echo "  Staging: $$newroot"; \
>   echo "  Final:   $$finalroot"; \
> else \
>   newroot="$$finalroot"; \
>   echo "Evaluation-layout migration dry run"; \
>   echo "  Model:      $$oldroot"; \
>   echo "  New layout: $$newroot"; \
> fi; \
> echo; \
> echo "Planned moves"; \
> plan_move "$$oldroot/testing.yaml" \
>   "$$newroot/configs/testing.yaml" \
>   "legacy generated testing configuration"; \
> plan_move "$$oldroot/testing.yaml.out" \
>   "$$newroot/testing.out" \
>   "successful planning log"; \
> plan_move "$$oldroot/testing.yaml.err" \
>   "$$newroot/testing.err" \
>   "failed-planning diagnostic log"; \
> plan_move "$$oldroot/inf_make.sh" \
>   "$$newroot/tasks/inf_make.sh" \
>   "generated inference Makefile"; \
> plan_move "$$oldroot/model-summary.yaml" \
>   "$$newroot/model-summary.yaml" \
>   "checkpoint-inspection summary"; \
> plan_move "$$oldroot/mammoth.selected" \
>   "$$newroot/mammoth.selected" \
>   "selected Mammoth source checkout"; \
> for b in \
>   inf_zeroshot.txt.input inf_zeroshot.txt \
>   inf_supervised.txt.input inf_supervised.txt; do \
>   plan_move "$$oldroot/$$b" "$$newroot/$$b" \
>     "pair-selection input or result"; \
> done; \
> for b in \
>   pairs_input.done \
>   preps.done pairs.done inference.done cnt.done metrics.done comet.done viz.done \
>   inference.submitted cnt.submitted metrics.submitted comet.submitted viz.submitted \
>   inference-planning.lock metrics-planning.lock; do \
>   plan_move "$$oldroot/$$b" "$$newroot/flags/$$b" \
>     "pipeline state marker"; \
> done; \
> plan_glob "$$legacy_out" '*.yaml' \
>   "$$newroot/configs" "per-task inference configuration"; \
> plan_glob "$$legacy_out" '*.hyp' \
>   "$$newroot/hypotheses" "supervised hypothesis"; \
> plan_glob "$$legacy_out" '*.0shyp' \
>   "$$newroot/hypotheses" "zero-shot hypothesis"; \
> for b in \
>   plan.out calls.out calls.sacre.out calls.comet.out \
>   inf.slurm cnt.slurm met.slurm \
>   inf.sbatch cnt.sbatch met.sbatch cmt.sbatch; do \
>   plan_move "$$legacy_out/$$b" "$$newroot/tasks/$$b" \
>     "planned command list or Slurm submission file"; \
> done; \
> plan_move "$$legacy_out/extraction_complete" \
>   "$$newroot/flags/extraction_complete" \
>   "legacy inference-configuration extraction completion marker"; \
> plan_move "$$oldroot/inf_logs" "$$newroot/logs" \
>   "inference, Slurm, and scoring logs"; \
> plan_move "$$oldroot/inf_scores" "$$newroot/scores" \
>   "SacreBLEU and COMET score files"; \
> plan_move "$$oldroot/eval3" "$$newroot/tsv" \
>   "derived evaluation summaries, including sacre.tsv for comparison tools"; \
> echo; \
> echo "Not moved: train.yaml and checkpoint files."; \
> if [ "$$plan" -eq 0 ]; then \
>   if [ "$$migrate" = 1 ]; then \
>     rmdir "$$newroot"; \
>     trap - ERR INT TERM; \
>   fi; \
>   echo "mk-paths.mk: ℹ️ No recognised legacy evaluation files found."; \
> elif [ "$$migrate" = 1 ]; then \
>   [ ! -d "$$legacy_out" ] || rmdir "$$legacy_out"; \
>   mv -- "$$newroot" "$$finalroot"; \
>   trap - ERR INT TERM; \
>   echo "mk-paths.mk: ✅ Migration complete: $$plan moves."; \
>   echo "mk-paths.mk:    New layout: $$finalroot"; \
> else \
>   [ ! -d "$$legacy_out" ] || \
>     printf '  rmdir %q  # legacy directory after its recognised contents move\n' \
>       "$$legacy_out"; \
>   echo "mk-paths.mk: ✅ Dry run complete: $$plan planned moves; no files changed."; \
> fi


# $ make finnish list-eval-files
# Model:            finnish
# Model directory:  /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-xtransformers/finnish/mammoth
# Evaluation layout: legacy (files are directly under the model directory)
# 
# Named evaluation files
#   model-summary.yaml                                   checkpoint architecture summary
#   mammoth.selected                                     selected Mammoth implementation
#   inf_zeroshot.txt.input                               input zero-shot pair selection
#   inf_supervised.txt.input                             input supervised pair selection
#   pairs_input.done                                     pair-input preparation marker
#   preps.done                                           basic setup completion marker
#   pairs.done                                           pair-selection completion marker
#   inference.done                                       inference completion marker
#   cnt.done                                             counting-stage completion marker
#   testing.yaml.out                                     successful planner log
#   inf_out/plan.out                                     planned evaluation runs (48 lines)
#   inf_out/calls.out                                    translation commands still required (0 lines)
#   inf_out/calls.sacre.out                              SacreBLEU commands still required (0 lines)
#   inf_out/calls.comet.out                              COMET commands still required (48 lines)
#   inf_out/inf.slurm                                    inference Slurm script
#   inf_out/cnt.slurm                                    counting Slurm script
#   inf_out/met.slurm                                    metrics Slurm script
#   inf_out/inf.sbatch                                   inference submission command
#   inf_out/met.sbatch                                   metrics submission command
#   eval3/sacre.tsv                                      long-form SacreBLEU task summary
# 
# Task-specific evaluation files
#   inf_out/*.yaml                                       28 files (4 zero-shot): inference configurations
#   inf_out/{*.hyp,*.0shyp}                              32 supervised, 16 zero-shot: translations
#   inf_scores/{*.sacre,*.0ssacre}                       32 supervised, 16 zero-shot: SacreBLEU results
#   inf_scores/{*.comet,*.0scomet}                       0 supervised, 0 zero-shot: COMET results
#   inf_logs/job<jobid>.<kind>_<pair>.<dataset>.err      313 files: per-task inference stderr; retained across retries
#     docmt                                              25 task stderr files
#     sentmt                                             288 task stderr files
#   inf_logs/infjob<jobid>.{out,err}                     272 stdout, 272 stderr: Slurm batch logs for distributed inference and its dispatcher
#   inf_logs/cnt<jobid>.{out,err}                        269 stdout, 269 stderr: Slurm batch logs for the cnt pipeline stage
#   inf_logs/sacrebleu<jobid>.{out,err}                  7 stdout, 7 stderr: Slurm batch logs for SacreBLEU scoring submissions
#   inf_logs/job<jobid>.{out,err}                        2 stdout, 2 stderr: legacy generic Slurm job logs
#
#
#------------------

# Model:            finnish
# Model directory:  /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-xtransformers/finnish/mammoth
# Evaluation layout: new (root: evaluation)
# 
# Named evaluation files
#   evaluation/model-summary.yaml                        checkpoint architecture summary
#   evaluation/mammoth.selected                          selected Mammoth implementation
#   evaluation/inf_zeroshot.txt.input                    input zero-shot pair selection
#   evaluation/inf_supervised.txt.input                  input supervised pair selection
#   evaluation/flags/preps.done                          basic setup completion marker
#   evaluation/flags/pairs.done                          pair-selection completion marker
#   evaluation/flags/inference.done                      inference completion marker
#   evaluation/flags/cnt.done                            counting-stage completion marker
#   evaluation/testing.out                               successful planner log
#   evaluation/tasks/plan.out                            planned evaluation runs (48 lines)
#   evaluation/tasks/calls.out                           translation commands still required (0 lines)
#   evaluation/tasks/calls.sacre.out                     SacreBLEU commands still required (0 lines)
#   evaluation/tasks/calls.comet.out                     COMET commands still required (48 lines)
#   evaluation/tasks/inf.slurm                           inference Slurm script
#   evaluation/tasks/cnt.slurm                           counting Slurm script
#   evaluation/tasks/met.slurm                           metrics Slurm script
#   evaluation/tasks/inf.sbatch                          inference submission command
#   evaluation/tasks/met.sbatch                          metrics submission command
#   evaluation/tsv/sacre.tsv                             long-form SacreBLEU task summary
# 
# Task-specific evaluation files
#   evaluation/configs/*.yaml                            28 files (4 zero-shot): inference configurations
#   evaluation/hypotheses/{*.hyp,*.0shyp}                32 supervised, 16 zero-shot: translations
#   evaluation/scores/{*.sacre,*.0ssacre}                32 supervised, 16 zero-shot: SacreBLEU results
#   evaluation/scores/{*.comet,*.0scomet}                0 supervised, 0 zero-shot: COMET results
#   evaluation/logs/job<jobid>.<kind>_<pair>.<dataset>.err 313 files: per-task inference stderr; retained across retries
#     docmt                                              25 task stderr files
#     sentmt                                             288 task stderr files
#   evaluation/logs/infjob<jobid>.{out,err}              272 stdout, 272 stderr: Slurm batch logs for distributed inference and its dispatcher
#   evaluation/logs/cnt<jobid>.{out,err}                 269 stdout, 269 stderr: Slurm batch logs for the cnt pipeline stage
#   evaluation/logs/sacrebleu<jobid>.{out,err}           7 stdout, 7 stderr: Slurm batch logs for SacreBLEU scoring submissions
#   evaluation/logs/job<jobid>.{out,err}                 2 stdout, 2 stderr: legacy generic Slurm job logs
# 

# /scratch/project_462001509/members/tiedeman/MARMoT/models/hpo-xtransformers/finnish/mammoth/evaluation/
# ├── configs
# │   ├── docmt1_eng-fin.yaml
# │   ├── ...
# │   ├── sentmt_swe-eng.0shot.yaml
# │   ├── ...
# │   └── wiki_swe-fin.yaml
# ├── flags
# │   ├── cnt.done
# │   ├── extraction_complete
# │   ├── inference.done
# │   ├── pairs.done
# │   ├── pairs_input.done
# │   └── preps.done
# ├── hypotheses
# │   ├── docmt_XX.eng-XX.fin.bqt.hyp
# │   ├── ...
# │   ├── sentmt_XX.swe-XX.eng.bqtpar.0shyp
# │   ├── ...
# │   └── sentmt_XX.swe-XX.fin.wmt.hyp
# ├── inf_supervised.txt.input
# ├── inf_zeroshot.txt.input
# ├── inf_supervised.txt
# ├── inf_zeroshot.txt
# ├── logs
# │   ├── cnt19500288.err
# │   ├── ...
# │   ├── infjob19471675.err
# │   ├── ...
# │   ├── job17914411.sentmt_XX.eng-XX.fin.err
# │   ├── ...
# │   ├── job19173139.err
# │   ├── job19173139.out
# │   ├── job19472848.docmt_XX.eng-XX.fin.bqt.err
# │   ├── job19472848.docmt_XX.eng-XX.fin.bqtpar.err
# │   ├── ...
# │   ├── sacrebleu19504794.err
# │   ├── ...
# │   └── sacrebleu19630418.out
# ├── mammoth.selected
# ├── model-summary.yaml
# ├── scores
# │   ├── docmt_XX.eng-XX.fin.bqtpar.sacre
# │   ├── docmt_XX.eng-XX.fin.bqt.sacre
# │   ├── ...
# │   ├── sentmt_XX.swe-XX.eng.wmt.0ssacre
# │   ├── ...
# │   └── sentmt_XX.swe-XX.fin.wmt.sacre
# ├── tasks
# │   ├── calls.comet.out
# │   ├── calls.out
# │   ├── calls.sacre.out
# │   ├── cnt.slurm
# │   ├── inf.sbatch
# │   ├── inf.slurm
# │   ├── met.sbatch
# │   ├── met.slurm
# │   └── plan.out
# ├── testing.out
# └── tsv
#     └── sacre.tsv
