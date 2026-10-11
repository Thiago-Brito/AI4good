from copy import deepcopy
import json
import zipfile

from jsonschema import Draft202012Validator
from pydantic import ValidationError
import pytest

from slidedsl.contextual import GenerationContext, contextual_schema, generate_contextual
from slidedsl.documents import add_document, retrieve_for_slides
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.planning import ContentBlock, DeckPlan, SemanticRole, plan_schema
from slidedsl.pipeline import validate_source
from slidedsl.semantic_planning import audit_semantics, review_plan, semantic_schema
from slidedsl.visual_planning import (
    constrain_visual_schema,
    normalize_visual_response,
    visual_decoder_schema,
)
from test_evolution import Answers
from test_expressive_planning import rich_data


class ReviewAnswers(Answers):
    """Recorded patch fixtures adapted to the fixed-field wire contract."""

    def generate(self, system, user, **options):
        raw = super().generate(system, user, **options)
        patch = json.loads(raw)
        context = json.loads(user)
        mapping = {f["path"]: f["key"] for f in context["allowed_fields"]}
        values = {f["key"]: None for f in context["allowed_fields"]}
        for edit in patch["edits"]:
            values[mapping.get(edit["path"], "unauthorized")] = edit["value"]
        raw = json.dumps({"edits": values})
        self.last_response["message"]["content"] = raw
        return raw


def semantic_data(layout="architecture_diagram", count=3):
    data = rich_data(layout, count)
    slide = data["slides"][0]
    slide.update(semantic=True, relationships=[])
    for col in slide["columns"]:
        for i, block in enumerate(col["content"]):
            block.update(
                role="component",
                sources=[],
                label=["Interface", "Negócio", "Dados"][i % 3],
                detail=["Recebe solicitações.", "Aplica regras do negócio.", "Persiste dados."][
                    i % 3
                ],
            )
        col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    return data


@pytest.mark.parametrize("role", SemanticRole.__args__)
def test_roles_are_optional_and_typed_for_legacy(role):
    assert ContentBlock(label="Nome", role=role).role == role
    assert "role" not in ContentBlock(label="Nome").model_dump()
    with pytest.raises(ValidationError):
        ContentBlock(label="Nome", role="unknown")
    assert "SemanticRelation" not in plan_schema(1)["$defs"]


def test_explicit_native_connections_and_labels(tmp_path):
    data = semantic_data()
    data["slides"][0]["relationships"] = [
        {"source": "c1_i1", "target": "c1_i2", "type": "calls"},
        {"source": "c1_i2", "target": "c1_i3", "type": "accesses"},
    ]
    plan = DeckPlan.model_validate(data)
    source, _, diagnostics = plan_to_dsl(plan)
    assert not diagnostics
    validation = validate_source(source)
    assert validation.success(True)
    assert len([e for e in validation.ir.slides[0].elements if e.type == "arrow"]) == 2
    compile_plan(plan, tmp_path / "diagram.pptx", strict=True)
    with zipfile.ZipFile(tmp_path / "diagram.pptx") as archive:
        xml = archive.read("ppt/slides/slide1.xml").decode()
        assert xml.count("<p:cxnSp>") == 2
        assert xml.count("stCxn") == 2 and xml.count("endCxn") == 2
        assert "chama" in xml and "acessa" in xml


def test_stack_without_explicit_edges_does_not_invent_connections():
    data = semantic_data()
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert not diagnostics
    assert not [e for e in validate_source(source).ir.slides[0].elements if e.type == "arrow"]
    old = deepcopy(data)
    old["slides"][0].pop("semantic")
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(old))
    assert not diagnostics
    assert len([e for e in validate_source(source).ir.slides[0].elements if e.type == "arrow"]) == 2


@pytest.mark.parametrize(
    "relation,code",
    [
        ({"source": "c1_i1", "target": "c1_i6", "type": "calls"}, "K002"),
        ({"source": "c1_i1", "target": "c1_i1", "type": "calls"}, "K002"),
        ({"source": "c1_i1", "target": "c1_i3", "type": "calls"}, "K004"),
        ({"source": "c1_i2", "target": "c1_i1", "type": "calls"}, "K004"),
        ({"source": "c1_i1", "target": "c1_i2", "type": "precedes"}, "K003"),
    ],
)
def test_invalid_relation_blocks_compiler_without_phantom_nodes(relation, code):
    data = semantic_data()
    data["slides"][0]["relationships"] = [relation]
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert code in {d.code for d in diagnostics}
    assert "c1_i6_panel" not in source


