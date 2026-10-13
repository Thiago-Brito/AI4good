"""SlideDSL Alto: GLC, validação, layouts, extensões 1.1, GBNF, pesquisa e geração."""

import json
import zipfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from slidedsl.alto import AltoDeck, parse_alto, print_alto, validate_alto
from slidedsl.alto_compile import build_alto, compile_alto
from slidedsl.alto_generation import (
    check_slide,
    create_presentation,
    generate_alto,
    json_to_slide,
    outline_schema,
    score_slide,
    slide_schema,
    translate_path,
)
from slidedsl.cli import main
from slidedsl.diagnostics import DSLException
from slidedsl.gbnf import GBNFMatcher, alto_gbnf, low_level_gbnf
from slidedsl.ir import semantic_snapshot
from slidedsl.models.llamacpp_model import LlamaCppTextModel
from slidedsl.parser import parse
from slidedsl.research import Dossier, Fact, html_to_text, passages, research, verify_fact
from slidedsl.semantic import analyze, validate_ir
from slidedsl.serializer import to_dsl

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples/alto").glob("*.slda"))


def strip_positions(deck):
    data = deck.model_dump()
    for s in data["slides"]:
        s.pop("line"), s.pop("column")
    return data


# --------------------------------------------------------------------- GLC alto


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_examples_parse_print_roundtrip_and_compile_strict(path, tmp_path):
    deck = parse_alto(path.read_text("utf-8"))
    assert strip_positions(parse_alto(print_alto(deck))) == strip_positions(deck)
    result, info = compile_alto(path.read_text("utf-8"), tmp_path / "x.pptx", strict=True)
    relevant = [d for d in result.all_diagnostics if d.severity != "INFORMAÇÃO"]
    assert relevant == []
    assert info["inspection"]["slide_count"] == len(deck.slides)


def test_all_slide_kinds_are_covered_by_examples():
    from slidedsl.alto import SLIDE_KINDS

    kinds = {s.kind for p in EXAMPLES for s in parse_alto(p.read_text("utf-8")).slides}
    assert kinds == set(SLIDE_KINDS)


def test_pptx_keeps_bold_alignment_rounded_shapes_and_notes(tmp_path):
    compile_alto(
        (ROOT / "examples/alto/microsservicos.slda").read_text("utf-8"), tmp_path / "m.pptx"
    )
    with zipfile.ZipFile(tmp_path / "m.pptx") as z:
        slide = z.read("ppt/slides/slide2.xml").decode()
        notes = [n for n in z.namelist() if n.startswith("ppt/notesSlides/notesSlide")]
        note_text = "".join(z.read(n).decode() for n in notes)
    assert 'b="1"' in slide and 'algn="ctr"' in slide and "roundRect" in slide
    assert "Fontes:" in note_text


def test_syntax_error_has_line_and_column():
    with pytest.raises(DSLException) as exc:
        parse_alto('deck "x" {\n  topicos {\n    titulo 3\n  }\n}')
    d = exc.value.diagnostics[0]
    assert d.code == "P001" and d.line == 3


def test_limits_lengths_unknown_facts_and_invented_numbers():
    deck = parse_alto(
        'deck "x" { topicos { titulo "T" item "a" "Facilita tudo." fontes F9 }'
        ' numeros { titulo "Dados" valor "73%" "das empresas usam" fontes F1 } }'
    )
    facts = {"F1": {"claim": "Pesquisa com 500 empresas", "quote": "500 empresas responderam"}}
    codes = {d.code for d in validate_alto(deck, facts)}
    assert {"A003", "A006", "A007"} <= codes
    long = parse_alto(
        'deck "x" { topicos { titulo "' + "x" * 90 + '" item "a" "b" item "c" "d" } }'
    )
    assert any(d.code == "A005" for d in validate_alto(long))


def test_layout_reports_overflow_with_field_path():
    text = " ".join(["palavra"] * 60)
    deck = parse_alto(
        f'deck "x" {{ comparacao {{ titulo "T" lado "A" {{ item "a" "{text[:78]}" item "b" "c d e f" }}'
        f' lado "B" {{ item "a" "{text[:78]}" item "b" "c d e f" item "c" "{text[:78]}"'
        f' item "d" "{text[:78]}" }} }} }}'
    )
    result = build_alto(deck)
    paths = [d.evidence["path"] for d in result.diagnostics if d.code == "A010"]
    assert paths and all(p.startswith("slides.0.sides") for p in paths)


