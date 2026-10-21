#!/usr/bin/env python3
# plan_eval3_inference.py
#
# Plan Mammoth evaluation: write inference YAMLs and command lists.
# Normally invoked by the eval2 Makefile.
#
# Reads
# -----
# TRAINCONFIG       Mammoth training YAML.
# INFTASKS         Selected training task names, one task per line.
# DATADIR          Benchmark root: Flores+, Bouquet, Bouquet-par, WMT24++.
#
# Required environment
# --------------------
# MODEL            Model path passed to translate.py.
# MAMMOTH          Mammoth source directory containing translate.py.
# TSKDIR           Directory for the plan and command lists.
# CFGDIR           Directory for generated inference YAMLs.
# HYPDIR           Directory for translation hypotheses.
# LOGDIR           Directory for inference stderr logs.
# SCRDIR           Directory for scoring results.
# MAMMOTH_TYPE
#
# All output directories must already exist.
# The Makefile selects the directory layout and supplies these paths.
# For the legacy layout, TSKDIR, CFGDIR, and HYPDIR share inf_out.
#
# Writes
# ------
# CFGDIR/<orig_task>.yaml         Supervised inference configuration.
# CFGDIR/<orig_task>.yaml         Inference configuration.
# TSKDIR/plan.out                 Inventory of planned evaluation runs.
# TSKDIR/calls.out                Commands for missing/incomplete hypotheses.
# TSKDIR/calls.sacre.out          Commands for pending SacreBLEU scoring.
# TSKDIR/calls.comet.out          Commands for COMET scoring.
# TSKDIR/<hypothesis-stem>.inf    One durable inference task per hypothesis.
#
# Generated YAMLs and command lists are overwritten when planning runs.
# Diagnostics go to stderr; the Makefile captures the planning log.
#
# Workflow
# --------
# Expand selected training tasks into localized evaluation tasks.
# Resolve task-specific sharing groups, vocabularies, and YAML templates.
# Generate commands for benchmarks whose source/reference files exist.
#
# Existing hypotheses are considered complete when their line count matches
# the source. Scoring commands are generated only for complete hypotheses,
# so rerun planning after inference to prepare scoring.
#
# SacreBLEU results larger than 500 bytes are treated as already scored.
# COMET commands are generated for every complete hypothesis.
#
# This script only plans work. The generated commands later write hypotheses
# to HYPDIR, inference logs to LOGDIR, and metric results to SCRDIR.
#
# Notes
# -----
# - Inference YAMLs are derived from the training configuration: training-only
#   keys are removed, tasks and source/target vocabularies are narrowed to the
#   selected task, and inference settings such as beam and batch size are added.
# - Inference YAMLs retain the original training task name as their task key.
# - Training task names are opaque identifiers.  Evaluation languages are
#   obtained from each selected task's structured src_tgt field, never by
#   parsing prefixes such as mt_, zero_, or denoise_.
# - Run through the surrounding Makefile workflow, which supplies the required
#   environment variables and creates the output directories.

import sys
sys.stderr.write("plan_eval3_inference.py:    running...\n")

import os
import re
import shlex
import shutil
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set
import copy
try:
    import yaml
except ImportError:
    sys.stderr.write("Missing dependency: pyyaml\n")
    sys.stderr.write("Install with: pip install pyyaml\n")
    sys.exit(1)

# RFC-EVAL-YAML has one authoritative train.yaml -> inference.yaml conversion.
# Per-task planner YAMLs are narrowed views of that conversion, not a second
# independently maintained conversion implementation.
from make_inference_yaml import convert as convert_eval3_inference_yaml

def die(msg: str) -> None:
    log(msg)
    sys.exit(1)
def log(msg: str, before: str = "plan_eval3_inference.py: ", end: str = "\n") -> None:
    sys.stderr.write(f"{before}{msg}{end}")

DROP_TOP_LEVEL_KEYS = [
    "early_stopping",
    "valid_timeout",
    "valid_decode_timeout",
    "valid_max_length",
    "tensorboard",
    "tensorboard_log_dir",
    "report_tflops",
    "denoising_objective",
    "mask_ratio",
    "mask_length",
    "poisson_lambda",
    "replace_length",
    "reset_optim",
    "src_seq_length_min",
    "tgt_seq_length_min",
    "src_seq_length_max",
    "tgt_seq_length_max",
    "train_steps",
    "accum_count",
    "lookahead_minibatches",
    "normalization",
    "queue_size",
    "valid_batch_size",
    "optim",
    "learning_rate",
    "adam_beta1",
    "adam_beta2",
    "weight_decay",
    "max_grad_norm",
    "label_smoothing",
    "warmup_steps",
    "decay_method",
    "learning_rate_decay",
    "start_decay_steps",
    "average_decay",
    "n_nodes",
    "task_distribution_strategy",
    "valid_steps",
    "valid_metrics",
    "save_checkpoint_steps",
    "keep_checkpoint",
    "log_model_structure",
    "report_every",
    "report_training_accuracy",
    "save_model",
    "save_strategy",
]

DROP_TASK_KEYS = [
    "path_src",
    "path_tgt",
    "path_valid_src",
    "path_valid_tgt",
]

DEFAULT_XT_BEAM_SIZE = 4
DEFAULT_PT_BEAM_SIZE = 5
DEFAULT_BATCH_SIZE = 32
DEFAULT_BATCH_TYPE = "sents"
DEFAULT_GPU = 0
DEFAULT_WORLD_SIZE = 1
DEFAULT_GPU_RANKS = [0]



