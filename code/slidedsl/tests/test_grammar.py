import pytest

from slidedsl.diagnostics import DSLException
from slidedsl.parser import parse
from slidedsl.printer import print_ast


def wrap(command, theme="claro"):
    return f'apresentacao "Teste" {{ tema {theme} slide 1 {{ {command} }} }}'


@pytest.mark.parametrize(
    "command",
    [
        "adicionar retangulo id a em (0, 0) tamanho (40, 20) cor #FFAA00",
        "adicionar elipse id a em canto superior direito tamanho (40, 20) cor #aaff00",
        'adicionar texto id a "Olá \\"mundo\\"" em (18.5, -10) tamanho (40, 20) fonte 40 cor #14233D',
        'adicionar imagem id a arquivo "assets/imagem_demo.png" em (0,0) tamanho (40,20)',
        "remover a",
        "mover a para abaixo de b com margem 24",
        "mover a para a direita de b com margem 10",
        "redimensionar a para (50, 10)",
        "mudar cor de a para #FF0000",
        "trazer a para frente",
        "enviar a para tras",
        "alinhar a com b pela esquerda",
    ],
)
def test_all_commands_parse_and_print(command):
    ast = parse(wrap(command))
    again = parse(print_ast(ast))
    assert ast.slides[0].commands[0].model_dump(exclude={"line", "column"}) == again.slides[
        0
    ].commands[0].model_dump(exclude={"line", "column"})


@pytest.mark.parametrize(
    "command",
    [
        "adicionar triangulo id a em (0,0) tamanho (1,1) cor #FFFFFF",
        "adicionar retangulo id a em (0,0) tamanho (1,1) cor #FFF",
        "remover",
        "mover a para (2;3)",
        'adicionar texto id a "aberto',
        "remover a; remover b",
        "mover a para (1,2,3)",
    ],
)
def test_invalid_syntax_has_location(command):
    with pytest.raises(DSLException) as exc:
        parse(wrap(command))
    assert exc.value.diagnostics[0].line == 1
    assert exc.value.diagnostics[0].column > 0


def test_theme_retained():
    assert parse(wrap("remover a", "escuro")).theme == "escuro"


def test_no_commands_outside_slide():
    with pytest.raises(DSLException):
        parse('apresentacao "X" { tema claro remover a slide 1 { remover b } }')
