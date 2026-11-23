"""Controles financeiros do lote real testados sem rede/credenciais reais."""

import json
from pathlib import Path
import runpy

import httpx
import pytest

from slidedsl.model_usage import RecordedModel
from slidedsl.models.base import GenerationLimitError

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def harness(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return runpy.run_path(str(SCRIPTS / "testes_reais_r6.py"))


def test_requested_model_and_only_configured_fallback(harness, monkeypatch):
    price = dict(input=.75, cached_input=.075, output=4.5, date="2026-11-11")
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", json.dumps({"gpt-5.4-mini": price}))
    assert harness["select_model"]() == ("gpt-5.4-mini", None)
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", json.dumps({"gpt-4.1-mini": price}))
    monkeypatch.delenv("SLIDEDSL_OPENAI_MODEL", raising=False)
    assert harness["select_model"]()[0] == "gpt-4.1-mini"
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", "{}")
    with pytest.raises(ValueError, match="nenhuma chamada"):
        harness["select_model"]()


def test_unknown_calls_survive_resume_and_stop_http_at_global_cap(harness, monkeypatch, tmp_path):
    price = dict(input=.75, cached_input=.075, output=4.5, date="2026-11-11")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-fixture")
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", json.dumps({"gpt-5.4-mini": price}))
    previous = tmp_path / "previous"
    budget = harness["Budget"](price, limit=.5)
    budget.ledger_path = tmp_path / "ledger.json"
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(401))) as client:
        model = harness["PaidModel"]("gpt-5.4-mini", budget, previous, client=client, output_tokens=2200)
        tracked = RecordedModel(model, previous, on_usage=lambda usage: budget.note(previous, usage))
        with pytest.raises(Exception, match="HTTP 401"):
            tracked.generate("system", "request", seed=42)
    assert tracked.summary()["unknown_usage_calls"] == 1
    assert budget.spent == 0 and budget.upper_bound > 0
    resumed = harness["Budget"](price, limit=.5)
    harness["carry_budget"](resumed, budget.ledger_path)
    assert resumed.upper_bound == budget.upper_bound
    resumed.note(tmp_path / "known", dict(known_cost_usd=.48, unknown_usage_calls=0))
    with httpx.Client(transport=httpx.MockTransport(lambda r: pytest.fail("HTTP fora do teto"))) as client:
        model = harness["PaidModel"]("gpt-5.4-mini", resumed, tmp_path / "new",
                                     client=client, output_tokens=2200)
        with pytest.raises(GenerationLimitError, match="reservar"):
            model.generate("system", "request")