TRIPLES = [
    ("bos", "bos_Latn", ["bs_??"]),
    ("bul", "bul_Cyrl", ["bg_BG"]),
    ("cat", "cat_Latn", ["ca_ES"]),
    ("ces", "ces_Latn", ["cs_CZ"]),
    ("dan", "dan_Latn", ["da_DK"]),
    ("deu", "deu_Latn", ["de_DE"]),
    ("ell", "ell_Grek", ["el_GR"]),
    ("est", "ekk_Latn", ["et_EE"]),
    ("eng", "eng_Latn", ["en_??"]),
    ("eus", "eus_Latn", ["eu_??"]),
    ("fin", "fin_Latn", ["fi_FI"]),
    ("fra", "fra_Latn", ["fr_CA", "fr_FR"]),
    ("gle", "gle_Latn", ["ga_??"]),
    ("glg", "glg_Latn", ["gl_??"]),
    ("hrv", "hrv_Latn", ["hr_HR"]),
    ("hun", "hun_Latn", ["hu_HU"]),
    ("isl", "isl_Latn", ["is_IS"]),
    ("ita", "ita_Latn", ["it_IT"]),
    ("kat", "kat_Geor", ["ka_??"]),
    ("lav", "lvs_Latn", ["lv_LV"]),
    ("lit", "lit_Latn", ["lt_LT"]),
    ("mkd", "mkd_Cyrl", ["mk_??"]),
    ("mlt", "mlt_Latn", ["mt_??"]),
    ("nld", "nld_Latn", ["nl_NL"]),
    ("nno", "nno_Latn", ["nn_??"]),
    ("nob", "nob_Latn", ["no_NO"]),
    ("pol", "pol_Latn", ["pl_PL"]),
    ("por", {"default": "por_Latn","flo": "por_Latn","bqt": "por_Latn","bqtpar": "por_Latn_braz1246",}, ["pt_PT", "pt_BR"]),
    ("ron", "ron_Latn", ["ro_RO"]),
    ("slk", "slk_Latn", ["sk_SK"]),
    ("slv", "slv_Latn", ["sl_SI"]),
    ("spa", "spa_Latn", ["es_MX"]),
    ("sqi", "als_Latn", ["sq_??"]),
    ("srp_Cyrl", "srp_Cyrl", ["sr_RS"]),
    ("swe", "swe_Latn", ["sv_SE"]),
    ("tur", "tur_Latn", ["tr_TR"]),
    ("ukr", "ukr_Cyrl", ["uk_UA"]),
]
@dataclass
class LanguageInventory:
    """
    valid_codes:
        Set of all known language codes
    code_to_ref:
        Language code -> benchmark file stem
        Example: "fra" -> "fra_Latn"
        Used in emit_tasks
    code_to_dataset_ref:
        Dict[str, Dict[str, str]] = field(default_factory=dict)
    code_to_xcodes:
        Language code -> all localized task-xcode labels
        Example: "fra" -> ["CA.fra", "FR.fra"]
    xcode_to_code:
        Localized xcode label -> language code
        Example: "CA.fra" -> "fra"
    valid_xcodes:
        Set of all known localized xcode labels
    xcode_to_wmt_locale:
        Localized xcode label -> WMT locale string
        Example: "CA.fra" -> "fr_CA"
        Used in emit_tasks
    """
    valid_codes: Set[str] = field(default_factory=set)
    code_to_ref: Dict[str, str] = field(default_factory=dict)
    code_to_dataset_ref: Dict[str, Dict[str, str]] = field(default_factory=dict)
    code_to_xcodes: Dict[str, List[str]] = field(default_factory=dict)
    xcode_to_code: Dict[str, str] = field(default_factory=dict)
    valid_xcodes: Set[str] = field(default_factory=set)
    xcode_to_wmt_locale: Dict[str, str] = field(default_factory=dict)
    code_to_model_code: Dict[str, str] = field(default_factory=dict)

def build_language_inventory() -> LanguageInventory:
    def variant_tag_for_locale(locale: str) -> str:
        if "_" in locale:
            tag = locale.rsplit("_", 1)[1]
        else:
            tag = "XX"
        if not tag or tag == "??":
            tag = "XX"
        return tag
    inv = LanguageInventory()
    for code, refspec, locales in TRIPLES:
        inv.valid_codes.add(code)
        if isinstance(refspec, dict):
            default_ref = refspec.get("default")
            if not default_ref:
                die(f"TRIPLES entry for {code} has dict refspec but no 'default'")
            inv.code_to_ref[code] = default_ref
            inv.code_to_dataset_ref[code] = dict(refspec)
            inv.code_to_model_code[code] = refspec.get("model", code)
        else:
            inv.code_to_ref[code] = refspec
            inv.code_to_dataset_ref[code] = {
                "default": refspec,
                "flo": refspec,
                "bqt": refspec,
                "bqtpar": refspec,
                "wmt": refspec,
            }
            inv.code_to_model_code[code] = code
        xcodes: List[str] = []
        if not locales:
            log(f"ERROR: no locale for {code}")
            exit(1)
        for locale in locales:
            variant = variant_tag_for_locale(locale)
            if len(locales) == 1:
                variant = "XX"
            xcode = f"{variant}.{code}"
            inv.valid_xcodes.add(xcode)
            inv.xcode_to_code[xcode] = code
            inv.xcode_to_wmt_locale[xcode] = locale
            xcodes.append(xcode)
        inv.code_to_xcodes[code] = xcodes
    return inv

