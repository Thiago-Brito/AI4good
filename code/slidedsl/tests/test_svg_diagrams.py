import re
import xml.etree.ElementTree as ET

import pytest

from slidedsl.alto import Bar, Item, parse_alto, print_alto
from slidedsl.svg_diagrams import barras_svg, ciclo_svg, deck_svgs, etapas_svg, wrap

NS = "{http://www.w3.org/2000/svg}"

DECK = """deck "Teste" {
  etapas {
    titulo "Fluxo"
    item "Pedido" "O estudante escreve o que quer"
    item "Compilador" "Calcula posição e fonte"
    item "Slide" "Sai editável"
  }
  ciclo {
    titulo "Água"
    item "Evaporação" "O sol aquece"
    item "Condensação" "Formam-se nuvens"
    item "Chuva" "A água cai"
  }
  grafico {
    titulo "Notas"
    unidade "pontos"
    barra "A" 10
    barra "B" 5
    barra "C" 2.5
  }
}"""


def _roles(svg, role):
    root = ET.fromstring(svg)
    return [el for el in root.iter() if el.get("data-role") == role]


def test_ciclo_e_bloco_proprio_que_volta_ao_imprimir():
    deck = parse_alto(DECK)
    assert [(s.kind, s.cycle) for s in deck.slides] == [
        ("etapas", False), ("etapas", True), ("grafico", False)]
    assert "  ciclo {" in print_alto(deck)
    def strip(d):
        return [x.model_dump(exclude={"line", "column"}) for x in d.slides]

    assert strip(parse_alto(print_alto(deck))) == strip(deck)


def test_deck_gera_um_svg_por_diagrama_com_tipo_certo():
    kinds = [(n, r.kind) for n, r in deck_svgs(parse_alto(DECK))]
    assert kinds == [(1, "etapas"), (2, "ciclo"), (3, "grafico")]


def test_etapas_mantem_ordem_e_setas_entre_vizinhos():
    items = [Item(label=f"Passo {k}", detail="Detalhe curto") for k in range(1, 5)]
    result = etapas_svg(items)
    boxes = _roles(result.svg, "etapa")
    xs = [float(b.get("x")) for b in boxes]
    assert xs == sorted(xs) and len(boxes) == 4
    arrows = [(a.get("data-from"), a.get("data-to")) for a in _roles(result.svg, "seta")]
    assert arrows == [("1", "2"), ("2", "3"), ("3", "4")]
    assert result.warnings == []


def test_ciclo_fecha_com_seta_da_ultima_para_a_primeira():
    items = [Item(label=n) for n in ("A", "B", "C", "D", "E")]
    arrows = [(a.get("data-from"), a.get("data-to")) for a in _roles(ciclo_svg(items).svg, "seta")]
    assert arrows[-1] == ("5", "1") and len(arrows) == 5


def test_caixas_do_ciclo_nao_se_sobrepoem():
    items = [Item(label=f"Etapa {k}", detail="Um detalhe de duas linhas talvez") for k in range(6)]
    boxes = [(float(b.get("x")), float(b.get("y")), float(b.get("width")), float(b.get("height")))
             for b in _roles(ciclo_svg(items).svg, "etapa")]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0]
                    or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])


def test_barras_tem_altura_exatamente_proporcional():
    bars = [Bar(label="A", value=10), Bar(label="B", value=5), Bar(label="C", value=2.5)]
    rects = _roles(barras_svg(bars).svg, "barra")
    heights = [float(r.get("height")) for r in rects]
    for h, bar in zip(heights, bars):
        assert h / heights[0] == pytest.approx(bar.value / 10, abs=1e-3)
    bottoms = {round(float(r.get("y")) + float(r.get("height")), 1) for r in rects}
    assert len(bottoms) == 1


def test_texto_longo_encolhe_e_avisa_sem_cortar():
    long = "palavra " * 150
    result = etapas_svg([Item(label="Curto", detail=long)] + [Item(label=f"P{k}") for k in range(5)])
    assert any("detalhe" in w for w in result.warnings)
    assert "palavra" in result.svg


def test_texto_e_escapado_e_svg_e_xml_valido():
    result = etapas_svg([Item(label="A < B & C"), Item(label='"aspas"')])
    ET.fromstring(result.svg)
    assert "A &lt; B &amp; C" in result.svg


def test_limites_e_valores_negativos_sao_recusados():
    with pytest.raises(ValueError):
        etapas_svg([Item(label="só um")])
    with pytest.raises(ValueError):
        ciclo_svg([Item(label="a"), Item(label="b")])
    with pytest.raises(ValueError):
        barras_svg([Bar(label="a", value=-1), Bar(label="b", value=2)])


def test_wrap_respeita_largura_e_recusa_palavra_maior_que_a_caixa():
    lines = wrap("um dois três quatro cinco seis", 80, 14)
    assert lines and len(lines) > 1
    assert wrap("supercalifragilístico", 20, 14) is None


def test_saida_e_deterministica():
    deck = parse_alto(DECK)
    first = [r.svg for _, r in deck_svgs(deck)]
    assert first == [r.svg for _, r in deck_svgs(deck)]
    assert all(re.search(r'viewBox="0 0 \d+ \d+"', s) for s in first)
