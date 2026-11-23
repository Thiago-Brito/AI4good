"""Regras editoriais da rodada 2, sem inferência nem rede."""

import zipfile

import pytest

from slidedsl.alto import AltoDeck, AltoSlide, Item, Side
from slidedsl.alto_compile import build_alto
from slidedsl.alto_layout import alto_to_ast
from slidedsl.editorial import balanced_title, composition
from slidedsl.media import automatic_candidate, relevant_image


def items():
    return [Item(label="Luz disponível", detail="A folha recebe luz durante o dia."),
            Item(label="Troca gasosa", detail="A planta troca gases com o ambiente.")]


@pytest.mark.parametrize("title", ["Git", "Energia solar", "Fotossíntese", "Internet"])
def test_cover_has_no_decorative_data(title):
    ast, _, _ = alto_to_ast(AltoDeck(title=title, slides=[AltoSlide(kind="capa", title=title)]))
    assert not any("barra" in (c.id or "") or "base" in (c.id or "") for c in ast.slides[0].commands)
    assert not any((c.text or "").isdigit() for c in ast.slides[0].commands)


def test_composition_responds_to_density_and_avoids_neighbor_repeat():
    slides = [AltoSlide(kind="topicos", title="Luz alimenta a planta", items=items()) for _ in range(3)]
    deck = AltoDeck(title="Plantas", slides=slides)
    assert [composition(s, deck, k) for k, s in enumerate(slides)] == ["cards", "rows", "cards"]
    slides[0].items[0].detail = "Uma explicação muito extensa. " * 5
    assert composition(slides[0], deck, 0) == "rows"


def test_non_sequence_never_gets_step_numbers():
    slide = AltoSlide(kind="etapas", title="A planta usa recursos", items=items())
    ast, _, _ = alto_to_ast(AltoDeck(title="Plantas", slides=[slide]))
    assert not any("num_txt" in (c.id or "") or "trilho" in (c.id or "") for c in ast.slides[0].commands)


def test_redundant_label_kept_when_sibling_labels_are_distinct():
    # Suprimir só um rótulo deixava uma linha sem rótulo no grupo; agora o grupo é uniforme.
    repeated = Item(label="Troca gasosa", detail="A planta troca gases com o ambiente.")
    slide = AltoSlide(kind="comparacao", title="A planta usa recursos", sides=[
        Side(name="Troca gasosa", items=[repeated, items()[0]]),
        Side(name="Outra condição", items=items()),
    ])
    ast, _, _ = alto_to_ast(AltoDeck(title="Plantas", slides=[slide]))
    texts = [c.text for c in ast.slides[0].commands if c.element_type == "text"]
    # cabeçalho + rótulo mantido na 1ª coluna + rótulo da outra coluna
    assert texts.count("Troca gasosa") == 3
    assert texts.count(repeated.detail) == 2


def test_fixed_role_scale_and_body_minimum_across_slides():
    from slidedsl.text_metrics import optical_size
    deck = AltoDeck(title="Plantas", slides=[AltoSlide(kind=k, title="A planta usa recursos", items=items())
                                           for k in ("topicos", "etapas", "conclusao")])
    result = build_alto(deck)
    assert result.success(), result.report()
    for slide in result.validation.ir.slides:
        for e in slide.elements:
            if "_rotulo_" in e.id:
                assert e.font_size == optical_size(23.5, e.font_face, 20)
            if "_detalhe_" in e.id:
                assert e.font_size == optical_size(20, e.font_face, 16, effective_minimum=18)


def test_title_balance_preserves_words_without_orphan():
    title = "Git evita confusão e perda de arquivos"
    shown = balanced_title(title, 680)
    assert " ".join(shown.split()) == title
    assert all(len(line.split()) >= 2 for line in shown.splitlines())
    assert "\n" in shown


def test_irrelevant_macro_rejected_even_with_full_query_score():
    candidate = dict(title="Fly on green leaf", query="green leaf", lexical_score=1,
                     width=1200, height=800, license_url="https://creativecommons.org/licenses/by-sa/4.0/")
    assert not automatic_candidate(candidate)
    assert relevant_image({**candidate, "title": "Green leaf in sunlight"})
    assert not relevant_image({**candidate, "title": "A mountain"})
    assert automatic_candidate({**candidate, "title": "Leaf in sunlight", "lexical_score": 0.5})


def test_label_contained_in_heading_is_redundant():
    from slidedsl.editorial import distinct_label
    assert not distinct_label("Função do inversor", "Função do inversor na energia solar")
    assert distinct_label("Corrente alternada", "Função do inversor na energia solar")


def test_statistical_image_rejected_without_data_intent():
    candidate = dict(title="Git commits by month", query="git repository commit",
                     description="A graph of commits per month.", lexical_score=1,
                     width=1200, height=800, license_url="https://creativecommons.org/licenses/by/4.0/")
    assert not automatic_candidate(candidate)


def test_photo_has_visible_credit_and_pptx_keeps_co2(tmp_path, monkeypatch):
    from slidedsl import media
    from slidedsl.compiler import compile_ir
    monkeypatch.setattr(media, "resolve_asset", lambda f: dict(
        author="Autora teste", license="CC BY-SA 4.0", attribution="Foto teste",
        page="https://example.org/foto", license_url="https://creativecommons.org/licenses/by-sa/4.0/"))
    slide = AltoSlide(kind="imagem", title="A planta usa CO₂", items=items(),
                      image_file="assets/imagem_demo.png")
    result = build_alto(AltoDeck(title="Plantas", slides=[slide]))
    assert result.success(), result.report()
    texts = [e.text for e in result.validation.ir.slides[0].elements if e.type == "text"]
    assert any("Autora teste" in t and "CC BY-SA" in t for t in texts)
    path = tmp_path / "photo.pptx"
    compile_ir(result.validation.ir, path)
    with zipfile.ZipFile(path) as archive:
        assert "CO₂" in archive.read("ppt/slides/slide1.xml").decode()


def test_image_schema_and_validation_use_photo_space_before_download():
    from slidedsl.alto_generation import check_slide, slide_schema
    assert slide_schema("imagem", [])["properties"]["itens"]["maxItems"] == 2
    slide = AltoSlide(kind="imagem", title="Repositório e commits organizam o histórico local",
                      image_query="git history", items=items() + items()[:1])
    assert any(d.code == "A010" for d in check_slide(slide, {}))
    assert slide.image_file is None  # apenas a composição de prova recebe um arquivo


def test_long_title_feedback_is_local_and_uses_existing_repair_path():
    from slidedsl.alto_generation import check_slide
    slide = AltoSlide(kind="topicos", title="Energia Solar Residencial: Entenda Antes de Avaliar", items=items())
    assert any(d.code == "A018" and d.evidence["path"] == "slides.0.title"
               for d in check_slide(slide, {}))


def test_preview_subscript_keeps_the_measured_family():
    from pathlib import Path
    from slidedsl.ir_preview import _font
    from slidedsl.text_metrics import font_file
    font = _font(20, False, 1, "CO₂")
    metric = font_file("Arial", False)
    if metric is not None:
        assert Path(font.path) == metric


def test_body_below_minimum_is_diagnosed(compile_scene):
    from slidedsl.design_rules import check_design
    ir = compile_scene('adicionar texto id corpo "Texto" '
                       'em (80,80) tamanho (500,100) fonte 12 cor #14233D papel corpo')
    assert any(d.code == "D006" and d.evidence.get("minimum") == 16 for d in check_design(ir))
