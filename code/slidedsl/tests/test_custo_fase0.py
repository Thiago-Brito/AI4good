"""Fase 0 do plano do TCC: tokens e tempo por chamada, custo.json por deck.

Tudo offline: servidores Ollama/llama.cpp/OpenAI simulados com httpx.MockTransport.
"""

import json

import httpx

from slidedsl.alto_generation import GenerationResult, _call, create_presentation
from slidedsl.model_usage import RecordedModel, cost_breakdown, normalized_usage
from slidedsl.models.llamacpp_model import LlamaCppTextModel
from slidedsl.models.ollama_model import OllamaTextModel


def ollama_handler(request):
    if request.url.path == "/api/show":
        return httpx.Response(200, json={})
    return httpx.Response(
        200,
        json={
            "model": "qwen3:4b",
            "message": {"content": "ok"},
            "done_reason": "stop",
            "prompt_eval_count": 120,
            "eval_count": 30,
            "prompt_eval_duration": 250_000_000,  # ns -> 250 ms
            "eval_duration": 1_500_000_000,  # ns -> 1500 ms
            "load_duration": 10_000_000,
            "total_duration": 1_800_000_000,
        },
    )


def llamacpp_handler(request):
    return httpx.Response(
        200,
        json={
            "model": "qwen3-1.7b-q4",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 16},
            "timings": {
                "prompt_n": 80,
                "prompt_ms": 40.5,
                "predicted_n": 16,
                "predicted_ms": 320.0,
                "predicted_per_second": 50.0,
            },
        },
    )


def test_ollama_durations_become_ms():
    with httpx.Client(transport=httpx.MockTransport(ollama_handler)) as client:
        model = OllamaTextModel("qwen3:4b", client=client)
        model.generate("s", "u")
    usage = normalized_usage(model.metadata, "ollama")
    assert usage["input_tokens"] == 120 and usage["output_tokens"] == 30
    assert usage["prefill_ms"] == 250.0 and usage["decode_ms"] == 1500.0
    assert usage["load_ms"] == 10.0 and usage["server_total_ms"] == 1800.0
    assert model.metadata["finish_reason"] == "stop"


def test_llamacpp_timings_and_fallback_counts():
    with httpx.Client(transport=httpx.MockTransport(llamacpp_handler)) as client:
        model = LlamaCppTextModel(client=client)
        model.generate("s", "u", grammar='root ::= "ok"')
    usage = normalized_usage(model.metadata, "llamacpp")
    assert usage["input_tokens"] == 80 and usage["output_tokens"] == 16
    assert usage["prefill_ms"] == 40.5 and usage["decode_ms"] == 320.0
    assert usage["server_total_ms"] == 360.5
    # Sem `usage`, as contagens vêm de timings.
    old = {"timings": model.metadata["timings"]}
    assert normalized_usage(old, "llamacpp")["output_tokens"] == 16


def test_unknown_values_are_none_not_zero():
    usage = normalized_usage({}, "ollama")
    assert usage["prefill_ms"] is None and usage["input_tokens"] is None
    bad = normalized_usage({"eval_duration": -5, "prompt_eval_duration": True}, "ollama")
    assert bad["decode_ms"] is None and bad["prefill_ms"] is None


def test_call_copies_usage_and_custo_totals_match(tmp_path):
    with httpx.Client(transport=httpx.MockTransport(ollama_handler)) as client:
        tracked = RecordedModel(OllamaTextModel("qwen3:4b", client=client), tmp_path)
        result = GenerationResult(request="x")
        for stage, slide, attempt in (("topicos", None, 0), ("slide", 1, 0), ("slide", 1, 1)):
            _call(
                tracked,
                result,
                stage=stage,
                slide=slide,
                candidate=None,
                attempt=attempt,
                system="s",
                user="u",
            )
    assert all(c.usage["output_tokens"] == 30 for c in result.calls)
    assert result.calls[0].usage["wall_ms"] >= 0
    custo = json.loads((tmp_path / "custo.json").read_text("utf-8"))
    assert custo["total"]["calls"] == 3
    assert custo["total"]["input_tokens"] == 360 and custo["total"]["output_tokens"] == 90
    assert custo["total"]["decode_ms"] == 4500.0
    assert set(custo["by_stage"]) == {"topicos", "slide", "reparo"}
    assert custo["by_stage"]["reparo"]["calls"] == 1
    per_line = [json.loads(x) for x in (tmp_path / "uso_chamadas.jsonl").read_text().splitlines()]
    assert sum(r["output_tokens"] for r in per_line) == custo["total"]["output_tokens"]


def test_breakdown_reports_unknown_calls():
    rows = [
        {"stage": "slide", "attempt": 0, "status": "completed", "input_tokens": 10},
        {"stage": "slide", "attempt": 0, "status": "failed", "input_tokens": None},
    ]
    total = cost_breakdown(rows)["total"]
    assert total["input_tokens"] == 10 and total["input_tokens_unknown_calls"] == 1
    assert total["failed_calls"] == 1 and total["wall_ms"] is None


def test_create_presentation_writes_custo_and_usage_per_call(monkeypatch, tmp_path):
    from test_openai_alto import fixture_handler

    from slidedsl.models.base import generate_text
    from slidedsl.models.openai_model import OpenAITextModel
    from slidedsl.research import Dossier

    def research(topic, *, model, **kwargs):
        generate_text(model, "s", "u", context={"stage": "research_extract"})
        return Dossier(topic=topic)

    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    monkeypatch.setattr("slidedsl.research.research", research)

    def handler(request):
        if json.loads(request.content).get("response_format") is None:
            return httpx.Response(
                200,
                json={
                    "model": "fixture-model",
                    "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 2,
                        "completion_tokens_details": {"reasoning_tokens": 1},
                    },
                },
            )
        return fixture_handler(request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        report = create_presentation(
            "Boas práticas",
            tmp_path,
            OpenAITextModel("fixture-model", client=client),
            n_slides=3,
            allow_without_facts=True,
            preview=False,
        )
    custo = json.loads((tmp_path / "custo.json").read_text("utf-8"))
    assert custo["total"]["calls"] == report["calls"]
    assert custo["total"]["input_tokens"] == report["usage"]["known_input_tokens"]
    assert custo["total"]["output_tokens"] == report["usage"]["known_output_tokens"]
    assert custo["total"]["wall_ms_unknown_calls"] == 0
    # pesquisa informa 1; cada chamada de conteúdo da fixture informa 5
    assert custo["total"]["reasoning_tokens"] == 1 + 5 * (report["calls"] - 1)
    assert "research_extract" in custo["by_stage"] and "slide" in custo["by_stage"]
    content_calls = [
        json.loads(x) for x in (tmp_path / "chamadas.jsonl").read_text("utf-8").splitlines()
    ]
    assert content_calls and all(c["usage"]["provider"] == "openai" for c in content_calls)
    assert all(c["usage"]["wall_ms"] is not None for c in content_calls)