def test_mixed_roles_and_criteria_are_rejected():
    data = semantic_data("comparison_visual", 2)
    for col in data["slides"][0]["columns"]:
        col["representation"] = "cards"
        for block in col["content"]:
            block["role"] = "comparison_criterion"
    data["slides"][0]["columns"][1]["content"][0]["label"] = "Outro critério"
    for col in data["slides"][0]["columns"]:
        col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    assert "K005" in {d.code for d in plan_to_dsl(DeckPlan.model_validate(data))[2]}
    data = semantic_data()
    data["slides"][0]["columns"][0]["content"][0]["role"] = "concept"
    assert "K003" in {d.code for d in plan_to_dsl(DeckPlan.model_validate(data))[2]}


def test_editorial_links_never_become_dependency_arrows():
    data = semantic_data("concept_map", 2)
    col = data["slides"][0]["columns"][0]
    col["content"][0]["role"] = "example"
    col["content"][1]["role"] = "claim"
    data["slides"][0]["relationships"] = [
        {"source": "c1_i1", "target": "c1_i2", "type": "supports"}
    ]
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert not diagnostics
    assert not [e for e in validate_source(source).ir.slides[0].elements if e.type == "arrow"]


def repetition_data():
    data = semantic_data("concept_map", 2)
    col = data["slides"][0]["columns"][0]
    col["content"][0]["detail"] = data["slides"][0]["title"]
    col["content"][0]["role"] = "claim"
    col["content"][1]["role"] = "concept"
    col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    return data


