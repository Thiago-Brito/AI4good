"""Diagramas no próprio slide: etapas em caixas com setas e ciclo em círculo, com formas editáveis."""

import pytest

from slidedsl.alto import AltoDeck, AltoSlide, Item, parse_alto
from slidedsl.alto_compile import build_alto
from slidedsl.alto_generation import json_to_slide, slide_schema


def items(n, detail="O que acontece nesta fase do processo."):
    return [Item(label=f"Fase {k + 1}", detail=detail) for k in range(n)]


def elements(slide_kind, n, theme="claro", cycle=False, its=None):
    deck = AltoDeck(title="Teste", theme=theme, slides=[
        AltoSlide(kind="capa", title="Teste de diagramas"),
        AltoSlide(kind=slide_kind, title="Como o processo funciona", items=its or items(n), cycle=cycle)])
    result = build_alto(deck)
    assert result.success(), result.report()
    return result.validation.ir.slides[1].elements


def count(els, name):
    return [e for e in els if f"_{name}_" in e.id]


@pytest.mark.parametrize("theme", ["claro", "escuro", "editorial", "vibrante", "natural", "noturno"])
def test_etapas_viram_caixas_com_setas_em_todos_os_estilos(theme):
    els = elements("etapas", 4, theme)
    assert len(count(els, "etapa")) == 4 and [e.text for e in count(els, "seta")] == ["→"] * 3
    labels = sorted(count(els, "rotulo"), key=lambda e: e.x)
    assert [e.text for e in labels] == ["Fase 1", "Fase 2", "Fase 3", "Fase 4"]


@pytest.mark.parametrize("n", [3, 4])
def test_ciclo_desenha_n_caixas_e_n_setas_fechando_o_circulo(n):
    els = elements("etapas", n, cycle=True)
    boxes = count(els, "etapa")
    assert len(boxes) == n and len(count(els, "seta")) == n
    for i, a in enumerate(boxes):  # nenhuma caixa sobre outra
        for b in boxes[i + 1:]:
            assert a.x + a.width <= b.x or b.x + b.width <= a.x or a.y + a.height <= b.y or b.y + b.height <= a.y


def test_ciclo_de_cinco_e_texto_que_nao_cabe_voltam_para_a_lista():
    assert not count(elements("etapas", 5, cycle=True), "etapa")
    # Palavra mais larga que a caixa de 5 etapas (nem com 20 pt): o slide volta para a lista numerada.
    long = [Item(label=f"Responsabilidades {k}", detail="A equipe registra quem aprova cada mudança.") for k in "ABCDE"]
    assert not count(elements("etapas", 5, its=long), "etapa")


def test_geracao_aceita_ciclo_como_etapas_com_cycle():
    assert slide_schema("ciclo", [])["properties"]["itens"]["minItems"] == 3
    s = json_to_slide("ciclo", {"titulo": "O ciclo da água", "itens": [
        {"rotulo": "Evaporação", "detalhe": "O sol aquece a água."}] * 3, "fontes": [], "notas": ""})
    assert s.kind == "etapas" and s.cycle


def test_exemplo_de_diagramas_compila_estrito():
    from pathlib import Path

    deck = parse_alto((Path(__file__).parents[1] / "examples/alto/diagramas.slda").read_text("utf-8"))
    assert build_alto(deck).success(strict=True)
