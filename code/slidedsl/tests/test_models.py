import json

import httpx
import pytest

from slidedsl.generation import generate_file
from slidedsl.models.mock_model import MockTextModel
from slidedsl.models.ollama_model import OllamaTextModel
from slidedsl.models.openai_model import OpenAITextModel


def test_ollama_adapter_contract_and_probe():
    requests = []

    def handler(request):
        requests.append(request)
        if request.method == "GET":
            return httpx.Response(
                200, json={"models": [{"name": "qwen3:0.6b", "digest": "test-digest"}]}
            )
        if request.url.path == "/api/show":
            return httpx.Response(
                200, json={"thinking": {"values": [False, True], "default": True}}
            )
        return httpx.Response(
            200, json={"model": "qwen3:0.6b", "message": {"content": "programa"}, "eval_count": 10}
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        m = OllamaTextModel("qwen3:0.6b", client=c)
        assert m.available()[0]
        assert m.generate("s", "u", temperature=0, seed=42) == "programa"
        data = json.loads(requests[-1].content)
        assert data["think"] is False and data["stream"] is False and data["options"]["seed"] == 42
        assert data["options"]["num_ctx"] == 16384
        assert data["options"]["num_predict"] == 8192
        assert m.metadata["num_ctx"] == 16384 and m.metadata["num_predict"] == 8192
        assert m.metadata["model_digest"] == "test-digest"


def test_ollama_required_thinking_preserves_answer_and_prompts():
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"thinking": {"values": [True], "default": True}})
        return httpx.Response(
            200, json={"message": {"thinking": "raciocínio", "content": "programa intacto"}}
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = OllamaTextModel("qwen3:4b", client=client)
        assert model.generate("sistema original", "pedido original", seed=42) == "programa intacto"
        payload = json.loads(requests[-1].content)
        assert payload["think"] is True
        assert payload["messages"] == [
            {"role": "system", "content": "sistema original"},
            {"role": "user", "content": "pedido original"},
        ]
        assert model.metadata["thinking_requested"] is False and model.metadata["thinking"] is True
        assert model.metadata["thinking_output_chars"] == len("raciocínio")


def test_openai_request_and_secret_not_logged(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-secret-for-test")
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "model": "gpt-4.1-mini",
                "choices": [{"message": {"content": "programa"}, "finish_reason": "stop"}],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        m = OpenAITextModel("gpt-4.1-mini", client=c)
        assert m.generate("s", "u", temperature=0, seed=None) == "programa"
        assert "seed" not in json.loads(requests[0].content)
        assert "fake-secret-for-test" not in json.dumps(m.metadata)


def test_missing_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert OpenAITextModel("gpt-4.1").available()[0] is False


def test_generate_mock_saves_raw_and_refuses_overwrite(root, tmp_path):
    out = tmp_path / "mock.sld"
    result = generate_file(
        "mock", "fixture", root / "benchmark/prompts/tarefa_cinco_slides.txt", out
    )
    assert result["valid"] and result["is_mock"]
    assert out.read_bytes() == out.with_suffix(".raw.txt").read_bytes()
    with pytest.raises(FileExistsError):
        generate_file("mock", "fixture", root / "benchmark/prompts/tarefa_cinco_slides.txt", out)


def test_controlled_repair_keeps_first_failure(root, tmp_path):
    valid = (root / "examples/minimo.sld").read_text(encoding="utf-8")
    adapter = MockTextModel(["não é DSL", valid])
    out = tmp_path / "repair.sld"
    result = generate_file(
        "mock",
        "fixture",
        root / "benchmark/prompts/tarefa_cinco_slides.txt",
        out,
        repair_max=2,
        adapter=adapter,
    )
    assert not result["rounds"][0]["parse_success"] and result["rounds"][1]["parse_success"]
    assert (
        result["repair_rounds"] == 1
        and out.with_suffix(".raw.txt").read_text(encoding="utf-8") == "não é DSL"
    )
