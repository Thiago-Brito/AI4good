"""Offline comparison on identical recorded content and audit of actual local calls."""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import zipfile

from jsonschema import Draft202012Validator

from slidedsl.connections import NS
from slidedsl.expressive_composition import composition_report
from slidedsl.incremental import save_json
from slidedsl.layouts import compile_plan
from slidedsl.pipeline import validate_source
from slidedsl.paths import project_root
from slidedsl.planning import ContentBlock, DeckPlan
from slidedsl.requirements import evaluate_requirements
from slidedsl.visual_validation import check_visual


def read(path):
    return json.loads(path.read_text("utf-8"))


def inspect(folder):
    data = read(folder / "plan.json")
    validation = validate_source((folder / "presentation.sld").read_text("utf-8"))
    assert validation.success(strict=True)
    visual = check_visual(validation.ir)
    assert not [d for d in visual if d["severity"] == "ERRO"]
    rows = []
    with zipfile.ZipFile(folder / "presentation.pptx") as z:
        for spec, scene in zip(data["slides"], validation.ir.slides, strict=True):
            xml = ET.fromstring(z.read(f"ppt/slides/slide{scene.number}.xml"))
            native = ["".join(n.itertext()) for n in xml.findall(".//p:txBody", NS)]
            texts = [e.text for e in scene.elements if e.type == "text"]
            assert all(t in native for t in texts)
            if spec.get("expressive"):
                for col in spec["columns"]:
                    for block in col["content"]:
                        assert all(
                            not block[key] or block[key] in texts
                            for key in ["label", "detail", "explanation"]
                        )
            rows.append(
                {
                    "slide": scene.number,
                    "native_texts": len(native),
                    "images": len(xml.findall(".//p:pic", NS)),
                    "anchored_connections": len(xml.findall(".//p:cxnSp", NS)),
                    "body_font_min": min(
                        e.font_size
                        for e in scene.elements
                        if e.type == "text" and e.role == "corpo" and not e.id.endswith("_rodape")
                    ),
                    "explanations": sum(
                        bool(n["explanation"])
                        for c in spec["columns"]
                        for n in c.get("content", [])
                    ),
                }
            )
    reqs = data.get("refinement", {}).get("requirements", [])
    return {
        "folder": str(folder),
        "slides": rows,
        "requirements": evaluate_requirements(validation, reqs, data),
        "strict_valid": True,
        "visual_errors": [],
        "diagnostics": [d.model_dump() for d in validation.diagnostics],
        "aesthetic_assessment": None,
        "office_rendering": False,
    }


