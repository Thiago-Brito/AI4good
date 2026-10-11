from copy import deepcopy
import json
import zipfile
import xml.etree.ElementTree as ET

import pytest

from slidedsl.connections import NS, anchored_connections
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.parser import parse
from slidedsl.pipeline import validate_source
from slidedsl.planning import DeckPlan
from slidedsl.refinement import normalized, refinement_report, refine_slides
from slidedsl.serializer import to_dsl
from test_visual_planning import composed_data


@pytest.mark.parametrize(
    "layout",
    [
        "visual_cover",
        "architecture_diagram",
        "comparison_visual",
        "benefit_cards",
        "takeaway",
        "visual_sequence",
        "visual_flow",
    ],
)
def test_refinement_keeps_information_and_exports_editable_objects(layout, tmp_path):
    data = composed_data(layout)
    if layout == "visual_cover":
        data["slides"][0]["columns"][0]["items"] = data["slides"][0]["columns"][0]["items"][:2]
    data["refinement"] = {"style": ""}
    original = deepcopy(data)
    report = refinement_report(data)
    assert report["slides"][0]["accepted"], report
    assert data == original
    result = compile_plan(DeckPlan.model_validate(data), tmp_path / "deck.pptx", strict=True)
    validation = validate_source(result["source"])
    texts = " ".join(e.text or "" for e in validation.ir.slides[0].elements)
    for c in data["slides"][0]["columns"]:
        for value in c["items"]:
            assert normalized(value) in normalized(texts)
    assert all(e.font_size >= 22 for e in validation.ir.slides[0].elements if e.type == "text")
    assert result["inspection"]["image_objects"] == 0


def test_three_cards_balanced_candidates_and_style_preferences():
    data = composed_data("benefit_cards")
    data["refinement"] = {"style": ""}
    report = refinement_report(data)["slides"][0]
    assert len(report["candidates"]) == 2 and report["mode"] == "row"
    data["refinement"]["style"] = "compacto minimalista"
    report = refinement_report(data)["slides"][0]
    assert report["mode"] == "grid"
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert "_signal" not in source


def test_deduplication_preserves_message_and_verbatim_mode():
    data = composed_data("takeaway")
    title = data["slides"][0]["title"]
    data["slides"][0]["columns"][0]["items"] = [title, "Considere custos operacionais."]
    data["refinement"] = {"style": ""}
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert source.count(json.dumps(title, ensure_ascii=False)) == 1
    assert refinement_report(data)["slides"][0]["duplicates"][0]["text"] == title
    data["refinement"]["verbatim"] = True
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert source.count(json.dumps(title, ensure_ascii=False)) == 2


def test_spatial_constraints_are_never_reorganized():
    plan = DeckPlan.model_validate(composed_data("benefit_cards"))
    source, mapping, _ = plan_to_dsl(plan)
    ast = parse(source)
    from slidedsl.ast_nodes import Command

    ast.slides[0].commands.append(
        Command(op="align", id="s1_c1_i1", reference="s1_c1_i2", axis="left")
    )
    old = deepcopy(ast.slides)
    plan.refinement = {"style": ""}
    slides, _, accepted, report = refine_slides(plan, ast.slides, mapping)
    assert slides == old and not accepted and not report["slides"][0]["accepted"]


def test_long_content_rolls_back_without_font_reduction_or_loss():
    data = composed_data("benefit_cards")
    data["slides"][0]["columns"][0]["items"][0] = "Informação factual completa. " * 25
    plain = DeckPlan.model_validate(data)
    original, _, _ = plan_to_dsl(plain)
    plain.refinement = {"style": ""}
    source, _, diagnostics = plan_to_dsl(plain)
    assert source == original and any(d.code == "L004" for d in diagnostics)
    assert not refinement_report(plain.model_dump())["slides"][0]["accepted"]


def test_native_connectors_have_real_shape_ids_and_survive_dsl_roundtrip(tmp_path):
    data = composed_data("architecture_diagram")
    data["refinement"] = {"style": ""}
    result = compile_plan(DeckPlan.model_validate(data), tmp_path / "native.pptx", strict=True)
    deck = validate_source(result["source"]).ir
    assert len(anchored_connections(deck.slides[0])) == 2
    restored = validate_source(to_dsl(deck)).ir
    assert list(anchored_connections(restored.slides[0])) == list(
        anchored_connections(deck.slides[0])
    )
    with zipfile.ZipFile(tmp_path / "native.pptx") as archive:
        root = ET.fromstring(archive.read("ppt/slides/slide1.xml"))
        ids = {e.get("id") for e in root.findall(".//p:cNvPr", NS)}
        links = root.findall(".//p:cxnSp", NS)
        assert len(links) == 2
        for link in links:
            assert link.find(".//a:stCxn", NS).get("id") in ids
            assert link.find(".//a:endCxn", NS).get("id") in ids
            assert link.find(".//a:tailEnd", NS).get("type") == "triangle"
        assert any(r.get("b") == "1" for r in root.findall(".//a:rPr", NS))


def test_independent_services_do_not_gain_unplanned_connections(tmp_path):
    data = composed_data("architecture_diagram")
    data["slides"][0]["columns"][0]["representation"] = "services"
    data["refinement"] = {"style": ""}
    result = compile_plan(DeckPlan.model_validate(data), tmp_path / "services.pptx", strict=True)
    assert not anchored_connections(validate_source(result["source"]).ir.slides[0])
    with zipfile.ZipFile(tmp_path / "services.pptx") as archive:
        assert b"cxnSp" not in archive.read("ppt/slides/slide1.xml")


def test_natural_cards_request_does_not_override_every_slide():
    from slidedsl.contextual import explicit_layouts

    assert explicit_layouts("Cinco slides, incluindo três cards de benefícios", "", 5) == []
    assert explicit_layouts("Use o layout cards", "", 1) == ["cards"]
    assert explicit_layouts("Use title_content", "", 1) == ["title_content"]


def test_repeated_component_name_is_conserved_once_not_paraphrased():
    data = composed_data("architecture_diagram")
    data["slides"][0]["columns"][0]["items"][0] = "Interface: Interface recebe pedidos."
    data["refinement"] = {"style": ""}
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert '"recebe pedidos."' in source and source.count('"Interface:"') == 1
    report = refinement_report(data)["slides"][0]
    assert report["accepted"] and report["duplicates"][0]["kind"] == "component_label_prefix"


def test_refinement_rolls_back_when_previously_met_literal_requirement_is_lost():
    data = composed_data("architecture_diagram")
    value = "Interface: Interface recebe pedidos."
    data["slides"][0]["columns"][0]["items"][0] = value
    plain, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    data["refinement"] = {
        "requirements": [
            {
                "id": "literal",
                "kind": "text",
                "slide": 1,
                "value": value,
                "description": "Texto literal obrigatório",
            }
        ]
    }
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert source == plain
    assert refinement_report(data)["slides"][0]["candidates"][0]["lost_requirements"] == ["literal"]


def test_deduplication_keeps_meaningful_symbols_and_question_marks():
    data = composed_data("takeaway")
    data["slides"][0]["title"] = "Use C no módulo principal."
    data["slides"][0]["columns"][0]["items"] = [
        "Use C++ no módulo principal.",
        "Use C no módulo principal?",
    ]
    data["refinement"] = {"style": ""}
    source, _, _ = plan_to_dsl(DeckPlan.model_validate(data))
    assert "C++" in source and "principal?" in source
    assert refinement_report(data)["slides"][0]["duplicates"] == []
