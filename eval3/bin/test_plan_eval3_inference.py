#!/usr/bin/env python3
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("plan_eval3_inference", HERE / "plan_eval3_inference.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def spec(root: Path, *, src="src.txt"):
    return dict(
        task_id="mt_fra-eng",
        infer_src=str(root / src),
        infer_ref=str(root / "ref.txt"),
        infer_hyp=str(root / "hypotheses" / "mt_fra-eng.flores200.fra.eng.hyp"),
        inference_yaml=str(root / "configs" / "mt_fra-eng.yaml"),
        model=str(root / "model.pt"),
        mammoth=str(root / "mammoth"),
        logdir=str(root / "logs"),
    )


def main():
    assert mod.artifact_basename("mt_fra-eng", "flo", "fra", "eng") == \
        "mt_fra-eng.flores200.fra.eng"
    assert mod.artifact_basename("mt_eng-fra", "wmt", "eng", "fra_CA") == \
        "mt_eng-fra.wmt24pp.eng.fra_CA"
    assert mod.artifact_basename("mt_eng-fra", "wmt", "eng", "fra_FR") == \
        "mt_eng-fra.wmt24pp.eng.fra_FR"

    # RFC: task names are opaque.  A zero_* task is localized from src_tgt
    # metadata and retains its exact training task key in artifact names.
    cfg = {
        "tasks": {
            "zero_fin-swe": {
                "src_tgt": "fin-swe",
                "enc_sharing_group": ["enc"],
                "dec_sharing_group": ["dec"],
                "transforms": [],
            }
        }
    }
    inv = mod.build_language_inventory()
    support = mod.collect_task_support(cfg, inv)
    assert support.orig_task_names == ["zero_fin-swe"]
    assert len(support.task_set) == 1
    xtask = next(iter(support.task_set))
    assert support.task_to_orig[xtask] == "zero_fin-swe"
    assert support.task_to_src_xcode[xtask] == "XX.fin"
    assert support.task_to_tgt_xcode[xtask] == "XX.swe"
    assert mod.artifact_basename("zero_fin-swe", "flo", "fin", "swe") == \
        "zero_fin-swe.flores200.fin.swe"

    # Per-task YAMLs must be exact one-task views of the authoritative
    # RFC-EVAL-YAML conversion in make_inference_yaml.py.
    yaml_cfg = {
        "tasks": {
            "zero_ces-slk": {
                "src_tgt": "ces-slk",
                "weight": 0,
                "introduce_at_training_step": 12000,
                "node_gpu": "7:3",
                "enc_sharing_group": ["zlw", "all"],
                "dec_sharing_group": ["slk"],
                "transforms": ["filtertoolong"],
                "path_src": "/training/ces.src",
                "path_tgt": "/training/slk.tgt",
            },
            "other": {
                "src_tgt": "eng-fin",
                "weight": "1",
                "enc_sharing_group": ["all"],
                "dec_sharing_group": ["fin"],
            },
        },
        "src_vocab": {"ces": "/v/ces.json", "eng": "/v/eng.json"},
        "tgt_vocab": {"slk": "/v/slk.json", "fin": "/v/fin.json"},
        "enc_layers": [3, 3],
        "dec_layers": [6],
        "model_dim": 512,
        "model_dtype": "bf16",
        "max_length": 1024,
        "batch_size": 4096,
        "batch_type": "tokens",
        "beam_size": 1,
        "train_steps": 100000,
        "valid_steps": 1000,
    }
    yaml_support = mod.collect_task_support(yaml_cfg, inv)
    zx = next(x for x in yaml_support.task_set
              if yaml_support.task_to_orig[x] == "zero_ces-slk")
    one = mod.build_inference_config_from_template(
        cfg=yaml_cfg, support=yaml_support, xtask=zx, orig_task="zero_ces-slk",
        src_code="ces", tgt_code="slk", pair_type="selected",
        train_cfg_path="/model/train.yaml", mammoth_type="pytorch")
    from make_inference_yaml import convert
    whole = convert(yaml_cfg, "/model/train.yaml")
    expected = dict(whole)
    expected["tasks"] = {"zero_ces-slk": whole["tasks"]["zero_ces-slk"]}
    expected["src_vocab"] = {"ces": whole["src_vocab"]["ces"]}
    expected["tgt_vocab"] = {"slk": whole["tgt_vocab"]["slk"]}
    assert one == expected
    zcfg = one["tasks"]["zero_ces-slk"]
    assert zcfg["_training_weight"] == 0 and isinstance(zcfg["_training_weight"], int)
    assert zcfg["_training_introduce_at_training_step"] == 12000
    for forbidden in ("weight", "introduce_at_training_step", "_template_task",
                      "_pair_type", "_original_train_task"):
        assert forbidden not in zcfg
    for forbidden in ("task_id", "_expanded_task", "model", "src", "output"):
        assert forbidden not in one
    assert one["beam_size"] == 4
    assert one["batch_size"] == 32
    assert one["batch_type"] == "sents"
    assert one["max_length"] == 1024
    assert one["_train_config"] == "/model/train.yaml"

    # Same-language src_tgt tasks are denoising objectives.  They are valid
    # TRAINCONFIG task names, but they must never become evaluation tasks.
    denoise_cfg = {
        "tasks": {
            "denoise_swe": {
                "src_tgt": "swe-swe",
                "enc_sharing_group": ["enc"],
                "dec_sharing_group": ["dec"],
                "transforms": [],
            },
            # The rule is based on src_tgt, not on the opaque task name.
            "foo": {
                "src_tgt": "fin-fin",
                "enc_sharing_group": ["enc"],
                "dec_sharing_group": ["dec"],
                "transforms": [],
            },
            "translation": {
                "src_tgt": "fin-swe",
                "enc_sharing_group": ["enc"],
                "dec_sharing_group": ["dec"],
                "transforms": [],
            },
        }
    }
    denoise_support = mod.collect_task_support(denoise_cfg, inv)
    assert set(denoise_support.orig_task_names) == {"denoise_swe", "foo", "translation"}
    assert len(denoise_support.task_set) == 1
    only = next(iter(denoise_support.task_set))
    assert denoise_support.task_to_orig[only] == "translation"

    # Selecting only denoising tasks is legal but leaves no inference work.
    selected_denoise = mod.filter_selected_tasks(
        denoise_support, {"denoise_swe", "foo"}
    )
    assert selected_denoise.task_set == set()

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tasks = root / "tasks"
        tasks.mkdir()
        w = mod.InferenceTaskWriter(str(tasks))
        try:
            first = w.write(**spec(root))
            assert first.endswith("mt_fra-eng.flores200.fra.eng.inf")
            # The second localized French expansion describes the same Flores
            # artifact and must collapse to the already staged task.
            second = w.write(**spec(root))
            assert second == ""
            assert len(w.specs) == 1

            # Same RFC output with a genuinely different producer is an error.
            try:
                w.write(**spec(root, src="different-src.txt"))
            except ValueError as e:
                assert "conflicting producers" in str(e)
                assert "INFER_SRC" in str(e)
            else:
                raise AssertionError("conflicting duplicate was accepted")

            assert w.commit() == 1
            assert len(list(tasks.glob("*.inf"))) == 1
        finally:
            w.close()

    print("PASS: RFC names, YAML conversion parity, localized deduplication, and denoising exclusion")


if __name__ == "__main__":
    main()
