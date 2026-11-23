"""Guarda financeira e contabilização do harness sem efetuar chamadas pagas."""

import json
from pathlib import Path
import runpy

import httpx
import pytest

from slidedsl.model_usage import RecordedModel
from slidedsl.models.base import GenerationLimitError

HARNESS = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/comparar_alto_vs_sld.py"))
PRICE = {"input": 0.4, "cached_input": 0.1, "output": 1.6, "date": "2026-11-01"}


def setup_price(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-only")
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", json.dumps({"gpt-4.1-mini": PRICE}))


@pytest.mark.parametrize('seed', [42, 43, 44])
def test_budget_counts_all_rounds_cache_and_pins_parameters(monkeypatch, tmp_path, seed):
    setup_price(monkeypatch)
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "model": "gpt-4.1-mini", "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20,
                      "prompt_tokens_details": {"cached_tokens": 40}},
        })

    budget = HARNESS["Budget"](PRICE)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = HARNESS["ExperimentModel"](budget, client=client, experiment_seed=seed)
        tracked = RecordedModel(model, tmp_path, on_usage=lambda summary: budget.note(tmp_path, summary))
        for _ in range(3):
            tracked.generate("system", "brief", temperature=0.9, seed=999)
    assert tracked.summary()["calls"] == 3
    assert tracked.summary()["known_input_tokens"] == 300
    assert budget.spent == pytest.approx(3 * (60 * .4 + 40 * .1 + 20 * 1.6) / 1e6)
    assert all(r["temperature"] == .2 and r["seed"] == seed for r in requests)


def test_unknown_usage_without_reservation_aborts_before_second_http(monkeypatch, tmp_path):
    setup_price(monkeypatch)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={
            "model": "gpt-4.1-mini", "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
        })

    budget = HARNESS["Budget"](PRICE)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        tracked = RecordedModel(HARNESS["ExperimentModel"](budget, client=client), tmp_path,
                                on_usage=lambda s: budget.note(tmp_path, s))
        with pytest.raises(GenerationLimitError, match="desconhecido"):
            tracked.generate("system", "brief")
        with pytest.raises(GenerationLimitError):
            tracked.generate("system", "brief")
    assert len(requests) == 1
    assert tracked.summary()["cost_usd"] is None


def test_reserved_unknown_cost_is_bounded_never_zero(monkeypatch, tmp_path):
    setup_price(monkeypatch)
    budget = HARNESS["Budget"](PRICE)
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={
        "model": "gpt-4.1-mini", "choices": [{"finish_reason": "stop", "message": {"content": "ok"}}],
    }))) as client:
        tracked = RecordedModel(
            HARNESS["ExperimentModel"](budget, client=client, audit_folder=tmp_path), tmp_path,
            on_usage=lambda s: budget.note(tmp_path, s),
        )
        tracked.generate("system", "brief")
    assert tracked.summary()["cost_usd"] is None
    assert budget.unpriced_calls[tmp_path] == 1
    assert budget.upper_bound > budget.spent
    with pytest.raises(GenerationLimitError):
        budget.before("system", "brief" * 1000000, 7000, None, folder=tmp_path)


def test_budget_reserves_before_http_and_uses_all_run_totals(monkeypatch, tmp_path):
    setup_price(monkeypatch)
    budget = HARNESS["Budget"](PRICE, limit=.001)
    budget.note(tmp_path / "previous", {"known_cost_usd": .0009, "unknown_usage_calls": 0,
                                      "calls": 1, "cost_usd": .0009})
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail("HTTP proibido"))) as client:
        model = HARNESS["ExperimentModel"](budget, client=client)
        with pytest.raises(GenerationLimitError, match="reservar"):
            model.generate("system", "brief")


def test_budget_requires_pricing_and_stops_at_limit(tmp_path):
    with pytest.raises(ValueError, match="Tarifa"):
        HARNESS["Budget"](None)
    budget = HARNESS["Budget"](PRICE)
    with pytest.raises(GenerationLimitError, match="atingido"):
        budget.note(tmp_path, {"known_cost_usd": 1, "unknown_usage_calls": 0,
                              "calls": 1, "cost_usd": 1})


def test_diagnostic_categories_follow_project_rules():
    _, types = HARNESS["diagnostic_counts"]([
        {"code": "D001", "severity": "ERRO"}, {"code": "D008", "severity": "AVISO"},
        {"code": "D010", "severity": "AVISO"}, {"code": "D002", "severity": "INFORMAÇÃO"},
    ])
    assert types == {"fora_da_area": {"ERRO": 1, "AVISO": 0},
                     "sobreposicao_oclusao": {"ERRO": 0, "AVISO": 1},
                     "overflow": {"ERRO": 0, "AVISO": 1}}


def test_cost_per_valid_slide_includes_failed_runs_and_savings_use_total_cost():
    def row(condition, cost, valid):
        return dict(condition=condition, cost_usd=cost, valid=valid, pptx_generated=valid,
                    pptx_slides=5 if valid else 0, images=0, calls=1, input_tokens=100,
                    output_tokens=10, cached_input_tokens=0, errors=0 if valid else 1,
                    warnings=0, repair_rounds=0, generation_seconds=1)

    summary = HARNESS["aggregate"]([
        row("A", .01, True), row("A", .01, False), row("A", .01, False),
        row("B", .006, True), row("B", .006, True), row("B", .006, True),
    ])
    assert summary["A"]["cost_per_valid_slide"] == pytest.approx(.03 / 5)
    assert summary["B"]["cost_per_valid_slide"] == pytest.approx(.018 / 15)
    assert summary["B"]["saving_vs_A"] == pytest.approx(.4)
