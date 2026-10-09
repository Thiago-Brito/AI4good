import json

import httpx
import pytest

from slidedsl import incremental
from slidedsl.models.ollama_model import OllamaTextModel
from slidedsl.pipeline import validate_source
from slidedsl.structured_slide import SlideOutput, json_to_dsl


def slide_json(x=80):
    data = {
        "elements": [
            {
                "type": "text",
                "id": "titulo",
                "text": "Teste do conteúdo",
                "x": x,
                "y": 64,
                "width": 1100,
                "height": 110,
                "font_size": "titulo",
                "color": "texto",
                "role": "titulo",
            },
            {
                "type": "text",
                "id": "corpo",
                "text": "Um conteúdo original para o teste.",
                "x": 80,
                "y": 220,
                "width": 1100,
                "height": 120,
                "font_size": "corpo",
                "color": "texto",
                "role": "corpo",
            },
        ],
        "operations": [],
    }
    title, *texts = data.pop("elements")
    data.update(title=title, texts=texts, shapes=[], images=[])
    return json.dumps(data, ensure_ascii=False)


class TestAdapter:
    __test__ = False

    def __init__(self, answers, done_reason="stop"):
        self.answers = iter(answers)
        self.metadata = {"provider": "test", "done_reason": done_reason}
        self.last_response = {"done": True}
        self.last_request = None
        self.prompts = []

    def available(self):
        return True, "Adapter exclusivo de teste"

    def generate(self, system, user, **kwargs):
        self.prompts.append(user)
        self.last_request = {"system": system, "user": user, **kwargs}
        return next(self.answers)


def compile_spy(monkeypatch):
    calls = []

    def compile(source, out, strict=False):
        assert validate_source(source).success(strict)
        calls.append(source)
        return {"inspection": {"slide_count": 5}}

    monkeypatch.setattr(incremental, "compile_source", compile)
    return calls


def test_structured_output_passes_original_parser_and_semantics():
    raw = slide_json()
    source = json_to_dsl(raw)
    result = validate_source(source)
    assert result.success(strict=True)
    assert result.ast.slides[0].commands[0].text == "Teste do conteúdo"
    assert result.ir.slides[0].elements[0].x == 80
    assert json_to_dsl(raw) == source


def test_json_geometry_is_not_repaired_or_clamped():
    source = json_to_dsl(slide_json(x=1200))
    result = validate_source(source)
    assert result.parse_success and result.semantic_success
    assert any(d.code == "D001" for d in result.diagnostics)
    assert result.ir.slides[0].elements[0].x == 1200


def test_json_rejects_unknown_fields_and_invented_image_files():
    data = json.loads(slide_json())
    data["title"]["unknown"] = "not allowed"
    with pytest.raises(ValueError):
        json_to_dsl(json.dumps(data))
    data = json.loads(slide_json())
    data["images"].append(
        {
            "type": "image",
            "id": "foto",
            "file": "../secret.png",
            "x": 64,
            "y": 400,
            "width": 50,
            "height": 50,
            "role": "decoracao",
        }
    )
    with pytest.raises(ValueError):
        json_to_dsl(json.dumps(data))


