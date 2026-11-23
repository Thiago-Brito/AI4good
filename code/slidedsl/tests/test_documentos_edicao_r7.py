"""Document retrieval, bounded DOCX, factual edits and persisted undo, all offline."""

from io import BytesIO
import json
from zipfile import ZipFile

from fastapi.testclient import TestClient
import pytest

from slidedsl import documents, media
from slidedsl.alto import parse_alto
from slidedsl.alto_compile import build_alto
from slidedsl.alto_edit import ajustar_alto, export_edit, refazer_slide, slide_spans
from slidedsl.auto_theme import choose_theme
from slidedsl.models.base import ModelError
from slidedsl.research import Dossier, Fact, Source
from slidedsl.server import app


SOURCE = '''deck "SlideDSL" {
  tema claro
  capa { titulo "SlideDSL" }
  // a comment outside the edited block
  topicos {
    titulo "O compilador organiza a apresentação"
    item "Linguagem formal" "A gramática limita as estruturas aceitas pelo sistema."
    item "Cena explícita" "O compilador organiza os objetos antes da exportação."
  }
  conclusao {
    titulo "Revise a apresentação antes da defesa"
    item "Conferir as fontes" "Leia os trechos usados antes de apresentar os resultados."
    item "Abrir o PowerPoint" "Revise os objetos editáveis no programa de apresentação."
  }
}
'''


