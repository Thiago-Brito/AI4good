import pytest

from slidedsl.geometry import area, intersection, union_area

BASE = "adicionar retangulo id a em (80,100) tamanho (100,60) cor #FF0000"


@pytest.mark.parametrize(
    "position,xy",
    [
        ("(18.5, 20.5)", (18.5, 20.5)),
        ("canto superior direito", (1176, 64)),
        ("abaixo de a com margem 24", (80, 184)),
        ("a direita de a com margem 24", (204, 100)),
    ],
)
def test_relative_positions(compile_scene, position, xy):
    b = (
        compile_scene(BASE + f" adicionar elipse id b em {position} tamanho (40,20) cor #000000")
        .slides[0]
        .elements[1]
    )
    assert (b.x, b.y) == xy


def test_move_and_align(compile_scene):
    deck = compile_scene(
        BASE
        + " adicionar elipse id b em (300,200) tamanho (40,20) cor #000000 mover a para (120,80) alinhar b com a pela esquerda"
    )
    a, b = deck.slides[0].elements
    assert (a.x, a.y, b.x, b.y) == (120, 80, 120, 200)
    assert deck.slides[0].relations[0].kind == "left"


@pytest.mark.parametrize(
    "command,order",
    [
        ("trazer a para frente", ["b", "a"]),
        ("enviar b para tras", ["b", "a"]),
        ("enviar a para tras", ["a", "b"]),
    ],
)
def test_z_order(compile_scene, command, order):
    s = compile_scene(
        BASE + " adicionar elipse id b em (100,100) tamanho (40,20) cor #000000 " + command
    ).slides[0]
    assert [e.id for e in s.elements] == order
    assert [e.z for e in s.elements] == [0, 1]


def test_union_never_double_counts():
    a, b, c = (0, 0, 100, 100), (50, 0, 150, 100), (60, 10, 70, 20)
    assert union_area([a, b, c]) == 15000
    assert area(intersection(a, b)) == 5000
    assert intersection(a, (100, 0, 200, 100)) is None
