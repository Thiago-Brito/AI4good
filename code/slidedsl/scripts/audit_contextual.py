"""Audit executed snapshots, paired plans, immutable criteria and native PPTX text."""

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

from slidedsl.compiler import inspect_pptx
from slidedsl.incremental import save_json


def audit(folder):
    evaluation = json.loads((folder / "evaluation.json").read_text("utf-8"))
    cfg = json.loads((folder / "configuration.json").read_text("utf-8"))
    checked = 0
    for path in [folder, *folder.glob("*/planned"), *folder.glob("sources_*")]:
        hashes = path / "source_hashes.json"
        if hashes.exists():
            for name, digest in json.loads(hashes.read_text("utf-8")).items():
                assert (
                    hashlib.sha256((path / "sources_snapshot" / name).read_bytes()).hexdigest()
                    == digest
                )
                checked += 1
    responses, tokens, digests, schema_checks = [], 0, set(), 0
    for file in folder.rglob("response.json"):
        data = json.loads(file.read_text("utf-8"))
        if not data or "message" not in data:
            continue
        assert data["done"] and data["done_reason"] == "stop"
        raw = file.parent / "raw.txt"
        # A historical incremental baseline uses output.txt, not raw.txt.
        if not raw.exists():
            raw = file.parent / "output.txt"
        if not raw.exists():
            options = list(file.parent.glob("*.txt"))
            raw = next(
                (p for p in options if p.read_bytes() == data["message"]["content"].encode()), None
            )
        assert raw and raw.read_bytes() == data["message"]["content"].encode("utf-8")
        request = json.loads((file.parent / "request.json").read_text("utf-8"))
        assert request["model"] == cfg["model"] and request["options"]["seed"] == cfg["seed"]
        assert request["options"]["temperature"] == cfg["temperature"]
        if isinstance(request.get("format"), dict):
            Draft202012Validator(request["format"]).validate(json.loads(data["message"]["content"]))
            schema_checks += 1
        responses.append(file.relative_to(folder).as_posix())
        tokens += data.get("eval_count", 0)
    for file in folder.rglob("model_show.json"):
        # Digest is recorded in report metadata; /api/show describes the model.
        json.loads(file.read_text("utf-8"))
    for file in folder.rglob("report.json"):
        report = json.loads(file.read_text("utf-8"))
        digest = (report.get("model_metadata") or {}).get("model_digest")
        if digest:
            digests.add(digest)
    pairs = []
    for case in cfg["cases"]:
        plan_file = folder / case["id"] / "planned/plan.json"
        if not plan_file.exists():
            pairs.append({"case": case["id"], "reached": False})
            continue
        initial = json.loads(plan_file.read_text("utf-8"))
        encoded = json.dumps(initial, sort_keys=True).encode()
        sha = hashlib.sha256(encoded).hexdigest()
        for condition in ["baseline", "validator", "deterministic"]:
            path = folder / case["id"] / condition
            assert json.loads((path / "initial_plan.json").read_text("utf-8")) == initial
            assert (
                json.loads((path / "requirements.json").read_text("utf-8")) == case["requirements"]
            )
        pairs.append({"case": case["id"], "initial_plan_sha256": sha, "conditions": 3})
    pptx = []
    for file in folder.rglob("presentation.pptx"):
        # Intermediate initial files with unresolved aliases are not condition exports.
        ir = file.parent / "ir.json"
        if not ir.exists():
            continue
        deck = json.loads(ir.read_text("utf-8"))
        inspection = inspect_pptx(file)
        assert len(deck["slides"]) == inspection["slide_count"]
        for scene, actual in zip(deck["slides"], inspection["slides"], strict=True):
            expected = Counter(
                e["text"] for e in scene["elements"] if e["type"] == "text" and e["text"]
            )
            emitted = Counter(o["text"] for o in actual["objects"] if o["text"])
            assert expected == emitted, file
            assert sum(e["type"] == "image" for e in scene["elements"]) == sum(
                o["kind"] == "pic" for o in actual["objects"]
            )
        pptx.append(file.relative_to(folder).as_posix())
    grouped = defaultdict(list)
    for row in evaluation["rows"]:
        grouped[row["condition"]].append(row)
    assert (
        len(responses) == evaluation["actual_http_calls"] and tokens == evaluation["output_tokens"]
    )
    result = {
        "actual_http_calls": len(responses),
        "output_tokens": tokens,
        "model_digests": sorted(digests),
        "snapshot_files_checked": checked,
        "schema_responses_checked": schema_checks,
        "paired_initial_plans": pairs,
        "pptx_files_checked": pptx,
        "conditions": {
            key: {
                "compiled": sum(r["compile_success"] for r in rows),
                "total": len(rows),
                "requirements_met": sum(r["requirements_met"] for r in rows),
                "requirements_total": sum(r["requirements_total"] for r in rows),
            }
            for key, rows in grouped.items()
        },
        "human_evaluation_applied": False,
        "response_paths": responses,
        "scope": "Verifica evidência de execução, igualdade de planos e objetos nativos; não mede estética, relevância ou verdade factual.",
    }
    save_json(folder / "audit.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), ensure_ascii=True, indent=2))
