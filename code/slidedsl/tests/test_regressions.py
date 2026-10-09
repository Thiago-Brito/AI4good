import re

from fastapi.testclient import TestClient

from slidedsl.benchmarking import evaluate
from slidedsl.pipeline import validate_source
from slidedsl.server import app


def test_benchmark_geometry_error_preserves_metrics(root, tmp_path):
    raw = (
        (root / "examples/cinco_slides.sld")
        .read_text(encoding="utf-8")
        .replace("em (170, 230)", "em (1300, 230)")
    )
    metrics = evaluate(raw, tmp_path, design=True, root=root)
    assert metrics["parse_success"] and metrics["semantic_success"]
    assert not metrics["compile_success"]
    assert metrics["design_errors"] >= 1
    assert (tmp_path / "raw.txt").is_file() and (tmp_path / "metrics.json").is_file()


def test_ir_rejects_properties_incompatible_with_type(root):
    deck = validate_source(
        (root / "examples/minimo.sld").read_text(encoding="utf-8")
    ).ir.model_dump()
    deck["slides"][0]["elements"][0]["file"] = "assets/imagem_demo.png"
    with TestClient(app) as client:
        report = client.post("/api/validate", json={"ir": deck}).json()
        assert not report["valid"] and any(d["code"] == "S006" for d in report["diagnostics"])
        assert client.post("/api/export", json={"ir": deck}).status_code == 422


def test_production_editor_serves_its_bundled_assets(root):
    if not (root / "editor/dist/index.html").exists():
        import pytest

        pytest.skip("Build do editor ainda não disponível; execute npm run build.")
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        urls = re.findall(r'(?:src|href)="([^"]+)"', response.text)
        assert len(urls) >= 2
        for url in urls:
            assert url.startswith("/editor-assets/")
            assert client.get(url).status_code == 200
        assert client.get("/assets/imagem_demo.png").status_code == 200
