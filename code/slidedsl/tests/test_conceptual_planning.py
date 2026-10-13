from copy import deepcopy
import json

import pytest

from slidedsl.conceptual_planning import inspect_concepts, materialize_concepts, plan_concepts
from slidedsl.contextual import generate_contextual
from slidedsl.planning import ContentBlock
from slidedsl.semantic_planning import audit_semantics, review_plan
from test_evolution import Answers
from test_semantic_planning import ReviewAnswers, semantic_data


def concept_data():
    return {
        "goal": "Entender numerador e denominador.",
        "definitions": [
            {"name": "Numerador", "meaning": "Conta as partes escolhidas.", "sources": []},
            {"name": "Denominador", "meaning": "Conta as partes iguais do todo.", "sources": []},
        ],
        "entities": [],
        "steps": [],
        "examples": [
            {
                "about": "definition_1",
                "scenario": "Uma pizza cortada em quatro partes iguais.",
                "observation": "Comer três partes representa 3/4 da pizza.",
                "sources": [],
            }
        ],
        "claims": [],
        "alternatives": [],
        "criteria": [],
        "synthesis": {
            "statement": "A fração conta partes iguais do mesmo todo.",
            "based_on": ["definition_1", "definition_2"],
        },
    }


@pytest.mark.parametrize("mutation", ["example", "synthesis", "source", "comparison", "duplicate"])
def test_content_reference_checks_without_factual_score(mutation):
    data = concept_data()
    if mutation == "example":
        data["examples"][0]["about"] = "Não existe"
    elif mutation == "synthesis":
        data["synthesis"]["based_on"] = ["Não existe"]
    elif mutation == "source":
        data["definitions"][0]["sources"] = ["invented"]
    elif mutation == "comparison":
        data["alternatives"] = ["A", "B"]
    else:
        data["definitions"][1]["name"] = "Numerador"
    audit = inspect_concepts(data)
    assert audit["issues"] and not audit["factual_verified"]


def test_conceptual_raw_response_and_invalid_reference_are_preserved(tmp_path):
    data = concept_data()
    data["examples"][0]["about"] = "definition_4"
    adapter = Answers([json.dumps(data)])
    with pytest.raises(ValueError, match="inexistente"):
        plan_concepts(adapter, "Frações", {}, tmp_path / "concepts")
    assert (tmp_path / "concepts/raw.txt").exists()
    assert (tmp_path / "concepts/response.json").exists()
    assert json.loads((tmp_path / "concepts/audit.json").read_text("utf-8"))["issues"]


def test_concepts_flow_through_existing_dsl_and_native_export(tmp_path):
    concept = concept_data()
    outline = {
        "slides": [
            {
                "intent": "concept",
                "message": "Frações contam partes iguais.",
                "focus": "Numerador e denominador com exemplo.",
                "reason": "Conceitos em cards.",
                "content_refs": ["definition_1", "definition_2", "example_1"],
                "relationships": [],
            }
        ]
    }
    adapter = Answers([json.dumps(concept), json.dumps(outline)])
    report = generate_contextual(
        "qwen3:4b-instruct",
        "C",
        "Crie um slide sobre frações",
        tmp_path / "run",
        context={"conceptual_planning": True},
        adapter=adapter,
        repair_max=0,
    )
    assert report["compile_success"] and report["calls"] == 2
    assert report["protocol"] == "conceptual-planning-v1"
    assert report["conceptual_plan"] == concept
    assert "conceptual_plan" in adapter.calls[1]["user"]
    assert report["conceptual_projection"]["verbatim_projection"]
    assert (tmp_path / "run/presentation.sld").exists()
    assert (tmp_path / "run/presentation.pptx").exists()


def test_conceptual_mode_cannot_change_restricted_contract_or_model(tmp_path):
    for model, context in [("qwen3:4b-instruct", {"grounding": "restricted"}), ("other", {})]:
        with pytest.raises(ValueError):
            generate_contextual(
                model,
                "C",
                "Frações",
                tmp_path / model,
                context={"conceptual_planning": True, **context},
            )


