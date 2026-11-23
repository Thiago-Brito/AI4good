"""Contratos offline da grade, fontes, métricas, candidatos e corpus da rodada 4."""

from dataclasses import fields
from itertools import combinations
from pathlib import Path

from PIL import Image
import pytest

from slidedsl.alto import AltoDeck, AltoSlide, Item, parse_alto, print_alto
from slidedsl.alto_compile import build_alto
from slidedsl.alto_layout import STYLES, needed_height
from slidedsl.design_system import Estilo, col, distribute
from slidedsl.ir import Element
from slidedsl.layout_score import (aggregate, alignment, balance, choose, occupancy,
                                  occupation_score, regularity, rhythm)
from slidedsl.paths import project_root
from slidedsl.text_metrics import font_file, text_height, text_width

ROOT = project_root()
CORPUS = [*sorted((ROOT / "examples/alto").glob("*.slda")),
          *sorted((ROOT / "outputs/estilos").glob("*.slda")),
          *sorted((ROOT / "outputs/comparacao_alto_sld/20261101-2227").glob("*_s42/apresentacao.slda"))]


def test_grid_and_vertical_distribution():
    assert col(0, 12) == (64, 1152)
    assert col(6, 6)[0] - sum(col(0, 6)) == 24
    with pytest.raises(ValueError):
        col(11, 2)
    y, h = distribute(200, 100, 3)
    assert h >= .6 * (636 - 200)
    assert y < 200 + ((636 - 200) - h) / 2


def test_styles_differ_in_at_least_three_non_color_attributes():
    keys = [f.name for f in fields(Estilo) if f.name not in {"comum", "destaque", "tema"}]
    for a, b in combinations(STYLES.values(), 2):
        assert sum(getattr(a, key) != getattr(b, key) for key in keys) >= 3


def test_occupation_uses_union_clipping_and_target_plateau():
    region = (0, 0, 100, 100)
    assert occupancy([(0, 0, 50, 100)] * 2, region) == .5
    assert occupancy([(-50, 0, 50, 100)], region) == .5
    assert occupation_score(.55) == occupation_score(.78) == 1
    assert occupation_score(.1) < occupation_score(.4)
    assert occupation_score(.95) < occupation_score(.75)


def test_balance_uses_visual_mass():
    region = (0, 0, 100, 100)
    assert balance([(25, 25, 75, 75)], region) == 1
    boxes = [(0, 0, 10, 10), (90, 90, 100, 100)]
    assert balance(boxes, region) > balance(boxes, region, [10, 1])
    assert balance([], region) == 0


def test_alignment_tolerates_two_pixels():
    same = [(0, 0, 10, 10), (2, 2, 12, 12)]
    scattered = [(0, 0, 10, 10), (30, 30, 40, 40)]
    assert alignment(same) == 1
    assert alignment(scattered) < alignment(same)


def test_regularity_of_sizes_and_gaps():
    equal = [(0, 0, 10, 10), (20, 0, 30, 10), (40, 0, 50, 10)]
    assert regularity(equal) == 1
    assert regularity(equal[:-1] + [(60, 0, 90, 20)]) < 1


def test_rhythm_and_negative_power_mean():
    assert rhythm("rows", "rows") < rhythm("rows", "cards", "rows", "rows") < rhythm("rows", "cards")
    good = dict(ocupacao=1, equilibrio=1, alinhamento=1, regularidade=1, ritmo=1)
    assert aggregate(good) == 1
    assert aggregate({**good, "equilibrio": .1}) < .3
    assert 0 < aggregate({**good, "equilibrio": 0}) < .1


def test_choice_discards_invalid_avoids_repetition_and_ties_by_order():
    rows = [dict(variant="cards", valid=False, score=1),
            dict(variant="rows", valid=True, score=.8),
            dict(variant="grid", valid=True, score=.8)]
    assert choose(rows)["variant"] == "rows"
    assert choose(rows, previous="rows")["variant"] == "grid"
    assert choose([rows[1]], previous="rows")["variant"] == "rows"


@pytest.mark.parametrize("family", ["Arial", "Calibri", "Cambria", "Georgia", "Trebuchet MS", "Verdana"])
def test_measurement_accepts_family_and_matches_preview(family):
    from slidedsl.ir_preview import _font
    path = font_file(family, True)
    if path:
        assert Path(_font(24, True, 1, family=family).path) == path
    assert needed_height("Texto com palavras", 300, 24, True, family) >= text_height(
        "Texto com palavras", 300, 24, True, family)


@pytest.mark.parametrize("style", list(STYLES))
@pytest.mark.parametrize("source", CORPUS, ids=lambda p: p.parent.name + "_" + p.stem)
def test_fixed_corpus_fits_every_style_without_changing_alto(source, style):
    deck = parse_alto(source.read_text("utf-8"))
    deck.theme = style
    frozen = print_alto(deck)
    result = build_alto(deck)
    assert print_alto(deck) == frozen
    blockers = [d for d in result.all_diagnostics if d.code in {"A010", "A019", "D010", "D001", "D008"}]
    assert not blockers, [(d.code, d.slide, d.element, d.evidence) for d in blockers]
    assert result.success(), result.report()
    for slide in result.validation.ir.slides:
        for e in slide.elements:
            if e.type == "text":
                assert text_height(e.text, e.width, e.font_size, e.bold, e.font_face) <= e.height
                assert max((text_width(w, e.font_size, e.bold, e.font_face)
                            for w in e.text.split()), default=0) <= e.width - 16