def test_dark_theme_compiles_without_contrast_warnings():
    source = (ROOT / "examples/alto/microsservicos.slda").read_text("utf-8")
    result = build_alto(source.replace("tema claro", "tema escuro"))
    assert result.success(strict=True)
    assert not [d for d in result.all_diagnostics if d.code == "D002" and d.severity == "AVISO"]


# ------------------------------------------------------------- extensões 1.1


def test_low_level_style_extensions_roundtrip(compile_scene, root):
    d = compile_scene(
        "adicionar retangulo id card em (80,100) tamanho (300,200) cor primaria arredondado\n"
        'adicionar texto id t "Olá" em (100,120) tamanho (260,60) fonte 24 cor #FFFFFF '
        'familia "Arial" negrito alinhado centro\nnotas "Fala do apresentador"'
    )
    elements = {e.id: e for e in d.slides[0].elements}
    assert elements["card"].rounded and elements["t"].bold and elements["t"].align == "center"
    assert d.slides[0].notes == "Fala do apresentador"
    assert semantic_snapshot(analyze(parse(to_dsl(d)), root)) == semantic_snapshot(d)


def test_validate_ir_rejects_text_style_on_shapes(compile_scene, root):
    d = compile_scene("adicionar retangulo id a em (80,100) tamanho (100,60) cor primaria")
    d.slides[0].elements[0].bold = True
    assert any(x.code == "S006" for x in validate_ir(d, root))


# ------------------------------------------------------------------------ GBNF


def test_gbnf_accepts_examples_and_rejects_invalid_programs():
    matcher = GBNFMatcher(alto_gbnf())
    for path in EXAMPLES:
        source = "\n".join(
            line
            for line in path.read_text("utf-8").splitlines()
            if not line.strip().startswith("//")
        )
        assert matcher.accepts(source), path.name
    assert not matcher.accepts('deck "x" { topicos { titulo 3 } }')
    assert not matcher.accepts('deck "x" { slide 1 { } }')


def test_gbnf_per_slide_rule_and_low_level_grammar():
    deck = parse_alto((ROOT / "examples/alto/catalogo.slda").read_text("utf-8"))
    from slidedsl.alto import print_slide

    for slide in deck.slides:
        assert GBNFMatcher(alto_gbnf(slide.kind)).accepts(print_slide(slide, ""))
    low = GBNFMatcher(low_level_gbnf())
    for path in (ROOT / "examples").glob("*.sld"):
        assert low.accepts(path.read_text("utf-8")), path.name
    assert "::=" in alto_gbnf() and "root ::=" in alto_gbnf()


def test_llamacpp_sends_grammar():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        )

    model = LlamaCppTextModel(client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert model.generate("s", "u", grammar='root ::= "a"', seed=1) == "ok"
    assert seen["grammar"] == 'root ::= "a"' and seen["seed"] == 1


# -------------------------------------------------------------------- pesquisa

TEXT = (
    "Microsserviços são uma abordagem em que a aplicação é composta por serviços pequenos. "
    "O termo foi popularizado em 2014 por James Lewis e Martin Fowler.\n\n"
    "Em 2023, a equipe do Prime Video reduziu em 90% o custo de infraestrutura ao reunir "
    "um serviço de monitoramento em um único processo."
)


def wiki_fetcher(url, **kw):
    query = parse_qs(urlsplit(url).query)
    if query.get("list") == ["search"]:
        body = {"query": {"search": [{"title": "Microsserviços", "snippet": "<b>x</b>"}]}}
    else:
        body = {"query": {"pages": {"1": {"extract": TEXT}}}}
    return json.dumps(body).encode(), "application/json"


class ExtractModel:
    def generate(self, system, user, temperature=0, seed=None, response_schema=None):
        if "consultas" in json.dumps(response_schema):
            return json.dumps({"consultas": ["microsserviços", "microsserviços prime video"]})
        return json.dumps(
            {
                "fatos": [
                    {
                        "afirmacao": "Prime Video cortou 90% do custo ao voltar a um processo único",
                        "tipo": "numero",
                        "valor": "90%",
                        "trecho": "Em 2023, a equipe do Prime Video reduziu em 90% o custo de infraestrutura",
                    },
                    {
                        "afirmacao": "A Netflix tem 700 microsserviços",
                        "tipo": "numero",
                        "valor": "700",
                        "trecho": "A Netflix tem 700 microsserviços.",
                    },
                ]
            }
        )


def test_research_keeps_only_facts_anchored_in_the_page(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))
    dossier = research(
        "Microsserviços",
        model=ExtractModel(),
        provider="wikipedia",
        langs=("pt",),
        fetcher=wiki_fetcher,
    )
    assert [f.value for f in dossier.facts] == ["90%"]
    assert dossier.facts[0].url == "https://pt.wikipedia.org/wiki/Microsservi%C3%A7os"
    assert dossier.rejected[0]["reason"].startswith("trecho não encontrado")
    dossier.save(tmp_path / "d.json")
    assert Dossier.load(tmp_path / "d.json").fact_map().keys() == {"F1"}
    # Cache permite repetir offline.
    offline = research(
        "Microsserviços",
        model=ExtractModel(),
        provider="wikipedia",
        langs=("pt",),
        fetcher=lambda *a, **k: 1 / 0,
        offline=True,
    )
    assert len(offline.facts) == 1


