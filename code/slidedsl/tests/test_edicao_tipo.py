"""Edição de um slide: o tipo só muda quando a instrução pede (achado do teste real de 23/11/2026)."""

import json

from slidedsl.alto import parse_alto
from slidedsl.alto_edit import allowed_kinds, refazer_slide

SOURCE = """deck "Git" {
  tema claro
  capa {
    titulo "Git para iniciantes"
  }
  topicos {
    titulo "Por que usar Git"
    item "Histórico" "Cada mudança fica registrada com autor e data."
    item "Cópias locais" "Cada pessoa trabalha sem depender de conexão."
  }
}
"""


def test_keeps_current_kind_without_explicit_request():
    assert allowed_kinds("Reescreva com frases mais curtas e diretas.", "topicos") == ["topicos"]
    assert allowed_kinds("Adapte a linguagem para alunos do ensino fundamental.", "numeros") == ["numeros"]
    # Mencionar uma palavra de tipo sem pedir troca não muda o tipo.
    assert allowed_kinds("Cite a fonte da foto no texto.", "topicos") == ["topicos"]


def test_explicit_request_selects_only_requested_kind():
    assert allowed_kinds("Transforme este slide em uma comparação entre duas opções.", "topicos") == [
        "comparacao"]
    assert allowed_kinds("Compare", "topicos") == ["comparacao"]
    assert allowed_kinds("Vire etapas, passo a passo", "topicos") == ["etapas"]
    assert allowed_kinds("Mude para uma linha do tempo", "topicos") == ["linha_do_tempo"]
    assert "secao" not in allowed_kinds("Transforme em comparação", "topicos")


class SchemaModel:
    def __init__(self, kind, content):
        self.schemas, self.users, self.kind, self.content = [], [], kind, content

    def generate(self, system, user, **kwargs):
        self.schemas.append(kwargs["response_schema"])
        self.users.append(user)
        return json.dumps({"slide": {"tipo": self.kind, "conteudo": self.content}})


def test_schema_offers_only_current_kind_and_prompt_says_keep():
    content = {"titulo": "Por que usar Git", "itens": [
        {"rotulo": "Histórico", "detalhe": "Cada mudança fica registrada."},
        {"rotulo": "Cópias locais", "detalhe": "Trabalho sem conexão."}], "fontes": [], "notas": ""}
    model = SchemaModel("topicos", content)
    result = refazer_slide(SOURCE, 2, "Reescreva com frases mais curtas.", {}, model)
    slide_schema = model.schemas[0]["properties"]["slide"]
    assert "anyOf" not in slide_schema
    assert slide_schema["properties"]["tipo"]["enum"] == ["topicos"]
    assert "Mantenha o tipo atual (topicos)" in model.users[0]
    assert parse_alto(result).slides[1].kind == "topicos"
