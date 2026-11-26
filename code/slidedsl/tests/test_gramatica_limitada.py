"""Limites do compilador na gramática do PC (noite de 26/11, T4)."""

import re

from slidedsl.alto import AltoSlide, Item, Side, TEXT_LIMITS
from slidedsl.alto_generation import trim_at_limit, trim_slide_limits
from slidedsl.gbnf import alto_gbnf, alto_gbnf_limitada


def test_gramatica_limitada_poe_o_limite_de_cada_campo():
    g = alto_gbnf_limitada("comparacao")
    assert f'titulo ::= ws "titulo" ws t-s{TEXT_LIMITS["title"]}' in g
    assert "item ::= ws \"item\" ws t-s48 (ws t-s80)?" in g  # detalhe da comparação: 80
    assert re.search(r"^t-s48 ::= .*\{0,48\}", g, re.M)
    g = alto_gbnf_limitada("topicos")
    assert "item ::= ws \"item\" ws t-s48 (ws t-s170)?" in g
    assert "notas ::= ws \"notas\" ws t-s600" in g  # notas ficam no teto antigo


def test_gramatica_limitada_aceita_o_mesmo_que_a_generica_dentro_dos_limites():
    # Mesmas regras de estrutura; só as strings mudam.
    estrutura = lambda g: sorted(l.split(" ::= ")[0] for l in g.splitlines() if not l.startswith("t-s"))
    assert estrutura(alto_gbnf_limitada("numeros")) == estrutura(alto_gbnf("numeros"))


def test_texto_cortado_termina_na_pausa_ou_palavra_inteira():
    assert trim_at_limit("Curto.", 48) == "Curto."
    cortado = "O programa grava o arquivo mesmo com erros, e o texto estoura a cai"
    assert trim_at_limit(cortado, len(cortado)) == "O programa grava o arquivo mesmo com erros"
    sem_pausa = "Sem conhecimento avançado o usuário consegue usar a ferramenta do"
    assert trim_at_limit(sem_pausa, len(sem_pausa)) == "Sem conhecimento avançado o usuário consegue usar a ferramenta"
    completo = "Esta frase tem exatamente o tamanho do limite e termina bem."
    assert trim_at_limit(completo, len(completo)) == completo


def test_slide_aparado_nos_campos_que_bateram_no_limite():
    label = ("rótulo comprido " * 5)[:48]  # exatamente no limite, cortado no meio de "comprido"
    assert len(label) == 48
    s = AltoSlide(kind="comparacao", title="Título",
                  sides=[Side(name="A", items=[Item(label=label, detail="ok")]),
                         Side(name="B", items=[Item(label="Curto", detail="x" * 10)])])
    assert trim_slide_limits(s, "comparacao") == ["sides.0.items.0.label"]
    assert s.sides[0].items[0].label.split()[-1] in ("rótulo", "comprido") and len(s.sides[0].items[0].label) < 48


def test_limite_padrao_de_chamadas_cresce_com_os_slides():
    from slidedsl.alto_generation import default_max_calls
    assert default_max_calls(6) == 60 and default_max_calls(4) == 60  # o padrão antigo continua para decks curtos
    assert default_max_calls(8) == 80 and default_max_calls(30) == 200