def test_local_review_prioritizes_one_slide_and_feeds_rejection(tmp_path):
    data = semantic_data("concept_map", 1)
    data["slides"] += [deepcopy(data["slides"][0])]
    for i, slide in enumerate(data["slides"]):
        slide["title"] = "Interface recebe solicitações."
        block = slide["columns"][0]["content"][0]
        block.update(role="concept", detail="Recebe solicitações" if i else "Recebe solicitações.")
        slide["columns"][0]["items"] = [ContentBlock.model_validate(block).full_text()]
    path = "slides.1.columns.0.content.0.detail"
    adapter = ReviewAnswers(
        [
            json.dumps({"edits": [{"path": path, "value": "É essencial."}]}),
            json.dumps({"edits": [{"path": path, "value": "Recebe solicitações."}]}),
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Explique interface",
        requirements=[],
        max_calls=2,
    )
    assert not report["attempts"][0]["accepted"] and report["attempts"][1]["accepted"]
    assert json.loads(adapter.calls[1]["user"])["previous_rejection"]["regressions"]
    assert result["slides"][0] == data["slides"][0]
    assert all(p.startswith("slides.1.") for a in report["attempts"] for p in a["paths"])


def test_extended_abstract_names_and_generalized_examples_remain_signals():
    data = semantic_data()
    data["slides"][0]["columns"][0]["content"][0]["label"] = "Camadas de arquitetura"
    col = data["slides"][0]["columns"][0]
    col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    assert any(d["code"] == "Q003" for d in audit_semantics(data)["diagnostics"])


def test_projection_keeps_full_scenario_and_matching_criteria():
    data = concept_data()
    data.update(
        alternatives=["A", "B"],
        criteria=[
            {
                "name": "Implantação",
                "left": "Uma unidade é publicada.",
                "right": "Publica serviços separadamente.",
                "sources": [],
            }
        ],
    )
    outline = {
        "slides": [
            {
                "intent": "comparison",
                "message": "A implantação difere.",
                "content_refs": ["criterion_1"],
                "structures": ["cards", "cards"],
                "relationships": [],
                "subjects": ["A", "B"],
            },
            {
                "intent": "concept",
                "message": "Numerador conta partes escolhidas.",
                "content_refs": ["definition_1", "example_1"],
                "structures": ["cards"],
                "relationships": [],
                "subjects": [],
            },
        ]
    }
    plan, trace = materialize_concepts(data, outline)
    left, right = plan["slides"][0]["columns"]
    assert left["content"][0]["label"] == right["content"][0]["label"]
    example = plan["slides"][1]["columns"][0]["content"][1]
    assert example["detail"] == data["examples"][0]["scenario"]
    assert example["explanation"] == data["examples"][0]["observation"]
    assert trace["unselected"] == ["definition_2", "synthesis"]
    broken = deepcopy(outline)
    broken["slides"][0]["content_refs"] = ["definition_1"]
    with pytest.raises(ValueError, match="incompatível"):
        materialize_concepts(data, broken)


def test_contract_disables_unrequested_comparison(tmp_path):
    adapter = Answers([json.dumps(concept_data())])
    plan_concepts(adapter, "Explique como comparar com o elemento central", {}, tmp_path / "plan")
    schema = adapter.calls[0]["response_schema"]
    assert schema["properties"]["criteria"]["maxItems"] == 0
    assert schema["properties"]["definitions"]["minItems"] == 1


def test_title_absolutes_are_visible_and_negated_guarantees_are_not():
    data = semantic_data()
    data["slides"][0]["title"] = "Arquitetura garante independência."
    assert any(
        d["code"] == "Q002" and d["path"].endswith("title")
        for d in audit_semantics(data)["diagnostics"]
    )
    data["slides"][0]["title"] = "Arquitetura não garante independência."
    assert not any(d["code"] == "Q002" for d in audit_semantics(data)["diagnostics"])


def test_relabeling_a_guarantee_as_condition_cannot_hide_the_warning():
    data = semantic_data("concept_map", 1)
    col = data["slides"][0]["columns"][0]
    block = col["content"][0]
    block.update(label="Condição", role="condition", detail="Garante que todos entendam o pedido.")
    col["items"] = [ContentBlock.model_validate(block).full_text()]
    assert any(d["code"] == "Q002" for d in audit_semantics(data)["diagnostics"])
