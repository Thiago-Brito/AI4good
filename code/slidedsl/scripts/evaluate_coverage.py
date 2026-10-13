"""Frozen A/B/C runs plus exact-selection replay; never overwrite experimental evidence."""

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from evaluate_content_planning import freeze, write


def read(path):
    return json.loads(path.read_text("utf-8"))


def prepare(root, out, seeds):
    configuration = out / "configuration.json"
    if configuration.exists():
        return read(configuration)
    manifest = read(root / "benchmark/content_final_requests.json")
    known = read(root / manifest["known_manifest"])["cases"]
    cases = known + manifest["held_out"]
    for case in cases:
        if "prompt_file" in case:
            case["prompt"] = (root / case["prompt_file"]).read_text("utf-8-sig")
    freeze(root, out, manifest["baseline_commit"])
    shutil.copytree(out / "runtime/control", out / "runtime/A")
    shutil.copytree(root / "outputs/coverage/investigation_01/runtime/B", out / "runtime/B")
    shutil.copytree(out / "runtime/after", out / "runtime/C")
    for mode in ("A", "B", "C"):
        write(
            out / "runtime" / mode / "hashes.json",
            {
                p.relative_to(out / "runtime" / mode).as_posix(): hashlib.sha256(
                    p.read_bytes()
                ).hexdigest()
                for p in (out / "runtime" / mode / "src").rglob("*")
                if p.is_file()
            },
        )
    data = {
        "protocol": "coverage-abc-v1",
        "cases": cases,
        "seeds": seeds,
        "model": "qwen3:4b-instruct",
        "temperature": 0.1,
        "num_ctx": 8192,
        "num_predict": 4096,
        "thinking": False,
        "baseline_commit": manifest["baseline_commit"],
        "review_max_B_C": 2,
        "repair_max": 0,
        "scope": "A historical semantic; B frozen pre-coverage conceptual; C coverage enabled. Prompts/schemas differ only as required for coverage in B/C. Matched replay uses identical C records and original selection, no SLM review. IDs do not prove semantic fulfillment. Independent human assessment is null.",
    }
    write(configuration, data)
    shutil.copyfile(Path(__file__), out / "runner_snapshot.py")
    return data


def run_worker(root, out, config, case, condition, seed):
    from slidedsl.contextual import generate_contextual

    folder = out / f"seed_{seed}" / case["id"] / condition
    context = {"semantic_planning": True, "research": "off"}
    if condition in {"B", "C"}:
        context.update(conceptual_planning=True, semantic_review_max=2)
    if condition == "C":
        context.update(coverage_validation=True, coverage_recovery=True)
    started = time.perf_counter()
    try:
        report = generate_contextual(
            config["model"],
            "C",
            case["prompt"],
            folder,
            context=context,
            repair_max=0,
            strict=True,
            seed=seed,
        )
        report["experiment_wall_ms"] = (time.perf_counter() - started) * 1000
        write(folder / "report.json", report)
        print(case["id"], condition, seed, "PPTX", report.get("compile_success"), flush=True)
    except Exception as exc:
        folder.mkdir(parents=True, exist_ok=True)
        write(
            folder / "execution_error.json",
            {
                "type": type(exc).__name__,
                "error": str(exc),
                "wall_ms": (time.perf_counter() - started) * 1000,
            },
        )
        print(case["id"], condition, seed, "FAILED", type(exc).__name__, str(exc), flush=True)
    write(
        folder / "execution.json",
        {"module": generate_contextual.__code__.co_filename, "condition": condition, "seed": seed},
    )
    snapshot = out / "runtime" / condition
    # Record and copy the imported snapshot, not the live project files.
    for p in (snapshot / "src").rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            target = folder / "sources_snapshot" / p.relative_to(snapshot)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
    hashes_path = folder / "source_hashes.json"
    hashes = read(hashes_path) if hashes_path.exists() else {}
    hashes.update(read(snapshot / "hashes.json"))
    write(hashes_path, hashes)


