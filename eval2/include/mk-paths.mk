# Setting the layout of the output directories

# Training configuration and checkpoints ==>  $(MODELDIR_CLEAN)
# Model inspection summary, Mammoth selection, pair files, evaluation markers => $(EVALROOT)

TRAINCONFIG := $(MODELDIR_CLEAN)/train.yaml
EVALDIR     := $(MODELDIR_CLEAN)/evaluation

# Select the layout
ifneq ($(wildcard $(EVALDIR)/.),)
  # new layout
  EVALROOT    := $(EVALDIR)
  FLGDIR      := $(EVALROOT)/flags
  TSKDIR      := $(EVALROOT)/tasks
  CFGDIR      := $(EVALROOT)/configs
  HYPDIR      := $(EVALROOT)/hypotheses
  LOGDIR      := $(EVALROOT)/logs
  SCRDIR      := $(EVALROOT)/scores
  PLAN_LOG    := $(EVALROOT)/testing.out
  PLAN_ERR    := $(EVALROOT)/testing.err
else
  # old layout
  EVALROOT    := $(MODELDIR_CLEAN)
  FLGDIR      := $(EVALROOT)
  TSKDIR      := $(EVALROOT)/inf_out
  CFGDIR      := $(EVALROOT)/inf_out
  HYPDIR      := $(EVALROOT)/inf_out
  LOGDIR      := $(EVALROOT)/inf_logs
  SCRDIR      := $(EVALROOT)/inf_scores
  PLAN_LOG    := $(EVALROOT)/testing.yaml.out
  PLAN_ERR    := $(EVALROOT)/testing.yaml.err
endif
EVAL_DIRS := $(sort $(FLGDIR) $(TSKDIR) $(CFGDIR) $(HYPDIR) $(LOGDIR) $(SCRDIR))

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

INF_CALLS   := $(TSKDIR)/calls.out
SACRE_CALLS := $(TSKDIR)/calls.sacre.out
COMET_CALLS := $(TSKDIR)/calls.comet.out
INF_SCRIPT  := $(TSKDIR)/inf.slurm
CNT_SCRIPT  := $(TSKDIR)/cnt.slurm
MET_SCRIPT  := $(TSKDIR)/met.slurm
INF_SBATCH  := $(TSKDIR)/inf.sbatch
MET_SBATCH  := $(TSKDIR)/met.sbatch

