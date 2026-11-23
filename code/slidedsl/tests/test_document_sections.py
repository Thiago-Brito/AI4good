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
