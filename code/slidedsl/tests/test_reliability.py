from copy import deepcopy
import json

from fastapi.testclient import TestClient
import pytest

from slidedsl.evolution import _validate_plan
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.planning import DeckPlan
from slidedsl.reliability import evaluate_state, run_reliability
from slidedsl.reliability import preserve_good_fields
from slidedsl.requirements import evaluate_requirements, extract_requirements
from slidedsl.server import app
from slidedsl.visual_validation import check_visual
from test_evolution import Answers, plan_data


def test_requirements_detect_actual_missing_shapes_and_layer_operations():
    reqs = extract_requirements(
        "Crie um slide. No primeiro slide coloque duas formas coloridas, uma imagem e uma demonstração de camadas.",
        1,
    )
    data = plan_data()
    _, validation, _, _ = _validate_plan(data, 1)
    result = evaluate_requirements(validation, reqs)
    assert not result["all_met"]
    assert {r["kind"] for r in result["details"] if not r["met"]} == {"shapes", "images", "layers"}
    assert all(d["code"] == "R001" and d["slide"] == 1 for d in result["diagnostics"])


def test_deterministic_addition_preserves_existing_shape_texts_and_other_slides(tmp_path):
    data = plan_data()
    existing = {"kind": "ellipse", "slot": "left", "color": "primaria"}
    data["slides"][0]["decorations"] = [existing]
    data["slides"].append(deepcopy(data["slides"][0]))
    reqs = extract_requirements(
        "Crie dois slides. Slide 1: duas formas coloridas. Slide 2: conclusão.", 2
    )
    result = run_reliability(
        data, "duas formas", tmp_path / "run", count=2, requirements=reqs, mode="deterministic"
    )
    saved = json.loads((tmp_path / "run/plan.json").read_text(encoding="utf-8"))
    assert result["faithful"] and result["compile_success"]
    assert saved["slides"][0]["decorations"][0] == existing
    assert saved["slides"][0]["columns"] == data["slides"][0]["columns"]
    assert saved["slides"][1] == data["slides"][1]
    assert (tmp_path / "run/repair_1/before.json").exists()
    assert (tmp_path / "run/repair_1/after.json").exists()


def test_noop_reference_patch_stops_without_inventing_an_element(tmp_path):
    data = plan_data()
    relation = {"kind": "front", "target": "d2", "reference": ""}
    data["slides"][0]["relations"] = [relation]
    adapter = Answers(
        [json.dumps({"edits": [{"path": "slides.0.relations.0", "value": relation}]})]
    )
    result = run_reliability(
        data,
        "Crie um slide",
        tmp_path / "run",
        count=1,
        requirements=extract_requirements("Crie um slide", 1),
        adapter=adapter,
        repair_max=10,
    )
    assert not result["compile_success"] and len(adapter.calls) == 1
    assert result["attempts"][0]["reason"] == "repeated_or_unchanged_patch"
    assert json.loads((tmp_path / "run/plan.json").read_text())["slides"][0]["decorations"] == []


def test_new_error_patch_is_rejected_and_next_patch_can_progress(tmp_path):
    data = plan_data()
    data["slides"][0]["relations"] = [{"kind": "front", "target": "absent", "reference": ""}]
    # Moves body into the title: V001/D010/new blockers must roll back.
    bad = {"kind": "top", "target": "c1_i2", "reference": "titulo"}
    good = {"kind": "front", "target": "c1_i2", "reference": ""}
    adapter = Answers(
        [json.dumps({"edits": [{"path": "slides.0.relations.0", "value": r}]}) for r in [bad, good]]
    )
    result = run_reliability(
        data,
        "Crie um slide",
        tmp_path / "run",
        count=1,
        requirements=extract_requirements("Crie um slide", 1),
        adapter=adapter,
    )
    assert result["compile_success"] and result["failed_corrections"] == 1
    assert result["attempts"][0]["reason"] == "new_errors"
    assert json.loads((tmp_path / "run/repair_1/after.json").read_text(encoding="utf-8")) == data


@pytest.mark.parametrize("layout", ["cards", "sequence", "flow"])
def test_components_produce_real_editable_pptx_with_verified_requirements(layout, tmp_path):
    data = plan_data()
    data["slides"][0]["layout"] = layout
    data["slides"][0]["columns"][0]["heading"] = ""
    if layout == "flow":
        data["slides"][0]["relations"] = [{"kind": "next", "target": "c1_i2", "reference": "c1_i1"}]
    plan = DeckPlan.model_validate(data)
    reqs = [
        {"id": "component", "kind": "component", "slide": 1, "value": layout, "description": layout}
    ]
    state = evaluate_state(data, 1, reqs)
    assert state["valid"] and state["requirements"]["all_met"]
    report = compile_plan(plan, tmp_path / f"{layout}.pptx", strict=True)
    assert report["inspection"]["slide_count"] == 1
    assert report["inspection"]["text_objects"] >= 3


def test_component_does_not_silently_truncate_or_drop_heading():
    data = plan_data()
    data["slides"][0]["layout"] = "cards"
    data["slides"][0]["columns"][0]["items"] = ["Muito texto " * 300]
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert "Muito texto " * 300 in source
    assert "Componentes" in source
    assert any(d.code == "L004" for d in diagnostics)


