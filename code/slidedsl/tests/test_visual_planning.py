from copy import deepcopy
import json
import zipfile

from jsonschema import Draft202012Validator, ValidationError
import pytest

from slidedsl.contextual import contextual_schema, generate_contextual
from slidedsl import media
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.pipeline import validate_source
from slidedsl.planning import DeckPlan
from slidedsl.visual_validation import check_visual
from slidedsl.visual_planning import (
    COMPOSED_LAYOUTS,
    constrain_visual_schema,
    normalize_visual_response,
    visual_decoder_schema,
)
from test_evolution import Answers, plan_data


def composed_data(layout):
    data = plan_data()
    slide = data["slides"][0]
    slide.update(
        layout=layout,
        title="A estrutura conecta responsabilidades distintas.",
        footer="",
        decorations=[],
        relations=[],
        media=[],
        sources=[],
    )
    col = {
        "heading": "",
        "items": [
            "Interface: recebe pedidos.",
            "Serviço: executa regras.",
            "Dados: registra resultados.",
        ],
        "group": False,
        "representation": "stack" if layout == "architecture_diagram" else "cards",
    }
    if layout == "takeaway":
        col["items"] = ["Escolha a estrutura adequada ao contexto.", "Considere equipe e escala."]
    slide["columns"] = [col]
    if layout == "comparison_visual":
        col["heading"] = "Camadas"
        col["representation"] = "stack"
        other = deepcopy(col)
        other.update(heading="Microsserviços", representation="services")
        slide["columns"].append(other)
    return data


@pytest.mark.parametrize("layout", sorted(COMPOSED_LAYOUTS))
def test_compositions_export_native_text_shapes_and_safe_spacing(layout, tmp_path):
    plan = DeckPlan.model_validate(composed_data(layout))
    source, mapping, diagnostics = plan_to_dsl(plan)
    assert not diagnostics
    result = validate_source(source)
    assert result.success(strict=True)
    assert not [d for d in check_visual(result.ir) if d["severity"] == "ERRO"]
    body_text = [e.text for e in result.ir.slides[0].elements if e.type == "text"]
    assert all(text in body_text for c in plan.slides[0].columns for text in c.items)
    output = tmp_path / (layout + ".pptx")
    inspection = compile_plan(plan, output, strict=True)["inspection"]
    assert inspection["shape_objects"] >= 1 and inspection["image_objects"] == 0
    if layout in {"architecture_diagram", "comparison_visual", "visual_flow", "visual_sequence"}:
        with zipfile.ZipFile(output) as z:
            assert b"downArrow" in z.read("ppt/slides/slide1.xml")


def test_decoder_binds_content_to_intentions_and_keeps_raw_fields():
    outline = {
        "slides": [
            {
                "intent": "comparison",
                "message": "A estrutura depende do contexto.",
                "subjects": ["Camadas", "Microsserviços"],
                "structures": ["stack", "services"],
            }
        ]
    }
    schema = constrain_visual_schema(contextual_schema(1, [], []), outline)
    decoder = visual_decoder_schema(schema)
    data = composed_data("comparison_visual")
    data["slides"][0]["title"] = outline["slides"][0]["message"]
    slide = data["slides"][0]
    for col in slide["columns"]:
        col["items"] = [{"label": "Interface", "detail": "recebe pedidos"}] * 2
    slide["column_1"], slide["column_2"] = slide.pop("columns")
    slide["vector_flow"] = False
    wire = {"title": data["title"], "theme": data["theme"], "slide_1": slide}
    Draft202012Validator(decoder).validate(wire)
    converted = normalize_visual_response(wire, 1)
    Draft202012Validator(schema).validate(converted)
    assert converted["slides"][0]["columns"][0]["items"][0] == "Interface: recebe pedidos"
    assert "column_1" in wire["slide_1"]  # normalization cannot mutate evidence
    broken = deepcopy(wire)
    broken["slide_1"]["column_1"]["heading"] = "Vantagens"
    with pytest.raises(ValidationError):
        Draft202012Validator(decoder).validate(broken)


