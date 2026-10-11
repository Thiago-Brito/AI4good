from copy import deepcopy
import json
import zipfile

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from pydantic import ValidationError as PlanError
import pytest

from slidedsl.contextual import contextual_schema, generate_contextual
from slidedsl.expressive_composition import select_candidate
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.planning import ContentBlock, DeckPlan, plan_schema
from slidedsl.pipeline import validate_source
from slidedsl.visual_planning import (
    constrain_visual_schema,
    normalize_visual_response,
    visual_decoder_schema,
)
from slidedsl.visual_validation import check_visual
from test_visual_planning import composed_data
from test_evolution import Answers


def rich_data(layout="concept_map", count=4, explanation=""):
    data = composed_data(layout)
    slide = data["slides"][0]
    slide.update(expressive=True, composition="auto")
    for col in slide["columns"]:
        nodes = [
            ContentBlock(
                label=f"Parte {i + 1}", detail="Função específica.", explanation=explanation
            )
            for i in range(count)
        ]
        col.update(content=[n.model_dump() for n in nodes], items=[n.full_text() for n in nodes])
    return data


@pytest.mark.parametrize(
    "layout,count",
    [
        ("concept_map", 6),
        ("benefit_cards", 5),
        ("architecture_diagram", 5),
        ("visual_flow", 4),
        ("visual_sequence", 4),
        ("comparison_visual", 3),
        ("visual_cover", 3),
        ("takeaway", 4),
    ],
)
def test_capacity_is_measured_and_all_content_is_readable(layout, count):
    plan = DeckPlan.model_validate(rich_data(layout, count))
    source, mapping, ds = plan_to_dsl(plan)
    assert not ds
    v = validate_source(source)
    assert v.success(strict=True)
    assert not [d for d in check_visual(v.ir, mapping) if d["severity"] == "ERRO"]
    elements = v.ir.slides[0].elements
    assert all(e.font_size >= 22 for e in elements if e.type == "text" and e.role == "corpo")
    for col in plan.slides[0].columns:
        for node in col.content:
            assert node.detail in [e.text for e in elements]


def test_conceptual_explanation_has_distinct_native_objects(tmp_path):
    explanation = "Separar responsabilidades permite testar regras sem depender da interface."
    plan = DeckPlan.model_validate(rich_data(count=2, explanation=explanation))
    out = tmp_path / "native.pptx"
    result = compile_plan(plan, out, strict=True)
    with zipfile.ZipFile(out) as z:
        xml = z.read("ppt/slides/slide1.xml").decode()
    assert explanation in xml and "Função específica." in xml
    assert "_explanation" in result["source"] and "_ref_label" in result["source"]


def test_long_explanation_rejects_capacity_without_cutting_or_small_fonts():
    explanation = "Explicação completa e específica que precisa permanecer inteira. " * 5
    data = rich_data(count=6, explanation=explanation)
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert any(d.code == "L004" for d in ds)
    assert explanation in source
    assert "fonte 18" not in source


def test_same_intention_supports_variants_and_never_changes_stack_order():
    data = rich_data(count=3)
    positions = []
    for mode in ["grid", "row", "vertical"]:
        slide = DeckPlan.model_validate(data).slides[0].model_copy(update={"composition": mode})
        node, _, failures, report = select_candidate(slide, 1, "claro")
        assert not failures and report["chosen"] == mode
        assert len([c for c in node.commands if c.element_type == "text"]) == 7
        positions.append(
            [(c.position.x, c.position.y) for c in node.commands if c.element_type == "rectangle"]
        )
    assert len({tuple(p) for p in positions}) == 3
    stacked = DeckPlan.model_validate(rich_data("architecture_diagram", 4)).slides[0]
    _, _, failures, _ = select_candidate(
        stacked.model_copy(update={"composition": "grid"}), 1, "claro"
    )
    assert any(code == "L007" for code, _, _ in failures)
    independent = stacked.model_copy(deep=True)
    independent.columns[0].representation = "services"
    node, _, failures, _ = select_candidate(independent, 1, "claro")
    assert not failures and not [c for c in node.commands if c.element_type == "arrow"]