def test_research_without_model_uses_extractive_sentences(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))
    dossier = research("Microsserviços", provider="wikipedia", langs=("pt",), fetcher=wiki_fetcher)
    assert dossier.facts and all(f.quote in TEXT for f in dossier.facts)


def test_fact_verification_rules_and_html_extraction():
    passage = "Em 2016 a Netflix concluiu a migração para a nuvem."
    ok = {"afirmacao": "A Netflix concluiu a migração para a nuvem em 2016", "valor": "2016",
          "trecho": passage}
    assert verify_fact(ok, passage) is None
    assert "valor" in verify_fact({**ok, "valor": "2018"}, passage)
    assert "número" in verify_fact({**ok, "afirmacao": "A Netflix começou a migração em 2010"},
                                   passage)
    assert "incompleta" in verify_fact({**ok, "afirmacao": "Plataforma Observatório Sebra"},
                                       passage)
    assert "relevante" in verify_fact({**ok, "relevancia": "baixa"}, passage)
    cut = {**ok, "trecho": "Em 2016 a Netflix concluiu a migração..."}
    assert verify_fact(cut, passage + " Em 2016 a Netflix concluiu a migração...")
    quote_passage = 'Segundo Martin Fowler, "monolito primeiro é uma boa estratégia".'
    quote = {"afirmacao": "Martin Fowler defende começar com um monolito", "tipo": "citacao",
             "valor": "", "trecho": "monolito primeiro é uma boa estratégia"}
    unattributed = {**quote, "autor": "Fulano"}
    assert verify_fact(unattributed, quote_passage) is None
    assert unattributed["tipo"] == "definicao"  # vira fato comum, não citação
    attributed = {**quote, "autor": "Martin Fowler"}
    assert verify_fact(attributed, quote_passage) is None and attributed["tipo"] == "citacao"
    off_topic = {**ok, "afirmacao": "A Netflix concluiu a migração para a nuvem em 2016"}
    assert "fora do assunto" in verify_fact(off_topic, passage, ["monolito", "microsserviços"])
    assert verify_fact(dict(ok), passage, ["netflix"]) is None
    from slidedsl.research import decode_body

    assert decode_body("ação".encode("cp1252")) == "ação"
    title, text = html_to_text(
        "<html><title>T</title><nav>menu menu menu menu menu menu menu menu menu</nav>"
        "<p>" + "Conteúdo principal com informação útil. " * 3 + "</p><script>x()</script></html>"
    )
    assert title == "T" and "Conteúdo principal" in text and "menu" not in text
    assert all(len(p) <= 1000 for p in passages(TEXT * 10))


# -------------------------------------------------------------------- geração