@pytest.mark.parametrize("invalid_node", [False, True])
def test_two_stage_mock_generation_records_original_http_content(tmp_path, invalid_node):
    outline = {
        "slides": [
            {
                "intent": "benefits",
                "message": "Separação facilita a evolução.",
                "focus": "Benefícios",
                "reason": "Comparar benefícios em cards.",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    data = composed_data("benefit_cards")
    slide = data["slides"][0]
    slide["title"] = outline["slides"][0]["message"]
    slide["vector_flow"] = False
    slide["columns"][0]["representation"] = "cards"
    slide["columns"][0]["items"] = [
        {"label": "Manutenção", "detail": "isola mudanças"},
        {"label": "Escala", "detail": "separa serviços"},
    ]
    wire = {"title": data["title"], "theme": data["theme"], "slide_1": slide}
    if invalid_node:
        slide["columns"][0]["items"][0]["unexpected"] = "Cannot disappear in normalization"
    adapter = Answers([json.dumps(outline), json.dumps(wire)])
    out = tmp_path / "run"
    report = generate_contextual(
        "unit",
        "C",
        "Crie um slide sobre benefícios",
        out,
        context={"visual_planning": True},
        adapter=adapter,
    )
    assert report["is_mock"] and report["calls"] == 2
    if invalid_node:
        assert not report["compile_success"]
        assert any(d["code"] == "J001" for d in report["diagnostics"])
        assert not (out / "initial/round_0/normalized_response.json").exists()
        assert not (out / "presentation.pptx").exists()
        return
    assert report["compile_success"]
    assert len(adapter.calls) == 2
    http = json.loads((out / "initial/round_0/response.json").read_text("utf-8"))
    assert (out / "initial/round_0/raw.txt").read_bytes() == http["message"]["content"].encode()
    normalized = json.loads((out / "initial/round_0/normalized_response.json").read_text("utf-8"))
    assert normalized["slides"][0]["columns"][0]["items"][0] == "Manutenção: isola mudanças"


def test_provider_selection_falls_back_and_excludes_unreviewed_nasa(monkeypatch):
    attempted = []
    good = {
        "id": "a" * 64,
        "provider": "openverse",
        "lexical_score": 1,
        "width": 900,
        "height": 600,
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
    }

    def search(provider, query, **kw):
        assert query == "moon"
        attempted.append(provider)
        if provider == "nasa":
            return {"results": [{**good, "provider": "nasa", "review_required": True}]}
        if provider == "openverse":
            raise OSError("offline")
        return {"results": [good]}

    monkeypatch.setattr(media, "search_images", search)
    response = media.automatic_search("moon real photo")
    assert attempted == ["nasa", "openverse", "commons"]
    assert response["results"][0] == good
    assert response["providers"][1]["error"] == "offline"
    assert response["original_query"] == "moon real photo" and response["query"] == "moon"


def test_long_content_remains_in_dsl_and_cannot_pass_by_truncation():
    data = composed_data("benefit_cards")
    long = "Conteúdo completo que precisa ser preservado. " * 20
    data["slides"][0]["columns"][0]["items"][0] = long
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert long in source and any(d.code == "L004" for d in diagnostics)


def test_restricted_visual_decoder_keeps_literal_source_constraint():
    outline = {
        "slides": [
            {"intent": "benefits", "message": "Mensagem", "subjects": [], "structures": ["cards"]}
        ]
    }
    chunks = [{"id": "source1", "text": "Primeira frase. Segunda frase."}]
    schema = constrain_visual_schema(
        contextual_schema(1, [], ["source1"], excerpts=chunks), outline, restricted=True
    )
    decoder = visual_decoder_schema(schema, restricted=True)
    item = decoder["properties"]["slide_1"]["properties"]["columns"]["items"]["properties"][
        "items"
    ]["items"]
    assert item["type"] == "string" and "Primeira frase." in item["enum"]
    assert "Mensagem" not in decoder["properties"]["slide_1"]["properties"]["title"]["enum"]


def test_unavailable_image_preserves_content_in_native_fallback(tmp_path):
    outline = {
        "slides": [
            {
                "intent": "image",
                "message": "A Lua orbita a Terra.",
                "focus": "Lua",
                "reason": "Fotografia explicativa.",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    data = composed_data("concept_map")
    slide = data["slides"][0]
    slide.update(
        layout="text_image",
        title=outline["slides"][0]["message"],
        vector_flow=False,
        media=[{"query": "moon", "asset": "", "caption": "Lua"}],
    )
    slide["columns"][0]["representation"] = "cards"
    original = deepcopy(slide["columns"][0]["items"])
    slide["columns"][0]["heading"] = "Explicação preservada"
    slide["columns"][0]["items"] = [
        {"label": item.split(": ")[0], "detail": item.split(": ")[1]} for item in original
    ]
    wire = {"title": data["title"], "theme": data["theme"], "slide_1": slide}
    report = generate_contextual(
        "unit",
        "C",
        "Crie um slide",
        tmp_path / "fallback",
        context={"visual_planning": True, "research": "off"},
        adapter=Answers([json.dumps(outline), json.dumps(wire)]),
    )
    assert report["compile_success"] and not report["image_searches"]
    final = json.loads((tmp_path / "fallback/plan.json").read_text("utf-8"))["slides"][0]
    assert final["layout"] == "concept_map" and final["columns"][0]["items"] == original + ["Lua"]
    assert report["visual_fallbacks"][0]["before"]["media"][0]["caption"] == "Lua"
