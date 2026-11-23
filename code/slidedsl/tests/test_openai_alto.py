"""Integração paga testada offline: HTTP simulado, compilador/PPTX reais."""

from copy import deepcopy
import json
import ssl
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from slidedsl.alto_generation import create_presentation, slide_schema
from slidedsl.local_settings import load_local_settings
from slidedsl.model_usage import RecordedModel, pricing_for
from slidedsl.models.base import GenerationLimitError, ModelError, generate_text
from slidedsl.models.openai_model import OpenAITextModel, strict_schema
from slidedsl.research import Dossier
from slidedsl.server import app


def answer(content, *, finish="stop", refusal=None, usage=True):
    data = {
        "model": "fixture-model",
        "choices": [
            {
                "message": {"content": content, "refusal": refusal},
                "finish_reason": finish,
            }
        ],
    }
    if usage:
        data["usage"] = {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "prompt_tokens_details": {"cached_tokens": 40},
            "completion_tokens_details": {"reasoning_tokens": 5},
        }
    return httpx.Response(200, json=data)


def tariff(monkeypatch):
    monkeypatch.setenv(
        "SLIDEDSL_OPENAI_PRICING",
        json.dumps(
            {
                "fixture-model": {
                    "input": 2,
                    "cached_input": 0.5,
                    "output": 8,
                    "date": "2026-11-01",
                },
            }
        ),
    )


def test_schema_is_strict_recursive_and_does_not_mutate_domain():
    original = slide_schema("conclusao", [])
    before = deepcopy(original)
    schema = strict_schema(original)
    assert original == before
    assert schema["additionalProperties"] is False
    item = schema["properties"]["itens"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"])
    assert "maxLength" not in schema["properties"]["titulo"]
    assert schema["properties"]["fontes"]["items"] == {"type": "string"}


def test_openai_sends_strict_schema_and_counts_failed_paid_response(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret")
    tariff(monkeypatch)
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return answer('{"value":"ok"}')
        return answer(None, refusal="fixture refusal")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = RecordedModel(OpenAITextModel("fixture-model", client=client), tmp_path)
        schema = {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        }
        assert json.loads(generate_text(model, "s", "u", response_schema=schema)) == {"value": "ok"}
        with pytest.raises(ModelError, match="recusou"):
            generate_text(model, "s", "u", response_schema=schema)
    assert requests[0]["response_format"]["json_schema"]["strict"] is True
    summary = json.loads((tmp_path / "uso.json").read_text("utf-8"))
    assert summary["calls"] == 2 and summary["failed_calls"] == 1
    assert summary["known_input_tokens"] == 200 and summary["known_output_tokens"] == 40
    # Cache faz parte da entrada; reasoning já faz parte da saída.
    assert summary["cost_usd"] == pytest.approx(2 * (60 * 2 + 40 * 0.5 + 20 * 8) / 1_000_000)
    assert "fixture-secret" not in (tmp_path / "uso_chamadas.jsonl").read_text("utf-8")
    assert "fixture refusal" not in (tmp_path / "uso_chamadas.jsonl").read_text("utf-8")


def test_transport_failure_does_not_reuse_previous_usage_and_limit_prevents_post(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    tariff(monkeypatch)
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 2:
            raise httpx.ReadTimeout("fixture", request=request)
        return answer("ok")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = RecordedModel(
            OpenAITextModel("fixture-model", client=client), tmp_path, max_calls=2
        )
        assert model.generate("s", "u") == "ok"
        with pytest.raises(ModelError):
            model.generate("s", "u")
        with pytest.raises(GenerationLimitError):
            model.generate("s", "u")
    assert len(attempts) == 2
    assert model.records[1]["input_tokens"] is None
    assert model.summary()["unknown_usage_calls"] == 1
    assert model.summary()["cost_usd"] is None
    assert model.summary()["known_cost_usd"] > 0


@pytest.mark.parametrize(
    "finish,content", [("length", "{}"), ("content_filter", None), ("stop", "bad JSON")]
)
def test_interrupted_or_invalid_response_keeps_usage(monkeypatch, tmp_path, finish, content):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: answer(content, finish=finish))
    ) as client:
        model = RecordedModel(OpenAITextModel("fixture-model", client=client), tmp_path)
        with pytest.raises(ModelError):
            generate_text(model, "s", "u", response_schema={"type": "object"})
    assert model.summary()["known_usage_calls"] == 1
    assert model.summary()["failed_calls"] == 1


def test_unsupported_schema_is_not_silently_removed_or_typeerror_retried():
    class NoSchema:
        def generate(self, system, user, *, temperature=0, seed=None):
            pytest.fail("Não deveria iniciar inferência sem o schema solicitado")

    with pytest.raises(ModelError, match="response_schema"):
        generate_text(NoSchema(), "s", "u", response_schema={"type": "object"})

    class Broken:
        calls = 0

        def generate(self, system, user, **kwargs):
            self.calls += 1
            raise TypeError("erro dentro do adaptador")

    broken = Broken()
    with pytest.raises(TypeError):
        generate_text(broken, "s", "u", response_schema={"type": "object"})
    assert broken.calls == 1


def test_default_client_verifies_tls_with_system_trust_store(monkeypatch):
    # Raízes de antivírus/proxy (ex.: Kaspersky) ficam no repositório do sistema, não no certifi.
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    seen = {}

    class FakeClient:
        def __init__(self, **kwargs):
            seen.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, method, url, **kwargs):
            return httpx.Response(200, json={"id": "m"}, request=httpx.Request(method, url))

    monkeypatch.setattr("slidedsl.models.openai_model.httpx.Client", FakeClient)
    assert OpenAITextModel("m").available()[0]
    assert isinstance(seen["verify"], ssl.SSLContext)
    assert seen["verify"].verify_mode == ssl.CERT_REQUIRED