FACTS = {
    "F1": {
        "id": "F1",
        "claim": "Prime Video reduziu 90% do custo de infraestrutura",
        "kind": "numero",
        "value": "90%",
        "quote": "reduced infrastructure cost by over 90%",
        "source_id": "S1",
        "url": "https://www.primevideotech.com/a",
        "source_title": "Prime",
    },
    "F2": {
        "id": "F2",
        "claim": "Equipes da Amazon se comunicam por serviços",
        "kind": "exemplo",
        "value": "",
        "quote": "teams communicate through service interfaces",
        "source_id": "S2",
        "url": "https://example.org/b",
        "source_title": "Exemplo",
    },
}
OUTLINE = {
    "titulo": "Microsserviços na prática",
    "slides": [
        {
            "tipo": "capa",
            "mensagem": "Quando microsserviços compensam",
            "objetivo": "abrir",
            "fatos": [],
        },
        {
            "tipo": "numeros",
            "mensagem": "Voltar ao monolito cortou custos",
            "objetivo": "dado",
            "fatos": ["F1"],
        },
        {
            "tipo": "topicos",
            "mensagem": "Três sinais de que vale dividir",
            "objetivo": "exemplos",
            "fatos": ["F2"],
        },
        {
            "tipo": "capa",
            "mensagem": "Divida quando a dor for real",
            "objetivo": "fechar",
            "fatos": [],
        },
    ],
}
SLIDES = {
    "capa": {
        "titulo": "Quando microsserviços compensam",
        "subtitulo": "Casos reais",
        "autor": "",
        "notas": "",
    },
    "numeros": {
        "titulo": "Voltar ao monolito cortou 90% do custo",
        "valores": [{"valor": "90%", "legenda": "redução de custo no Prime Video"}],
        "fontes": ["F1"],
        "notas": "",
    },
    "topicos": {
        "titulo": "Três sinais de que vale dividir",
        "itens": [
            {
                "rotulo": "Escala desigual",
                "detalhe": "Na Black Friday só o serviço de pagamentos precisa de dez vezes mais réplicas.",
            },
            {
                "rotulo": "Equipes independentes",
                "detalhe": "Times da Amazon publicam serviços sem coordenar implantações entre si.",
            },
        ],
        "fontes": ["F2"],
        "notas": "Cada sinal vem com um exemplo concreto do mercado.",
    },
    "conclusao": {
        "titulo": "Divida quando a dor for real",
        "itens": [
            {
                "rotulo": "Comece modular",
                "detalhe": "Fronteiras claras dentro de um único processo custam pouco e ajudam depois.",
            },
            {
                "rotulo": "Meça o custo",
                "detalhe": "Some rede, observabilidade e plantão antes de criar um novo serviço.",
            },
        ],
        "fontes": [],
        "notas": "",
    },
}


class FakeSLM:
    supports_grammar = True
    metadata = {"provider": "fake"}

    def __init__(self, text=False, broken=False, topics=None):
        self.text, self.broken, self.calls = text, broken, []
        self.topics = topics or []

    def generate(self, system, user, temperature=0, seed=None, response_schema=None, grammar=None):
        self.calls.append({"user": user, "schema": response_schema, "grammar": grammar})
        if "roteirista" in system:
            return json.dumps(OUTLINE, ensure_ascii=False)
        if "confere se frases" in system:
            n = response_schema["properties"]["avaliacoes"]["minItems"]
            verdicts = [{"frase": k + 1, "veredito": "sustentada", "motivo": "", "correcao": ""}
                        for k in range(n)]
            return json.dumps({"avaliacoes": verdicts})
        if "Liste os tópicos" in system:
            return json.dumps({"topicos": self.topics})
        if "planeja pesquisas" in system:
            return json.dumps({"consultas": ["microsserviços", "monolito"]})
        if "extrai fatos" in system:
            return json.dumps({"fatos": []})
        import re

        kind = re.search(r"\(tipo (\w+)\)", user).group(1)
        data = json.loads(json.dumps(SLIDES[kind]))
        if self.broken and kind == "topicos" and "Problemas encontrados" not in user:
            data["itens"] = data["itens"][:1]
        if self.text:
            from slidedsl.alto import print_slide

            return "```\n" + print_slide(json_to_slide(kind, data), "") + "\n```"
        return json.dumps(data, ensure_ascii=False)


