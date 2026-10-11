"""Audit shared content, actual model responses and native editable output.

No aesthetic score or unobserved Office rendering is inferred from these checks.
"""

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

from jsonschema import Draft202012Validator

from slidedsl.connections import NS
from slidedsl.incremental import save_json
from slidedsl.pipeline import validate_source
from slidedsl.refinement import normalized
from slidedsl.requirements import evaluate_requirements
from slidedsl.visual_validation import check_visual


def read(file):
    return json.loads(file.read_text("utf-8"))


def audit(before, after, generation=None):
    first, final = read(before / "plan.json"), read(after / "plan.json")
    first.pop("refinement", None)
    final.pop("refinement", None)
    assert first == final, "Comparison changed the shared content plan"
    report = read(after / "refinement.json")
    validation = validate_source((after / "presentation.sld").read_text("utf-8"))
    assert validation.success(strict=True)
    criteria = read(after / "plan.json").get("refinement", {}).get("requirements", [])
    original_validation = validate_source((before / "presentation.sld").read_text("utf-8"))
    original_requirements = evaluate_requirements(original_validation, criteria, first)
    final_requirements = evaluate_requirements(validation, criteria, final)
    assert all(
        not met or final_requirements["items"][key]
        for key, met in original_requirements["items"].items()
    )
    deck = validation.ir
    slides = []
    with zipfile.ZipFile(after / "presentation.pptx") as archive:
        for spec, scene, refinement in zip(
            final["slides"], deck.slides, report["slides"], strict=True
        ):
            texts = [e.text for e in scene.elements if e.type == "text"]
            emitted = normalized(" ".join(texts))
            assert normalized(spec["title"]) in emitted
            for ci, column in enumerate(spec["columns"]):
                assert normalized(column["heading"]) in emitted
                for ti, value in enumerate(column["items"]):
                    if normalized(value) in emitted:
                        continue
                    path = f"slides.{scene.number - 1}.columns.{ci}.items.{ti}"
                    duplicates = [d for d in refinement.get("duplicates", []) if d["path"] == path]
                    assert duplicates, (path, value)
                    for d in duplicates:
                        if d.get("kind") == "component_label_prefix":
                            label, _, detail = value.partition(": ")
                            assert detail.casefold().startswith(label.casefold() + " ")
                            assert (
                                d["retained_text"] == label + ": " + detail[len(label) :].lstrip()
                            )
                            assert normalized(d["retained_text"]) in emitted
                        else:
                            assert normalized(d["text"]) in normalized(spec["title"])
                            label = value.partition(": ")[0] if ": " in value else ""
                            assert normalized(label) in emitted
            root = ET.fromstring(archive.read(f"ppt/slides/slide{scene.number}.xml"))
            native = ["".join(n.itertext()) for n in root.findall(".//p:txBody", NS)]
            assert all(text in native for text in texts)
            ids = {e.get("id") for e in root.findall(".//p:cNvPr", NS)}
            links = root.findall(".//p:cxnSp", NS)
            for link in links:
                assert link.find(".//a:stCxn", NS).get("id") in ids
                assert link.find(".//a:endCxn", NS).get("id") in ids
            slides.append(
                {
                    "slide": scene.number,
                    "content_conserved": True,
                    "native_texts": len(texts),
                    "native_anchored_connections": len(links),
                    "title_fonts": sorted(
                        {e.font_size for e in scene.elements if e.role == "titulo"}
                    ),
                    "body_fonts": sorted(
                        {
                            e.font_size
                            for e in scene.elements
                            if e.type == "text" and e.role == "corpo"
                        }
                    ),
                    "refined": refinement["accepted"],
                    "duplicates": refinement.get("duplicates", []),
                }
            )
    compiled_snapshots = 0
    for name, digest in read(after / "source_hashes.json").items():
        assert (
            hashlib.sha256((after / "sources_snapshot" / name).read_bytes()).hexdigest() == digest
        )
        compiled_snapshots += 1
    calls, input_tokens, output_tokens, snapshots = 0, 0, 0, 0
    if generation:
        for file in generation.rglob("response.json"):
            response = read(file)
            if "message" not in response:
                continue
            assert response["done"] and response["done_reason"] == "stop"
            raw = (file.parent / "raw.txt").read_bytes()
            assert raw == response["message"]["content"].encode("utf-8")
            request = read(file.parent / "request.json")
            assert request["model"] == "qwen3:4b-instruct"
            assert request["options"] == {
                "temperature": 0.1,
                "seed": 42,
                "num_ctx": 8192,
                "num_predict": 4096,
            }
            Draft202012Validator(request["format"]).validate(json.loads(raw))
            calls += 1
            input_tokens += response["prompt_eval_count"]
            output_tokens += response["eval_count"]
        for name, digest in read(generation / "source_hashes.json").items():
            assert (
                hashlib.sha256((generation / "sources_snapshot" / name).read_bytes()).hexdigest()
                == digest
            )
            snapshots += 1
        original = read(generation / "plan.json")
        original.pop("refinement", None)
        assert original == final
    visual = check_visual(deck)
    return {
        "shared_content": True,
        "before": str(before),
        "after": str(after),
        "slides": slides,
        "strict_valid": True,
        "visual_errors": [d for d in visual if d["severity"] == "ERRO"],
        "diagnostics": [d.model_dump() for d in validation.diagnostics],
        "real_calls": calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "generation_snapshots_checked": snapshots,
        "compiled_snapshots_checked": compiled_snapshots,
        "requirements": final_requirements,
        "aesthetic_assessment": None,
        "office_rendering": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--generation", type=Path)
    args = parser.parse_args()
    result = audit(args.before, args.after, args.generation)
    save_json(args.after / "audit.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