def docx_bytes(xml=None, macro=False):
    xml = xml or '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body><w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>SlideDSL</w:t></w:r></w:p>
      <w:p><w:r><w:t>SlideDSL é uma linguagem formal para criar apresentações com objetos editáveis.</w:t></w:r></w:p>
      <w:tbl><w:tr><w:tc><w:p><w:r><w:t>Camada</w:t></w:r></w:p></w:tc>
      <w:tc><w:p><w:r><w:t>Compilador</w:t></w:r></w:p></w:tc></w:tr></w:tbl></w:body></w:document>'''
    data = BytesIO()
    with ZipFile(data, "w") as archive:
        archive.writestr("word/document.xml", xml)
        if macro:
            archive.writestr("word/vbaProject.bin", b"macro")
    return data.getvalue()


@pytest.fixture
def local_docs(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "document_root", lambda: tmp_path / "documents")
    return tmp_path


def test_docx_headings_paragraphs_tables_and_portable_source(local_docs):
    doc = documents.add_document("C:/privado/meu.docx", docx_bytes())
    index = json.loads((documents.document_path(doc["id"]) / "index.json").read_text("utf-8"))
    assert index["name"] == "meu.docx"
    assert all(c["heading"] == "SlideDSL" for c in index["chunks"])
    assert any(c["text"] == "Camada | Compilador" for c in index["chunks"])
    dossier = documents.dossier_from_documents([doc["id"]], "SlideDSL")
    assert dossier.facts and dossier.facts[0].url.startswith("documento:meu.docx#trecho-")
    assert "privado" not in dossier.facts[0].url


@pytest.mark.parametrize("name,data", [
    ("macro.docm", b"data"), ("encrypted.docx", b"not a zip"),
    ("macro.docx", docx_bytes(macro=True)),
    ("entities.docx", docx_bytes('<!DOCTYPE doc [<!ENTITY x "abc">]><doc/>')),
    ("invalid.docx", docx_bytes("<bad")), ("large.txt", b"x" * (2 * 1024 * 1024 + 1)),
    ("large.docx", b"x" * (5 * 1024 * 1024 + 1)),
], ids=["docm", "encrypted", "macro", "entities", "xml", "large-txt", "large-docx"])
def test_documents_reject_unsafe_or_oversized(local_docs, name, data):
    with pytest.raises(ValueError):
        documents.add_document(name, data)


class FactModel:
    supports_response_schema = True

    def generate(self, system, user, **kw):
        return json.dumps({"fatos": [
            {"afirmacao": "SlideDSL possui uma gramática formal para criar apresentações editáveis.",
             "tipo": "definicao", "valor": "", "trecho": "SlideDSL possui uma gramática formal para criar apresentações editáveis."},
            {"afirmacao": "O projeto atingiu 99 por cento de qualidade visual comprovada.",
             "tipo": "numero", "valor": "99", "trecho": "O projeto atingiu 99 por cento de qualidade visual comprovada."}
        ]})


def test_document_facts_reject_hallucinated_quote_and_limit_count(local_docs):
    doc = documents.add_document("base.md", "SlideDSL possui uma gramática formal para criar apresentações editáveis.".encode())
    dossier = documents.dossier_from_documents([doc["id"]], "SlideDSL", FactModel())
    assert len(dossier.facts) == 1 and len(dossier.rejected) == 1
    assert dossier.facts[0].id == "F1"
    with pytest.raises(ValueError):
        documents.dossier_from_documents([doc["id"]] * 9, "SlideDSL")


def test_documento_com_titulo_e_9_secoes_usa_todas_as_secoes(local_docs):
    sections = "\n\n".join(
        f"## SlideDSL parte {i}\nO SlideDSL tem a parte {i} descrita aqui." for i in range(1, 10)
    )
    doc = documents.add_document("sem.md", ("# Título do SlideDSL\n\n" + sections).encode())
    dossier = documents.dossier_from_documents([doc["id"]], "SlideDSL")
    texts = [s.text for s in dossier.sources]
    assert len(texts) == 9 and not any(t.startswith("# Título") for t in texts)
    assert any("parte 9" in t for t in texts)


def test_document_priority_over_overlapping_web_claim(local_docs):
    doc = Dossier(topic="projeto", sources=[Source("S1", "base.md", "documento:base.md#trecho-1", "documentos")],
        facts=[Fact("F1", "SlideDSL usa gramática e compilador para exportar slides", "definicao", "trecho", "S1", "documento:base.md", "base.md")])
    web = Dossier(topic="projeto", sources=[Source("S1", "web", "https://example.org", "web")],
        facts=[Fact("F1", "SlideDSL usa gramática e compilador para exportar imagens", "definicao", "trecho", "S1", "https://example.org", "web")])
    result = documents.merge_document_dossier(doc, web)
    assert len(result.facts) == 1 and result.facts[0].source_title == "base.md"
    assert result.rejected[0]["reason"] == "prioridade documental"


@pytest.mark.parametrize("brief,theme", [
    ("Ciências para público infantil", "vibrante"), ("Programação para ensino médio", "vibrante"),
    ("Introdução ao Git", "escuro"), ("Tecnologia de computadores", "escuro"),
    ("Horta e alimentação", "natural"), ("Meio ambiente", "natural"),
    ("História da internet", "editorial"), ("Leitura e humanidades", "editorial"),
    ("TCC SlideDSL para a banca", "claro"), ("Pesquisa de software", "claro"),
    ("Apresentar minhas ideias", "claro"), ("Digitalização de arquivo", "claro"),
])
def test_auto_theme_table(brief, theme):
    assert choose_theme(brief) == theme


class EditModel:
    supports_response_schema = True
    metadata = {"provider": "fixture", "model_requested": "mock"}

    def __init__(self, invalid=False):
        self.calls = []
        self.invalid = invalid

    def generate(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        items = [{"rotulo": "Estrutura", "detalhe": "A gramática limita as estruturas aceitas."},
                 {"rotulo": "Execução", "detalhe": "O compilador posiciona os objetos no slide."}]
        return json.dumps({"slide": {"tipo": "comparacao", "conteudo": {
            "titulo": "Compare os modos de geração",
            "lados": [{"nome": "SLM sozinho", "itens": [] if self.invalid else items},
                      {"nome": "SLM com gramática", "itens": items}], "fontes": [], "notas": ""}}})


def test_refazer_changes_type_and_preserves_other_blocks_byte_for_byte():
    source = SOURCE.replace("\n", "\r\n")
    model = EditModel()
    result = refazer_slide(source, 2, "Vire comparação entre SLM sozinho e SLM com gramática", {}, model)
    before, after = slide_spans(source), slide_spans(result)
    for number in (0, 2):
        assert source[slice(*before[number])].encode() == result[slice(*after[number])].encode()
    assert source[:before[1][0]] == result[:after[1][0]]
    assert source[before[1][1]:] == result[after[1][1]:]
    assert parse_alto(result).slides[1].kind == "comparacao"
    assert len(model.calls) == 1
    assert "Vizinhos" in model.calls[0][1] and "Roteiro" in model.calls[0][1]


def test_refazer_only_one_repair_and_out_of_range_before_model():
    model = EditModel(invalid=True)
    with pytest.raises(Exception):
        refazer_slide(SOURCE, 2, "Compare", {}, model, repair_max=8)
    assert len(model.calls) == 2
    with pytest.raises(ValueError):
        refazer_slide(SOURCE, 20, "Compare", {}, model)
    assert len(model.calls) == 2


def test_zero_cost_move_delete_theme_and_full_export(tmp_path):
    themed = ajustar_alto(SOURCE, tema="editorial")
    assert themed.replace("tema editorial", "tema claro") == SOURCE
    moved = ajustar_alto(SOURCE, numero=2, mover_para=3)
    assert parse_alto(moved).slides[2].title == parse_alto(SOURCE).slides[1].title
    deleted = ajustar_alto(moved, numero=3, excluir=True)
    assert len(parse_alto(deleted).slides) == 2
    export_edit(themed, tmp_path)
    assert (tmp_path / "apresentacao.pptx").is_file()
    assert (tmp_path / "contato.png").is_file()


@pytest.mark.parametrize("items", [False, True])
def test_unresolved_image_has_cards_or_typographic_statement(items):
    source = 'deck "Horta" { imagem { titulo "Cultive perto da janela" buscar "balcony garden" legenda "A luz orienta o cultivo" '
    if items:
        source += 'item "Luz direta" "Observe a incidência de luz antes de escolher a planta." item "Água no vaso" "Confira a umidade da terra antes de regar novamente." '
    built = build_alto(source + "} }")
    assert built.success(), built.report()
    slide = built.validation.ir.slides[0]
    if items:
        assert any("card" in e.id for e in slide.elements)
    else:
        assert any(e.font_size and e.font_size >= 36 and e.role != "titulo" for e in slide.elements)


def test_commons_categories_and_description_approve_relevant_photo():
    item = dict(title="IMG_0001.jpg", description="Vegetable beds on an apartment balcony",
                categories=["Category:Balcony gardens"], query="balcony garden",
                lexical_score=1, width=1200, height=800, license_url="https://creativecommons.org/licenses/by/4.0/")
    assert media.photographic_candidate(item)
    assert not media.photographic_candidate({**item, "title": "Speaker at garden conference",
                                             "categories": ["Category:People", "Category:Portraits"]})
    assert not media.photographic_candidate({**item, "description": "Street with motorcycles", "categories": []})


def test_broad_fallback_cannot_replace_central_subject():
    item = dict(title="Conference with Git developers", description="Speaker on stage", categories=["People"],
                query="git", central_query="git repository computer", lexical_score=1,
                width=1200, height=800, license_url="https://creativecommons.org/licenses/by/4.0/")
    assert not media.photographic_candidate(item)


@pytest.mark.parametrize("title", ["Code for Africa presentation at Wikimania 2025.jpg",
                                   "John Smith Git.jpg", "Technology conference speaker"])
def test_event_and_named_person_veto_even_with_high_lexical_score(title):
    item = dict(title=title, description="Code and software presentation", query="presentation code editor",
                lexical_score=1, width=1280, height=800,
                license_url="https://creativecommons.org/licenses/by/4.0/")
    assert not media.photographic_candidate(item)


def test_narrative_retrieval_precedes_cli_boilerplate(local_docs):
    text = ('## Operação\n\n```powershell\n.\\.venv\\Scripts\\slidedsl.exe --out output/SlideDSL\n```\n\n'
            '## Resumo\n\nSlideDSL é um projeto que combina modelos pequenos e gramática formal para criar apresentações editáveis.')
    doc = documents.add_document("projeto.md", text.encode())
    dossier = documents.dossier_from_documents([doc["id"]], "SlideDSL")
    assert dossier.sources[0].text.startswith("SlideDSL é um projeto")


def test_caption_number_without_fact_is_warned():
    from slidedsl.alto import AltoSlide
    from slidedsl.alto_generation import check_slide

    diagnostics = check_slide(AltoSlide(kind="imagem", title="Evidência", image_query="garden",
                                       caption="O projeto atingiu 99% de qualidade."), {})
    assert any(d.code == "A012" and d.evidence["path"].endswith("caption") for d in diagnostics)


def test_commons_without_description_cannot_approve_a_diagram_as_photo():
    item = dict(provider="commons", title="Devices connected to Switch.JPG", description="",
                categories=["Computer networks", "Network architecture"], query="connected computers network",
                lexical_score=1, width=1200, height=800,
                license_url="https://creativecommons.org/licenses/by/4.0/")
    assert not media.photographic_candidate(item)


def test_api_document_ids_validate_before_queue(local_docs):
    client = TestClient(app)
    response = client.post("/api/criar", json={"pedido": "SlideDSL", "model": "mock",
                                               "documentos": ["not-an-id"]})
    assert response.status_code == 422


def test_persisted_edit_undo_keeps_usage_after_reload(tmp_path, monkeypatch):
    from slidedsl import alto_jobs

    monkeypatch.setattr(alto_jobs, "project_root", lambda: tmp_path)
    monkeypatch.setattr(alto_jobs, "jobs", {})
    id = "a" * 32
    out = alto_jobs.folder(id)
    out.mkdir(parents=True)
    built = build_alto(SOURCE)
    original = dict(alto=SOURCE, source=built.dsl, ir=built.validation.ir.model_dump(mode="json"),
                    folder="outputs/fixture", report={"valid": True, "calls": 0})
    job = dict(id=id, state="completed", result=original, payload={"provider": "fixture"}, usage=None)
    alto_jobs._persist(job)
    first = alto_jobs.edit_job(id, {"acao": "ajustar", "slide": 1, "tema": "natural"})
    assert first["history"] and first["result"]["report"]["theme"] == "natural"
    alto_jobs.jobs.clear()
    restored = alto_jobs.edit_job(id, {"acao": "desfazer", "slide": 1})
    assert restored["result"]["alto"] == SOURCE and not restored["history"]
    assert len(list((out / "versoes").glob("*/anterior.json"))) == 1


def test_failed_edit_is_charged_and_original_is_preserved(tmp_path, monkeypatch):
    from slidedsl import alto_jobs

    monkeypatch.setattr(alto_jobs, "project_root", lambda: tmp_path)
    monkeypatch.setattr(alto_jobs, "jobs", {})
    class Failed(EditModel):
        def generate(self, *args, **kwargs):
            raise ModelError("Falha simulada")
    monkeypatch.setattr(alto_jobs, "_model", lambda _: Failed())
    id = "b" * 32
    job = dict(id=id, state="completed", result={"alto": SOURCE, "report": {}}, payload={}, usage=None)
    alto_jobs._persist(job)
    with pytest.raises(ModelError):
        alto_jobs.edit_job(id, {"acao": "refazer", "slide": 2, "instrucao": "Compare"})
    saved = alto_jobs.read_job(id)
    assert saved["result"]["alto"] == SOURCE
    assert saved["usage"]["calls"] == saved["usage"]["unknown_usage_calls"] == 1
    assert saved["usage"]["cost_usd"] is None and not saved["editing"]