def replay(root, out, config):
    from slidedsl.conceptual_planning import materialize_concepts
    from slidedsl.coverage import recover_selection, validate_coverage
    from slidedsl.ir import Presentation
    from slidedsl.compiler import inspect_pptx
    from slidedsl.reliability import run_reliability

    for seed in config["seeds"]:
        for case in config["cases"]:
            source = out / f"seed_{seed}" / case["id"] / "C"
            if (
                not (source / "visual_outline/outline.json").exists()
                or not (source / "conceptual_plan/plan.json").exists()
            ):
                continue
            requirements = read(source / "content_requirements.json")
            conceptual = read(source / "conceptual_plan/plan.json")
            outline = read(source / "visual_outline/outline.json")
            structural = read(source / "requirements.json")
            origin_hash = hashlib.sha256(
                (source / "visual_outline/outline.json").read_bytes()
            ).hexdigest()
            conceptual_hash = hashlib.sha256(
                (source / "conceptual_plan/plan.json").read_bytes()
            ).hexdigest()
            for enabled in (False, True):
                folder = (
                    out
                    / "replay"
                    / f"seed_{seed}"
                    / case["id"]
                    / ("recovery" if enabled else "validation")
                )
                if folder.exists():
                    continue
                started = time.perf_counter()
                folder.mkdir(parents=True)
                selected, plan, recovery = recover_selection(
                    requirements, conceptual, outline, structural, enabled=enabled
                )
                write(folder / "recovery.json", recovery)
                write(folder / "outline.json", selected)
                write(
                    folder / "origin.json",
                    {
                        "path": source.relative_to(out).as_posix(),
                        "outline_sha256": origin_hash,
                        "conceptual_sha256": conceptual_hash,
                        "calls": 0,
                        "review_calls": 0,
                    },
                )
                materialize_concepts(
                    conceptual, selected
                )  # Validate the exact selected contract again.
                report = run_reliability(
                    plan,
                    case["prompt"],
                    folder / "validated",
                    count=len(plan["slides"]),
                    requirements=structural,
                    mode="validator",
                    repair_max=0,
                    strict=True,
                )
                ir_path = folder / "validated/ir.json"
                ir = (
                    Presentation.model_validate_json(ir_path.read_text("utf-8"))
                    if ir_path.exists()
                    else None
                )
                mapping_path = folder / "validated/element_paths.json"
                mapping = read(mapping_path) if mapping_path.exists() else {}
                native_path = folder / "validated/presentation.pptx"
                native = inspect_pptx(native_path) if native_path.exists() else None
                final = validate_coverage(
                    requirements,
                    conceptual,
                    selected,
                    read(folder / "validated/plan.json"),
                    ir,
                    mapping,
                    native,
                )
                write(folder / "coverage.json", final)
                write(
                    folder / "report.json",
                    {
                        **report,
                        "coverage": final,
                        "coverage_recovery": recovery,
                        "experiment_wall_ms": (time.perf_counter() - started) * 1000,
                    },
                )
                print(
                    "REPLAY",
                    case["id"],
                    seed,
                    enabled,
                    "accepted",
                    recovery["accepted"],
                    flush=True,
                )


