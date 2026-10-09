from fastapi.testclient import TestClient
import hashlib
import json

from slidedsl.ir import Presentation, semantic_snapshot
from slidedsl.pipeline import validate_source
from slidedsl.server import app

client = TestClient(app)


def test_import_edit_validate_export_and_compile(root, tmp_path):
    source = (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")
    response = client.post("/api/parse", json={"source": source})
    assert response.status_code == 200
    d = response.json()["ir"]
    d["slides"][0]["elements"][1]["text"] = "Título editado"
    d["slides"][0]["elements"][1]["x"] = 1300
    r = client.post("/api/validate", json={"ir": d}).json()
    assert not r["valid"] and any(x["code"] == "D001" for x in r["diagnostics"])
    assert client.post("/api/compile", json={"ir": d}).status_code == 422
    d["slides"][0]["elements"][1]["x"] = 170
    assert client.post("/api/validate", json={"ir": d}).json()["valid"]
    text = client.post("/api/export", json={"ir": d}).json()["source"]
    back = validate_source(text)
    assert semantic_snapshot(back.ir) == semantic_snapshot(Presentation.model_validate(d))
    pptx = client.post("/api/compile", json={"ir": d})
    assert pptx.status_code == 200 and pptx.content[:2] == b"PK"


def test_api_rejects_invalid_asset(root):
    d = validate_source(
        (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")
    ).ir.model_dump()
    d["slides"][3]["elements"][2]["file"] = "../escape.png"
    assert client.post("/api/compile", json={"ir": d}).status_code == 422


def test_dimension_zero_and_relation(root):
    source = 'apresentacao "A" { tema claro slide 1 { adicionar retangulo id a em (80,80) tamanho (100,100) cor primaria adicionar retangulo id b em (400,400) tamanho (100,100) cor primaria } }'
    d = client.post("/api/parse", json={"source": source}).json()["ir"]
    r = client.post(
        "/api/relation",
        json={
            "ir": d,
            "slide": 1,
            "relation": {"kind": "below", "target": "b", "reference": "a", "margin": 24},
        },
    )
    assert r.status_code == 200
    b = r.json()["ir"]["slides"][0]["elements"][1]
    assert (b["x"], b["y"]) == (80, 204)
    d["slides"][0]["elements"][0]["height"] = 0
    assert any(
        x["code"] == "D009"
        for x in client.post("/api/validate", json={"ir": d}).json()["diagnostics"]
    )


def test_api_parse_negative_and_schema_validation():
    assert client.post("/api/parse", json={"source": "não é DSL"}).status_code == 422
    assert client.post("/api/validate", json={"ir": {"schema_version": "9"}}).status_code == 422
    assert client.get("/api/examples/../../segredo").status_code == 404


def test_demo_loader_verifies_path_and_actual_file_bytes(monkeypatch, tmp_path):
    from slidedsl import server

    monkeypatch.setattr(server, "project_root", lambda: tmp_path)
    folder = tmp_path / "outputs/demo_local"
    folder.mkdir(parents=True)
    assert client.get("/api/local-demo").status_code == 404
    source = b"programa com CRLF\r\n"
    (folder / "presentation.sld").write_bytes(source)
    manifest = {
        "source": "outputs/demo_local/presentation.sld",
        "sha256": hashlib.sha256(source).hexdigest(),
    }
    (folder / "latest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert client.get("/api/local-demo").json()["source"] == source.decode()
    (folder / "presentation.sld").write_bytes(b"modified")
    assert client.get("/api/local-demo").status_code == 409
    manifest["source"] = "../escape.sld"
    (folder / "latest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert client.get("/api/local-demo").status_code == 409