def test_requirements_revalidation_uses_edited_ir_not_model_claim():
    data = plan_data()
    data["slides"][0]["decorations"] = [
        {"kind": "rectangle", "slot": "left", "color": "primaria"},
        {"kind": "ellipse", "slot": "right", "color": "destaque"},
    ]
    _, v, _, _ = _validate_plan(data, 1)
    reqs = [
        {
            "id": "two",
            "kind": "shapes",
            "slide": 1,
            "minimum": 2,
            "distinct_colors": True,
            "description": "Duas formas coloridas",
        }
    ]
    client = TestClient(app)
    payload = {"ir": v.ir.model_dump(), "requirements": reqs}
    assert client.post("/api/requirements/validate", json=payload).json()["all_met"]
    payload["ir"]["slides"][0]["elements"] = [
        e for e in payload["ir"]["slides"][0]["elements"] if e["id"] != "s1_d2"
    ]
    assert not client.post("/api/requirements/validate", json=payload).json()["all_met"]


def test_overlapping_text_is_reported_even_with_transparent_boxes():
    _, v, _, _ = _validate_plan(plan_data(), 1)
    a, b = [e for e in v.ir.slides[0].elements if e.role == "corpo"][:2]
    b.x, b.y = a.x, a.y
    assert any(d["code"] == "V001" for d in check_visual(v.ir))


def test_invalid_attempt_budget_is_rejected_before_model(tmp_path):
    with pytest.raises(ValueError):
        run_reliability(plan_data(), "um slide", tmp_path, count=1, requirements=[], repair_max=11)


def test_informative_cards_are_not_incorrectly_interpreted_as_shapes():
    reqs = extract_requirements("Crie um slide. Slide 1: cards informativos.", 1)
    assert not any(r["kind"] == "shapes" for r in reqs)


def test_simple_negation_does_not_create_positive_requirements():
    reqs = extract_requirements(
        "Crie um slide. Slide 1: duas formas coloridas, sem imagem e sem rodapé.", 1
    )
    assert any(r["kind"] == "shapes" for r in reqs)
    assert not any(r["kind"] in {"images", "footer"} for r in reqs)


def test_missing_group_patch_cannot_rewrite_correct_body_content():
    data = plan_data()
    requirements = [
        {"id": "group", "kind": "groups", "slide": 1, "minimum": 2, "description": "Dois grupos"}
    ]
    state = evaluate_state(data, 1, requirements)
    candidate = deepcopy(data)
    candidate["slides"][0]["columns"][0]["items"][0] = "Conteúdo substituído"
    assert not preserve_good_fields(data, candidate, ["slides.0.columns"], state)


def test_compact_decorations_keep_complete_long_text_and_fit_the_canvas(tmp_path):
    data = plan_data("two_columns")
    data["slides"][0]["columns"][0]["items"] = [
        "Uma explicação completa sobre diferenças de contraste entre objetos e seu fundo."
    ] * 2
    reqs = extract_requirements("Crie um slide. Slide 1: duas formas coloridas.", 1)
    result = run_reliability(
        data, "duas formas", tmp_path / "run", count=1, requirements=reqs, mode="deterministic"
    )
    assert result["faithful"] and result["compile_success"]
    assert (
        json.loads((tmp_path / "run/plan.json").read_text(encoding="utf-8"))["slides"][0]["columns"]
        == data["slides"][0]["columns"]
    )


def test_component_preserves_requested_native_group():
    data = plan_data()
    data["slides"][0]["layout"] = "cards"
    data["slides"][0]["columns"][0]["heading"] = ""
    data["slides"][0]["columns"][0]["group"] = True
    _, validation, _, ds = _validate_plan(data, 1)
    assert not any(d["severity"] == "ERRO" for d in ds)
    assert validation.ir.slides[0].groups[0].members == ["s1_c1_i1", "s1_c1_i2"]


def test_duplicate_requirement_ids_are_rejected():
    criterion = {"id": "same", "kind": "slides", "description": "Um slide"}
    with pytest.raises(ValueError, match="IDs únicos"):
        evaluate_requirements(None, [criterion, criterion])


def test_multiline_comparison_heading_fits_without_rewriting_content():
    data = plan_data("comparison")
    data["slides"][0]["columns"][0]["heading"] = "Arquitetura com múltiplos serviços independentes"
    state = evaluate_state(data, 1, [])
    assert state["valid"]
    heading = next(e for e in state["validation"].ir.slides[0].elements if e.id == "s1_c1_heading")
    assert heading.height > 64 and heading.text == data["slides"][0]["columns"][0]["heading"]


def test_one_column_layout_repair_does_not_invent_missing_content(tmp_path):
    data = plan_data()
    data["slides"][0]["layout"] = "two_columns"
    report = run_reliability(
        data,
        "um slide",
        tmp_path / "run",
        count=1,
        requirements=extract_requirements("um slide", 1),
        mode="deterministic",
    )
    saved = json.loads((tmp_path / "run/plan.json").read_text(encoding="utf-8"))
    assert report["compile_success"]
    assert saved["slides"][0]["columns"] == data["slides"][0]["columns"]
    assert saved["slides"][0]["layout"] == "title_content"