@pytest.mark.parametrize("mode", ["json", "gramatica", "direto"])
def test_generation_modes_repair_and_fix_outline(mode):
    model = FakeSLM(text=mode != "json", broken=True)
    result = generate_alto("Microsserviços", model, facts=FACTS, n_slides=4, mode=mode)
    kinds = [s.kind for s in result.deck.slides]
    assert kinds == ["capa", "numeros", "topicos", "conclusao"]  # última vira conclusão
    repaired = [c for c in result.candidates if c["slide"] == 3][0]
    assert repaired["attempts"] == 2
    assert build_alto(result.deck, FACTS).success(strict=True)
    if mode == "gramatica":
        slide_calls = [c for c in model.calls if "(tipo " in c["user"]]
        assert slide_calls and all(c["grammar"] for c in slide_calls)
        assert any("topicos ::=" in c["grammar"] for c in slide_calls)


def test_gramatica_mode_requires_grammar_provider():
    class NoGrammar(FakeSLM):
        supports_grammar = False

    with pytest.raises(ValueError):
        generate_alto("x", NoGrammar(), mode="gramatica")


def test_schemas_offer_only_real_facts_and_hide_data_slides_without_research():
    schema = outline_schema(5, ["capa", "topicos", "conclusao"], [])
    assert "fatos" not in schema["properties"]["slides"]["items"]["properties"]
    model = FakeSLM()
    result = generate_alto("x", model, facts={}, n_slides=4)  # roteiro pede numeros sem fatos
    assert "numeros" not in [s.kind for s in result.deck.slides]
    roteiro = model.calls[0]["schema"]["properties"]["slides"]["items"]["properties"]["tipo"]
    assert "numeros" not in roteiro["enum"] and "grafico" not in roteiro["enum"]
    assert slide_schema("numeros", ["F1"])["properties"]["fontes"]["items"]["enum"] == ["F1"]


def test_score_prefers_concrete_cited_content():
    concrete = json_to_slide("topicos", SLIDES["topicos"])
    vague = json_to_slide(
        "topicos",
        {
            "titulo": "Vantagens",
            "itens": [
                {"rotulo": "Escala", "detalhe": "Facilita a escala."},
                {"rotulo": "Manutenção", "detalhe": "Melhora a manutenção."},
            ],
        },
    )
    assert score_slide(concrete, check_slide(concrete, FACTS), FACTS) > score_slide(
        vague, check_slide(vague, FACTS), FACTS
    )
    assert translate_path("slides.0.items.1.detail") == "itens[1].detalhe"


def test_best_of_n_and_audit_files(tmp_path):
    dossier = Dossier(topic="x", facts=[Fact(**f) for f in FACTS.values()])
    report = create_presentation(
        "Microsserviços",
        tmp_path / "run",
        FakeSLM(),
        dossier=dossier,
        n_slides=4,
        candidates=2,
        research_provider=None,
    )
    assert report["valid"] and report["inspection"]["slide_count"] == 4
    names = {p.name for p in (tmp_path / "run").iterdir()}
    assert {
        "apresentacao.pptx",
        "apresentacao.slda",
        "apresentacao.sld",
        "chamadas.jsonl",
        "candidatos.json",
        "roteiro.json",
        "dossie.json",
        "previa.png",
    } <= names
    candidates = json.loads((tmp_path / "run/candidatos.json").read_text("utf-8"))
    assert len(candidates) == 8


def test_cli_alto_commands(tmp_path):
    example = str(ROOT / "examples/alto/microsservicos.slda")
    assert main(["alto-validate", example, "--strict"]) == 0
    assert main(["alto-compile", example, "--out", str(tmp_path / "a.pptx")]) == 0
    assert main(["alto-dsl", example, "--out", str(tmp_path / "a.sld")]) == 0
    assert main(["validate", str(tmp_path / "a.sld"), "--strict"]) == 0
    assert main(["gbnf", "--out", str(tmp_path / "g.gbnf"), "--regra", "etapas"]) == 0
    assert main(["previa", example, "--out", str(tmp_path / "p")]) == 0
    assert (tmp_path / "p/previa.png").is_file()


# ------------------------------------------------------------- API do editor


