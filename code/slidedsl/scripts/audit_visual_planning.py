"""Audit this requested before/after case without assigning aesthetic scores."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import zipfile

from jsonschema import Draft202012Validator

from slidedsl.compiler import inspect_pptx
from slidedsl.incremental import save_json
from slidedsl.pipeline import validate_source
from slidedsl.visual_planning import normalize_visual_response
from slidedsl.visual_validation import check_visual


def read(file):
    return json.loads(file.read_text("utf-8"))


def audit(folder):
    report = read(folder / "report.json")
    plan = read(folder / "plan.json")
    responses = []
    for file in folder.rglob("response.json"):
        response = read(file)
        if not response or "message" not in response:
            continue
        assert response["done"] and response["done_reason"] == "stop"
        raw = file.parent / "raw.txt"
        assert raw.read_bytes() == response["message"]["content"].encode("utf-8")
        request = read(file.parent / "request.json")
        assert request["options"]["seed"] == 42
        assert request["options"]["temperature"] == 0.1
        assert request["options"]["num_ctx"] == 8192
        assert request["options"]["num_predict"] == 4096
        assert request["model"] == "qwen3:4b-instruct"
        if isinstance(request.get("format"), dict):
            Draft202012Validator(request["format"]).validate(json.loads(raw.read_text("utf-8")))
        responses.append(response)
    snapshot_count = 0
    if (folder / "source_hashes.json").exists():
        for name, digest in read(folder / "source_hashes.json").items():
            assert (
                hashlib.sha256((folder / "sources_snapshot" / name).read_bytes()).hexdigest()
                == digest
            )
            snapshot_count += 1
    converted = folder / "initial/round_0/normalized_response.json"
    if converted.exists():
        wire = read(folder / "initial/round_0/response.json")["message"]["content"]
        assert normalize_visual_response(json.loads(wire), len(plan["slides"])) == read(converted)
    validation = validate_source((folder / "presentation.sld").read_text("utf-8"))
    assert validation.ir is not None
    deck = validation.ir
    inspection = inspect_pptx(folder / "presentation.pptx")
    assert inspection["slide_count"] == len(deck.slides)
    with zipfile.ZipFile(folder / "presentation.pptx") as archive:
        arrows = sum(
            archive.read(s["xml"]).count(b'prst="downArrow"') for s in inspection["slides"]
        )
    for slide, native in zip(deck.slides, inspection["slides"], strict=True):
        native_text = [o["text"] for o in native["objects"] if o["text"]]
        assert all(e.text in native_text for e in slide.elements if e.type == "text")
    for i, slide in enumerate(plan["slides"]):
        emitted = [e.text for e in deck.slides[i].elements if e.type == "text"]
        assert slide["title"] in emitted
        assert all(item in emitted for column in slide["columns"] for item in column["items"])
    bodies = [
        e.font_size
        for s in deck.slides
        for e in s.elements
        if e.type == "text" and e.role == "corpo"
    ]
    titles = [
        e.font_size
        for s in deck.slides
        for e in s.elements
        if e.type == "text" and e.role == "titulo"
    ]
    visual = check_visual(deck)
    return {
        "folder": str(folder),
        "compile_success": report["compile_success"],
        "strict_validation": validation.success(strict=True),
        "layouts": dict(Counter(s["layout"] for s in plan["slides"])),
        "slide_layouts": [s["layout"] for s in plan["slides"]],
        "model_digest": report["model_metadata"]["model_digest"],
        "responses": len(responses),
        "output_tokens": sum(r.get("eval_count", 0) for r in responses),
        "input_tokens": sum(r.get("prompt_eval_count", 0) for r in responses),
        "snapshots_checked": snapshot_count,
        "corrections": report["corrections"],
        "diagnostics": dict(Counter(d["code"] for d in report["diagnostics"])),
        "generic_requirements": report["requirements"],
        "native_objects": {
            k: inspection[k] for k in ["text_objects", "shape_objects", "image_objects"]
        },
        "native_arrows": arrows,
        "plan_text_preserved": True,
        "ir_text_in_native_pptx": True,
        "minimum_body_font": min(bodies),
        "title_fonts": sorted(set(titles)),
        "visual_box_diagnostics": visual,
        "limitation": "These measurements do not establish factual fidelity, readability in PowerPoint, aesthetics or learning. The generic requirement recognizer measures only its reported criteria.",
    }


if __name__ == "__main__":
    before, after, output = map(Path, sys.argv[1:])
    results = {
        "protocol": "visual-planning-case-v1",
        "before": audit(before),
        "after": audit(after),
        "human_participants": None,
        "aesthetic_score": None,
    }
    save_json(output, results)
    print(
        json.dumps(
            {
                label: {
                    k: results[label][k]
                    for k in [
                        "slide_layouts",
                        "responses",
                        "native_arrows",
                        "minimum_body_font",
                        "diagnostics",
                    ]
                }
                for label in ["before", "after"]
            },
            ensure_ascii=False,
        )
    )
