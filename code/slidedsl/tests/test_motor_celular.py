"""Motor igual ao celular: lista de modelos, validação na API e conversão dos fatos do app para o dossiê."""

from fastapi.testclient import TestClient

from slidedsl import motor_celular
from slidedsl.server import app


def test_modelos_locais_marca_arquivos_existentes(tmp_path, monkeypatch):
    (tmp_path / "Qwen3-1.7B-Q4_K_M.gguf").write_bytes(b"x")
    monkeypatch.setenv("SLIDEDSL_GGUF_DIR", str(tmp_path))
    modelos = {m["id"]: m["disponivel"] for m in motor_celular.modelos_locais()}
    assert modelos["qwen3-1.7b"] is True and modelos["qwen3-0.6b-lora"] is False
    assert sum(m.get("padrao", False) for m in motor_celular.modelos_locais()) == 1


def test_api_valida_motor_celular(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_GGUF_DIR", str(tmp_path))
    client = TestClient(app)
    base = {"pedido": "Ciclo da água", "model": "x", "motor": "celular", "slides": 5}
    r = client.post("/api/criar", json=base | {"modelo_local": "qwen3-1.7b"})
    assert r.status_code == 422 and "não encontrado" in r.json()["detail"]
    (tmp_path / "Qwen3-1.7B-Q4_K_M.gguf").write_bytes(b"x")
    r = client.post("/api/criar", json=base | {"modelo_local": "qwen3-1.7b", "slides": 10})
    assert r.status_code == 422 and "4 a 8" in r.json()["detail"]
    assert client.get("/api/modelos-locais").json()["modelos"][0]["id"] == "qwen3-0.6b-lora"


def test_fatos_do_app_viram_dossie():
    facts = {"F1": {"claim": "A agricultura usa 70% da água doce.", "quote": "70% da água doce", "kind": "numero",
                    "value": "70%", "author": "", "relevance": "alta", "source_id": "S3", "source_title": "agua.txt",
                    "url": "documento:agua.txt#trecho-3", "extra": "ignorado"}}
    fact_map = motor_celular._dossie("água", facts).fact_map()
    assert fact_map["F1"]["value"] == "70%" and fact_map["F1"]["url"].endswith("trecho-3")
    assert "extra" not in fact_map["F1"]


def test_fotos_do_app_entram_no_catalogo_com_credito(tmp_path, monkeypatch):
    import io
    import json

    from PIL import Image

    from slidedsl.alto import AltoDeck

    monkeypatch.setenv("SLIDEDSL_ROOT", str(tmp_path))
    out = tmp_path / "saida"
    (out / "imagens").mkdir(parents=True)
    buf = io.BytesIO()
    Image.new("RGB", (1200, 800), (40, 90, 160)).save(buf, "JPEG")
    (out / "imagens" / "foto_2.jpg").write_bytes(buf.getvalue())
    (out / "imagens.json").write_text(json.dumps({"info": {"foto_2.jpg": {"width": 1200, "height": 800, "metadata": {
        "author": "Maria Silva", "license": "CC BY-SA", "license_url": "https://cc/by-sa", "page": "https://x/p",
        "attribution": "Solar panels — Maria Silva (openverse)"}}}, "log": []}), "utf-8")
    deck = AltoDeck.model_validate({"title": "Solar", "slides": [
        {"kind": "capa", "title": "Energia solar"},
        {"kind": "imagem", "title": "Painéis", "image_file": "foto_2.jpg", "image_query": "solar panels"}]})
    motor_celular._registrar_fotos(deck, out)
    asset = deck.slides[1].image_file
    assert asset.startswith("assets/media/") and (tmp_path / asset).is_file()
    catalog = json.loads(next((tmp_path / "outputs/media/assets").glob("*.json")).read_text("utf-8"))
    assert catalog["author"] == "Maria Silva" and catalog["license"] == "CC BY-SA" and catalog["provider"] == "openverse"
