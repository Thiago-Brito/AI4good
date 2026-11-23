"""F1 do TCC: plano pareado, execução retomável e dossiês fixos (tudo offline)."""

import csv
import importlib.util
import json
from pathlib import Path

import pytest

from slidedsl.experiment_runner import load_requests, plan_runs, run_matrix
from slidedsl.paths import project_root
from slidedsl.research import Dossier

REQUESTS = project_root() / "benchmark/format_requests.json"


def test_format_requests_cover_four_themes_three_levels():
    data = load_requests(REQUESTS)
    reqs = data["requests"]
    assert len(reqs) == 12
    assert {(r["theme"], r["level"]) for r in reqs} == {
        (t, lv) for t in {r["theme"] for r in reqs} for lv in ("tema", "detalhado", "obrigatorio")
    }
    assert all(r["obligations"] for r in reqs if r["level"] == "obrigatorio")
    assert len(data["seeds"]) == 5


def test_plan_is_paired_and_reproducible():
    reqs = load_requests(REQUESTS)["requests"]
    a = plan_runs(reqs, ["A", "C"], [1, 2], order_seed=7)
    b = plan_runs(reqs, ["A", "C"], [1, 2], order_seed=7)
    assert [r.run_id for r in a] == [r.run_id for r in b]
    assert len({r.run_id for r in a}) == 12 * 2 * 2
    assert [r.run_id for r in a] != [r.run_id for r in plan_runs(reqs, ["A", "C"], [1, 2], 8)]
    with pytest.raises(ValueError):
        plan_runs(reqs, ["A", "A"], [1], 1)


def rows(path):
    with (path / "results.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_run_matrix_resumes_without_overwriting(tmp_path):
    reqs = [{"id": "p1"}, {"id": "p2"}]
    runs = plan_runs(reqs, ["A", "B"], [1], order_seed=3)
    calls = []

    def flaky(run, folder):
        calls.append(run.run_id)
        if len(calls) == 2:
            raise KeyboardInterrupt  # simula queda do processo
        (folder / "saida.txt").write_text("ok")
        return {"tokens": 10}

    with pytest.raises(KeyboardInterrupt):
        run_matrix(runs, flaky, tmp_path, metric_fields=["tokens"])
    assert len(rows(tmp_path)) == 1

    def boom_once(run, folder):
        calls.append(run.run_id)
        if run.run_id == runs[2].run_id:  # posição fixa: ainda não executada
            raise RuntimeError("falhou")
        return {"tokens": 5}

    counts = run_matrix(runs, boom_once, tmp_path, metric_fields=["tokens"])
    assert counts["skipped"] == 1 and counts["ok"] + counts["error"] == 3
    table = rows(tmp_path)
    assert len(table) == 4 and len({r["run_id"] for r in table}) == 4
    assert table[0]["tokens"] == "10"  # a primeira linha não foi sobrescrita
    err = [r for r in table if r["status"] == "error"]
    assert len(err) == 1 and "falhou" in err[0]["error"]
    assert (tmp_path / "runs" / err[0]["run_id"] / "erro.txt").exists()

    # Refazer só os erros acrescenta uma linha e não repete os concluídos.
    before = len(calls)
    counts = run_matrix(
        runs, lambda r, f: {"tokens": 1}, tmp_path, metric_fields=["tokens"], retry_errors=True
    )
    assert counts == {"skipped": 3, "ok": 1, "error": 0} and len(calls) == before
    with pytest.raises(ValueError, match="Cabeçalho"):
        run_matrix(runs, lambda r, f: {}, tmp_path, metric_fields=["outra"])


def test_unknown_metric_is_an_error_row(tmp_path):
    runs = plan_runs([{"id": "p"}], ["A"], [1], 1)
    run_matrix(runs, lambda r, f: {"nao_declarada": 1}, tmp_path, metric_fields=["tokens"])
    assert rows(tmp_path)[0]["status"] == "error"


def test_build_dossiers_is_resumable(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "build_dossiers", Path(project_root() / "scripts/build_dossiers.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reqs = tmp_path / "req.json"
    reqs.write_text(
        json.dumps(
            {"requests": [{"id": "x", "prompt": "Tema x"}, {"id": "y", "prompt": "Tema y"}]}
        ),
        "utf-8",
    )
    seen = []

    def fake_research(topic, **kwargs):
        seen.append(topic)
        return Dossier(topic=topic)

    out = tmp_path / "dossies"
    out.mkdir()
    Dossier(topic="pronto").save(out / "x.json")
    manifest = module.build(
        reqs,
        out,
        tmp_path / "uso",
        None,
        provider="wikipedia",
        fallback_wikipedia=False,
        research_fn=fake_research,
        progress=lambda m: None,
    )
    assert seen == ["Tema y"]
    assert Dossier.load(out / "x.json").topic == "pronto"
    assert manifest["y"]["facts"] == 0 and (out / "y.json").exists()
