"""Frozen baseline/treatment runs and paired review, with unscored human rubric."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def freeze(root, out, baseline):
    for mode in ("control", "after"):
        folder = out / "runtime" / mode / "src/slidedsl"
        if folder.exists():
            continue
        folder.mkdir(parents=True)
        if mode == "after":
            shutil.copytree(
                root / "src/slidedsl",
                folder,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        else:
            files = (
                subprocess.check_output(
                    ["git", "ls-tree", "-r", "--name-only", baseline, "src/slidedsl"], cwd=root
                )
                .decode()
                .splitlines()
            )
            for name in files:
                target = out / "runtime" / mode / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(
                    subprocess.check_output(
                        ["git", "show", f"{baseline}:code/slidedsl/{name}"], cwd=root
                    )
                )
        hashes = {
            p.relative_to(folder.parent.parent).as_posix(): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in folder.rglob("*")
            if p.is_file()
        }
        write(out / "runtime" / mode / "hashes.json", hashes)


def worker(root, out, mode, case):
    # Imports happen only in a child whose PYTHONPATH selects the frozen version.
    from slidedsl.contextual import generate_contextual
    from slidedsl.models.ollama_model import OllamaTextModel
    from slidedsl.reliability import run_reliability
    from slidedsl.semantic_planning import review_plan

    folder = out / case["id"] / mode
    started = time.perf_counter()
    if mode == "review":
        folder.mkdir(parents=True, exist_ok=False)
        origin = root / "outputs/semantic/experiment_02" / case["id"] / "B"
        initial = json.loads((origin / "semantic_review/plan.json").read_text("utf-8"))
        requirements = json.loads((origin / "requirements.json").read_text("utf-8"))
        write(folder / "initial_plan.json", initial)
        write(folder / "requirements.json", requirements)
        plan, review = review_plan(
            initial,
            folder / "semantic_review",
            adapter=OllamaTextModel("qwen3:4b-instruct", context_length=8192, output_tokens=4096),
            request=case["prompt"],
            requirements=requirements,
            max_calls=2,
        )
        report = run_reliability(
            plan,
            case["prompt"],
            folder / "validated",
            count=len(plan["slides"]),
            requirements=requirements,
            mode="validator",
            repair_max=0,
            strict=True,
        )
        report["semantic_review"] = review
        for name in ("plan.json", "ir.json", "presentation.sld", "presentation.pptx"):
            if (folder / "validated" / name).exists():
                shutil.copyfile(folder / "validated" / name, folder / name)
    else:
        report = generate_contextual(
            "qwen3:4b-instruct",
            "C",
            case["prompt"],
            folder,
            context={
                "semantic_planning": True,
                "conceptual_planning": True,
                "semantic_review_max": 2,
                "research": "off",
            }
            if mode == "after"
            else {"semantic_planning": True, "research": "off"},
            repair_max=0,
            strict=True,
            seed=42,
        )
    report["experiment_wall_ms"] = (time.perf_counter() - started) * 1000
    write(folder / "report.json", report)
    # project_root refers to the real assets/renderer. Record the actual Python
    # sources imported by this isolated child, replacing the generic root copy.
    runtime = out / "runtime" / ("after" if mode == "review" else mode)
    hashes_path = folder / "source_hashes.json"
    hashes = json.loads(hashes_path.read_text("utf-8")) if hashes_path.exists() else {}
    for p in (runtime / "src/slidedsl").rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            relative = p.relative_to(runtime)
            target = folder / "sources_snapshot" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, target)
            hashes[relative.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    write(hashes_path, hashes)
    write(
        folder / "execution.json",
        {"module": generate_contextual.__code__.co_filename, "runtime": str(runtime), "mode": mode},
    )
    print(case["id"], mode, "PPTX", report.get("compile_success"), flush=True)


def summarize(root, out, manifest, cases):
    from evaluate_semantic_planning import audit_calls
    from slidedsl.compiler import inspect_pptx
    from slidedsl.ir import Presentation
    from slidedsl.pipeline import validate_source

    rows = []
    for case in cases:
        for mode in ("control", "after", "review"):
            folder = out / case["id"] / mode
            if not (folder / "report.json").exists():
                continue
            report = json.loads((folder / "report.json").read_text("utf-8"))
            native = (
                inspect_pptx(folder / "presentation.pptx")
                if (folder / "presentation.pptx").exists()
                else None
            )
            validation = (
                validate_source((folder / "presentation.sld").read_text("utf-8"))
                if (folder / "presentation.sld").exists()
                else None
            )
            if native:
                ir = Presentation.model_validate_json((folder / "ir.json").read_text("utf-8"))
                for scene, slide in zip(ir.slides, native["slides"], strict=True):
                    texts = {x["name"]: x["text"] for x in slide["objects"]}
                    assert all(texts[e.id] == e.text for e in scene.elements if e.type == "text")
            rows.append(
                {
                    "case": case["id"],
                    "held_out": case.get("held_out", False),
                    "condition": mode,
                    "path": folder.relative_to(root).as_posix(),
                    "plan_valid": (folder / "plan.json").exists(),
                    "dsl_parse": bool(validation and validation.parse_success),
                    "dsl_semantics": bool(validation and validation.semantic_success),
                    "pptx_strict": bool(native),
                    "native_text_verified": bool(native),
                    "requirements": report.get("requirements"),
                    "diagnostics": report.get("diagnostics"),
                    "review": report.get("semantic_review"),
                    "wall_ms": report.get("experiment_wall_ms"),
                    "human_assessment": {
                        key: None for key in manifest["rubric"] if key not in {"dsl", "cost"}
                    },
                }
            )
    calls = audit_calls(out)
    write(out / "evaluation.json", {"configuration": manifest, "rows": rows, "audit": calls})
    write(
        out / "human_rubric.json",
        {
            "rubric": manifest["rubric"],
            "cases": cases,
            "rows": [
                {
                    "case": r["case"],
                    "condition": r["condition"],
                    "assessment": r["human_assessment"],
                    "evidence": [],
                }
                for r in rows
            ],
        },
    )
    print(
        json.dumps(
            {
                "calls": calls["actual_calls"],
                "pptx": {
                    mode: sum(r["pptx_strict"] for r in rows if r["condition"] == mode)
                    for mode in ("control", "after", "review")
                },
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--requests-file", default="benchmark/content_requests.json")
    parser.add_argument(
        "--mode", choices=["control", "after", "review", "summarize"], required=True
    )
    parser.add_argument("--case", help="Optional single case")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    configuration = out / "configuration.json"
    manifest = json.loads(
        (configuration if configuration.exists() else root / args.requests_file).read_text("utf-8")
    )
    known = json.loads((root / manifest["known_manifest"]).read_text("utf-8"))["cases"]
    cases = []
    for item in known + manifest["held_out"]:
        case = dict(item)
        case["prompt"] = (
            (root / case["prompt_file"]).read_text("utf-8-sig")
            if "prompt_file" in case
            else case["prompt"]
        )
        case["held_out"] = case["id"] in {c["id"] for c in manifest["held_out"]}
        cases.append(case)
    frozen_cases = out / "cases.json"
    if frozen_cases.exists():
        cases = json.loads(frozen_cases.read_text("utf-8"))
    elif args.mode != "summarize":
        write(frozen_cases, cases)
    if args.worker:
        worker(root, out, args.mode, next(c for c in cases if c["id"] == args.case))
    elif args.mode == "summarize":
        summarize(root, out, manifest, cases)
    else:
        freeze(root, out, manifest["baseline_commit"])
        if not configuration.exists():
            write(configuration, manifest)
            shutil.copyfile(Path(__file__), out / "runner_snapshot.py")
        for case in cases:
            if args.case and case["id"] != args.case or args.mode == "review" and case["held_out"]:
                continue
            if (out / case["id"] / args.mode).exists():
                continue  # Resume only missing cases; never overwrite evidence.
            write(out / case["id"] / "request.json", case)
            env = dict(
                os.environ,
                PYTHONPATH=str(
                    out / "runtime" / ("after" if args.mode == "review" else args.mode) / "src"
                ),
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
                    "--mode",
                    args.mode,
                    "--case",
                    case["id"],
                    "--worker",
                ],
                env=env,
                cwd=root,
                check=True,
            )
