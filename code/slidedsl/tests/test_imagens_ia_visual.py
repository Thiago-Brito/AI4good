"""Imagens por IA, contabilização e identidade visual de abertura/fechamento (offline)."""

import base64
from io import BytesIO
import json

import httpx
from PIL import Image
import pytest

from slidedsl import media
from slidedsl.ai_images import generate_image
from slidedsl.alto import AltoDeck, AltoSlide, Item
from slidedsl.alto_compile import build_alto
from slidedsl.alto_generation import fallback_queries, resolve_images
from slidedsl.editorial import capitalize_visible
from slidedsl.model_usage import RecordedModel


def jpeg():
    buffer = BytesIO()
    Image.new("RGB", (96, 64), (40, 120, 200)).save(buffer, "JPEG")
    return buffer.getvalue()


def client(usage=True, status=200):
    def handler(request):
        body = json.loads(request.content)
        assert body["size"] == "1536x1024" and body["output_format"] == "jpeg"
        assert "No text" in body["prompt"]
        data = {"data": [{"b64_json": base64.b64encode(jpeg()).decode()}]}
        if usage:
            data["usage"] = {"input_tokens": 100, "output_tokens": 400}
        return httpx.Response(status, json=data if status == 200 else {"error": {}})
    return httpx.Client(transport=httpx.MockTransport(handler))


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture")
    monkeypatch.setattr(media, "project_root", lambda: tmp_path)
    return tmp_path


def test_ai_image_is_stored_with_ai_credit_and_cost_from_usage(isolated):
    records = []
    asset, record = generate_image("Redes ligam computadores", "network cables",
                                   client=client(), on_record=records.append)
    assert asset["author"] == "Imagem gerada por IA" and asset["license"] == "gpt-image-2"
    assert (isolated / asset["asset"]).exists()
    # 400 tokens de imagem × US$ 30/M + 100 de texto × US$ 5/M
    assert record["cost_usd"] == pytest.approx(0.0125)
    assert records == [record] and record["status"] == "completed"


def test_ai_image_without_usage_uses_dated_table_and_http_error_costs_nothing(isolated):
    _, record = generate_image("T", "q", profile="media", client=client(usage=False))
    assert record["cost_usd"] == 0.015 and "tabela" in record["cost_basis"]
    records = []
    with pytest.raises(ValueError):
        generate_image("T", "q", client=client(status=400), on_record=records.append)
    assert records[0]["status"] == "failed" and records[0]["cost_usd"] == 0.0


def test_recorded_model_adds_image_cost_to_total(tmp_path):
    class Model:
        metadata = {"provider": "openai", "model_requested": "sem-tarifa"}
    tracked = RecordedModel(Model(), tmp_path)
    tracked.record_image({"stage": "imagem_ia", "cost_usd": 0.005, "status": "completed"})
    summary = tracked.summary()
    assert summary["image_calls"] == 1 and summary["image_cost_usd"] == 0.005
    assert summary["known_cost_usd"] == 0.005
    assert (tmp_path / "uso_imagens.jsonl").exists()


def deck_with_image_slides(n):
    return AltoDeck(title="Redes", slides=[
        AltoSlide(kind="capa", title="Redes", image_query="network cables"),
        *[AltoSlide(kind="imagem", title=f"Rede {k}", image_query="server rack",
                    items=[Item(label="Cabo", detail="Liga máquinas próximas."),
                           Item(label="Sinal", detail="Viaja sem fio.")]) for k in range(n)]])


@pytest.mark.parametrize("source,searched,generated", [
    ("livres", True, 0), ("livres_ia", True, 3), ("ia", False, 3)])
def test_image_sources_and_ai_limit(monkeypatch, source, searched, generated):
    queries, made = [], []
    monkeypatch.setattr(media, "automatic_search", lambda q, **kw: queries.append(q) or {"results": []})

    def fake(title, query, **kw):
        made.append(title)
        return {"asset": "assets/imagem_demo.png"}, {}
    monkeypatch.setattr("slidedsl.ai_images.generate_image", fake)
    deck = deck_with_image_slides(3)
    resolve_images(deck, source=source)
    assert bool(queries) is searched and len(made) == generated
    # R7: fourth image keeps its kind for the compiler's cards fallback.
    if generated:
        assert deck.slides[-1].kind == "imagem" and not deck.slides[-1].image_file


def test_fallback_queries_simplify_abstract_search():
    assert fallback_queries("microservices architecture diagram")[:3] == [
        "microservices architecture diagram", "microservices architecture", "microservices"]


def test_visible_text_starts_with_capital():
    slide = capitalize_visible(AltoSlide(kind="conclusao", title="decisão depende do estágio",
                                         items=[Item(label="avaliar fase atual", detail="escolha monolito.")]))
    assert slide.title.startswith("Decisão") and slide.items[0].label == "Avaliar fase atual"
    assert slide.items[0].detail == "Escolha monolito."


def test_cover_and_conclusion_use_inverted_palette_without_design_errors():
    deck = AltoDeck(title="Git", slides=[
        AltoSlide(kind="capa", title="Comece a usar Git hoje", subtitle="Controle de versões"),
        AltoSlide(kind="topicos", title="Commits registram versões", items=[
            Item(label="Histórico", detail="Cada commit guarda uma versão escolhida."),
            Item(label="Equipe", detail="Uma branch permite testar sem afetar a principal.")]),
        AltoSlide(kind="conclusao", title="Pratique em um projeto pequeno", items=[
            Item(label="Crie um repositório", detail="Comece com um trabalho da disciplina."),
            Item(label="Faça commits curtos", detail="Registre cada mudança com uma mensagem clara.")])])
    result = build_alto(deck)
    assert result.success(), result.report()
    ir = result.validation.ir
    backgrounds = [any("_fundo_" in e.id for e in s.elements) for s in ir.slides]
    assert backgrounds == [True, False, True]
    assert not [d for d in result.all_diagnostics if d.code in {"D001", "D003"}]


@pytest.mark.parametrize("style", ["claro", "escuro", "editorial", "vibrante", "natural", "noturno"])
def test_every_style_compiles_without_design_warnings_and_roundtrips(style):
    from slidedsl.alto import parse_alto, print_alto
    deck = AltoDeck(title="Git", theme=style, slides=[
        AltoSlide(kind="capa", title="Comece a usar Git hoje", subtitle="Controle de versões"),
        AltoSlide(kind="topicos", title="Commits registram versões", items=[
            Item(label="Histórico", detail="Cada commit guarda uma versão escolhida."),
            Item(label="Equipe", detail="Uma branch permite testar sem afetar a principal."),
            Item(label="Revisão", detail="O histórico mostra quem mudou cada arquivo.")]),
        AltoSlide(kind="conclusao", title="Pratique em um projeto pequeno", items=[
            Item(label="Crie um repositório", detail="Comece com um trabalho da disciplina."),
            Item(label="Faça commits curtos", detail="Registre cada mudança com uma mensagem clara.")])])
    assert parse_alto(print_alto(deck)).theme == style
    result = build_alto(deck)
    assert result.success(), result.report()
    # Fio não tem fundo: a união de caixas pode ser <30% sem overflow.
    assert not [d for d in result.all_diagnostics
                if d.severity in ("ERRO", "AVISO") and d.code != "A021"]
    assert result.validation.ir.theme in ("claro", "escuro")