def dataset_ref(inventory: LanguageInventory, code: str, dataset_tag: str) -> str:
    refs = inventory.code_to_dataset_ref.get(code)
    if not refs:
        return inventory.code_to_ref[code]
    return refs.get(dataset_tag, refs.get("default", inventory.code_to_ref[code]))


TESTSET_NAMES = {
    "flo": "flores200",
    "bqt": "bouquet",
    "bqtpar": "bouquetpar",
    "wmt": "wmt24pp",
}

# Explicit dataset-language registry refinements required by RFC-EVAL-ARTIFACTS.
# Most datasets use the project's canonical language code directly.
DATASET_LANGUAGE_OVERRIDES = {
    ("bqtpar", "por"): "por_BR",
}

from functools import lru_cache


@lru_cache(maxsize=None)
def testset_line_count(path: str) -> int:
    with open(path, "r", encoding="utf-8", errors="strict") as f:
        n = sum(1 for _ in f)

    if n <= 0:
        raise ValueError(f"empty test set: {path}")

    return n

def hypothesis_line_count(path: str) -> int | None:
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as f:
            return sum(1 for _ in f)
    except (OSError, UnicodeError):
        return None


def dataset_language_id(inventory: LanguageInventory, code: str, dataset_tag: str,
                        xcode: str) -> str:
    """Return the RFC evaluation-language identifier for one dataset side."""
    override = DATASET_LANGUAGE_OVERRIDES.get((dataset_tag, code))
    if override:
        return override
    if dataset_tag == "wmt":
        # Preserve a WMT region only when the training-language inventory has
        # multiple registered WMT locales (currently fra and por).  Otherwise
        # the canonical project code is sufficient, e.g. srp_Cyrl.
        if len(inventory.code_to_xcodes.get(code, ())) > 1:
            locale = inventory.xcode_to_wmt_locale.get(xcode, "")
            if "_" in locale:
                region = locale.rsplit("_", 1)[1]
                if region and region != "??":
                    return f"{code}_{region}"
    return code

def artifact_basename(task_name: str, dataset_tag: str, src_lang: str, tgt_lang: str) -> str:
    """RFC-EVAL-ARTIFACTS basename: task.testset.eval-src.eval-tgt."""
    return f"{task_name}.{TESTSET_NAMES[dataset_tag]}.{src_lang}.{tgt_lang}"

def check_data_coverage(support, valid_xcodes):
    """Validate localized evaluation languages without parsing task names."""
    bad = []
    for task in sorted(support.task_set):
        src_xcode = support.task_to_src_xcode[task]
        tgt_xcode = support.task_to_tgt_xcode[task]
        if src_xcode not in valid_xcodes or tgt_xcode not in valid_xcodes:
            bad.append((support.task_to_orig.get(task, task), src_xcode, tgt_xcode))
    if bad:
        log("❌ Following designated tasks do not have test-language coverage:")
        for orig_task, src_xcode, tgt_xcode in bad:
            log(f"   {orig_task}: {src_xcode} -> {tgt_xcode}")
        die("Stopping before planning uncovered evaluation tasks")
    log("✅ All designated tasks covered (at least partially) by data")

def require_env(name: str, extra: str = "") -> str:
    value = os.environ.get(name)
    if not value:
        if extra:
            die(f"{name} must be set {extra}")
        die(f"{name} must be set")
    return value

