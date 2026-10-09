import pytest

from slidedsl.diagnostics import DSLException
from slidedsl.ir import semantic_snapshot
from slidedsl.parser import parse
from slidedsl.printer import print_ast
from slidedsl.semantic import analyze
from slidedsl.serializer import to_dsl

BASE = """adicionar retangulo id a em (80,100) tamanho (100,60) cor primaria
adicionar elipse id b em (240,200) tamanho (40,20) cor secundaria
adicionar texto id titulo "Título" em (300,400) tamanho (300,100) fonte titulo cor texto"""


@pytest.mark.parametrize(
    "op",
    [
        "agrupar [a,b] como g mover g para (100,200) redimensionar g para (400,200)",
        'agrupar [a,b] como g rotulo "Comparação" desagrupar g',
        "alinhar b com a pela direita",
        "alinhar b com a pelo centro horizontal",
        "alinhar b com a pelo topo",
        "distribuir horizontalmente [a,b,titulo] com intervalo 24",
        "definir camada de a como 8",
        "definir camada de titulo como -5",
    ],
)
def test_extension_roundtrip(compile_scene, root, op):
    d = compile_scene(BASE + "\n" + op)
    assert semantic_snapshot(analyze(parse(to_dsl(d)), root)) == semantic_snapshot(d)
    ast = parse(to_dsl(d))
    assert parse(print_ast(ast)).title == d.title


def test_group_geometry(compile_scene):
    s = compile_scene(
        BASE + " agrupar [a,b] como g mover g para (100,200) redimensionar g para (400,240)"
    ).slides[0]
    a, b, _ = s.elements
    assert (a.x, a.y, a.width, a.height) == (100, 200, 200, 120)
    assert (b.x, b.y, b.width, b.height) == (420, 400, 80, 40)


@pytest.mark.parametrize(
    "axis,xy",
    [
        ("pela direita", (140, 200)),
        ("pelo centro horizontal", (110, 200)),
        ("pelo topo", (240, 100)),
    ],
)
def test_alignment_axes(compile_scene, axis, xy):
    b = compile_scene(BASE + f" alinhar b com a {axis}").slides[0].elements[1]
    assert (b.x, b.y) == xy


def test_distribution(compile_scene):
    a, b, c = (
        compile_scene(BASE + " distribuir horizontalmente [a,b,titulo] com intervalo 24")
        .slides[0]
        .elements
    )
    assert (a.x, b.x, c.x) == (80, 204, 268)


def test_layout_and_label(compile_scene, root):
    s = compile_scene('grupo "Comparação" { ' + BASE + " }")
    assert s.slides[0].groups[0].label == "Comparação"
    assert semantic_snapshot(analyze(parse(to_dsl(s)), root)) == semantic_snapshot(s)


@pytest.mark.parametrize(
    "op",
    [
        "agrupar [a,a] como g",
        "agrupar [a,futuro] como g",
        "agrupar [a,b] como a",
        "agrupar [a,b] como g agrupar [b,titulo] como h",
        "distribuir horizontalmente [a,b] com intervalo 24",
        "desagrupar a",
    ],
)
def test_extension_rejections(compile_scene, op):
    with pytest.raises(DSLException):
        compile_scene(BASE + " " + op)


def test_explicit_role_and_font(compile_scene):
    e = (
        compile_scene(
            'adicionar texto id a "A" em (0,0) tamanho (100,100) fonte corpo cor texto papel titulo familia "Calibri"'
        )
        .slides[0]
        .elements[0]
    )
    assert (e.font_size, e.role, e.font_face) == (24, "titulo", "Calibri")