def test_choice_is_deterministic_and_records_candidates():
    slide = AltoSlide(kind="topicos", title="Registre as versões", items=[
        Item(label="Histórico", detail="Cada commit preserva o estado escolhido."),
        Item(label="Equipe", detail="Uma branch permite experimentar com os colegas.")])
    deck = AltoDeck(title="Git", slides=[slide, slide.model_copy(deep=True),
                                        slide.model_copy(deep=True)])
    first, second = build_alto(deck), build_alto(deck)
    assert first.dsl == second.dsl
    chosen = [d.evidence for d in first.diagnostics if d.code == "A030"]
    assert all(len(row["candidates"]) == 2 for row in chosen)
    assert all(a["variant"] != b["variant"] for a, b in zip(chosen, chosen[1:]))
    assert [d.model_dump() for d in first.diagnostics] == [d.model_dump() for d in second.diagnostics]


def test_missing_family_falls_back_with_logged_safety_margin(caplog):
    assert font_file("FonteAusenteR4", False) == font_file("Arial", False)
    assert "FonteAusenteR4" in caplog.text
    assert text_width("Teste de segurança", 24, family="FonteAusenteR4") > text_width(
        "Teste de segurança", 24, family="Arial")


def test_card_padding_gap_and_sibling_details_share_top():
    from slidedsl.alto_layout import Builder, editorial_items
    from slidedsl.design_system import CARD_PADDING, LABEL_GAP
    b = Builder(1, STYLES["claro"].comum, style=STYLES["claro"], variant="cards")
    items = [Item(label="Equipe", detail="Uma branch permite experimentar."),
             Item(label="Histórico das versões escolhidas", detail="O commit guarda os arquivos.")]
    editorial_items(b, items, "slides.0.items", 64, 200, 1152, 636, cards=True)
    labels = [c for c in b.commands if "_rotulo_" in c.id]
    details = [c for c in b.commands if "_detalhe_" in c.id]
    cards = [c for c in b.commands if "_card_" in c.id]
    assert details[0].position.y == details[1].position.y
    assert labels[0].position.y == labels[1].position.y
    for card, label, detail in zip(cards, labels, details):
        assert label.position.x - card.position.x == CARD_PADDING
        assert detail.position.y - (label.position.y + label.size[1]) == LABEL_GAP


def test_short_section_has_transition_without_giant_number():
    slide = AltoSlide(kind="secao", title="Agora vamos praticar", subtitle="Registre uma mudança")
    short = build_alto(AltoDeck(title="Git", slides=[slide])).validation.ir.slides[0]
    assert not any(e.font_size == 96 for e in short.elements)
    long = build_alto(AltoDeck(title="Git", slides=[slide] * 8)).validation.ir.slides[0]
    assert any(e.font_size == 96 for e in long.elements)


def test_small_local_image_warns_without_blocking(tmp_path):
    Image.new("RGB", (800, 400)).save(tmp_path / "small.png")
    deck = AltoDeck(title="Imagem", slides=[AltoSlide(kind="imagem", title="Veja o equipamento",
        image_file="small.png", items=[Item(label="Inspecione", detail="Observe os conectores.")])])
    result = build_alto(deck, root=tmp_path)
    assert result.success(), result.report()
    warning = next(d for d in result.diagnostics if d.code == "A031")
    assert warning.severity == "AVISO" and warning.evidence["width"] == 800


def test_resolution_warning_does_not_request_model_text_repair():
    from slidedsl.alto_generation import check_slide
    slide = AltoSlide(kind="imagem", title="A planta recebe luz", image_query="green leaf",
        items=[Item(label="Luz", detail="Observe a folha perto da janela.")])
    ds = check_slide(slide, {})
    assert not any(d.code == "A031" for d in ds)
    assert slide.image_file is None


def test_automatic_search_rejects_small_photo_when_large_alternative_exists(monkeypatch):
    from slidedsl import media
    common = dict(query="solar panel", title="Solar panel", lexical_score=1,
                  license_url="https://creativecommons.org/publicdomain/zero/1.0/")
    small = dict(common, id="small", width=800, height=600)
    large = dict(common, id="large", width=1200, height=800)
    calls = []
    def search(provider, query, **kw):
        calls.append(provider)
        return {"results": [small] if provider == "one" else [large]}
    monkeypatch.setattr(media, "search_images", search)
    found = media.automatic_search("solar panel", providers=["one", "two"], offline=True)
    assert calls == ["one", "two"]
    assert [i["id"] for i in found["results"]] == ["large"]
    fallback = media.automatic_search("solar panel", providers=["one"], offline=True)
    assert fallback["results"][0]["id"] == "small"


def test_empty_family_rejected_by_semantic_validation():
    from slidedsl.ir import Presentation, Slide
    from slidedsl.semantic import validate_ir
    e = Element(id="text", type="text", text="Texto", x=64, y=64, width=500, height=100,
                font_size=24, font_face=" ", color="#000000")
    assert any(d.code == "S005" for d in validate_ir(Presentation(title="Teste", theme="claro",
                                                               slides=[Slide(number=1, elements=[e])])))
