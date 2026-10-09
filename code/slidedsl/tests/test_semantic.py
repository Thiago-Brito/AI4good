import pytest

from slidedsl.diagnostics import DSLException
from slidedsl.parser import parse
from slidedsl.semantic import analyze

SHAPE = "adicionar retangulo id a em (80, 100) tamanho (100, 60) cor #FF0000"


@pytest.mark.parametrize(
    "commands,code",
    [
        ("remover desconhecido", "S003"),
        (SHAPE + " " + SHAPE, "S002"),
        (SHAPE.replace("(100, 60)", "(-50, 100)"), "S004"),
        (SHAPE.replace("(100, 60)", "(0, 100)"), "S004"),
        (SHAPE.replace("(80, 100)", "abaixo de futuro com margem 5"), "S003"),
        (SHAPE + " remover a mover a para (0,0)", "S003"),
        ('adicionar imagem id foto arquivo "assets/ausente.png" em (0,0) tamanho (50,50)', "S007"),
        ('adicionar imagem id foto arquivo "../fora.png" em (0,0) tamanho (50,50)', "S007"),
        ('adicionar imagem id foto arquivo "https://x/a.png" em (0,0) tamanho (50,50)', "S007"),
        ('adicionar texto id t "A" em (0,0) tamanho (100,100) fonte 9 cor #FFFFFF', "S005"),
        ('adicionar texto id t "A" em (0,0) tamanho (100,100) fonte 97 cor #FFFFFF', "S005"),
        (SHAPE + " alinhar a com futuro pela esquerda", "S003"),
    ],
)
def test_negative_semantics(compile_scene, commands, code):
    with pytest.raises(DSLException) as exc:
        compile_scene(commands)
    assert code in {d.code for d in exc.value.diagnostics}
    assert all(d.line and d.column and d.slide == 1 for d in exc.value.diagnostics)


def test_slide_order(root):
    with pytest.raises(DSLException) as exc:
        analyze(
            parse(f'apresentacao "A" {{ tema claro slide 1 {{ {SHAPE} }} slide 3 {{ {SHAPE} }} }}'),
            root,
        )
    assert exc.value.diagnostics[0].code == "S001"


def test_scope_and_duplicate_across_slides(root):
    ast = parse(f'apresentacao "A" {{ tema claro slide 1 {{ {SHAPE} }} slide 2 {{ {SHAPE} }} }}')
    assert len(analyze(ast, root).slides) == 2
    ast.slides[1].commands = (
        parse('apresentacao "A" { tema claro slide 1 { mover a para (0,0) } }').slides[0].commands
    )
    with pytest.raises(DSLException):
        analyze(ast, root)


def test_remove_and_reuse_id(compile_scene):
    deck = compile_scene(SHAPE + " remover a " + SHAPE)
    assert [e.id for e in deck.slides[0].elements] == ["a"]


def test_dimension_and_color_changes(compile_scene):
    e = (
        compile_scene(SHAPE + " redimensionar a para (400,200) mudar cor de a para #00ff00")
        .slides[0]
        .elements[0]
    )
    assert (e.width, e.height, e.color) == (400, 200, "#00FF00")
