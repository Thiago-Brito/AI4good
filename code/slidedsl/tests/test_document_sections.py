import json

from slidedsl import documents
from slidedsl.alto_generation import generate_alto
from tests.test_alto import FACTS, OUTLINE, FakeSLM

DOC = (
    "# Seminário\n\n"
    "## A ideia\nA IA escreve o conteúdo e o compilador desenha o diagrama.\n\n"
    "## O competidor\nO Presenton é aberto e roda com modelo local.\n\n"
    "## O caminho\nO teste roda em 25/11 e o pitch é em 02/12.\n"
).encode("utf-8")


def _doc(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    record = documents.add_document("sem3.md", DOC)
    chunks = json.loads((documents.document_path(record["id"]) / "index.json").read_text("utf-8"))
    passage = {c["heading"]: c["passage"] for c in chunks["chunks"]}
    return record["id"], passage


def test_secoes_seguem_a_ordem_do_documento_e_ignoram_titulo(tmp_path, monkeypatch):
    doc_id, passage = _doc(tmp_path, monkeypatch)
    facts = [
        {"id": "F1", "url": f"documento:sem3.md#trecho-{passage['O caminho']}"},
        {"id": "F2", "url": f"documento:sem3.md#trecho-{passage['A ideia']}"},
        {"id": "F3", "url": f"documento:sem3.md#trecho-{passage['O competidor']}"},
        {"id": "F4", "url": f"documento:sem3.md#trecho-{passage['O caminho']}"},
        {"id": "F5", "url": "https://exemplo.org/pagina"},
    ]
    assert documents.document_sections([doc_id], facts) == [
        ("A ideia", ["F2"]), ("O competidor", ["F3"]), ("O caminho", ["F1", "F4"])]


def test_titulo_de_secao_nao_vira_fato(tmp_path, monkeypatch):
    doc_id, _ = _doc(tmp_path, monkeypatch)

    class Extractor:
        metadata = {"provider": "fake"}

        def generate(self, system, user, **kw):
            return json.dumps({"fatos": [{
                "afirmacao": "O SlideDSL vai provar o competidor", "trecho": "## O competidor",
                "tipo": "definicao", "valor": "", "autor": "", "relevancia": "alta"}]})

    dossier = documents.dossier_from_documents([doc_id], "competidor", Extractor())
    assert not dossier.facts
    assert any(r["reason"] == "título de seção não é fato" for r in dossier.rejected)


def test_documento_curto_com_muitas_secoes_e_lido_ate_o_fim(tmp_path, monkeypatch):
    # Caso real (25/11): um .md de 5,5 mil caracteres virou ~25 trechos; o limite de 12 por pontuação parava no
    # meio, e os slides do fim (celular, avaliação, limitações) saíam sem fatos ou inventados.
    monkeypatch.setattr(documents, "project_root", lambda: tmp_path)
    text = "# Testes\n\n" + "".join(f"## Teste {k}\nO teste {k} mediu a grandeza {k} com cuidado.\n\n" for k in range(1, 21))
    record = documents.add_document("testes.md", text.encode("utf-8"))
    seen = []

    class Extractor:
        metadata = {"provider": "fake"}

        def generate(self, system, user, **kw):
            trecho = user.split("TRECHO:\n", 1)[1].strip().splitlines()[-1]
            seen.append(trecho)
            return json.dumps({"fatos": [{"afirmacao": trecho, "trecho": trecho, "tipo": "definicao",
                                          "valor": "", "autor": "", "relevancia": "alta"}]})

    dossier = documents.dossier_from_documents([record["id"]], "teste", Extractor())
    assert len(seen) == 20 and "teste 20" in seen[-1] and "teste 1 " in seen[0]  # todos, na ordem
    assert len(dossier.facts) == 20


def test_roteiro_ve_todos_os_fatos_quando_ha_muitos():
    from slidedsl.alto_generation import facts_block
    facts = {f"F{k}": {"kind": "definicao", "claim": f"afirmação {k}", "quote": "x" * 400} for k in range(1, 60)}
    text = facts_block(list(facts), facts, all_facts=True)
    assert "F59 (definicao): afirmação 59" in text and "trecho" not in text  # todos, sem o trecho longo
    few = {k: v for k, v in list(facts.items())[:5]}
    assert 'trecho: "' in facts_block(list(few), few, all_facts=True)  # poucos fatos: formato completo


def test_roteiro_segue_as_secoes_quando_o_modelo_deixa_secoes_de_fora():
    from slidedsl.alto_generation import outline_from_sections
    model = {"titulo": "T", "slides": [
        {"tipo": "capa", "mensagem": "T", "objetivo": "x", "fatos": ["F1"], "topicos": []},
        {"tipo": "numeros", "mensagem": "A", "objetivo": "x", "fatos": ["F2"], "topicos": []},
        {"tipo": "comparacao", "mensagem": "A de novo", "objetivo": "x", "fatos": ["F2"], "topicos": []},
        {"tipo": "conclusao", "mensagem": "B", "objetivo": "x", "fatos": ["F3"], "topicos": []}]}
    sections = [("Seção A", ["F2"]), ("Seção B", ["F3", "F4"]), ("Limites", ["F9"])]
    out = outline_from_sections(model, sections, 4)
    assert [s["mensagem"] for s in out["slides"]] == ["T", "Seção A", "Seção B", "Limites"]
    assert [s["tipo"] for s in out["slides"]] == ["capa", "numeros", "comparacao", "conclusao"]
    assert out["slides"][2]["fatos"] == ["F3", "F4"]
    # Seção com mais de 6 fatos: os que têm números (resultados) entram primeiro.
    many = [f"F{k}" for k in range(10, 19)]
    facts = {i: {"claim": "passo do método"} for i in many[:7]} | {"F17": {"claim": "1 de 24"}, "F18": {"claim": "p = 0,002"}}
    out = outline_from_sections(model, [("A", ["F2"]), ("B", many), ("L", ["F9"])], 4, facts)
    assert out["slides"][2]["fatos"][:2] == ["F17", "F18"] and len(out["slides"][2]["fatos"]) == 6
    # Seções que não cabem nos slides: o roteiro do modelo fica como está.
    assert outline_from_sections(model, sections + [("Extra", ["F5"])], 4) is model


def test_slide_da_secao_leva_os_resultados_da_secao():
    from slidedsl.alto_generation import ensure_section_results
    facts = {"F1": {"claim": "Pergunta do teste"}, "F2": {"claim": "Lado A escreve código"},
             "F3": {"claim": "Lado B escreve SlideDSL"}, "F4": {"claim": "Lado A teve 1 de 24"},
             "F5": {"claim": "Lado B teve 13 de 24"}, "F6": {"claim": "Fim"}}
    sections = [("Teste 1", ["F1", "F2", "F3", "F4", "F5"]), ("Fim", ["F6"])]
    outline = {"slides": [{"tipo": "capa", "fatos": []},
                          {"tipo": "topicos", "fatos": ["F1", "F2", "F3"]}, {"tipo": "conclusao", "fatos": ["F6"]}]}
    out = ensure_section_results(outline, sections, facts, cap=4)
    # F4 entra na vaga livre; F5 toma o lugar do último fato sem número (F3).
    assert out["slides"][1]["fatos"] == ["F1", "F2", "F5", "F4"]
    assert out["slides"][2]["fatos"] == ["F6"]


def test_roteiro_aceita_ate_seis_fatos_por_slide():
    from slidedsl.alto_generation import outline_schema
    schema = outline_schema(4, ["capa", "topicos", "conclusao"], [f"F{k}" for k in range(1, 10)])
    assert schema["properties"]["slides"]["items"]["properties"]["fatos"]["maxItems"] == 6


def _planner(first_topics):
    class Planner(FakeSLM):
        def generate(self, system, user, **kw):
            if "roteirista" in system:
                self.calls.append({"user": user, "schema": kw.get("response_schema"),
                                   "grammar": None})
                outline = json.loads(json.dumps(OUTLINE))
                if "Faltaram os tópicos" in user:
                    outline["slides"][0]["topicos"] = ["A ideia"]
                    outline["slides"][1]["topicos"] = ["O competidor"]
                    outline["slides"][2]["topicos"] = ["O caminho"]
                else:
                    outline["slides"][1]["topicos"] = first_topics
                return json.dumps(outline, ensure_ascii=False)
            return super().generate(system, user, **kw)

    return Planner()


def test_secoes_do_documento_viram_topicos_obrigatorios_do_roteiro():
    sections = [("A ideia", ["F1"]), ("O competidor", ["F2"]), ("O caminho", ["F1"])]
    model = _planner(["A ideia"])
    result = generate_alto("Seminário em 4 slides", model, facts=FACTS, n_slides=4,
                           repair_max=0, sections=sections)
    outline_calls = [c for c in model.calls if c["schema"] and "slides" in c["schema"].get(
        "properties", {})]
    first = outline_calls[0]["user"]
    assert "SEÇÕES DO DOCUMENTO" in first and "- O competidor: F2" in first
    # Faltou o competidor no primeiro roteiro: o modelo é chamado de novo para cobri-lo.
    assert len(outline_calls) == 2 and "Faltaram os tópicos" in outline_calls[1]["user"]
    names = [t["nome"] for t in result.topics]
    assert names[-3:] == ["A ideia", "O competidor", "O caminho"]
    # A primeira seção (introdução) pode ficar na capa.
    assert result.outline["slides"][0]["topicos"] == ["A ideia"]


def test_sem_secoes_o_roteiro_nao_muda():
    model = FakeSLM()
    generate_alto("Microsserviços", model, facts=FACTS, n_slides=4, repair_max=0,
                  sections=[("Só uma", ["F1"])])
    outline_call = [c for c in model.calls if c["schema"] and "slides" in c["schema"].get(
        "properties", {})][0]
    assert "SEÇÕES DO DOCUMENTO" not in outline_call["user"]
