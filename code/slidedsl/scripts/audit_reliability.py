"""Audit immutable HTTP answers, paired plans, patch scope and native PPTX texts."""

from collections import defaultdict
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from slidedsl.evolution import apply_patch_response
from slidedsl.incremental import save_json, sha
from slidedsl.reliability import evaluate_state


def audit(out):
    out = Path(out)
    config = json.loads((out / "configuration.json").read_text(encoding="utf-8"))
    for name, digest in config["source_hashes"].items():
        assert sha((out / "sources_snapshot" / name).read_text(encoding="utf-8")) == digest
    evaluation = json.loads((out / "evaluation.json").read_text(encoding="utf-8"))
    groups = defaultdict(set)
    calls, tokens, pptx_count, attempts = 0, 0, 0, 0
    for response_file in out.rglob("response.json"):
        response = json.loads(response_file.read_text(encoding="utf-8"))
        assert response["done"] and response["done_reason"] == "stop"
        assert response_file.with_name("raw.txt").read_bytes() == response["message"][
            "content"
        ].encode("utf-8")
        request = json.loads(response_file.with_name("request.json").read_text(encoding="utf-8"))
        assert request["model"] == config["model"]
        assert request["format"]
        assert request["options"]["temperature"] == config["temperature"]
        assert request["options"]["num_ctx"] == config["num_ctx"]
        assert request["options"]["num_predict"] == config["num_predict"]
        assert request["options"]["seed"] in range(42, 42 + config["repetitions"])
        calls += 1
        tokens += response.get("eval_count", 0)
    for row in evaluation["runs"]:
        groups[(row["case"], row["repeat"])].add(row["initial_plan_sha256"])
        folder = out / row["path"]
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        criteria = json.loads((folder / "requirements.json").read_text(encoding="utf-8"))
        case = next(c for c in config["cases"] if c["id"] == row["case"])
        assert criteria == case["requirements"]
        current = json.loads((folder / "initial_plan.json").read_text(encoding="utf-8"))
        initial_path = folder.parent / "initial/plan.json"
        assert current == json.loads(initial_path.read_text(encoding="utf-8"))
        for attempt in report["attempts"]:
            repair = folder / f"repair_{attempt['attempt']}"
            before = json.loads((repair / "before.json").read_text(encoding="utf-8"))
            candidate = json.loads((repair / "candidate.json").read_text(encoding="utf-8"))
            after = json.loads((repair / "after.json").read_text(encoding="utf-8"))
            assert before == current
            if attempt["accepted"]:
                edits = []
                for path in attempt["paths"]:
                    value = candidate
                    for token in path.split("."):
                        value = value[int(token)] if isinstance(value, list) else value[token]
                    edits.append({"path": path, "value": value})
                assert (
                    apply_patch_response(before, json.dumps({"edits": edits}), attempt["paths"])
                    == candidate
                )
                assert after == candidate
            else:
                assert after == before
            current = after
            attempts += 1
        assert current == json.loads((folder / "plan.json").read_text(encoding="utf-8"))
        state = evaluate_state(current, case["slides"], criteria)
        assert state["requirements"]["items"] == report["requirements"]["items"]
        if row["compile_success"]:
            assert state["valid"]
            with ZipFile(folder / "presentation.pptx") as z:
                for slide in state["validation"].ir.slides:
                    root = ET.fromstring(z.read(f"ppt/slides/slide{slide.number}.xml"))
                    ns = {
                        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
                        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
                    }
                    actual = [
                        "\n".join("".join(p.itertext()) for p in sp.findall("p:txBody/a:p", ns))
                        for sp in root.findall("p:cSld/p:spTree/p:sp", ns)
                        if sp.find("p:txBody", ns) is not None
                    ]
                    expected = [e.text for e in slide.elements if e.type == "text"]
                    assert sorted(actual) == sorted(expected), (
                        folder,
                        slide.number,
                        actual,
                        expected,
                    )
            pptx_count += 1
    assert all(len(hashes) == 1 for hashes in groups.values())
    assert calls == evaluation["actual_calls"]
    result = {
        "passed": True,
        "paired_groups": len(groups),
        "initial_plans_identical": True,
        "actual_http_calls": calls,
        "actual_output_tokens": tokens,
        "pptx_inspected": pptx_count,
        "attempts_checked": attempts,
        "raw_bytes_verified": True,
        "criteria_immutable": True,
        "scope_and_rollbacks_verified": True,
        "snapshot_hashes_verified": True,
    }
    save_json(out / "audit.json", result)
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    audit(sys.argv[1])