@pytest.mark.parametrize(
    "layout", ["visual_cover", "concept_map", "benefit_cards", "takeaway", "comparison_visual"]
)
def test_selected_image_integrates_with_multiple_intentions(layout, monkeypatch):
    from slidedsl import media

    # Use the existing local demo only as an explicitly selected compiler fixture.
    monkeypatch.setattr(media, "resolve_asset", lambda path: {"width": 800, "height": 600})
    data = rich_data(layout, 2)
    slide = data["slides"][0]
    for col in slide["columns"]:
        col["representation"] = "cards"
    slide["media"] = [
        {"asset": "assets/imagem_demo.png", "query": "", "caption": "Imagem selecionada"}
    ] * len(slide["columns"])
    source, mapping, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds
    v = validate_source(source)
    assert v.success(strict=True)
    assert not [d for d in check_visual(v.ir, mapping) if d["severity"] == "ERRO"]
    assert len([e for e in v.ir.slides[0].elements if e.type == "image"]) == len(slide["columns"])


def test_raw_expressive_schema_retains_fields_and_legacy_schema_stays_compatible():
    outline = {
        "slides": [
            {
                "intent": "benefits",
                "message": "Vantagens dependem do contexto.",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    schema = constrain_visual_schema(contextual_schema(1, [], []), outline, expressive=True)
    decoder = visual_decoder_schema(schema)
    data = rich_data("benefit_cards", 5)
    slide = data["slides"][0]
    slide["title"] = outline["slides"][0]["message"]
    slide["vector_flow"] = False
    col = slide["columns"][0]
    col["items"] = col.pop("content")
    wire = {"title": data["title"], "theme": "claro", "slide_1": slide}
    Draft202012Validator(decoder).validate(wire)
    normalized = normalize_visual_response(wire, 1)
    Draft202012Validator(schema).validate(normalized)
    assert len(normalized["slides"][0]["columns"][0]["content"]) == 5
    broken = deepcopy(wire)
    broken["slide_1"]["columns"][0]["items"][0]["coordinates"] = [10, 20]
    with pytest.raises(ValidationError):
        Draft202012Validator(decoder).validate(broken)
    assert "content" not in plan_schema(1)["$defs"]["ColumnPlan"]["properties"]
    assert "ContentBlock" not in plan_schema(1)["$defs"]
    old = DeckPlan.model_validate(composed_data("benefit_cards")).model_dump()
    assert "expressive" not in old["slides"][0] and "content" not in old["slides"][0]["columns"][0]
    normalized["slides"][0]["columns"][0]["items"][0] = "Informação apagada"
    with pytest.raises(PlanError):
        DeckPlan.model_validate(normalized)


def test_expressive_mode_preserves_restricted_literal_contract():
    outline = {
        "slides": [
            {"intent": "concept", "message": "Mensagem", "subjects": [], "structures": ["cards"]}
        ]
    }
    schema = constrain_visual_schema(
        contextual_schema(1, [], ["s1"], excerpts=[{"id": "s1", "text": "Frase literal."}]),
        outline,
        restricted=True,
        expressive=True,
    )
    decoder = visual_decoder_schema(schema, restricted=True)
    props = decoder["properties"]["slide_1"]["properties"]
    assert "expressive" not in props
    assert "Frase literal." in props["columns"]["items"]["properties"]["items"]["items"]["enum"]


def test_two_call_integration_and_evidence(tmp_path):
    outline = {
        "slides": [
            {
                "intent": "benefits",
                "message": "Vantagens dependem do contexto.",
                "focus": "Condições",
                "reason": "Explicar vantagens",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    data = rich_data("benefit_cards", 2, "Exige responsabilidades bem definidas.")
    slide = data["slides"][0]
    slide["title"] = outline["slides"][0]["message"]
    slide["vector_flow"] = False
    col = slide["columns"][0]
    col["items"] = col.pop("content")
    wire = {"title": data["title"], "theme": data["theme"], "slide_1": slide}
    out = tmp_path / "run"
    adapter = Answers([json.dumps(outline), json.dumps(wire)])
    report = generate_contextual(
        "unit",
        "C",
        "Crie um slide sobre vantagens",
        out,
        context={"expressive_planning": True},
        repair_max=0,
        adapter=adapter,
    )
    assert report["compile_success"] and report["calls"] == 2 and report["is_mock"]
    assert report["protocol"] == "expressive-planning-v1"
    assert len(report["composition"]["slides"][0]["candidates"]) == 3
    assert (out / "composition.json").is_file()


def test_multislide_validation_does_not_reject_slide_numbers_above_one():
    data = rich_data(count=2)
    data["slides"] *= 5
    plan = DeckPlan.model_validate(data)
    source, _, ds = plan_to_dsl(plan)
    assert not ds
    result = validate_source(source)
    assert result.success(strict=True) and len(result.ir.slides) == 5
    assert [s.number for s in result.ir.slides] == [1, 2, 3, 4, 5]


def test_requirements_choose_a_matching_variant_and_inspect_emitted_components():
    from slidedsl.requirements import evaluate_requirements

    data = rich_data(count=3)
    criterion = {
        "id": "columns",
        "kind": "columns",
        "slide": 1,
        "minimum": 2,
        "description": "Duas colunas",
    }
    data["refinement"] = {"requirements": [criterion]}
    plan = DeckPlan.model_validate(data)
    node, _, ds, report = select_candidate(plan.slides[0], 1, plan.theme, requirements=[criterion])
    assert not ds and report["chosen"] in {"grid", "row"}
    source, _, ds = plan_to_dsl(plan)
    v = validate_source(source)
    assert evaluate_requirements(v, [criterion])["all_met"]
    for layout, kind in [
        ("benefit_cards", "cards"),
        ("visual_sequence", "sequence"),
        ("visual_flow", "flow"),
    ]:
        source, _, ds = plan_to_dsl(DeckPlan.model_validate(rich_data(layout, 4)))
        assert not ds
        req = {"id": kind, "kind": "component", "slide": 1, "value": kind, "description": kind}
        assert evaluate_requirements(validate_source(source), [req])["all_met"]


def test_local_patch_rebuilds_only_the_derived_text_of_the_affected_column():
    from slidedsl.evolution import apply_patch_response

    data = rich_data(count=2)
    data["slides"].append(deepcopy(data["slides"][0]))
    path = "slides.0.columns.0.content.0.explanation"
    patched = apply_patch_response(
        data, json.dumps({"edits": [{"path": path, "value": "Condição explícita."}]}), [path]
    )
    assert DeckPlan.model_validate(patched)
    assert patched["slides"][1] == data["slides"][1]
    assert (
        patched["slides"][0]["columns"][0]["content"][1]
        == data["slides"][0]["columns"][0]["content"][1]
    )
    assert patched["slides"][0]["columns"][0]["items"][0].endswith("Condição explícita.")


def test_image_count_reduces_schema_capacity_and_unavailable_asset_blocks_export():
    outline = {
        "slides": [
            {
                "intent": "benefits",
                "message": "Benefícios condicionais.",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    schema = constrain_visual_schema(contextual_schema(1, ["image1"], []), outline, expressive=True)
    decoder = visual_decoder_schema(schema)
    data = rich_data("benefit_cards", 4)
    slide = data["slides"][0]
    slide.update(
        title=outline["slides"][0]["message"],
        vector_flow=False,
        media=[{"asset": "image1", "query": "", "caption": ""}],
    )
    col = slide["columns"][0]
    col["items"] = col.pop("content")
    with pytest.raises(ValidationError):
        Draft202012Validator(decoder).validate(
            {"title": data["title"], "theme": data["theme"], "slide_1": slide}
        )
    data = rich_data(count=2)
    data["slides"][0]["media"] = [{"asset": "", "query": "moon", "caption": ""}]
    _, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert any(d.code == "M001" for d in ds)


def test_comparison_measures_long_descriptions_and_footer_before_export():
    data = rich_data("comparison_visual", 2)
    slide = data["slides"][0]
    slide["title"] = "Compare duas estruturas."
    for col in slide["columns"]:
        for node in col["content"]:
            node["detail"] = "Cada serviço é autônomo e pode ser desenvolvido separadamente."
        col["items"] = [ContentBlock.model_validate(n).full_text() for n in col["content"]]
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds
    v = validate_source(source)
    assert v.success(strict=True)
    assert not [d for d in check_visual(v.ir) if d["severity"] == "ERRO"]
    slide["footer"] = "Compare responsabilidades e implantação."
    _, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert any(d.code == "L004" for d in ds)  # Footer consumes capacity, never shrinks text.
    for col in slide["columns"]:
        for node in col["content"]:
            node["detail"] = "Função específica."
        col["items"] = [ContentBlock.model_validate(n).full_text() for n in col["content"]]
    _, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds
    slide["footer"] *= 6
    _, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert any(d.code == "L004" for d in ds)


def test_exact_requirement_remains_measurable_across_rich_text_boxes():
    from slidedsl.requirements import evaluate_requirements

    data = rich_data(count=2, explanation="Depende de responsabilidades claras.")
    requirement = {
        "id": "whole",
        "kind": "text",
        "slide": 1,
        "value": data["slides"][0]["columns"][0]["items"][0],
        "description": "Mensagem integral",
    }
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds
    checks = evaluate_requirements(validate_source(source), [requirement])
    assert checks["all_met"] and len(checks["details"][0]["elements"]) == 3


@pytest.mark.parametrize("layout", ["visual_cover", "benefit_cards", "takeaway"])
def test_stack_metadata_does_not_invent_connections_in_non_diagram_components(layout):
    data = rich_data(layout, 2)
    data["slides"][0]["columns"][0]["representation"] = "stack"
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds and "adicionar seta" not in source


def test_word_measurement_has_conservative_offline_fallback(monkeypatch):
    from slidedsl import text_metrics

    monkeypatch.setattr(text_metrics, "local_font", lambda *args: None)
    assert text_metrics.text_width("Escalabilidade", 24, True) > 164 - 16
    data = rich_data("comparison_visual", 2)
    for col in data["slides"][0]["columns"]:
        col["content"][0]["label"] = "Escalabilidade"
        col["items"] = [ContentBlock.model_validate(n).full_text() for n in col["content"]]
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert not ds
    v = validate_source(source)
    assert v.success(strict=True)
    labels = [e for e in v.ir.slides[0].elements if e.text == "Escalabilidade"]
    assert all(e.width > 400 for e in labels)  # Above description; whole word fits.


def test_single_concept_does_not_require_fabricating_another_node():
    outline = {
        "slides": [
            {
                "intent": "concept",
                "message": "Uma ideia pode ser aprofundada.",
                "subjects": [],
                "structures": ["cards"],
            }
        ]
    }
    schema = constrain_visual_schema(contextual_schema(1, [], []), outline, expressive=True)
    decoder = visual_decoder_schema(schema)
    data = rich_data(
        "concept_map",
        1,
        "Uma explicação conceitual pode incluir um exemplo ou uma condição de validade.",
    )
    slide = data["slides"][0]
    slide.update(title=outline["slides"][0]["message"], vector_flow=False)
    col = slide["columns"][0]
    col["items"] = col.pop("content")
    wire = {"title": data["title"], "theme": data["theme"], "slide_1": slide}
    Draft202012Validator(decoder).validate(wire)
    normalized = normalize_visual_response(wire, 1)
    Draft202012Validator(schema).validate(normalized)
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(normalized))
    assert not ds and validate_source(source).success(strict=True)
