"""Regressões de acabamento: irmãos, altura natural, fotos e transições."""

from PIL import Image
import pytest

from slidedsl.alto import AltoDeck, AltoSlide, Item
from slidedsl.alto_compile import build_alto
from slidedsl.alto_layout import Builder, STYLES, editorial_items
from slidedsl.design_system import CARD_PADDING, CONTENT_BOTTOM, LABEL_GAP


@pytest.mark.parametrize("style", list(STYLES))
@pytest.mark.parametrize("kind", ["topicos", "conclusao"])
def test_sibling_tops_natural_height_and_internal_numbers(style, kind):
    items = [Item(label="Placas por tipo", detail="A escola indica o destino de cada resíduo."),
             Item(label="Lixeiras identificadas lado a lado", detail="A turma compara as opções no mesmo lugar."),
             Item(label="Rotina", detail="Os alunos repetem o ponto de descarte.")]
    result = build_alto(AltoDeck(title="Descarte", theme=style, slides=[
        AltoSlide(kind=kind, title="O ponto de descarte guia a turma", items=items)]))
    assert result.success(), result.report()
    slide = result.validation.ir.slides[0]
    labels = [e for e in slide.elements if "_rotulo_" in e.id]
    details = [e for e in slide.elements if "_detalhe_" in e.id]
    cards = [e for e in slide.elements if "_card_" in e.id]
    assert len(cards) == 3
    assert len({e.y for e in labels}) == len({e.y for e in details}) == 1
    assert details[0].y == labels[0].y + labels[0].height + LABEL_GAP
    if STYLES[style].cartao != "fio":
        assert all(c.y + c.height - d.y - d.height == CARD_PADDING for c, d in zip(cards, details))
    title = next(e for e in slide.elements if e.role == "titulo")
    top = title.y + title.height + 16
    if STYLES[style].cartao != "fio":
        center = cards[0].y + cards[0].height / 2
        assert center == pytest.approx(max(top + cards[0].height / 2,
                                          top + .45 * (CONTENT_BOTTOM - top)), abs=1)
    if kind == "conclusao":
        numbers = [e for e in slide.elements if "_acao_" in e.id]
        assert len(numbers) == 3
        assert all(n.x == lab.x and c.y < n.y < lab.y and n.font_size >= 32
                   for c, n, lab in zip(cards, numbers, labels))
        assert not any("_marcador_" in e.id for e in slide.elements)


def test_grid_row_slots_do_not_overlap():
    b = Builder(1, STYLES["claro"].comum, style=STYLES["claro"], variant="grid")
    editorial_items(b, [Item(label="Ação", detail="Confira o resultado.")] * 4,
                    "slides.0.items", 64, 180, 1152, 636, cards=True)
    cards = [c for c in b.commands if "_card_" in c.id]
    assert cards[0].position.y + cards[0].size[1] < cards[2].position.y
    assert not b.diagnostics


@pytest.mark.parametrize("dimensions", [(599, 400), (600, 400), (800, 400), (400, 1200)])
def test_photo_geometry_is_independent_of_style_and_low_resolution_warns(tmp_path, dimensions):
    Image.new("RGB", dimensions, "#609080").save(tmp_path / "foto.png")
    geometries, variants = set(), set()
    for style in STYLES:
        result = build_alto(AltoDeck(title="Foto", theme=style, slides=[
            AltoSlide(kind="imagem", title="Veja a folha", image_file="foto.png",
                      items=[Item(label="Observar", detail="A folha recebe luz perto da janela.")])]), root=tmp_path)
        assert result.success(), result.report()
        photos = [e for e in result.validation.ir.slides[0].elements if e.type == "image"]
        geometries.add(tuple((e.x, e.y, e.width, e.height) for e in photos))
        variants.add(next(d.evidence["variant"] for d in result.diagnostics if d.code == "A030"))
        assert any(d.code == "A031" for d in result.diagnostics) == (max(dimensions) < 1000)
    assert len(geometries) == len(variants) == 1
    assert geometries == ({((664, 0, 616, 600),)} if max(dimensions) >= 600 else {()})


@pytest.mark.parametrize("style", list(STYLES))
def test_short_transition_has_large_phrase_and_third_canvas_motif(style):
    result = build_alto(AltoDeck(title="Transição", theme=style, slides=[
        AltoSlide(kind="secao", title="Agora vamos praticar", subtitle="Registre uma mudança")]))
    assert result.success(), result.report()
    elements = result.validation.ir.slides[0].elements
    title = next(e for e in elements if e.role == "titulo")
    block = next(e for e in elements if "_transicao_bloco_" in e.id)
    assert 48 <= title.font_size <= 54
    assert block.width * block.height == pytest.approx(1280 * 720 / 3, abs=720)
    assert not any(e.font_size == 96 for e in elements)


def test_tiny_cover_falls_back_to_full_width_typography(tmp_path):
    Image.new("RGB", (599, 300)).save(tmp_path / "tiny.png")
    result = build_alto(AltoDeck(title="Capa", slides=[AltoSlide(
        kind="capa", title="Cultive em casa", image_file="tiny.png")]), root=tmp_path)
    assert result.success(), result.report()
    elements = result.validation.ir.slides[0].elements
    assert not any(e.type == "image" for e in elements)
    assert next(e for e in elements if e.role == "titulo").width > 900
    assert any(d.code == "A031" for d in result.diagnostics)