def load_trainconfig(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg if isinstance(cfg, dict) else {}

def get_env_vars():
    datadir = require_env("DATADIR", "to the location of training data")
    cfgdir = require_env("CFGDIR", "to a subdirectory of the model directory")
    tskdir = require_env("TSKDIR", "to a subdirectory of the model directory")
    hypdir = require_env("HYPDIR", "to a subdirectory of the model directory")
    model = require_env("MODEL", "to the model directory; it must end with slash")
    trainconfig = require_env("TRAINCONFIG", "to the training config file")
    inftasks = require_env("INFTASKS","to the file listing selected inference tasks")
    mammoth = require_env("MAMMOTH", "to the Mammoth source directory")
    logdir = require_env("LOGDIR", "to the log directory")
    scrdir = require_env("SCRDIR", "to the scoring output directory")
    mammoth_type = require_env("MAMMOTH_TYPE", "using xtransformers or pytorch")
    if not os.path.exists(model):
        die(f"Error: MODEL must be an existing file or directory: {model}")
    if not os.path.isfile(trainconfig):
        die(f"Error: TRAINCONFIG must be an existing file: {trainconfig}")
    if not os.path.isdir(tskdir):
        die(f"Error: TSKDIR must be an existing directory: {tskdir}")
    if not os.path.isdir(cfgdir):
        die(f"Error: CFGDIR must be an existing directory: {cfgdir}")
    if not os.path.isdir(hypdir):
        die(f"Error: HYPDIR must be an existing directory: {hypdir}")
    if not os.path.isdir(datadir):
        die(f"Error: DATADIR must be an existing directory: {datadir}")
    if not os.path.isfile(inftasks):
        die(f"Error: INFTASKS must be an existing file: {inftasks}")
    if not os.path.isdir(mammoth):
        die(f"Error: MAMMOTH must be an existing directory: {mammoth}")
    if not os.path.isdir(logdir):
        die(f"Error: LOGDIR must be an existing directory: {logdir}")
    if not os.path.isdir(scrdir):
        die(f"Error: SCRDIR must be an existing directory: {scrdir}")
    if not mammoth_type in ["xtransformers", "pytorch"]:
        die(f"Error: MAMMOTH_TYPE must be 'xtransformers' or 'pytorch'")

    inventory = build_language_inventory()
    log(f"✅ Loaded internal language codes")
    cfg = load_trainconfig(trainconfig)
    log(f"✅ Loaded the training config file {trainconfig}")
    log(f"✨ Environment validated")
    return (datadir, tskdir, cfgdir, hypdir, model, trainconfig, inftasks,
            mammoth, logdir, scrdir, cfg, inventory, mammoth_type)

def read_task_file(path):
    tasks = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tasks.add(line)

    return tasks

class InferenceTaskWriter:
    """Stage a complete set of one-output inference tasks and commit atomically per file.

    The staging directory prevents a failed planning pass from leaving a mixture
    of old and new task definitions.  commit() is called only after all planned
    datasets and inference YAMLs have been produced successfully.
    """
    def __init__(self, tskdir: str):
        self.tskdir = os.path.abspath(tskdir)
        self.stage = tempfile.mkdtemp(prefix=".inf-tasks.", dir=self.tskdir)
        # task filename -> complete producer specification.  Several localized
        # training-language variants may intentionally collapse to the same RFC
        # evaluation artifact (for example fra_CA/fra_FR -> Flores fra).  Such
        # duplicates are harmless only when they describe exactly the same job.
        self.specs: dict[str, tuple[tuple[str, str], ...]] = {}
        self.committed = False

    @staticmethod
    def _assignment(name: str, value: str) -> str:
        return f"{name}={shlex.quote(str(value))}\n"

    def write(self, *, task_id: str, infer_src: str, infer_ref: str,
              infer_hyp: str, inference_yaml: str, model: str, mammoth: str,
              logdir: str) -> str:
        hyp = os.path.abspath(infer_hyp)
        stem = os.path.basename(hyp)
        if not stem.endswith(".hyp"):
            raise ValueError(f"canonical inference output must end in .hyp: {hyp}")
        task_name = stem[:-len(".hyp")] + ".inf"
        task_path = os.path.join(self.stage, task_name)
        infer_log = os.path.join(logdir, f"job${{SLURM_JOB_ID}}.{stem[:-len('.hyp')]}.err")
        values = (
            ("TASK_ID", task_id),
            ("INFER_SRC", os.path.abspath(infer_src)),
            ("INFER_REF", os.path.abspath(infer_ref)),
            ("INFER_HYP", hyp),
            ("INFERENCE_YAML", os.path.abspath(inference_yaml)),
            ("MODEL", os.path.abspath(model)),
            ("MAMMOTH", os.path.abspath(mammoth)),
            ("LOGDIR", os.path.abspath(logdir)),
            ("INFER_LOG", infer_log),
        )
        previous = self.specs.get(task_name)
        if previous is not None:
            if previous == values:
                log(f"##      SAME  - RFC artifact already planned: {task_name}")
                return ""
            old = dict(previous)
            new = dict(values)
            changed = ", ".join(
                name for name in old.keys() | new.keys() if old.get(name) != new.get(name)
            )
            raise ValueError(
                f"conflicting producers for inference task/output stem {task_name}; "
                f"different fields: {changed}"
            )
        self.specs[task_name] = values
        with open(task_path, "x", encoding="utf-8", newline="\n") as f:
            f.write("# Generated by plan_eval3_inference.py; one task -> one .hyp\n")
            for name, value in values:
                f.write(self._assignment(name, value))
            f.flush()
            os.fsync(f.fileno())
        return task_path

    def commit(self) -> int:
        if not self.specs:
            raise ValueError("planning produced no inference .inf tasks")
        # Semaphore management is Make's responsibility.  Replace only *.inf;
        # calls.out, inf.slurm, and other evaluation/tasks files are untouched.
        for old in Path(self.tskdir).glob("*.inf"):
            old.unlink()
        for name in sorted(self.specs):
            os.replace(os.path.join(self.stage, name), os.path.join(self.tskdir, name))
        os.rmdir(self.stage)
        self.committed = True
        return len(self.specs)

    def close(self) -> None:
        if not self.committed:
            shutil.rmtree(self.stage, ignore_errors=True)

class CallWriters:
    def __init__(self, tskdir: str):
        self.plan_path  = os.path.join(tskdir, "plan.out") # file
        self.calls_path = os.path.join(tskdir, "calls.out") # file
        self.sacre_path = os.path.join(tskdir, "calls.sacre.out") # file
        self.comet_path = os.path.join(tskdir, "calls.comet.out") # file

        self.plan  = open(self.plan_path,  "w", encoding="utf-8")
        self.calls = open(self.calls_path, "w", encoding="utf-8")
        self.sacre = open(self.sacre_path, "w", encoding="utf-8")
        self.comet = open(self.comet_path, "w", encoding="utf-8")

    def flush(self):
        for stream in (self.plan, self.calls, self.sacre, self.comet):
            stream.flush()

    def close(self):
        self.plan.close()
        self.calls.close()
        self.sacre.close()
        self.comet.close()

def validate_calls_out(tskdir: str):
    calls_path = os.path.join(tskdir, "calls.out") # file
    if not os.path.exists(calls_path):
        return
    bad = []
    with open(calls_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if line and not line.startswith("python"):
                bad.append((i, line))
    if bad:
        log("❌ FAIL: not every line in calls.out starts with 'python'")
        for i, line in bad:
            log(f"  line {i}: {line}")
        raise ValueError("calls.out contains non-python lines")
    log("✅ Every line in calls.out starts with 'python'")

def files_available(dataset, input_path, refer_path, config_file):
    log(f"##    {dataset}")
    if not os.path.exists(input_path):
        log(f"##      FAIL  - Source file    missed: {input_path}")
        return False
    else:
        log(f"##      HAVE  - Source file     found: {input_path}")
    if not os.path.exists(refer_path):
        log(f"##      FAIL  - Reference file missed: {refer_path}")
        return False
    else:
        log(f"##      HAVE  - Reference file  found: {refer_path}")
    if not os.path.exists(config_file):
        log(f"##      FAIL  - Config file    missed: {config_file}")
        return False
    else:
        log(f"##      HAVE  - Config file     found: {config_file}")
    return True

def plan_translation_and_scoring(
    *,
    writers: CallWriters,
    task_writer: InferenceTaskWriter,
    dataset: str,
    input_path: str,
    refer_path: str,
    config_path: str,
    model_path: str,
    mammoth_dir: str,
    logdir: str,
    scrdir: str,
    hypdir: str,
    xtask: str,
    orig_task: str,
    data_tag: str,
    eval_src: str,
    eval_tgt: str,
    pair_type: str,
) -> bool:
    basename = artifact_basename(orig_task, data_tag, eval_src, eval_tgt)
    shortoutput = f"{basename}.hyp"
    sacre_path = os.path.join(scrdir, f"{basename}.sacre")
    comet_path = os.path.join(scrdir, f"{basename}.comet")
    output_path = os.path.join(hypdir, shortoutput)
    if not files_available(dataset, input_path, refer_path, config_path):
         return False

    task_path = task_writer.write(
        task_id=orig_task, infer_src=input_path, infer_ref=refer_path,
        infer_hyp=output_path, inference_yaml=config_path, model=model_path,
        mammoth=mammoth_dir, logdir=logdir,
    )
    if not task_path:
        # Multiple localized training variants can map to one dataset artifact.
        # The first identical producer owns the .inf and all legacy plan/scoring
        # entries; do not duplicate those entries either.
        return True

    writers.plan.write(
        f'--task_id "{orig_task}" --src "{input_path}" --output "{output_path}" --refer "{refer_path}" '
        f'--log "{logdir}/job${{SLURM_JOB_ID}}.{basename}.err"\n'
    )
    expected_lines = testset_line_count(input_path)
    output_lines = hypothesis_line_count(output_path)
    if output_lines == expected_lines:
        if os.path.exists(sacre_path) and os.path.getsize(sacre_path) > 500:
            log(f"##      GOOD - already scored: {sacre_path}")
        else:
            log(f"##      DONE - ({expected_lines} lines) -- ready to measure")
            log(f"##             Contrasting {refer_path} VS {output_path}")
            writers.sacre.write(f'if [ -s "{sacre_path}" ] && [ "$(stat -c%s "{sacre_path}")" -gt 500 ]; then ')
            writers.sacre.write(f'    echo "Skipping {sacre_path} because it already exists and is >500 bytes"; ')
            writers.sacre.write("else ")
            writers.sacre.write(f'    date | tee "{sacre_path}"; ')
            writers.sacre.write(
                f'    echo {TESTSET_NAMES[data_tag]} {orig_task} '
                f'Contrasting {refer_path} VS {output_path} | tee -a "{sacre_path}"; ')
            writers.sacre.write(f'    sacrebleu "{refer_path}" -i "{output_path}" -m bleu chrf | tee -a "{sacre_path}"; ')
            writers.sacre.write("fi\n")
        writers.comet.write(f'comet-score -r "{refer_path}" -t "{output_path}" -s "{input_path}" --gpus 1 | tee "{comet_path}"\n')
        return True
    if os.path.exists(output_path):
        if output_lines is None:
            log(f"##      REDO - unreadable hypothesis; re-translate ==> {shortoutput}")
        else:
            log(f"##      REDO - ({output_lines} vs {expected_lines} lines; re-translate) ==> {shortoutput}")
    else:
        log(f"##      TODO - ({expected_lines} lines expected; translate now) ==> {shortoutput}")
        log(f"##      TODO - translate=> {output_path}")
    runner = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "run_eval3_inference.py",)
    writers.calls.write(
        f'python -u "{runner}" '
        f'--mammoth "{mammoth_dir}" '
        f'--config "{config_path}" '
        f'--model "{model_path}" '
        f'--task-id "{orig_task}" '
        f'--src "{input_path}" '
        f'--expected-lines {expected_lines} '
        f'--output "{output_path}" '
        f'--log "{logdir}/job${{SLURM_JOB_ID}}.{basename}.err"\n'
    )
    return True


@dataclass
class TaskSupport:
    """
    orig_task_names:
        Original task names in the training config
    task_set:
        Internal localized evaluation identities.  These are not artifact names.
    task_to_type:
        Internal selection label; no semantics are inferred from task-name prefixes.
    task_to_orig:
        Internal localized identity -> exact original YAML task name.
    """
    orig_task_names: List[str] = field(default_factory=list)
    task_set: Set[str] = field(default_factory=set)
    task_to_type: Dict[str, str] = field(default_factory=dict)
    task_to_orig: Dict[str, str] = field(default_factory=dict)
    task_to_enc_group: Dict[str, object] = field(default_factory=dict)
    task_to_dec_group: Dict[str, object] = field(default_factory=dict)
    task_to_src_vocab_code: Dict[str, str] = field(default_factory=dict)
    task_to_tgt_vocab_code: Dict[str, str] = field(default_factory=dict)
    task_to_transforms: Dict[str, object] = field(default_factory=dict)
    task_to_src_xcode: Dict[str, str] = field(default_factory=dict)
    task_to_tgt_xcode: Dict[str, str] = field(default_factory=dict)

def collect_task_support(cfg, inventory):
    """Expand training tasks using structured src_tgt metadata.

    Task names are opaque RFC artifact identifiers.  In particular, zero_*
    tasks are not special-cased and mt_/zero_/denoise_ prefixes are never
    parsed to discover languages or task type.
    """
    def expand_langspec(spec: str) -> list[str]:
        if spec in inventory.valid_xcodes:
            return [spec]
        return list(inventory.code_to_xcodes.get(spec, []))

    train_tasks = cfg.get("tasks", {})
    support = TaskSupport()
    support.orig_task_names = list(train_tasks.keys())
    for orig_task in support.orig_task_names:
        task_cfg = train_tasks.get(orig_task)
        if not isinstance(task_cfg, dict):
            log(f"❌ Malformed TRAINCONFIG task mapping: {orig_task}")
            continue
        src_tgt = task_cfg.get("src_tgt")
        if not isinstance(src_tgt, str) or "-" not in src_tgt:
            log(f"❌ Missing or malformed src_tgt in TRAINCONFIG task: {orig_task}")
            continue
        src_spec, tgt_spec = src_tgt.split("-", 1)
        if src_spec == tgt_spec:
            # Same-language training tasks are denoising objectives, not
            # translation directions.  Keep the YAML task name known so that
            # selecting it is not reported as a missing task, but do not
            # create any evaluation identities or inference artifacts for it.
            log(f"   SKIP  - denoising task {orig_task}: src_tgt={src_tgt}")
            continue
        src_xcodes = expand_langspec(src_spec)
        tgt_xcodes = expand_langspec(tgt_spec)
        if not src_xcodes or not tgt_xcodes:
            log(f"❌ Could not expand src_tgt={src_tgt!r} for YAML task '{orig_task}'")
            continue

        train_src_vocab, train_tgt_vocab = src_spec, tgt_spec
        enc_group = task_cfg.get("enc_sharing_group", [])
        dec_group = task_cfg.get("dec_sharing_group", [])
        transforms = task_cfg.get("transforms")
        if transforms is None:
            transforms = task_cfg.get("train_transforms", [])
        for src_xcode in src_xcodes:
            for tgt_xcode in tgt_xcodes:
                # Internal expansion identity only; never used as an artifact
                # task name or Mammoth --task_id.
                xtask = f"{orig_task}@@{src_xcode}@@{tgt_xcode}"
                support.task_set.add(xtask)
                support.task_to_type[xtask] = "selected"
                support.task_to_orig[xtask] = orig_task
                support.task_to_src_xcode[xtask] = src_xcode
                support.task_to_tgt_xcode[xtask] = tgt_xcode
                support.task_to_src_vocab_code[xtask] = train_src_vocab
                support.task_to_tgt_vocab_code[xtask] = train_tgt_vocab
                support.task_to_enc_group[xtask] = enc_group
                support.task_to_dec_group[xtask] = dec_group
                support.task_to_transforms[xtask] = transforms

    log("✅ Extracted training tasks and localized them from structured src_tgt metadata")
    return support

def produce_infyamls_and_calls(inventory, support, datadir, cfgdir, hypdir, trainconfig, cfg, writers, task_writer,
                               model, mammoth, logdir, scrdir, mammoth_type):
    log(f"producing the testing tasks (stdout) ...", end="")
    for xtask in sorted(support.task_set):
        emit_tasks(xtask=xtask, inventory=inventory, support=support,
                   datadir=datadir, cfgdir=cfgdir, hypdir=hypdir, cfg_path=trainconfig, cfg=cfg,
                   writers=writers, task_writer=task_writer, model=model, mammoth=mammoth, logdir=logdir, scrdir=scrdir,
                   mammoth_type=mammoth_type)
    log(f'✨ Completed producing inference config files')

def emit_tasks(*, xtask: str, support: TaskSupport,
               inventory: LanguageInventory, datadir: str, cfgdir: str, hypdir: str,
               cfg_path: str,cfg: dict, writers: CallWriters, task_writer: InferenceTaskWriter,
               model: str, mammoth: str, logdir: str, scrdir: str,
               mammoth_type: str) -> bool:
    pair_type = support.task_to_type.get(xtask, "selected")
    orig_task = support.task_to_orig.get(xtask, xtask)
    src_xcode = support.task_to_src_xcode[xtask]
    tgt_xcode = support.task_to_tgt_xcode[xtask]
    log(f"## {orig_task} [{src_xcode} -> {tgt_xcode}]:")
    src = inventory.xcode_to_code.get(src_xcode)
    tgt = inventory.xcode_to_code.get(tgt_xcode)
    if src is None or tgt is None:
        log(f"  Skipping {xtask}: could not decode language xcode(s)")
        exit(1)
    if src not in inventory.code_to_ref or tgt not in inventory.code_to_ref:
        log(f"  Skipping {xtask}: unknown language code(s)")
        exit(1)
    src_ref = inventory.code_to_ref[src]
    tgt_ref = inventory.code_to_ref[tgt]
    flo_src_ref = dataset_ref(inventory, src, "flo")
    flo_tgt_ref = dataset_ref(inventory, tgt, "flo")
    bqt_src_ref = dataset_ref(inventory, src, "bqt")
    bqt_tgt_ref = dataset_ref(inventory, tgt, "bqt")
    bqtpar_src_ref = dataset_ref(inventory, src, "bqtpar")
    bqtpar_tgt_ref = dataset_ref(inventory, tgt, "bqtpar")

    flo_src_id = dataset_language_id(inventory, src, "flo", src_xcode)
    flo_tgt_id = dataset_language_id(inventory, tgt, "flo", tgt_xcode)
    bqt_src_id = dataset_language_id(inventory, src, "bqt", src_xcode)
    bqt_tgt_id = dataset_language_id(inventory, tgt, "bqt", tgt_xcode)
    bqtpar_src_id = dataset_language_id(inventory, src, "bqtpar", src_xcode)
    bqtpar_tgt_id = dataset_language_id(inventory, tgt, "bqtpar", tgt_xcode)
    wmt_src_id = dataset_language_id(inventory, src, "wmt", src_xcode)
    wmt_tgt_id = dataset_language_id(inventory, tgt, "wmt", tgt_xcode)

    src_wmt = inventory.xcode_to_wmt_locale.get(src_xcode, "")
    tgt_wmt = inventory.xcode_to_wmt_locale.get(tgt_xcode, "")
    inf_yaml_path_file = f"{cfgdir}/{orig_task}.yaml"
    inf_yaml_path = f"{cfgdir}/{orig_task}.yaml"

    write_inference_yaml(
        src_code=src, tgt_code=tgt, pair_type=pair_type,
        xtask=xtask, orig_task=orig_task, cfg=cfg,
        train_cfg=cfg_path, inf_yaml_path=inf_yaml_path_file, support=support,
        mammoth_type=mammoth_type)

    flo_input = os.path.join(datadir, "flores_plus", "devtest", f"{flo_src_ref}.txt")
    flo_refer = os.path.join(datadir, "flores_plus", "devtest", f"{flo_tgt_ref}.txt")

    plan_translation_and_scoring(
        writers=writers, task_writer=task_writer, dataset="Flores+", data_tag="flo", input_path=flo_input, refer_path=flo_refer,
        config_path=inf_yaml_path, model_path=model, mammoth_dir=mammoth,
        logdir=logdir, scrdir=scrdir, hypdir=hypdir,
        xtask=xtask, orig_task=orig_task, eval_src=flo_src_id, eval_tgt=flo_tgt_id, pair_type=pair_type)

    bqt_input = os.path.join(datadir, "bouquet", "test", f"{bqt_src_ref}.txt")
    bqt_refer = os.path.join(datadir, "bouquet", "test", f"{bqt_tgt_ref}.txt")
    plan_translation_and_scoring(
        writers=writers, task_writer=task_writer, dataset="BOUQuET", data_tag="bqt", input_path=bqt_input, refer_path=bqt_refer,
        config_path=inf_yaml_path, model_path=model, mammoth_dir=mammoth,
        logdir=logdir, scrdir=scrdir, hypdir=hypdir,
        xtask=xtask, orig_task=orig_task, eval_src=bqt_src_id, eval_tgt=bqt_tgt_id, pair_type=pair_type)

    bqtpar_input = os.path.join(datadir, "bouquet_par", "test", f"{bqtpar_src_ref}.txt")
    bqtpar_refer = os.path.join(datadir, "bouquet_par", "test", f"{bqtpar_tgt_ref}.txt")
    plan_translation_and_scoring(
        writers=writers, task_writer=task_writer, dataset="BOUQuETpar", data_tag="bqtpar", input_path=bqtpar_input, refer_path=bqtpar_refer,
        config_path=inf_yaml_path, model_path=model, mammoth_dir=mammoth,
        logdir=logdir, scrdir=scrdir, hypdir=hypdir,
        xtask=xtask, orig_task=orig_task, eval_src=bqtpar_src_id, eval_tgt=bqtpar_tgt_id, pair_type=pair_type)

    if src == "eng":
        wmt_input = os.path.join(datadir, "wmt24pp", "train", f"en-{tgt_wmt}", "source.en.txt")
        wmt_refer = os.path.join(datadir, "wmt24pp", "train", f"en-{tgt_wmt}", "reference.target.txt")
    elif tgt == "eng":
        wmt_input = os.path.join(datadir, "wmt24pp", "train", f"en-{src_wmt}", "reference.target.txt")
        wmt_refer = os.path.join(datadir, "wmt24pp", "train", f"en-{src_wmt}", "source.en.txt")
    else:
        wmt_input = os.path.join(datadir, "wmt24pp", "train", f"en-{src_wmt}", "reference.target.txt")
        wmt_refer = os.path.join(datadir, "wmt24pp", "train", f"en-{tgt_wmt}", "reference.target.txt")

    plan_translation_and_scoring(
        writers=writers, task_writer=task_writer, dataset="WMT24++", data_tag="wmt", input_path=wmt_input, refer_path=wmt_refer,
        config_path=inf_yaml_path, model_path=model, mammoth_dir=mammoth,
        logdir=logdir, scrdir=scrdir, hypdir=hypdir,
        xtask=xtask, orig_task=orig_task, eval_src=wmt_src_id, eval_tgt=wmt_tgt_id, pair_type=pair_type)

    return True

def build_inference_config_from_template(
    *,
    cfg: dict,
    support: TaskSupport,
    xtask: str,
    orig_task: str,
    src_code: str,
    tgt_code: str,
    pair_type: str,
    train_cfg_path: str,
    mammoth_type: str,
) -> dict:
    """Build a one-task view of the RFC-EVAL-YAML conversion.

    make_inference_yaml.convert() is authoritative for field removal, training
    metadata renaming, inference defaults, and provenance.  The planner only
    narrows its model-wide result to the selected training task and the two
    vocabularies required by that task.  It must not reintroduce eval2 helper
    fields or run-specific selectors.
    """
    del src_code, tgt_code, pair_type, mammoth_type  # conversion is task/config driven

    infer_cfg = convert_eval3_inference_yaml(cfg, train_cfg_path)
    if orig_task not in infer_cfg["tasks"]:
        raise KeyError(f"training task {orig_task!r} missing after RFC YAML conversion")

    src_vocab_code = support.task_to_src_vocab_code[xtask]
    tgt_vocab_code = support.task_to_tgt_vocab_code[xtask]
    src_vocab = infer_cfg.get("src_vocab", {})
    tgt_vocab = infer_cfg.get("tgt_vocab", {})
    if src_vocab_code not in src_vocab:
        raise KeyError(f"source vocab code {src_vocab_code!r} missing from converted src_vocab")
    if tgt_vocab_code not in tgt_vocab:
        raise KeyError(f"target vocab code {tgt_vocab_code!r} missing from converted tgt_vocab")

    infer_cfg["tasks"] = {orig_task: copy.deepcopy(infer_cfg["tasks"][orig_task])}
    infer_cfg["src_vocab"] = {src_vocab_code: src_vocab[src_vocab_code]}
    infer_cfg["tgt_vocab"] = {tgt_vocab_code: tgt_vocab[tgt_vocab_code]}
    return infer_cfg


def write_inference_yaml(*, src_code: str, tgt_code: str, pair_type: str,
                         xtask: str, orig_task: str, cfg: dict,
                         train_cfg: str, inf_yaml_path: str, support: TaskSupport,
                         mammoth_type: str) -> bool:
    enc_group      = support.task_to_enc_group[xtask]
    dec_group      = support.task_to_dec_group[xtask]
    src_vocab_code = support.task_to_src_vocab_code[xtask]
    tgt_vocab_code = support.task_to_tgt_vocab_code[xtask]
    log(f"##      TASK  - sharing groups: {enc_group} x {dec_group}")
    log(f"##      TASK  - src_tgt codes: {src_vocab_code}-{tgt_vocab_code}")
    infer_cfg = build_inference_config_from_template(
        cfg=cfg, support=support, xtask=xtask, orig_task=orig_task,
        src_code=src_code, tgt_code=tgt_code, pair_type=pair_type,
        train_cfg_path=train_cfg, mammoth_type=mammoth_type,
    )
    with open(inf_yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(infer_cfg, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

    log(f"##      WROTE - RFC-conformant one-task inference YAML: {inf_yaml_path}")
    return True


def filter_selected_tasks(support, selected_tasks):
    keep = {
        xtask
        for xtask in support.task_set
        if support.task_to_orig.get(xtask) in selected_tasks
    }
    missing = selected_tasks - set(support.orig_task_names)
    for task in sorted(missing):
        log(f"❌ Selected inference task is not in TRAINCONFIG: {task}")
    if missing:
        die(f"Selected inference tasks are missing from TRAINCONFIG")
    support.task_set = keep
    log(f"   Kept {len(keep)} localized inference tasks")
    return support


def main() -> int:
    (datadir, tskdir, cfgdir, hypdir, model, trainconfig, inftasks,
     mammoth, logdir, scrdir, cfg, lang_inventory, mammoth_type) = get_env_vars()
    writers = CallWriters(tskdir)
    task_writer = InferenceTaskWriter(tskdir)
    try:
        support = collect_task_support(cfg, lang_inventory)
        selected_tasks = read_task_file(inftasks)
        support = filter_selected_tasks(support, selected_tasks)
        check_data_coverage(support, lang_inventory.valid_xcodes)
        produce_infyamls_and_calls(lang_inventory, support, datadir, cfgdir, hypdir, trainconfig, cfg,
                                   writers, task_writer, model, mammoth, logdir, scrdir, mammoth_type=mammoth_type)
        writers.flush()
        validate_calls_out(tskdir)
        count = task_writer.commit()
        log(f"✅ Committed {count} one-hypothesis inference task files to {tskdir}")
    finally:
        writers.close()
        task_writer.close()
    log(f'✨ All stages of planning completed')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


