from copy import deepcopy
import json

import pytest

from slidedsl.compiler import inspect_pptx
from slidedsl.conceptual_planning import conceptual_units, materialize_concepts
from slidedsl.contextual import GenerationContext, generate_contextual
from slidedsl.coverage import recover_selection, validate_coverage
from slidedsl.layouts import plan_to_dsl
from slidedsl.pipeline import validate_source
from slidedsl.planning import DeckPlan
from slidedsl.requirements import content_requirements, extract_requirements
from test_conceptual_planning import concept_data
from test_evolution import Answers


REQUEST = "Crie um slide. Slide 1: explique numerador e denominador, com um exemplo concreto de partes iguais. Sem imagens ou rodapé."


def fixture():
    reqs = content_requirements(REQUEST, 1)
    data = concept_data()
    data["definitions"][0]["requirement_ids"] = ["R1"]
    data["definitions"][1]["requirement_ids"] = ["R1"]
    data["examples"][0]["requirement_ids"] = ["R2"]
    outline = {
        "slides": [
            {
                "intent": "concept",
                "message": "Frações contam partes iguais.",
                "focus": "Frações",
                "reason": "Definições",
                "structures": ["cards"],
                "subjects": [],
                "relationships": [],
                "content_refs": ["definition_1", "definition_2"],
            }
        ]
    }
    return reqs, data, outline


def codes(report):
    return {d["code"] for d in report["diagnostics"]}


def evidence(reqs, data, outline):
    plan, trace = materialize_concepts(data, outline)
    source, mapping, _ = plan_to_dsl(DeckPlan.model_validate(plan))
    validation = validate_source(source)
    return plan, trace, validation.ir, mapping


def test_exact_origins_and_separate_structural_contract():
    reqs, _, _ = fixture()
    assert len(reqs) == 2
    assert reqs[1]["description"] == "com um exemplo concreto de partes iguais"
    for req in reqs:
        origin = req["origin"]
        assert REQUEST[origin["start"] : origin["end"]] == origin["quote"]
        assert req["slide"] == 1 and req["verification"] == "manual"
    assert all(r["kind"] != "content" for r in extract_requirements(REQUEST, 1))


def test_coordinated_nouns_are_not_invented_requirements_and_global_clause_is_preserved():
    request = "Explique pilhas e filas, incluindo LIFO, FIFO e exemplos de remoção."
    reqs = content_requirements(request, 2)
    assert [r["description"] for r in reqs] == [
        "Explique pilhas e filas",
        "LIFO",
        "FIFO",
        "exemplos de remoção",
    ]
    assert all(r["slide"] is None for r in reqs)


@pytest.mark.parametrize("mutation", ["origin", "duplicate", "slide"])
def test_registered_requirements_reject_invalid_contract(mutation):
    reqs, _, _ = fixture()
    if mutation == "origin":
        reqs[0]["origin"]["quote"] = "Inventado"
    elif mutation == "duplicate":
        reqs[1]["id"] = reqs[0]["id"]
    else:
        reqs[0]["slide"] = 2
    with pytest.raises(ValueError):
        content_requirements(REQUEST, 1, reqs)


def test_c001_missing_content_and_c005_are_not_factual_success_or_blockers():
    reqs, data, outline = fixture()
    data["examples"][0]["requirement_ids"] = []
    plan, _ = materialize_concepts(data, outline)
    report = validate_coverage(reqs, data, outline, plan)
    assert "C001" in codes(report)
    assert all(d["severity"] != "ERRO" for d in report["diagnostics"])
    assert report["semantic_verified"] is None and not report["factual_verified"]
    assert not report["structural_retention_complete"]


def test_c002_c003_trace_loss_and_origin():
    reqs, data, outline = fixture()
    plan, _ = materialize_concepts(data, outline)
    report = validate_coverage(reqs, data, outline, plan)
    omission = next(d for d in report["diagnostics"] if d["code"] == "C002")
    assert omission["requirement"] == "R2" and omission["stage"] == "selection"
    assert omission["evidence"]["records"] == ["example_1"]
    assert omission["origin"] == reqs[1]["origin"] and omission["guidance"]
    assert "C003" in codes(report)


@pytest.mark.parametrize(
    "mutation", ["requirement", "example", "synthesis", "selection", "duplicate"]
)
def test_c004_reports_invalid_references_without_materialization(mutation):
    reqs, data, outline = fixture()
    if mutation == "requirement":
        data["examples"][0]["requirement_ids"] = ["R404"]
    elif mutation == "example":
        data["examples"][0]["about"] = "definition_404"
    elif mutation == "synthesis":
        data["synthesis"]["based_on"] = ["definition_404"]
    else:
        outline["slides"][0]["content_refs"].append(
            "unknown" if mutation == "selection" else "definition_1"
        )
    assert "C004" in codes(validate_coverage(reqs, data, outline))


def test_recovery_preserves_records_slide_count_and_ir_fields():
    reqs, data, outline = fixture()
    old = deepcopy(outline)
    recovered, plan, report = recover_selection(reqs, data, outline)
    assert report["accepted"] == 1 and report["calls"] == 0
    assert outline == old
    assert recovered["slides"][0]["content_refs"] == ["definition_1", "definition_2", "example_1"]
    assert len(plan["slides"]) == 1 and report["after"]["structural_retention_complete"]
    _, trace, ir, mapping = evidence(reqs, data, recovered)
    assert next(r for r in trace["records"] if r["record"] == "example_1")["requirement_ids"] == [
        "R2"
    ]
    final = validate_coverage(reqs, data, recovered, plan, ir, mapping)
    assert final["structural_retention_complete"] and "C003" not in codes(final)
    assert all(
        w["element"] in mapping
        for r in final["requirements"]
        for e in r["evidence"]
        for w in e["elements"]
    )
    assert final["semantic_verified"] is None and "C005" in codes(final)


