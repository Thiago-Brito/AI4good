"""Four-domain exploratory A/B/C comparison, sharing B's exact plan with C."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import time

from jsonschema import Draft202012Validator

from slidedsl.compiler import inspect_pptx
from slidedsl.contextual import generate_contextual
from slidedsl.incremental import save_json
from slidedsl.models.ollama_model import OllamaTextModel
from slidedsl.paths import project_root
from slidedsl.reliability import run_reliability
from slidedsl.semantic_planning import audit_semantics, review_plan


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def row(case, condition, folder, report, terms):
    plan_path = folder / "plan.json"
    data = json.loads(plan_path.read_text("utf-8")) if plan_path.exists() else None
    audit = audit_semantics(data) if data else None
    ir_path = folder / "ir.json"
    scene = json.loads(ir_path.read_text("utf-8")) if ir_path.exists() else None
    text = (
        " ".join(e.get("text") or "" for s in scene["slides"] for e in s["elements"]).casefold()
        if scene
        else ""
    )
    native = (
        inspect_pptx(folder / "presentation.pptx")
        if (folder / "presentation.pptx").exists()
        else None
    )
    bodies = (
        [
            e["font_size"]
            for s in scene["slides"]
            for e in s["elements"]
            if e["type"] == "text" and e.get("role") == "corpo"
        ]
        if scene
        else []
    )
    roles = (
        Counter(
            b.get("role", "legacy")
            for s in data["slides"]
            for c in s["columns"]
            for b in c.get("content", [])
        )
        if data
        else Counter()
    )
    return {
        "case": case,
        "condition": condition,
        "json_valid": bool(data),
        "pptx_strict": bool(native),
        "requirements": report.get("requirements"),
        "declared_terms": {term: term.casefold() in text for term in terms},
        "geometry_reached": bool(scene),
        "minimum_body_font": min(bodies) if bodies else None,
        "semantic_flags": Counter(d["code"] for d in audit["diagnostics"]) if audit else None,
        "roles": roles,
        "native": native,
        "editorial_audit": audit,
        "conceptual_accuracy": None,
        "example_relevance": None,
        "message_entailment": None,
        "human_visual_assessment": None,
        "duration_ms": report.get("duration_ms"),
        "review_attempts": report.get("semantic_review", {}).get("attempts", []),
        "path": folder.relative_to(project_root()).as_posix(),
    }


def audit_calls(out):
    calls = []
    snapshots = 0
    for response_path in sorted(out.rglob("response.json")):
        response = json.loads(response_path.read_text("utf-8"))
        if not response or "message" not in response:
            continue
        folder = response_path.parent
        request = json.loads((folder / "request.json").read_text("utf-8"))
        raw_path = folder / "raw.txt"
        assert raw_path.read_bytes() == response["message"]["content"].encode("utf-8")
        assert request["model"] == "qwen3:4b-instruct"
        assert request["options"] == {
            "temperature": 0.1,
            "num_ctx": 8192,
            "num_predict": 4096,
            "seed": 42,
        }
        assert request["stream"] is False and request["think"] is False
        try:
            Draft202012Validator(request["format"]).validate(
                json.loads(raw_path.read_text("utf-8"))
            )
            schema_valid = True
        except Exception:
            schema_valid = False
        calls.append(
            {
                "path": folder.relative_to(out).as_posix(),
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
                "done_reason": response.get("done_reason"),
                "raw_schema_valid": schema_valid,
            }
        )
    for hashes_path in out.rglob("source_hashes.json"):
        hashes = json.loads(hashes_path.read_text("utf-8"))
        for relative, expected in hashes.items():
            actual = hashlib.sha256(
                (hashes_path.parent / "sources_snapshot" / relative).read_bytes()
            ).hexdigest()
            assert expected == actual, relative
            snapshots += 1
    return {
        "actual_calls": len(calls),
        "input_tokens": sum(c["input_tokens"] for c in calls),
        "output_tokens": sum(c["output_tokens"] for c in calls),
        "calls": calls,
        "snapshot_files_verified": snapshots,
        "factual_verified": False,
    }


def evaluate(out, manifest, reuse=None):
    root = project_root()
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / "configuration.json", manifest)
    if reuse:
        previous = json.loads((reuse / "configuration.json").read_text("utf-8"))
        for key in ("cases", "model", "seed", "temperature", "num_ctx", "num_predict", "strict"):
            assert manifest[key] == previous[key], key
        save_json(
            out / "reuse.json",
            {
                "origin": reuse.relative_to(root).as_posix(),
                "scope": "A/B copied byte-for-byte and audited with current criteria; C reviews exact saved B initial plans.",
            },
        )
        hashes = {}
        for pattern in (
            "src/slidedsl/**/*.py",
            "src/slidedsl/grammar/*.lark",
            "config/*.yaml",
            "editor/src/*",
            "renderer/render.mjs",
            "scripts/evaluate_semantic_planning.py",
            "pyproject.toml",
            "requirements-lock.txt",
            "renderer/package-lock.json",
            "editor/package-lock.json",
        ):
            for file in root.glob(pattern):
                if file.is_file():
                    relative = file.relative_to(root)
                    target = out / "sources_snapshot" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(file, target)
                    hashes[relative.as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
        save_json(out / "source_hashes.json", hashes)
    rows, pairs = [], []
    for case in manifest["cases"]:
        request = (
            (root / case["prompt_file"]).read_text("utf-8-sig")
            if "prompt_file" in case
            else case["prompt"]
        )
        save_json(out / case["id"] / "request.json", {"request": request, "terms": case["terms"]})
        for condition in ("A", "B"):
            folder = out / case["id"] / condition
            if reuse:
                origin = reuse / case["id"] / condition
                folder.mkdir()
                for name in (
                    "plan.json",
                    "presentation.sld",
                    "presentation.pptx",
                    "ir.json",
                    "report.json",
                    "requirements.json",
                ):
                    if (origin / name).exists():
                        shutil.copyfile(origin / name, folder / name)
                report = json.loads((folder / "report.json").read_text("utf-8"))
                print(
                    f"{case['id']} {condition}: plano preservado, zero chamadas novas", flush=True
                )
            else:
                print(f"{case['id']} {condition}: Qwen3 local", flush=True)
                report = generate_contextual(
                    manifest["model"],
                    "C",
                    request,
                    folder,
                    context={
                        "expressive_planning": True,
                        "semantic_planning": condition == "B",
                        "research": "off",
                    },
                    repair_max=0,
                    seed=manifest["seed"],
                    strict=True,
                )
            rows.append(row(case["id"], condition, folder, report, case["terms"]))
            save_json(out / "evaluation.partial.json", rows)
        base = out / case["id"] / "B"
        plan_path = (reuse / case["id"] / "B" if reuse else base) / "semantic_review/plan.json"
        folder = out / case["id"] / "C"
        folder.mkdir()
        if not plan_path.exists():
            rows.append(
                {
                    "case": case["id"],
                    "condition": "C",
                    "skipped": "Initial B JSON invalid; no regeneration.",
                }
            )
            continue
        data = json.loads(plan_path.read_text("utf-8"))
        requirements = json.loads((base / "requirements.json").read_text("utf-8"))
        save_json(folder / "initial_plan.json", data)
        save_json(folder / "requirements.json", requirements)
        snapshot_origin = out if reuse else base
        shutil.copytree(snapshot_origin / "sources_snapshot", folder / "sources_snapshot")
        shutil.copyfile(snapshot_origin / "source_hashes.json", folder / "source_hashes.json")
        print(f"{case['id']} C: revisão do mesmo plano B", flush=True)
        started = time.perf_counter()
        adapter = OllamaTextModel(manifest["model"], context_length=8192, output_tokens=4096)
        reviewed, review = review_plan(
            deepcopy(data),
            folder / "semantic_review",
            adapter=adapter,
            request=request,
            requirements=requirements,
            max_calls=manifest["review_max"],
            seed=manifest["seed"],
        )
        report = run_reliability(
            reviewed,
            request,
            folder / "validated",
            count=len(data["slides"]),
            requirements=requirements,
            mode="validator",
            repair_max=0,
            strict=True,
        )
        report.update(semantic_review=review, duration_ms=(time.perf_counter() - started) * 1000)
        for name in ["plan.json", "presentation.sld", "presentation.pptx", "ir.json"]:
            if (folder / "validated" / name).exists():
                shutil.copyfile(folder / "validated" / name, folder / name)
        save_json(folder / "report.json", report)
        pairs.append(
            {
                "case": case["id"],
                "B_initial_hash": digest(data),
                "C_initial_hash": digest(
                    json.loads((folder / "initial_plan.json").read_text("utf-8"))
                ),
                "identical": True,
                "requirements_hash": digest(requirements),
            }
        )
        rows.append(row(case["id"], "C", folder, report, case["terms"]))
        save_json(out / "evaluation.partial.json", rows)
    audit = audit_calls(out)
    if reuse:
        prior_calls = [
            c for c in audit_calls(reuse)["calls"] if c["path"].split("/")[1] in {"A", "B"}
        ]
        audit["reused_initial_calls"] = prior_calls
        audit["reused_initial_input_tokens"] = sum(c["input_tokens"] for c in prior_calls)
        audit["reused_initial_output_tokens"] = sum(c["output_tokens"] for c in prior_calls)
    result = {
        "protocol": manifest["protocol"],
        "rows": rows,
        "paired_initial": pairs,
        "audit": audit,
        "factual_accuracy": None,
        "aesthetic_quality": None,
    }
    save_json(out / "evaluation.json", result)
    save_json(out / "audit.json", audit)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "calls": audit["actual_calls"],
                "pptx": {
                    c: sum(bool(r.get("pptx_strict")) for r in rows if r["condition"] == c)
                    for c in "ABC"
                },
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests-file", default="benchmark/semantic_requests.json")
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--reuse-existing",
        help="Reuse A/B from an earlier frozen experiment; only C may call Ollama.",
    )
    args = parser.parse_args()
    evaluate(
        Path(args.out).resolve(),
        json.loads(Path(args.requests_file).read_text("utf-8")),
        Path(args.reuse_existing).resolve() if args.reuse_existing else None,
    )
