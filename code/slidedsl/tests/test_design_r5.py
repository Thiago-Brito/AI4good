"""Regressões offline da calibragem: fotos, legibilidade, ocupação, ritmo e eixos."""

from PIL import Image, ImageFont
import pytest

from slidedsl.alto import AltoDeck, AltoSlide, Item
from slidedsl.alto_compile import build_alto
from slidedsl.alto_layout import STYLES, variants_for
from slidedsl.design_system import CONTENT_BOTTOM, col
from slidedsl.layout_score import (WEIGHTS, content_preference, occupation_score,
                                  rhythm, score_slide)
from slidedsl.text_metrics import FAMILIES, font_file, optical_size, x_height_ratio


def short_items(count=3):
    return [Item(label=f"Ação {k + 1}", detail="Guarde uma versão e confira o resultado.")
            for k in range(count)]


def test_plateau_and_steeper_sparse_penalty():
    assert WEIGHTS["ocupacao"] == .35 and WEIGHTS["equilibrio"] == .20
    assert sum(WEIGHTS.values()) == pytest.approx(1)
    assert all(occupation_score(x / 100) == 1 for x in range(55, 79))
    assert occupation_score(.44) - occupation_score(.34) > .10 / .45
    assert occupation_score(.45) == pytest.approx(.8)
    assert occupation_score(.79) < 1
    assert occupation_score(0) == occupation_score(1) == 0


@pytest.mark.parametrize("family", list(FAMILIES))
def test_optical_scale_is_computed_from_local_ttf(family):
    reference, target = font_file("Arial"), font_file(family)
    if reference is None or target is None:
        pytest.skip("Sem arquivo de fonte local")
    def height(path):
        _, y0, _, y1 = ImageFont.truetype(str(path), 1000).getbbox("x", anchor="ls")
        return y1 - y0
    ratio = height(target) / height(reference)
    assert x_height_ratio(family) == ratio
    assert optical_size(20, family) == round(20 / ratio)
    assert optical_size(16, family, minimum=16, effective_minimum=18) * ratio >= 18
    assert optical_size(24, family, minimum=24) >= 24


@pytest.mark.parametrize("dimensions", [(2000, 1000), (1200, 1200), (1000, 999),
                                        (800, 400), (900, 1600), (400, 1800), (1000, 1001)])
def test_photo_selection_and_minimum_contained_viewport(tmp_path, dimensions):
    Image.new("RGB", dimensions, "#609080").save(tmp_path / "asset.png")
    s = AltoSlide(kind="imagem", title="Observe o equipamento", image_file="asset.png",
                  items=short_items(2))
    candidates = variants_for(s, tmp_path)
    assert candidates == ["photo50"]
    result = build_alto(AltoDeck(title="Foto", slides=[s]), root=tmp_path)
    assert result.success(), result.report()
    selected = next(d.evidence["variant"] for d in result.diagnostics if d.code == "A030")
    slide = result.validation.ir.slides[0]
    image = next(e for e in slide.elements if e.type == "image")
    if selected == "photo40":
        title = next(e for e in slide.elements if e.role == "titulo")
        assert image.width >= .4 * col(0, 12)[1]
        assert image.height >= .5 * (CONTENT_BOTTOM - title.y - title.height - 16)
    else:
        assert (image.x, image.y, image.width, image.height) == (664, 0, 616, 600)
    assert any(d.code == "A031" for d in result.diagnostics) == (max(dimensions) < 1000)


def test_rhythm_remembers_three_slides_and_rewards_distinct_variants():
    assert rhythm("cards", "imagem", history=["cards", "secao", "imagem"]) < 1
    assert rhythm("cards", "imagem", history=["cards", "secao", "rows", "imagem"]) == 1
    result = build_alto(AltoDeck(title="Ritmo", slides=[
        AltoSlide(kind="topicos", title="Confira os arquivos", items=short_items())]))
    slide = result.validation.ir.slides[0]
    known = score_slide(slide, "cards", history=["cards", "secao", "rows", "imagem"])
    new = score_slide(slide, "grid", history=["cards", "secao", "rows", "imagem"])
    assert new["diversity_bonus"] > known["diversity_bonus"]


def test_compact_messages_favor_cards_but_long_descriptions_do_not():
    metrics = dict(variant="rows", score=.95)
    assert content_preference(metrics, "topicos", short_items())["score"] == .70
    assert content_preference({**metrics, "variant": "cards"}, "topicos", short_items())["score"] > .95
    long = short_items()
    long[0].detail = "Uma descrição longa. " * 8
    assert content_preference(metrics, "topicos", long)["score"] == .95
    assert content_preference(metrics, "topicos", short_items(4))["score"] == .95


@pytest.mark.parametrize("style", list(STYLES))
def test_content_axis_and_optical_body(style):
    deck = AltoDeck(title="Eixo", theme=style, slides=[
        AltoSlide(kind="topicos", title="Confira os arquivos", items=short_items()),
        AltoSlide(kind="conclusao", title="Pratique a mudança", items=short_items())])
    result = build_alto(deck)
    assert result.success(), result.report()
    for slide in result.validation.ir.slides:
        title = next(e for e in slide.elements if e.role == "titulo")
        mark = next(e for e in slide.elements if "_marca_" in e.id)
        assert title.align == "left" and title.x == mark.x
        for e in slide.elements:
            if e.role == "corpo":
                assert e.font_size * x_height_ratio(e.font_face) >= 18


def test_cover_and_transition_center_the_whole_group():
    result = build_alto(AltoDeck(title="Eixo", theme="vibrante", slides=[
        AltoSlide(kind=kind, title="Agora vamos praticar", subtitle="Guarde uma versão")
        for kind in ["capa", "secao"]]))
    for slide in result.validation.ir.slides:
        title = next(e for e in slide.elements if e.role == "titulo")
        subtitle = next(e for e in slide.elements if "_subtitulo_" in e.id)
        mark = next(e for e in slide.elements if "_marca_" in e.id)
        assert title.align == subtitle.align == "center"
        assert mark.x + mark.width / 2 == title.x + title.width / 2