def summarize(root, out, config):
    from jsonschema import Draft202012Validator
    from slidedsl.compiler import inspect_pptx
    from slidedsl.pipeline import validate_source

    rows, calls, fragments = [], [], []
    for folder in sorted(out.glob("seed_*/*/*")) + sorted(out.glob("replay/seed_*/*/*")):
        if not (folder / "report.json").exists():
            continue
        report = read(folder / "report.json")
        native_root = folder / "validated" if "replay" in folder.parts else folder
        source_path = native_root / "presentation.sld"
        v = validate_source(source_path.read_text("utf-8")) if source_path.exists() else None
        native_path = native_root / "presentation.pptx"
        native = inspect_pptx(native_path) if native_path.exists() else None
        if native:
            assert len(v.ir.slides) == native["slide_count"]
            for scene, slide in zip(v.ir.slides, native["slides"], strict=True):
                texts = {e["name"]: e["text"] for e in slide["objects"]}
                assert all(texts.get(e.id) == e.text for e in scene.elements if e.type == "text")
        coverage = report.get("coverage")
        recovery = report.get("coverage_recovery", {})
        rows.append(
            {
                "path": folder.relative_to(out).as_posix(),
                "condition": folder.name,
                "case": folder.parent.name,
                "seed": folder.parent.parent.name,
                "replay": "replay" in folder.parts,
                "parse": bool(v and v.parse_success),
                "semantics": bool(v and v.semantic_success),
                "pptx": bool(native),
                "native_text_verified": bool(native),
                "represented": coverage["represented_required"] if coverage else None,
                "required": coverage["required_count"] if coverage else None,
                "retained_complete": coverage["structural_retention_complete"]
                if coverage
                else None,
                "unselected": coverage["unselected"]
                if coverage
                else report.get("conceptual_projection", {}).get("unselected"),
                "recoveries_accepted": recovery.get("accepted", 0),
                "recoveries_rejected": recovery.get("rejected", 0),
                "diagnostics": report.get("diagnostics"),
                "coverage_diagnostics": coverage["diagnostics"] if coverage else None,
                "wall_ms": report.get("experiment_wall_ms"),
                "independent_human_assessment": None,
            }
        )
        texts = (
            [
                f"Slide {s.number}\n" + "\n".join(e.text for e in s.elements if e.type == "text")
                for s in v.ir.slides
            ]
            if v and v.ir
            else []
        )
        fragments.append(
            f"<h2>{html.escape(folder.relative_to(out).as_posix())}</h2><pre>{html.escape(chr(10).join(texts))}</pre>"
        )
    for response_path in sorted(out.glob("seed_*/**/response.json")):
        response = read(response_path)
        if not response or "message" not in response:
            continue
        request = read(response_path.parent / "request.json")
        raw = (response_path.parent / "raw.txt").read_bytes()
        assert raw == response["message"]["content"].encode("utf-8")
        assert request["model"] == config["model"] and request["think"] is False
        assert request["options"]["temperature"] == config["temperature"]
        assert request["options"]["num_ctx"] == config["num_ctx"]
        assert request["options"]["num_predict"] == config["num_predict"]
        assert request["options"]["seed"] in config["seeds"]
        try:
            Draft202012Validator(request["format"]).validate(json.loads(raw))
            schema_valid = True
        except Exception:
            schema_valid = False
        calls.append(
            {
                "path": response_path.parent.relative_to(out).as_posix(),
                "input_tokens": response.get("prompt_eval_count", 0),
                "output_tokens": response.get("eval_count", 0),
                "http_ns": response.get("total_duration", 0),
                "done_reason": response.get("done_reason"),
                "raw_schema_valid": schema_valid,
            }
        )
    # Audit imported source snapshots independently of reports.
    hashes_checked = 0
    for execution in out.glob("seed_*/*/*/execution.json"):
        folder = execution.parent
        mode = read(execution)["condition"]
        assert (
            Path(read(execution)["module"]).resolve()
            == (out / "runtime" / mode / "src/slidedsl/contextual.py").resolve()
        )
        for name, digest in read(out / "runtime" / mode / "hashes.json").items():
            assert (
                hashlib.sha256((folder / "sources_snapshot" / name).read_bytes()).hexdigest()
                == digest
            )
            hashes_checked += 1
    audit = {
        "calls": len(calls),
        "input_tokens": sum(c["input_tokens"] for c in calls),
        "output_tokens": sum(c["output_tokens"] for c in calls),
        "http_seconds": sum(c["http_ns"] for c in calls) / 1e9,
        "rows": calls,
        "hashes_checked": hashes_checked,
    }
    write(out / "evaluation.json", {"configuration": config, "rows": rows, "audit": audit})
    (out / "comparison.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Cobertura A/B/C e replay</title><style>body{font-family:system-ui;max-width:1100px;margin:auto}pre{white-space:pre-wrap}</style>"
        + "\n".join(fragments),
        "utf-8",
    )
    print(
        json.dumps(
            {
                "calls": audit["calls"],
                "pptx": {
                    mode: sum(r["pptx"] for r in rows if r["condition"] == mode)
                    for mode in ("A", "B", "C", "validation", "recovery")
                },
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42])
    parser.add_argument("--mode", choices=["generate", "replay", "summarize"], default="generate")
    parser.add_argument("--condition", choices=["A", "B", "C"])
    parser.add_argument("--case")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    config = prepare(root, out, args.seeds)
    if args.worker:
        run_worker(
            root,
            out,
            config,
            next(c for c in config["cases"] if c["id"] == args.case),
            args.condition,
            args.seed,
        )
    elif args.mode == "summarize":
        summarize(root, out, config)
    elif args.mode == "replay":
        replay(root, out, config)
    else:
        for seed in config["seeds"]:
            for case in config["cases"]:
                for mode in ("A", "B", "C"):
                    if (
                        args.condition
                        and args.condition != mode
                        or args.case
                        and args.case != case["id"]
                    ):
                        continue
                    folder = out / f"seed_{seed}" / case["id"] / mode
                    if folder.exists():
                        continue
                    env = dict(
                        os.environ,
                        PYTHONPATH=str(out / "runtime" / mode / "src"),
                        SLIDEDSL_ROOT=str(root),
                        PYTHONDONTWRITEBYTECODE="1",
                        PYTHONUTF8="1",
                    )
                    subprocess.run(
                        [
                            sys.executable,
                            str(Path(__file__).resolve()),
                            "--out",
                            str(out),
                            "--case",
                            case["id"],
                            "--condition",
                            mode,
                            "--seed",
                            str(seed),
                            "--worker",
                        ],
                        env=env,
                        cwd=root,
                        check=True,
                    )
