import json

import pytest

from slidedsl import evolution_experiment as experiment
from slidedsl.incremental import save_json


def test_experiment_pairs_seeds_requests_and_records_unavailable_without_fake_success(
    monkeypatch, tmp_path
):
    calls = []

    def unavailable(model, strategy, request, folder, **options):
        calls.append((model, strategy, request, options["seed"]))
        folder.mkdir(parents=True)
        report = {
            "status": "NAO_EXECUTADO",
            "is_mock": False,
            "generated_presentations": 0,
            "compile_success": False,
            "syntax_errors": 0,
            "semantic_errors": 0,
            "geometry_errors": None,
            "geometry_warnings": None,
            "corrections": 0,
            "duration_ms": None,
            "model_metadata": {},
            "requirements": {"numerator": 0, "denominator": 5, "all_met": False},
        }
        save_json(
            folder / ("evolution_report.json" if strategy in {"A", "B"} else "report.json"), report
        )
        return report

    monkeypatch.setattr(experiment, "generate_strategy", unavailable)
    cases = [{"id": "same", "prompt": "Crie um slide sobre arquitetura", "slides": 1}]
    out = tmp_path / "experiment"
    result = experiment.evaluate_strategies("unit", cases, out, repetitions=2)
    assert len(calls) == 8
    for seed in (42, 43):
        paired = [c for c in calls if c[3] == seed]
        assert {c[1] for c in paired} == {"A", "B", "C", "D"}
        assert {c[2] for c in paired} == {cases[0]["prompt"]}
    assert all(s["executed"] == s["compiled"] == s["generated"] == 0 for s in result["summary"])
    assert (out / "evaluation.csv").read_text(encoding="utf-8").count("NAO_EXECUTADO") == 8
    before = len(calls)
    experiment.evaluate_strategies("unit", cases, out, repetitions=2, resume=True)
    assert len(calls) == before
    with pytest.raises(ValueError):
        experiment.evaluate_strategies("different", cases, out, repetitions=2, resume=True)
    report_path = out / "runs/same/rep_01/C/report.json"
    partial = json.loads(report_path.read_text(encoding="utf-8"))
    partial["status"] = "EXECUTADO"
    save_json(report_path, partial)
    with pytest.raises(ValueError, match="parcial"):
        experiment.evaluate_strategies("unit", cases, out, repetitions=2, resume=True)


def test_duplicate_requests_and_unsafe_case_paths_are_rejected(tmp_path):
    cases = [{"id": "../escape", "prompt": "Crie um slide", "slides": 1}]
    with pytest.raises(ValueError):
        experiment.evaluate_strategies("unit", cases, tmp_path / "bad")
    cases = [{"id": "same", "prompt": "Crie um slide", "slides": 1}] * 2
    with pytest.raises(ValueError):
        experiment.evaluate_strategies("unit", cases, tmp_path / "duplicate")