def test_usage_before_research_failure_is_preserved(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")

    def research(topic, *, model, **kwargs):
        generate_text(model, "s", "u", context={"stage": "research_plan"})
        raise ValueError("fixture research failure")

    monkeypatch.setattr("slidedsl.research.research", research)
    with httpx.Client(transport=httpx.MockTransport(lambda r: answer("ok"))) as client:
        with pytest.raises(ValueError, match="research failure"):
            create_presentation("x", tmp_path, OpenAITextModel("fixture-model", client=client))
    report = json.loads((tmp_path / "relatorio.json").read_text("utf-8"))
    assert report["calls"] == 1 and not report["valid"]
    assert report["usage"]["known_usage_calls"] == 1
    assert (
        json.loads((tmp_path / "uso_chamadas.jsonl").read_text("utf-8"))["stage"] == "research_plan"
    )


def test_local_settings_never_override_environment_or_evaluate_text(monkeypatch, tmp_path):
    local = tmp_path / ".env"
    local.write_text(
        "OPENAI_API_KEY=local-fixture\nSLIDEDSL_OPENAI_MODEL='fixture-model'\nHOME=bad\n", "utf-8"
    )
    monkeypatch.setenv("OPENAI_API_KEY", "environment-fixture")
    monkeypatch.setenv("SLIDEDSL_OPENAI_MODEL", "placeholder")
    monkeypatch.delenv("SLIDEDSL_OPENAI_MODEL", raising=False)
    load_local_settings(local)
    import os

    assert os.environ["OPENAI_API_KEY"] == "environment-fixture"
    assert os.environ["SLIDEDSL_OPENAI_MODEL"] == "fixture-model"
    assert os.environ.get("HOME") != "bad"


def test_missing_key_and_limits_are_rejected_before_queueing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)
    payload = {"pedido": "Deck de teste", "model": "fixture-model", "provider": "openai"}
    assert client.get("/api/providers").json()["openai"]["configured"] is False
    assert client.post("/api/criar", json=payload).status_code == 422
    monkeypatch.setenv("OPENAI_API_KEY", "credential-for-test")
    assert client.post("/api/criar", json={**payload, "max_calls": 0}).status_code == 422
    assert client.post("/api/criar", json={**payload, "max_output_tokens": 9000}).status_code == 422
    assert "credential-for-test" not in client.get("/api/providers").text


