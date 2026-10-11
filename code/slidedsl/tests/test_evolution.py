import json

import pytest

from slidedsl import evolution
from slidedsl.compiler import inspect_pptx
from slidedsl.layouts import compile_plan, plan_to_dsl
from slidedsl.pipeline import validate_source
from slidedsl.planning import DeckPlan


def plan_data(layout="title_content"):
    return {
        "title": "Arquitetura de software",
        "theme": "claro",
        "slides": [
            {
                "title": 'Estruturas "editáveis"',
                "layout": layout,
                "columns": [
                    {
                        "heading": "Componentes",
                        "items": ["Separe responsabilidades.", "Defina interfaces claras."],
                        "group": False,
                    }
                    for _ in range(1 if layout == "title_content" else 2)
                ],
                "decorations": [],
                "relations": [],
                "footer": "Conclusão: interfaces explícitas.",
            }
        ],
    }


class Answers:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.metadata = {"provider": "test", "done_reason": "stop"}
        self.last_request = None
        self.last_response = None
        self.calls = []

    def available(self):
        return True, "Modelo exclusivo de teste"

    def generate(self, system, user, **options):
        self.calls.append({"system": system, "user": user, **options})
        raw = next(self.answers)
        self.last_request = self.calls[-1]
        self.last_response = {"message": {"content": raw}, "done": True, "done_reason": "stop"}
        return raw


@pytest.mark.parametrize("layout", ["title_content", "two_columns", "comparison"])
def test_layout_compiles_real_editable_objects_and_preserves_content(layout, tmp_path):
    plan = DeckPlan.model_validate(plan_data(layout))
    source, mapping, ds = plan_to_dsl(plan)
    assert not ds
    result = validate_source(source)
    assert result.success(strict=True)
    ids = [e.id for e in result.ir.slides[0].elements]
    assert len(ids) == len(set(ids)) == len(mapping)
    texts = [e.text for e in result.ir.slides[0].elements if e.type == "text"]
    assert plan.slides[0].title in texts
    compile_plan(plan, tmp_path / "real.pptx", strict=True)
    inspection = inspect_pptx(tmp_path / "real.pptx")
    assert inspection["slide_count"] == 1
    assert inspection["text_objects"] == len(texts)
    if layout != "title_content":
        bodies = [e for e in result.ir.slides[0].elements if "_i" in e.id]
        assert any(e.x >= 640 for e in bodies) and any(e.x < 640 for e in bodies)


def test_plan_reports_missing_reference_instead_of_guessing_or_publishing(tmp_path):
    data = plan_data()
    data["slides"][0]["relations"] = [{"kind": "left", "target": "missing", "reference": "titulo"}]
    report = evolution.generate_strategy(
        "unit", "C", "Crie um slide", tmp_path / "run", adapter=Answers([json.dumps(data)])
    )
    assert not report["valid"] and not report["compile_success"]
    assert any(d["code"] == "L002" for d in report["diagnostics"])


def test_patch_is_atomic_scoped_and_cannot_modify_unaffected_fields():
    data = plan_data()
    path = "slides.0.columns.0.items.0"
    patch = {"edits": [{"path": path, "value": "Responsabilidades bem definidas."}]}
    updated = evolution.apply_patch_response(data, json.dumps(patch), [path])
    assert (
        updated["slides"][0]["columns"][0]["items"][1]
        == data["slides"][0]["columns"][0]["items"][1]
    )
    assert data["slides"][0]["columns"][0]["items"][0] != patch["edits"][0]["value"]
    patch["edits"][0]["path"] = "title"
    with pytest.raises(Exception):
        evolution.apply_patch_response(data, json.dumps(patch), [path])


def test_d_repairs_only_affected_relation_and_exports_real_pptx(tmp_path):
    data = plan_data()
    data["slides"][0]["relations"] = [{"kind": "left", "target": "absent", "reference": "c1_i2"}]
    patch = {
        "edits": [
            {
                "path": "slides.0.relations.0",
                "value": {"kind": "left", "target": "c1_i1", "reference": "c1_i2"},
            }
        ]
    }
    adapter = Answers([json.dumps(data), json.dumps(patch)])
    report = evolution.generate_strategy(
        "unit", "D", "Crie um slide", tmp_path / "run", adapter=adapter
    )
    assert report["valid"] and report["compile_success"] and report["is_mock"]
    assert report["corrections"] == 1
    assert (
        adapter.calls[1]["response_schema"]["properties"]["edits"]["items"]["anyOf"][0][
            "properties"
        ]["path"]["const"]
        == "slides.0.relations.0"
    )
    saved = json.loads((tmp_path / "run/plan.json").read_text(encoding="utf-8"))
    assert saved["slides"][0]["columns"] == data["slides"][0]["columns"]
    with pytest.raises(FileExistsError):
        evolution.generate_strategy("unit", "D", "Crie um slide", tmp_path / "run", adapter=adapter)


