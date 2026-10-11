import json
import time

from fastapi.testclient import TestClient

from slidedsl import generation_jobs
from slidedsl.pipeline import validate_source
from slidedsl.server import app


client = TestClient(app)


def test_model_listing_unavailable_and_generation_payload_validation(monkeypatch):
    from slidedsl.models.base import ModelError
    from slidedsl.models.ollama_model import OllamaTextModel

    def unavailable(*args, **kwargs):
        raise ModelError("Ollama indisponível")

    monkeypatch.setattr(OllamaTextModel, "_request", unavailable)
    assert client.get("/api/models").json()["available"] is False
    assert client.post("/api/generations", json={"model": "x", "prompt": "  "}).status_code == 422
    assert (
        client.post("/api/generations", json={"model": "x", "prompt": "Crie 20 slides"}).status_code
        == 422
    )
    assert (
        client.post(
            "/api/generations", json={"model": "x", "prompt": "Um slide", "strategy": "Z"}
        ).status_code
        == 422
    )
    assert client.get("/api/generations/not-a-job").status_code == 404
    assert client.get("/api/generations/" + "a" * 32).status_code == 404


def test_generation_job_persists_progress_and_loads_original_ir(monkeypatch, tmp_path, root):
    from slidedsl.models.ollama_model import OllamaTextModel

    source = (root / "examples/minimo.sld").read_text(encoding="utf-8")
    monkeypatch.setattr(generation_jobs, "project_root", lambda: tmp_path)
    monkeypatch.setattr(OllamaTextModel, "available", lambda self: (True, "Somente teste"))

    def generate(model, strategy, prompt, out, **options):
        out.mkdir()
        (out / "presentation.sld").write_text(source, encoding="utf-8")
        options["event_callback"]({"stage": "repair", "round": 1, "paths": ["slides.0.title"]})
        return {
            "status": "EXECUTADO",
            "is_mock": True,
            "compile_success": False,
            "valid": True,
            "diagnostics": [],
            "corrections": 1,
            "requirements": {"numerator": 5, "denominator": 5, "all_met": True},
        }

    monkeypatch.setattr(generation_jobs, "generate_strategy", generate)
    response = client.post("/api/generations", json={"model": "test", "prompt": "Um slide"})
    assert response.status_code == 202
    id = response.json()["id"]
    for _ in range(100):
        job = client.get("/api/generations/" + id).json()
        if job["state"] in {"completed", "failed"}:
            break
        time.sleep(0.01)
    assert job["state"] == "completed"
    assert job["events"][0]["paths"] == ["slides.0.title"]
    assert job["result"]["source"] == source
    assert job["result"]["ir"] == validate_source(source).ir.model_dump()
    saved = json.loads(
        (tmp_path / "outputs/generation_jobs" / id / "job.json").read_text(encoding="utf-8")
    )
    assert saved["state"] == "completed" and saved["result"]["report"]["is_mock"]


def test_job_failure_is_reported_without_loading_a_manual_deck(monkeypatch, tmp_path):
    from slidedsl.models.ollama_model import OllamaTextModel

    monkeypatch.setattr(generation_jobs, "project_root", lambda: tmp_path)
    monkeypatch.setattr(OllamaTextModel, "available", lambda self: (True, "Somente teste"))

    def broken(*args, **kwargs):
        raise ValueError("Falha controlada")

    monkeypatch.setattr(generation_jobs, "generate_strategy", broken)
    response = client.post("/api/generations", json={"model": "test", "prompt": "Um slide"})
    id = response.json()["id"]
    for _ in range(100):
        job = client.get("/api/generations/" + id).json()
        if job["state"] == "failed":
            break
        time.sleep(0.01)
    assert job["result"] is None and "Falha controlada" in job["error"]