def fixture_handler(request):
    if request.method == "GET":
        return httpx.Response(200, json={"id": "fixture-model"})
    data = json.loads(request.content)
    schema = data["response_format"]["json_schema"]["schema"]
    assert schema["additionalProperties"] is False
    if "slides" in schema["properties"]:
        content = {
            "titulo": "Projetos pequenos precisam de foco",
            "slides": [
                {
                    "tipo": kind,
                    "mensagem": "Projetos pequenos precisam de foco",
                    "objetivo": "Explicar escolhas de escopo",
                }
                for kind in ("capa", "topicos", "conclusao")
            ],
        }
    else:
        content = {
            "titulo": "Projetos pequenos precisam de foco",
            "notas": "Explique as condições.",
        }
        if "subtitulo" in schema["properties"]:
            content.update(
                subtitulo="Comece pelo problema e delimite o resultado esperado.", autor=""
            )
        else:
            content.update(
                fontes=[],
                itens=[
                    {
                        "rotulo": "Definir escopo",
                        "detalhe": "A equipe reduz retrabalho quando define o resultado antes de começar.",
                    },
                    {
                        "rotulo": "Revisar entregas",
                        "detalhe": "A equipe verifica cada entrega e corrige problemas antes de seguir.",
                    },
                ],
            )
            # O cenário feliz não repete os mesmos itens no fechamento.
            if "(tipo conclusao)" in data["messages"][1]["content"]:
                content["itens"] = [
                    {"rotulo": "Documentar decisões",
                     "detalhe": "Registre as escolhas para orientar quem entrar depois no projeto."},
                    {"rotulo": "Planejar a continuidade",
                     "detalhe": "Escolha a próxima atividade com base no resultado da entrega atual."},
                ]
    return answer(json.dumps(content, ensure_ascii=False))


def test_openai_web_flow_uses_real_adapter_and_exports_editable_pptx(monkeypatch, tmp_path):
    from slidedsl import alto_jobs

    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    tariff(monkeypatch)
    monkeypatch.setattr(alto_jobs, "project_root", lambda: tmp_path)
    with httpx.Client(transport=httpx.MockTransport(fixture_handler)) as transport:
        monkeypatch.setattr(
            alto_jobs, "_model", lambda p: OpenAITextModel("fixture-model", client=transport)
        )
        client = TestClient(app)
        job = client.post(
            "/api/criar",
            json={
                "pedido": "Apresente boas práticas para projetos pequenos",
                "provider": "openai",
                "model": "fixture-model",
                "slides": 3,
                "buscador": "nenhum",
                "max_calls": 8,
            },
        ).json()
        for _ in range(200):
            job = client.get("/api/criar/" + job["id"]).json()
            if job["state"] in {"completed", "failed"}:
                break
            time.sleep(0.05)
    assert job["state"] == "completed", job
    assert job["result"]["report"]["valid"], job["result"]["report"]
    assert job["usage"]["calls"] == 4
    assert job["usage"]["known_usage_calls"] == 4
    assert job["usage"]["cost_usd"] is not None
    ir = job["result"]["ir"]
    assert len(ir["slides"]) == 3
    pptx = client.post("/api/compile", json={"ir": ir})
    assert pptx.status_code == 200 and pptx.content.startswith(b"PK")
    import zipfile
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(pptx.content)) as archive:
        xml = archive.read("ppt/slides/slide2.xml").decode()
        assert "Definir escopo" in xml and "<p:sp>" in xml


def test_research_calls_are_added_to_report_total(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")

    def research(topic, *, model, **kwargs):
        generate_text(model, "s", "u", context={"stage": "research_extract"})
        return Dossier(topic=topic)

    monkeypatch.setattr("slidedsl.research.research", research)

    def handler(request):
        if json.loads(request.content).get("response_format") is None:
            return answer("ok")
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
    assert report["calls"] == report["content_calls"] + 1 == 5
    assert report["usage"]["known_usage_calls"] == 5


def test_invalid_or_missing_tariff_is_unknown(monkeypatch):
    monkeypatch.delenv("SLIDEDSL_OPENAI_PRICING", raising=False)
    assert pricing_for("fixture-model") is None
    monkeypatch.setenv("SLIDEDSL_OPENAI_PRICING", '{"fixture-model":{"input":-1}}')
    assert pricing_for("fixture-model") is None


def test_pending_call_is_persisted_before_http_request(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-secret")

    def handler(request):
        summary = json.loads((tmp_path / "uso.json").read_text("utf-8"))
        assert summary["calls"] == 1 and summary["unknown_usage_calls"] == 1
        pending = (tmp_path / "uso_em_andamento.json").read_text("utf-8")
        assert json.loads(pending)["status"] == "running"
        assert "fixture-secret" not in pending
        return answer("ok")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = RecordedModel(OpenAITextModel("fixture-model", client=client), tmp_path)
        assert model.generate("s", "u") == "ok"
    assert not (tmp_path / "uso_em_andamento.json").exists()
    assert model.summary()["calls"] == 1