def test_api_opens_slda_in_editor():
    from fastapi.testclient import TestClient

    from slidedsl.server import app

    client = TestClient(app)
    source = (ROOT / "examples/alto/catalogo.slda").read_text("utf-8")
    data = client.post("/api/alto/parse", json={"source": source}).json()
    assert data["source"].startswith("apresentacao ") and len(data["ir"]["slides"]) == 7
    bad = client.post("/api/alto/parse", json={"source": 'deck "x" { topicos { } }'})
    assert bad.status_code == 422


def test_api_criar_job_loads_result_into_editor(monkeypatch, tmp_path):
    import time

    from fastapi.testclient import TestClient

    from slidedsl import alto_jobs
    from slidedsl.server import app

    class Available(FakeSLM):
        def available(self):
            return True, "teste"

    monkeypatch.setattr(alto_jobs, "project_root", lambda: tmp_path)
    monkeypatch.setattr(alto_jobs, "_model", lambda payload: Available())
    client = TestClient(app)
    payload = {"pedido": "Microsserviços", "model": "fake", "slides": 4, "buscador": "nenhum"}
    assert client.post("/api/criar", json={**payload, "modo": "gramatica"}).status_code == 422
    job = client.post("/api/criar", json=payload).json()
    for _ in range(100):
        job = client.get("/api/criar/" + job["id"]).json()
        if job["state"] in {"completed", "failed"}:
            break
        time.sleep(0.1)
    assert job["state"] == "completed", job["error"]
    result = job["result"]
    assert result["ir"]["slides"] and result["source"].startswith("apresentacao")
    assert result["alto"].startswith("deck ")
    assert job["events"] and (tmp_path / "outputs/criar" / job["id"] / "job.json").is_file()


def test_research_without_facts_stops_with_actionable_message(tmp_path, monkeypatch):
    from slidedsl.alto_generation import NoFactsError

    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))

    def forbidden(url, **kw):
        raise ValueError("HTTP 403 de pt.wikipedia.org: Please respect our robot policy")

    with pytest.raises(NoFactsError, match="contato"):
        create_presentation("Microsserviços", tmp_path / "run", FakeSLM(), n_slides=4,
                            research_provider="wikipedia", langs=("pt",), fetcher=forbidden)
    assert json.loads((tmp_path / "run/relatorio.json").read_text("utf-8"))["errors"]


def test_contact_goes_into_user_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))
    seen = []

    def fetch(url, **kw):
        seen.append(kw.get("headers", {}).get("User-Agent", ""))
        return wiki_fetcher(url, **kw)

    research("Microsserviços", provider="wikipedia", langs=("pt",), fetcher=fetch,
             contact="pessoa@example.org")
    assert seen and all("pessoa@example.org" in ua for ua in seen)


def test_numbers_without_facts_are_flagged_and_long_titles_shrink():
    deck = parse_alto('deck "x" { etapas { titulo "Transição leva 3 a 6 meses" '
                      'item "a" "b c d e" item "c" "d e f g" } }')
    assert any(d.code == "A012" for d in validate_alto(deck, {}))
    long_title = "Microsserviços permitem lançar funcionalidades novas sem recriar o sistema"
    result = build_alto(parse_alto(f'deck "x" {{ topicos {{ titulo "{long_title}" '
                                   'item "a" "b c d e" item "c" "d e f g" } }'))
    assert result.success() and not [d for d in result.diagnostics if d.code == "A010"]


