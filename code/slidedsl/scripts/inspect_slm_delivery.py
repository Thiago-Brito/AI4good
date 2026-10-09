"""Verify actual local responses, parsed scene provenance and native PPTX objects."""

import argparse
import hashlib
import json
from pathlib import Path

from slidedsl.compiler import inspect_pptx
from slidedsl.incremental import save_json, sha
from slidedsl.ir import semantic_snapshot
from slidedsl.pipeline import validate_source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    folder = args.folder
    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
    assert report["compile_success"] and not report["is_mock"]
    source = (folder / "presentation.sld").read_text(encoding="utf-8")
    assert sha(source) == report["source_sha256"]
    validation = validate_source(source)
    assert validation.success() and len(validation.ir.slides) == 5
    deck_snapshot = semantic_snapshot(validation.ir)
    provenance = []
    for s in report["slides"]:
        selected = s["selected_round"]
        location = folder / f"slides/slide_{s['number']:02d}/round_{selected}"
        metrics = json.loads((location / "metrics.json").read_text(encoding="utf-8"))
        raw = (location / "raw.txt").read_bytes()
        response = json.loads((location / "response.json").read_text(encoding="utf-8"))
        payload = json.loads((location / "request.json").read_text(encoding="utf-8"))
        assert raw.decode("utf-8") == response["message"]["content"]
        assert hashlib.sha256(raw).hexdigest() == metrics["raw_sha256"]
        assert sha(payload["messages"][1]["content"]) == metrics["user_sha256"]
        assert sha(payload["messages"][0]["content"]) == report["configuration"]["system_sha256"]
        individual = validate_source((location / "slide.sld").read_text(encoding="utf-8"))
        assert individual.success()
        expected = semantic_snapshot(individual.ir)["slides"][0]
        expected["number"] = s["number"]
        assert expected == deck_snapshot["slides"][s["number"] - 1]
        provenance.append(
            {
                "slide": s["number"],
                "selected_round": selected,
                "response_model": response["model"],
                "content_sha256": metrics["raw_sha256"],
                "element_count": len(expected["elements"]),
                "done_reason": response["done_reason"],
            }
        )
    inspection = inspect_pptx(folder / "presentation.pptx")
    assert inspection["slide_count"] == 5
    texts = [e.text for s in validation.ir.slides for e in s.elements if e.type == "text"]
    native_texts = [o["text"] for s in inspection["slides"] for o in s["objects"] if o["text"]]
    assert sorted(texts) == sorted(native_texts)
    audit = {
        "verified": True,
        "real_response_count": sum(len(s["rounds"]) for s in report["slides"]),
        "model": report["model"],
        "mode": report["mode"],
        "strict_valid": validation.success(True),
        "diagnostics": [d.model_dump() for d in validation.diagnostics],
        "provenance": provenance,
        "inspection": inspection,
        "source_file_sha256": hashlib.sha256(
            (folder / "presentation.sld").read_bytes()
        ).hexdigest(),
        "note": "raw hashes are exact bytes; prompt/source report hashes use UTF-8 text normalized to LF by Python text IO",
    }
    save_json(folder / "audit.json", audit)
    print(
        json.dumps(
            {
                k: audit[k]
                for k in ("verified", "real_response_count", "model", "mode", "strict_valid")
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
