"""Leitura por frases numeradas no PC (porte do app, noite de 26/11)."""

import json

from slidedsl import documents
from slidedsl.frases import fact_grammar, fact_value, numbered, parse_fact_lines, split_sentences
from slidedsl.gbnf import GBNFMatcher

TEXTO = ("Resultado: com todo o texto dentro das caixas, o lado A teve 1 de 24 apresentações, o lado B 13 de 24 "
         "e o lado C 19 de 24. B superou A em 13 pares contra 1 (McNemar, p = 0,002).")


def test_frases_e_numeracao():
    frases = split_sentences("## Teste 1\n" + TEXTO)
    assert len(frases) == 2 and frases[1].startswith("B superou A")
    assert numbered(frases).startswith("[1] Resultado:")


def test_gramatica_so_aceita_frases_crescentes():
    g = GBNFMatcher(fact_grammar(3, max_facts=2))
    linha = lambda n: f'fato {n} afirmacao "O lado B teve 13 de 24 apresentações válidas." tipo numero relevancia alta\n'
    assert g.accepts(linha(1) + linha(3))
    assert not g.accepts(linha(3) + linha(1))  # sem voltar nem repetir
    assert g.accepts("")  # nenhum fato útil


def test_citacao_e_a_frase_original_e_o_valor_vem_dela():
    frases = split_sentences(TEXTO)
    fatos = parse_fact_lines('fato 1 afirmacao "O lado B teve 13 de 24 apresentações com o texto nas caixas." '
                             'tipo numero relevancia alta\n', frases)
    assert fatos[0]["trecho"] == frases[0] and fatos[0]["valor"] == "13"
    assert fact_value("p de 0,002 no teste", frases[1]) == "0,002"


def test_documento_lido_por_frases_quando_o_modelo_tem_gramatica(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    record = documents.add_document("t.md", ("# T\n\n## Teste 1\n" + TEXTO + "\n").encode("utf-8"))

    class GrammarModel:
        supports_grammar = True
        metadata = {"provider": "fake"}

        def generate(self, system, user, **kw):
            assert kw.get("grammar") and "[1]" in user  # gramática de frases e trecho numerado
            return 'fato 1 afirmacao "O lado B teve 13 de 24 apresentações com o texto nas caixas." tipo numero relevancia alta\n'

    dossier = documents.dossier_from_documents([record["id"]], "teste", GrammarModel())
    assert len(dossier.facts) == 1 and "13 de 24" in dossier.facts[0].quote  # citação literal, aceita