def test_searxng_results_are_read_and_verified(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("SLIDEDSL_SEARXNG_URL", "http://127.0.0.1:8888")
    page = "<html><title>Blog</title><p>" + TEXT.replace("\n\n", "</p><p>") + "</p></html>"

    def fetch(url, **kw):
        if url.startswith("http://127.0.0.1:8888/search"):
            body = {"results": [{"title": "Blog", "url": "https://blog.example.org/a",
                                 "content": "resumo"}]}
            return json.dumps(body).encode(), "application/json"
        return page.encode(), "text/html"

    dossier = research("Microsserviços", provider="searxng", fetcher=fetch)
    assert dossier.sources[0].url == "https://blog.example.org/a"
    assert dossier.facts and all(f.quote in TEXT for f in dossier.facts)


# ------------------------------------------------- qualidade: rodada 12/10 (noite)


def test_number_tokens_compare_whole_numbers():
    from slidedsl.alto import number_tokens

    assert number_tokens("de 15 para mais de 1.300") == {"15", "1300"}
    assert number_tokens("20 mil empresas") == {"20", "20000"}
    assert number_tokens("como mostra F5") == set()
    deck = parse_alto('deck "x" { topicos { titulo "Equipes com menos de 5 membros" '
                      'item "a" "b c d e" item "c" "d e f g" fontes F1 } }')
    facts = {"F1": {"claim": "Pesquisa com 500 empresas", "quote": "500 empresas"}}
    assert any(d.code == "A012" for d in validate_alto(deck, facts))  # "5" ≠ "500"


def test_truncated_field_is_detected_and_repaired():
    class Truncating(FakeSLM):
        def generate(self, system, user, **kw):
            raw = super().generate(system, user, **kw)
            if "(tipo topicos)" in user and "Problemas encontrados" not in user:
                data = json.loads(raw)
                limit = kw["response_schema"]["properties"]["titulo"]["maxLength"]
                data["titulo"] = ("Três sinais de que vale dividir o sistema " * 9)[:limit]
                return json.dumps(data, ensure_ascii=False)
            return raw

    result = generate_alto("Microsserviços", Truncating(), facts=FACTS, n_slides=4)
    topicos = [c for c in result.candidates if c["slide"] == 3][0]
    assert topicos["attempts"] == 2
    assert result.deck.slides[2].title == "Três sinais de que vale dividir"


def test_support_check_repairs_or_corrects_distorted_claims():
    class Judge(FakeSLM):
        rounds = 0

        def generate(self, system, user, **kw):
            if "confere se frases" in system and "Voltar ao monolito" in user and "cortou" in user:
                n = kw["response_schema"]["properties"]["avaliacoes"]["minItems"]
                self.rounds += 1
                first = {"frase": 1, "veredito": "parcial",
                         "motivo": "o fato fala de infraestrutura do Prime Video",
                         "correcao": "Prime Video reduziu 90% do custo de infraestrutura"}
                rest = [{"frase": k + 1, "veredito": "sustentada", "motivo": "", "correcao": ""}
                        for k in range(1, n)]
                return json.dumps({"avaliacoes": [first, *rest]}, ensure_ascii=False)
            return super().generate(system, user, **kw)

    model = Judge()
    result = generate_alto("Microsserviços", model, facts=FACTS, n_slides=4, repair_max=1)
    numeros = result.deck.slides[1]
    assert numeros.title == "Prime Video reduziu 90% do custo de infraestrutura"
    assert any("NÃO sustentam" in c["user"] for c in model.calls)
    assert [x for x in result.support if x["slide"] == 2]


def test_required_topics_reach_outline_and_slides():
    topics = [{"nome": "Latência de rede", "termos": ["latência", "latency"]}]

    class Planner(FakeSLM):
        def generate(self, system, user, **kw):
            if "roteirista" in system:
                self.calls.append({"user": user, "schema": kw.get("response_schema"),
                                   "grammar": None})
                outline = json.loads(json.dumps(OUTLINE))
                if "Faltaram os tópicos" in user:
                    outline["slides"][2]["topicos"] = ["Latência de rede"]
                return json.dumps(outline, ensure_ascii=False)
            return super().generate(system, user, **kw)

    model = Planner(topics=topics)
    request = " ".join(["Explique monolito e microsserviços"] * 4) + " incluindo latência de rede"
    result = generate_alto(request, model, facts=FACTS, n_slides=4, repair_max=0)
    outline_calls = [c for c in model.calls if c["schema"] and "slides" in c["schema"].get(
        "properties", {})]
    assert len(outline_calls) == 2
    assert result.outline["slides"][2]["topicos"] == ["Latência de rede"]
    slide_call = [c for c in model.calls if "(tipo topicos)" in c["user"]][0]
    assert "DEVE tratar" in slide_call["user"]
    assert result.coverage == [{"topico": "Latência de rede", "slides_visiveis": [],
                                "slides_notas": [], "coberto": False}]
    assert any(d.code == "A016" for d in result.diagnostics)


def test_quote_slide_is_built_from_literal_attributed_fact():
    from slidedsl.alto_quality import quote_slide

    facts = {**FACTS, "F3": {"id": "F3", "claim": "Fowler recomenda começar pelo monolito",
                             "kind": "citacao", "value": "", "author": "Martin Fowler",
                             "quote": "Almost all the successful microservice stories have "
                                      "started with a monolith",
                             "url": "https://martinfowler.com/bliki/MonolithFirst.html",
                             "source_title": "MonolithFirst"}}
    slide = quote_slide(facts, ["F3"])
    assert slide.author == "Martin Fowler" and slide.text.startswith("Almost all")
    assert not [d for d in validate_alto(AltoDeck(title="x", slides=[slide]), facts)
                if d.severity == "ERRO"]
    bad = slide.model_copy(update={"author": "F3"})
    assert any(d.code == "A015" for d in validate_alto(AltoDeck(title="x", slides=[bad]), facts))
    assert quote_slide(FACTS, None) is None


def test_lowercase_scenario_detail_is_flagged_and_footer_fits():
    deck = parse_alto('deck "x" { topicos { titulo "Sombra reduz a produção" '
                      'item "Árvores" "uma casa com telhado inclinado em região com chuva" '
                      'item "Prédios" "Um prédio vizinho bloqueia o sol da manhã no telhado." } }')
    assert any(d.code == "A009" and "minúscula" in d.message for d in validate_alto(deck))
    facts = {f"F{k}": {"claim": "x", "quote": "x", "url": f"https://site{k}.example.org/a"}
             for k in range(1, 8)}
    long = parse_alto('deck "x" { topicos { titulo "T" item "a" "Frase completa aqui." '
                      'item "b" "Outra frase completa." fontes F1, F2, F3, F4, F5, F6, F7 } }')
    result = build_alto(long, facts)
    assert not [d for d in result.all_diagnostics if d.code == "D010"]


def test_searxng_is_the_default_and_wikipedia_fallback_is_opt_in(tmp_path, monkeypatch):
    monkeypatch.setenv("SLIDEDSL_RESEARCH_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("SLIDEDSL_SEARXNG_URL", "http://127.0.0.1:8888")
    calls = []

    def fetch(url, **kw):
        calls.append(url)
        if url.startswith("http://127.0.0.1:8888"):
            raise ValueError("SearXNG não respondeu em 30 s")
        return wiki_fetcher(url, **kw)

    from slidedsl.research import provider_auto

    assert provider_auto() == "searxng"
    only = research("Microsserviços", langs=("pt",), fetcher=fetch)
    assert not only.facts and not [c for c in calls if "wikipedia" in c]  # sem fallback
    calls.clear()
    events = []
    dossier = research("Microsserviços", provider="searxng", langs=("pt",), fetcher=fetch,
                       progress=events.append, fallback_wikipedia=True)
    searx_calls = [c for c in calls if c.startswith("http://127.0.0.1:8888")]
    assert len(searx_calls) == 2  # desiste depois de duas falhas seguidas
    assert dossier.facts and dossier.sources[0].provider == "wikipedia"
    assert any("tentando a Wikipedia" in e for e in events)


def test_fact_ids_are_removed_from_visible_text_and_data_slides_need_data():
    from slidedsl.alto_generation import data_kind_supported, strip_fact_ids

    assert strip_fact_ids("Revisa cada mudança, conforme destacado em F2.", ["F2"]) == (
        "Revisa cada mudança."
    )
    assert strip_fact_ids("Carro de F1 usa telemetria", ["F2"]) == "Carro de F1 usa telemetria"
    no_dates = {"F1": {"claim": "Segurança começa no início do ciclo", "quote": "desde o início"}}
    assert not data_kind_supported("linha_do_tempo", no_dates)
    assert not data_kind_supported("numeros", no_dates)
    assert data_kind_supported("numeros", FACTS)
    assert data_kind_supported("topicos", no_dates)


def test_searxng_status_endpoint_reports_missing_instance(monkeypatch):
    from fastapi.testclient import TestClient

    from slidedsl import research as research_module
    from slidedsl.server import app

    monkeypatch.setattr(research_module, "searxng_url", lambda: None)
    data = TestClient(app).get("/api/searxng/status").json()
    assert data["ok"] is False and "iniciar_searxng" in data["message"]