def test_schema_request_preserves_content_and_full_api_body():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"]})
        return httpx.Response(
            200,
            json={
                "message": {"content": slide_json(), "thinking": "separado"},
                "done": True,
                "done_reason": "stop",
                "eval_count": 100,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        model = OllamaTextModel("qwen3:4b-instruct", client=client, output_tokens=4096)
        schema = SlideOutput.model_json_schema()
        assert model.generate("s", "u", response_schema=schema) == slide_json()
        assert requests[-1]["format"] == schema
        assert model.last_request["options"]["num_predict"] == 4096
        assert model.last_response["message"]["thinking"] == "separado"


@pytest.mark.parametrize("mode", ["json", "direct"])
def test_five_slides_use_original_pipeline_before_compilation(mode, monkeypatch, tmp_path):
    calls = compile_spy(monkeypatch)
    raw = slide_json() if mode == "json" else json_to_dsl(slide_json())
    adapter = TestAdapter([raw] * 5)
    out = tmp_path / "deck"
    report = incremental.generate_deck("unit", mode, "Crie cinco slides", out, adapter=adapter)
    assert report["compile_success"] and report["is_mock"]
    assert len(adapter.prompts) == 5 and len(calls) == 1
    result = validate_source((out / "presentation.sld").read_text(encoding="utf-8"))
    assert [s.number for s in result.ast.slides] == [1, 2, 3, 4, 5]
    assert len(result.ir.slides) == 5
    with pytest.raises(ValueError):
        incremental.publish_demo(out, report)
    with pytest.raises(FileExistsError):
        incremental.generate_deck("unit", mode, "Crie cinco slides", out, adapter=adapter)


def test_repair_preserves_failure_and_explicit_feedback(monkeypatch, tmp_path):
    compile_spy(monkeypatch)
    bad = slide_json(x=1200)
    adapter = TestAdapter([bad] + [slide_json()] * 5)
    out = tmp_path / "repair"
    report = incremental.generate_deck("unit", "json", "Crie cinco slides", out, adapter=adapter)
    assert report["compile_success"] and report["corrections"] == 1
    assert "D001" in adapter.prompts[1]
    assert (out / "slides/slide_01/round_0/raw.txt").read_text(encoding="utf-8") == bad
    assert report["slides"][0]["selected_round"] == 1


@pytest.mark.parametrize(
    "raw,reason", [("", "stop"), ("inválido", "stop"), (slide_json(), "length")]
)
def test_exhausted_repairs_never_replace_model_output(raw, reason, monkeypatch, tmp_path):
    calls = compile_spy(monkeypatch)
    adapter = TestAdapter([raw] * 15, done_reason=reason)
    out = tmp_path / "failure"
    report = incremental.generate_deck("unit", "json", "Crie cinco slides", out, adapter=adapter)
    assert not report["compile_success"] and not calls
    assert report["corrections"] == 10
    assert not (out / "presentation.sld").exists()
    assert not (out / "presentation.pptx").exists()
    assert all(len(s["rounds"]) == 3 for s in report["slides"])
    assert (out / "slides/slide_01/round_0/raw.txt").read_text(encoding="utf-8") == raw


def test_duplicate_ids_still_fail_existing_semantics():
    data = json.loads(slide_json())
    data["texts"][0]["id"] = "titulo"
    result = validate_source(json_to_dsl(json.dumps(data)))
    assert result.parse_success and not result.semantic_success
    assert result.diagnostics[0].code == "S002"


def test_focus_extracts_user_request_without_manual_slide_content():
    prompt = incremental.slide_prompt(
        "Slide 1: capa. Slide 2: árvores. Slide 3: rios.", 2, [], "json"
    )
    assert "REQUISITO DESTE SLIDE: árvores." in prompt


def test_evaluation_resume_rejects_configuration_change(monkeypatch, tmp_path):
    out = tmp_path / "evaluation"
    out.mkdir()
    incremental.save_json(out / "configuration.json", {})
    with pytest.raises(ValueError, match="configuração"):
        incremental.evaluate_incremental(["unit"], ["json"], "Pedido", out, resume=True)


def test_direct_numbering_normalization_is_recorded(monkeypatch, tmp_path):
    compile_spy(monkeypatch)
    source = json_to_dsl(slide_json())
    answers = [source.replace("slide 1", f"slide {n}") for n in range(1, 6)]
    adapter = TestAdapter(answers)
    report = incremental.generate_deck(
        "unit", "direct", "Cinco slides", tmp_path / "deck", adapter=adapter
    )
    assert report["compile_success"]
    assert report["slides"][2]["rounds"][0]["normalization"]["original_slide_number"] == 3
    raw = (tmp_path / "deck/slides/slide_03/round_0/raw.txt").read_text(encoding="utf-8")
    assert "slide 3" in raw