def test_d_stops_after_two_repairs_and_retains_all_responses(tmp_path):
    data = plan_data()
    data["slides"][0]["relations"] = [{"kind": "front", "target": "absent", "reference": ""}]
    patch = json.dumps(
        {"edits": [{"path": "slides.0.relations.0", "value": data["slides"][0]["relations"][0]}]}
    )
    adapter = Answers([json.dumps(data), patch, patch])
    report = evolution.generate_strategy(
        "unit", "D", "Crie um slide", tmp_path / "run", adapter=adapter
    )
    assert not report["compile_success"] and report["corrections"] == 2
    assert len(list((tmp_path / "run").glob("round_*/raw.txt"))) == 3


def test_long_content_is_diagnosed_not_silently_truncated():
    data = plan_data("comparison")
    data["slides"][0]["columns"][0]["items"] = ["Conteúdo longo " * 100] * 6
    source, _, ds = plan_to_dsl(DeckPlan.model_validate(data))
    assert "Conteúdo longo " * 100 in source
    assert any(d.code == "L004" for d in ds)


def test_pptx_success_does_not_imply_requested_topics_are_met(tmp_path):
    report = evolution.generate_strategy(
        "unit",
        "C",
        "Crie um slide",
        tmp_path / "run",
        adapter=Answers([json.dumps(plan_data())]),
        requirements=[{"id": "required_topic", "slide": 1, "keywords": ["segurança"]}],
    )
    assert report["compile_success"] and not report["requirements"]["all_met"]


def test_requested_slide_count_and_schema_limit():
    assert evolution.requested_count("Crie três slides sobre componentes") == 3
    assert evolution.requested_count("Crie 7 slides") == 7
    with pytest.raises(ValueError):
        evolution.requested_count("Crie 20 slides")


def test_baseline_retains_geometry_errors_of_reached_slides_when_another_slide_fails(
    monkeypatch, tmp_path
):
    from slidedsl.incremental import error

    def rejected(*args, **kwargs):
        out = args[3]
        out.mkdir()
        return {
            "complete": True,
            "semantic_success": False,
            "compile_success": False,
            "slides": [
                {
                    "number": 1,
                    "rounds": [
                        {
                            "semantic_success": True,
                            "diagnostics": [error("D001", "Elemento fora do canvas")],
                        }
                    ],
                },
                {
                    "number": 2,
                    "rounds": [
                        {
                            "semantic_success": False,
                            "diagnostics": [error("S003", "Referência inexistente")],
                        }
                    ],
                },
            ],
        }

    monkeypatch.setattr(evolution, "generate_deck", rejected)
    report = evolution.generate_strategy("unit", "A", "Crie dois slides", tmp_path / "run")
    assert report["geometry_errors"] == 1 and report["semantic_errors"] == 1
    assert report["design_slides_reached"] == 1 and report["design_slides_potential"] == 2


def test_explicit_zero_slide_count_is_rejected_before_any_model_call(tmp_path):
    with pytest.raises(ValueError):
        evolution.generate_strategy(
            "unit", "C", "Crie cinco slides", tmp_path / "invalid", slide_count=0
        )
    assert not (tmp_path / "invalid").exists()


def test_rejected_baseline_draft_keeps_the_first_presentation_title(monkeypatch, tmp_path):
    def rejected(*args, **kwargs):
        out = args[3]
        for number, title in [(1, "Título da apresentação"), (2, "Título do último slide")]:
            folder = out / f"slides/slide_{number:02d}/round_0"
            folder.mkdir(parents=True)
            source = f'apresentacao "{title}" {{ tema claro slide 1 {{ adicionar retangulo id a em (1300,80) tamanho (100,100) cor primaria }} }}'
            (folder / "slide.sld").write_text(source, encoding="utf-8")
        return {
            "complete": True,
            "semantic_success": True,
            "compile_success": False,
            "slides": [
                {"number": number, "rounds": [{"semantic_success": True, "diagnostics": []}]}
                for number in (1, 2)
            ],
        }

    monkeypatch.setattr(evolution, "generate_deck", rejected)
    evolution.generate_strategy("unit", "A", "Crie dois slides", tmp_path / "run")
    source = (tmp_path / "run/attempted.sld").read_text(encoding="utf-8")
    assert validate_source(source).ir.title == "Título da apresentação"