def audit_calls(generation):
    calls = []
    for raw_file in sorted(generation.rglob("raw.txt")):
        folder = raw_file.parent
        request, response = read(folder / "request.json"), read(folder / "response.json")
        assert response["done"] and response["done_reason"] == "stop"
        raw = raw_file.read_bytes()
        assert raw == response["message"]["content"].encode("utf-8")
        options = request["options"]
        assert options == {"temperature": 0.1, "seed": 42, "num_ctx": 8192, "num_predict": 4096}
        assert request["model"] == "qwen3:4b-instruct"
        try:
            Draft202012Validator(request["format"]).validate(json.loads(raw))
            schema_valid = True
        except Exception:
            schema_valid = False  # Rejected real outputs remain evidence, never become successes.
        calls.append(
            {
                "path": str(folder),
                "schema_valid": schema_valid,
                "input_tokens": response["prompt_eval_count"],
                "output_tokens": response["eval_count"],
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    for name, digest in read(generation / "source_hashes.json").items():
        assert (
            hashlib.sha256((generation / "sources_snapshot" / name).read_bytes()).hexdigest()
            == digest
        )
    return calls


def compare(before, after, out):
    out.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for file in (
        list((project_root() / "src/slidedsl").rglob("*.py"))
        + list((project_root() / "src/slidedsl/grammar").glob("*.lark"))
        + list((project_root() / "config").glob("*.yaml"))
        + [project_root() / "renderer/render.mjs", Path(__file__)]
    ):
        relative = file.resolve().relative_to(project_root())
        target = out / "sources_snapshot" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        hashes[relative.as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    save_json(out / "source_hashes.json", hashes)
    fixed = out / "fixed_after"
    fixed.mkdir()
    original = read(before / "plan.json")
    converted = deepcopy(original)
    for slide in converted["slides"]:
        slide.update(expressive=True, composition="auto")
        for col in slide["columns"]:
            nodes = []
            for text in col["items"]:
                label, separator, detail = text.partition(": ")
                node = (
                    ContentBlock(label=label, detail=detail)
                    if separator
                    else ContentBlock(label="Síntese", detail=text)
                )
                nodes.append(node)
            col["content"] = [n.model_dump() for n in nodes]
            # Items retain every original byte except the explicit label for unstructured prose.
            col["items"] = [n.full_text() for n in nodes]
    plan = DeckPlan.model_validate(converted)
    result = compile_plan(plan, fixed / "presentation.pptx", strict=True)
    (fixed / "presentation.sld").write_text(result["source"], "utf-8")
    save_json(fixed / "plan.json", plan.model_dump())
    save_json(fixed / "composition.json", composition_report(plan))
    # Archive original source for reproducible paired viewing; no historical output is rewritten.
    baseline = out / "fixed_before"
    baseline.mkdir()
    for name in ["plan.json", "presentation.sld", "presentation.pptx"]:
        shutil.copyfile(before / name, baseline / name)
    for old, new in zip(original["slides"], converted["slides"], strict=True):
        restored = deepcopy(new)
        restored.pop("expressive")
        restored.pop("composition")
        for previous, column in zip(old["columns"], restored["columns"], strict=True):
            nodes = column.pop("content")
            assert len(nodes) == len(previous["items"])
            for value, block in zip(previous["items"], nodes, strict=True):
                node = ContentBlock.model_validate(block)
                assert (node.full_text() if ": " in value else node.detail) == value
            column["items"] = previous["items"]
        assert restored == old
    prompt_before = (before / "visual_outline/user.txt").read_text("utf-8").split("\nContexto")[0]
    prompt_after = (after / "visual_outline/user.txt").read_text("utf-8").split("\nContexto")[0]
    assert prompt_before == prompt_after
    assert (
        read(before / "report.json")["model_metadata"]["model_digest"]
        == read(after / "report.json")["model_metadata"]["model_digest"]
    )
    fixed_audit = inspect(fixed)
    current = out / "generated_after"
    current.mkdir()
    authored = DeckPlan.model_validate(read(after / "plan.json"))
    compiled = compile_plan(authored, current / "presentation.pptx", strict=True)
    (current / "presentation.sld").write_text(compiled["source"], "utf-8")
    save_json(current / "plan.json", authored.model_dump())
    save_json(current / "composition.json", composition_report(authored))
    assert authored.model_dump() == read(after / "plan.json")
    report = {
        "fixed_content": {
            "before": inspect(before),
            "after": fixed_audit,
            "all_original_fields_preserved": True,
            "added_labels_for_prose": "Síntese",
            "semantic_rewrite": False,
        },
        "new_local_generation": {
            "before": inspect(before),
            "after": inspect(after),
            "same_model_and_request": True,
            "same_initial_content": False,
            "causal_claim": None,
        },
        "current_recompilation": {
            "origin": str(after),
            "content_unchanged": True,
            **inspect(current),
        },
        "calls": {
            str(p): audit_calls(p)
            for p in sorted(before.parent.iterdir())
            if p.is_dir() and (p / "source_hashes.json").is_file()
        },
        "aesthetic_assessment": None,
    }
    save_json(out / "comparison.json", report)
    print("Comparação offline e bytes/schema/snapshots das chamadas auditados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    compare(args.before, args.after, args.out)