def test_local_review_preserves_other_fields_and_canonical_text(tmp_path):
    data = repetition_data()
    path = "slides.0.columns.0.content.0.detail"
    adapter = ReviewAnswers(
        [
            json.dumps(
                {
                    "edits": [
                        {"path": path, "value": "A estrutura encaminha solicitações ao negócio."}
                    ]
                }
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Explique a estrutura",
        requirements=[],
        max_calls=1,
    )
    assert report["calls"] == 1 and report["attempts"][0]["accepted"]
    assert (
        result["slides"][0]["columns"][0]["content"][1]
        == data["slides"][0]["columns"][0]["content"][1]
    )
    assert result["slides"][0]["title"] == data["slides"][0]["title"]
    assert (
        result["slides"][0]["columns"][0]["items"][0]
        == ContentBlock.model_validate(result["slides"][0]["columns"][0]["content"][0]).full_text()
    )
    assert (tmp_path / "review/attempt_1/before.json").exists()
    assert "slide_1" not in adapter.calls[0]["user"]


@pytest.mark.parametrize(
    "value,reason",
    [("", "regression_or_information_removed"), ("Palavra " * 120, "invalid_review")],
)
def test_reviewer_rolls_back_erasure_or_oversize(value, reason, tmp_path):
    data = repetition_data()
    adapter = ReviewAnswers(
        [json.dumps({"edits": [{"path": "slides.0.columns.0.content.0.detail", "value": value}]})]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Estrutura",
        requirements=[],
        max_calls=1,
    )
    assert result == data and not report["attempts"][0]["accepted"]
    assert report["attempts"][0]["reason"] == reason


def test_review_rejects_loss_of_frozen_text_requirement(tmp_path):
    data = repetition_data()
    required = data["slides"][0]["columns"][0]["content"][0]["detail"]
    criteria = [
        {
            "id": "retain",
            "kind": "text",
            "slide": 1,
            "value": required,
            "description": "Manter frase",
        }
    ]
    adapter = ReviewAnswers(
        [
            json.dumps(
                {
                    "edits": [
                        {
                            "path": "slides.0.columns.0.content.0.detail",
                            "value": "Recebe solicitações.",
                        }
                    ]
                }
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Manter frase",
        requirements=criteria,
        max_calls=1,
    )
    assert result == data and not report["attempts"][0]["accepted"]


def test_review_is_optional_and_rejects_unauthorized_field(tmp_path):
    data = repetition_data()
    adapter = ReviewAnswers([])
    result, report = review_plan(
        data, tmp_path / "off", adapter=adapter, request="Estrutura", requirements=[], max_calls=0
    )
    assert result == data and not adapter.calls and report["calls"] == 0
    adapter = ReviewAnswers(
        [json.dumps({"edits": [{"path": "slides.0.footer", "value": "Texto"}]})]
    )
    result, report = review_plan(
        data, tmp_path / "on", adapter=adapter, request="Estrutura", requirements=[], max_calls=1
    )
    assert result == data and report["attempts"][0]["reason"] == "invalid_review"


def test_no_safe_edit_stops_and_records_attempt(tmp_path):
    data = repetition_data()
    adapter = ReviewAnswers(['{"edits":[]}'])
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Estrutura",
        requirements=[],
        max_calls=2,
    )
    assert result == data and report["calls"] == 1
    assert report["attempts"][0]["reason"] == "no_safe_edit"


def test_sources_have_original_ids_and_do_not_prove_truth(tmp_path, monkeypatch):
    from slidedsl import documents

    monkeypatch.setattr(documents, "document_path", lambda id: tmp_path / id)
    doc = add_document(
        "fonte.txt",
        b"Plants use light for photosynthesis.\n\nTeams review requests before approval.",
    )
    outline = {
        "slides": [
            {"message": "Plants use light", "focus": "photosynthesis"},
            {"message": "Teams review requests", "focus": "approval"},
        ]
    }
    chunks, mapping = retrieve_for_slides([doc["id"]], outline)
    assert len(chunks) == 2 and mapping["1"] and mapping["2"]
    assert all(c["document_id"] == doc["id"] for c in chunks)
    data = semantic_data("concept_map", 1)
    block = data["slides"][0]["columns"][0]["content"][0]
    block.update(role="claim", sources=[chunks[0]["id"]])
    audit = audit_semantics(data, chunks, "grounded")
    assert (
        not audit["factual_verified"]
        and audit["claims"][0]["fragments"][0]["document_id"] == doc["id"]
    )
    block["sources"] = ["invented"]
    assert "F001" in {d["code"] for d in audit_semantics(data, chunks)["diagnostics"]}


def test_semantic_decoder_keeps_roles_and_tested_capacity():
    outline = {
        "slides": [
            {
                "intent": "architecture",
                "message": "Interface chama negócio.",
                "structures": ["stack"],
                "subjects": [],
            }
        ]
    }
    schema = semantic_schema(
        constrain_visual_schema(contextual_schema(1, [], []), outline, expressive=True), []
    )
    decoder = visual_decoder_schema(schema)
    slide = semantic_data()["slides"][0]
    slide["title"] = outline["slides"][0]["message"]
    slide["vector_flow"] = False
    col = slide["columns"][0]
    col["items"] = col.pop("content")
    wire = {"title": "Arquitetura", "theme": "claro", "slide_1": slide}
    Draft202012Validator(decoder).validate(wire)
    normalized = normalize_visual_response(wire, 1)
    Draft202012Validator(schema).validate(normalized)
    assert normalized["slides"][0]["columns"][0]["content"][0]["role"] == "component"


def test_semantic_generation_is_reviewed_before_first_compilation(tmp_path):
    outline = {
        "slides": [
            {
                "intent": "architecture",
                "message": "Interface chama negócio.",
                "focus": "Componentes",
                "reason": "Mostrar entidades",
                "structures": ["stack"],
                "subjects": [],
            }
        ]
    }
    data = semantic_data()
    slide = data["slides"][0]
    slide["title"] = outline["slides"][0]["message"]
    slide["vector_flow"] = False
    slide["columns"][0]["items"] = slide["columns"][0].pop("content")
    adapter = Answers(
        [
            json.dumps(outline),
            json.dumps({"title": data["title"], "theme": data["theme"], "slide_1": slide}),
        ]
    )
    report = generate_contextual(
        "qwen3:4b-instruct",
        "C",
        "Crie um slide de arquitetura",
        tmp_path / "run",
        context={"semantic_planning": True},
        repair_max=0,
        adapter=adapter,
    )
    assert report["compile_success"] and report["calls"] == 2
    assert report["protocol"] == "semantic-planning-v1"
    assert not (tmp_path / "run/initial/presentation.pptx").exists()
    assert (tmp_path / "run/semantic_audit.json").exists()


def test_restricted_and_online_or_other_models_are_not_silently_used(tmp_path):
    assert GenerationContext(semantic_review_max=2).semantic_review_max == 2
    with pytest.raises(ValidationError):
        GenerationContext(semantic_review_max=3)
    for model, context in [
        ("online", {"semantic_planning": True}),
        ("qwen3:4b-instruct", {"semantic_planning": True, "grounding": "restricted"}),
        ("qwen3:4b-instruct", {"semantic_review_max": 1}),
    ]:
        with pytest.raises(ValueError):
            generate_contextual(model, "C", "Crie um slide", tmp_path / "unused", context=context)


def test_incomplete_sentence_stays_localizable_and_blocks_export(tmp_path):
    data = semantic_data("concept_map", 1)
    block = data["slides"][0]["columns"][0]["content"][0]
    block["detail"] = "A estrutura encaminha solicitações para"
    data["slides"][0]["columns"][0]["items"] = [ContentBlock.model_validate(block).full_text()]
    assert "K006" in {d.code for d in plan_to_dsl(DeckPlan.model_validate(data))[2]}
    adapter = ReviewAnswers(
        [
            json.dumps(
                {
                    "edits": [
                        {
                            "path": "slides.0.columns.0.content.0.detail",
                            "value": "A estrutura encaminha solicitações para o negócio.",
                        }
                    ]
                }
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Estrutura",
        requirements=[],
        max_calls=1,
    )
    assert report["attempts"][0]["accepted"]
    assert not plan_to_dsl(DeckPlan.model_validate(result))[2]


def test_semantic_comparison_criteria_share_row_geometry():
    data = semantic_data("comparison_visual", 2)
    for col in data["slides"][0]["columns"]:
        col["heading"] = "Alternativa"
        col["representation"] = "cards"
        for block in col["content"]:
            block["role"] = "comparison_criterion"
    col = data["slides"][0]["columns"][1]
    col["content"][1]["detail"] = (
        "Aplica regras específicas para os dados com condições bem definidas."
    )
    for col in data["slides"][0]["columns"]:
        col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    source, _, diagnostics = plan_to_dsl(DeckPlan.model_validate(data))
    assert not diagnostics
    elements = {e.id: e for e in validate_source(source).ir.slides[0].elements}
    for i in (1, 2):
        left, right = elements[f"s1_c1_i{i}_panel"], elements[f"s1_c2_i{i}_panel"]
        assert left.y == right.y and left.height == right.height


def test_review_limits_and_loopback_are_enforced(tmp_path):
    data = repetition_data()
    adapter = ReviewAnswers([])
    with pytest.raises(ValueError):
        review_plan(
            data,
            tmp_path / "budget",
            adapter=adapter,
            request="Estrutura",
            requirements=[],
            max_calls=3,
        )
    adapter.base_url = "https://example.com"
    with pytest.raises(ValueError):
        review_plan(
            data,
            tmp_path / "remote",
            adapter=adapter,
            request="Estrutura",
            requirements=[],
            max_calls=1,
        )
    assert not adapter.calls


def test_abstract_component_authorizes_name_function_and_affected_message(tmp_path):
    data = semantic_data("architecture_diagram", 2)
    data["slides"][0]["title"] = "A estrutura conecta componentes."
    col = data["slides"][0]["columns"][0]
    col["content"][0]["label"] = "Estrutura"
    col["items"] = [ContentBlock.model_validate(b).full_text() for b in col["content"]]
    path = "slides.0.columns.0.content.0"
    adapter = ReviewAnswers(
        [
            json.dumps(
                {
                    "edits": [
                        {"path": path + ".label", "value": "Interface"},
                        {"path": path + ".detail", "value": "Recebe solicitações na estrutura."},
                    ]
                }
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Componentes",
        requirements=[],
        max_calls=1,
    )
    assert report["attempts"][0]["accepted"]
    assert path + ".label" in report["attempts"][0]["paths"]
    assert path + ".detail" in report["attempts"][0]["paths"]
    assert "slides.0.title" in report["attempts"][0]["paths"]
    assert result["slides"][0]["columns"][0]["content"][1] == col["content"][1]
    schema = adapter.calls[0]["response_schema"]
    assert schema["properties"]["edits"]["additionalProperties"] is False
    raw = json.loads((tmp_path / "review/attempt_1/raw.txt").read_text(encoding="utf-8"))
    assert isinstance(raw["edits"], dict)
    assert (tmp_path / "review/attempt_1/normalized_response.json").exists()


def test_general_example_and_unqualified_failure_isolation_are_flagged():
    data = semantic_data("benefit_cards", 1)
    col = data["slides"][0]["columns"][0]
    col["content"][0].update(
        role="example", explanation="Cada camada pode mudar sem afetar o todo."
    )
    col["items"] = [ContentBlock.model_validate(col["content"][0]).full_text()]
    audit = audit_semantics(data)
    assert {"Q002", "Q008"} <= {d["code"] for d in audit["diagnostics"]}
    assert not audit["factual_verified"]


def test_reviewer_preserves_existing_valid_source_ids(tmp_path):
    data = semantic_data("concept_map", 1)
    block = data["slides"][0]["columns"][0]["content"][0]
    block.update(role="claim", sources=["original", "invalid"])
    chunks = [
        {"id": "original", "text": "Recebe solicitações."},
        {"id": "other", "text": "Outra fonte."},
    ]
    adapter = ReviewAnswers(
        [
            json.dumps(
                {"edits": [{"path": "slides.0.columns.0.content.0.sources", "value": ["other"]}]}
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Fontes",
        requirements=[],
        chunks=chunks,
        grounding="grounded",
        max_calls=1,
    )
    assert result == data and not report["attempts"][0]["accepted"]
    assert report["attempts"][0]["reason"] == "regression_or_information_removed"


@pytest.mark.parametrize(
    "negation",
    ["Sem imagens ou rodapé.", "Sem imagem e rodapé.", "Não inclua imagens, rodapé ou formas."],
)
def test_coordinated_negations_do_not_create_positive_requirements(negation):
    from slidedsl.requirements import extract_requirements

    criteria = extract_requirements(
        "Crie dois slides. Slide 1: Conceito. Slide 2: Exemplo. " + negation, 2
    )
    assert not {"images", "footer", "shapes"} & {c["kind"] for c in criteria}


def test_unavailable_reviewer_does_not_count_or_reuse_previous_http_response(tmp_path):
    adapter = ReviewAnswers([])
    adapter.available = lambda: (False, "indisponível")
    adapter.last_request = {"old": True}
    adapter.last_response = {"message": {"content": "old"}}
    data = repetition_data()
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Estrutura",
        requirements=[],
        max_calls=1,
    )
    assert result == data and report["calls"] == 0 and not adapter.calls
    assert (
        json.loads((tmp_path / "review/attempt_1/response.json").read_text(encoding="utf-8"))
        is None
    )


def test_missing_serialized_sources_can_be_repaired_locally(tmp_path):
    data = semantic_data("concept_map", 1)
    block = data["slides"][0]["columns"][0]["content"][0]
    block["role"] = "claim"
    block.pop("sources")
    chunks = [{"id": "original_c1", "text": "Recebe solicitações."}]
    adapter = ReviewAnswers(
        [
            json.dumps(
                {
                    "edits": [
                        {"path": "slides.0.columns.0.content.0.sources", "value": ["original_c1"]}
                    ]
                }
            )
        ]
    )
    result, report = review_plan(
        data,
        tmp_path / "review",
        adapter=adapter,
        request="Fontes",
        requirements=[],
        chunks=chunks,
        grounding="grounded",
        max_calls=1,
    )
    assert report["attempts"][0]["accepted"]
    assert result["slides"][0]["columns"][0]["content"][0]["sources"] == ["original_c1"]
    assert result["slides"][0]["columns"][0]["items"] == data["slides"][0]["columns"][0]["items"]