@pytest.mark.parametrize("mutation", ["text", "mapping", "missing", "sources"])
def test_ids_alone_do_not_prove_evidence_reached_ir(mutation):
    reqs, data, outline = fixture()
    outline["slides"][0]["content_refs"].append("example_1")
    plan, _, ir, mapping = evidence(reqs, data, outline)
    key = next(k for k, p in mapping.items() if p.endswith("content.2.explanation"))
    if mutation == "text":
        next(e for e in ir.slides[0].elements if e.id == key).text = "Outro conteúdo."
    elif mutation == "mapping":
        mapping[key] = "slides.0.columns.0.content.1.explanation"
    elif mutation == "missing":
        ir.slides[0].elements = [e for e in ir.slides[0].elements if e.id != key]
    else:
        plan["slides"][0]["columns"][0]["content"][2]["sources"] = ["invented"]
    report = validate_coverage(reqs, data, outline, plan, ir, mapping)
    assert "C003" in codes(report) and not report["requirements"][1]["represented"]


def test_wrong_section_is_not_coverage_and_recovery_does_not_move_existing_content():
    reqs, data, outline = fixture()
    reqs[1]["slide"] = 2
    outline["slides"][0]["content_refs"].append("example_1")
    outline["slides"].append(deepcopy(outline["slides"][0]))
    outline["slides"][1]["content_refs"] = ["definition_1"]
    recovered, _, report = recover_selection(reqs, data, outline)
    assert recovered["slides"][0] == outline["slides"][0]
    assert recovered["slides"][1]["content_refs"] == ["definition_1", "example_1"]
    assert report["accepted"] == 1


def test_capacity_rejection_does_not_delete_existing_content():
    reqs, data, outline = fixture()
    outline["slides"][0]["intent"] = "conclusion"
    outline["slides"][0]["content_refs"].append("synthesis")
    recovered, _, report = recover_selection(reqs, data, outline)
    assert recovered == outline and report["accepted"] == 0
    assert report["attempts"][0]["reason"] == "capacity_or_role"
    assert "C002" in codes(report["after"])


def test_geometric_overflow_rejects_insertion_without_truncation():
    reqs, data, outline = fixture()
    data["examples"][0]["scenario"] = " ".join(["WWWWWWWWWWWW"] * 9)[:120]
    data["examples"][0]["observation"] = " ".join(["WWWWWWWWWWWW"] * 10)[:139] + "."
    recovered, _, report = recover_selection(reqs, data, outline)
    assert recovered == outline and report["accepted"] == 0
    assert report["attempts"][0]["reason"] == "validation_regression"
    assert any(
        d["code"] in {"L004", "D001", "D005", "D007"} for d in report["attempts"][0]["diagnostics"]
    )


def test_incompatible_role_and_disabled_recovery_keep_omission_visible():
    reqs, data, outline = fixture()
    data["entities"] = [{"name": "Objeto", "responsibility": "Guarda dados.", "sources": []}]
    outline["slides"][0].update(
        intent="architecture", structures=["services"], content_refs=["entity_1"]
    )
    assert recover_selection(reqs, data, outline)[2]["accepted"] == 0
    reqs, data, outline = fixture()
    recovered, _, report = recover_selection(reqs, data, outline, enabled=False)
    assert recovered == outline and not report["attempts"] and "C002" in codes(report["after"])


def test_negative_and_optional_requirements_are_never_recovered():
    reqs, data, outline = fixture()
    reqs[1]["polarity"] = "exclude"
    _, _, report = recover_selection(reqs, data, outline)
    assert not report["attempts"] and "C005" in codes(report["after"])
    reqs[1].update(polarity="include", required=False)
    assert not recover_selection(reqs, data, outline)[2]["attempts"]


def test_full_generation_flag_native_pptx_and_legacy_compatibility(tmp_path):
    reqs, data, outline = fixture()
    for record in [*data["definitions"], *data["examples"], data["synthesis"]]:
        record.setdefault("requirement_ids", [])
    raw_outline = deepcopy(outline)
    for slide in raw_outline["slides"]:
        slide.pop("structures")
        slide.pop("subjects")
    adapter = Answers([json.dumps(data), json.dumps(raw_outline)])
    report = generate_contextual(
        "qwen3:4b-instruct",
        "C",
        REQUEST,
        tmp_path / "run",
        context={"coverage_validation": True},
        adapter=adapter,
        repair_max=0,
    )
    assert report["compile_success"] and report["calls"] == 2
    assert report["coverage_recovery"]["accepted"] == 1
    assert (
        report["coverage"]["stage"] == "pptx"
        and report["coverage"]["structural_retention_complete"]
    )
    assert report["content_faithful"] is None
    assert inspect_pptx(tmp_path / "run/presentation.pptx")["slide_count"] == 1
    assert "requirement_ids" in conceptual_units(data)["example_1"]
    settings = GenerationContext().model_dump()
    assert "coverage_validation" not in settings and "content_requirements" not in settings


def test_pptx_text_mutation_is_reported_as_final_loss():
    reqs, data, outline = fixture()
    outline["slides"][0]["content_refs"].append("example_1")
    plan, _, ir, mapping = evidence(reqs, data, outline)
    native = {
        "slides": [{"objects": [{"name": e.id, "text": e.text} for e in ir.slides[0].elements]}]
    }
    next(o for o in native["slides"][0]["objects"] if o["name"].endswith("i3_explanation"))[
        "text"
    ] = "Outro texto."
    report = validate_coverage(reqs, data, outline, plan, ir, mapping, native)
    assert any(d["code"] == "C003" and d["stage"] == "pptx" for d in report["diagnostics"])
