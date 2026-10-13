"""Offline audit of frozen content trials; never assigns factual/human scores."""

import argparse
from collections import Counter
import hashlib
from html import escape
import json
from pathlib import Path
import zipfile

from evaluate_semantic_planning import audit_calls, digest
from slidedsl.compiler import inspect_pptx
from slidedsl.connections import anchored_connections
from slidedsl.incremental import save_json
from slidedsl.ir import Presentation


def read(path):
    return json.loads(path.read_text("utf-8"))


def native_check(folder, dsl="presentation.sld", pptx="presentation.pptx"):
    from slidedsl.pipeline import validate_source

    validation = validate_source((folder / dsl).read_text("utf-8"))
    result = {
        "parse": validation.parse_success,
        "semantics": validation.semantic_success,
        "pptx": (folder / pptx).exists(),
        "native_text": None,
        "connectors": None,
    }
    if not result["pptx"]:
        return result
    ir = Presentation.model_validate_json((folder / "ir.json").read_text("utf-8"))
    native = inspect_pptx(folder / pptx)
    connections = 0
    with zipfile.ZipFile(folder / pptx) as archive:
        for scene, slide in zip(ir.slides, native["slides"], strict=True):
            texts = {o["name"]: o["text"] for o in slide["objects"]}
            for element in scene.elements:
                if element.type == "text":
                    assert texts[element.id] == element.text, element.id
            count = len(anchored_connections(scene))
            assert archive.read(slide["xml"]).decode("utf-8").count("<p:cxnSp>") == count
            connections += count
    result.update(native_text=True, connectors=connections)
    return result


def calls_for(folder):
    calls = audit_calls(folder)
    durations = []
    for response in folder.rglob("response.json"):
        if not (response.parent / "raw.txt").exists():
            continue
        data = read(response) or {}
        if data.get("eval_count"):
            durations.append(data.get("total_duration", 0) / 1e9)
    return {**calls, "ollama_total_seconds": sum(durations)}


def snapshot_check(folder, expected):
    for name, sha in expected.items():
        assert hashlib.sha256((folder / "sources_snapshot" / name).read_bytes()).hexdigest() == sha
    execution = read(folder / "execution.json")
    assert str(Path(execution["runtime"]) / "src") in execution["module"]


def content_html(folder):
    plan = read(folder / "plan.json")
    sections = []
    for i, slide in enumerate(plan["slides"], 1):
        rows = []
        for ci, column in enumerate(slide["columns"], 1):
            for bi, block in enumerate(column.get("content", []), 1):
                path = f"slides.{i - 1}.columns.{ci - 1}.content.{bi - 1}"
                rows.append(
                    "<li><code>"
                    + escape(path)
                    + "</code><br><b>"
                    + escape(block["label"])
                    + "</b> ["
                    + escape(block.get("role", ""))
                    + "]<p>"
                    + escape(block.get("detail", ""))
                    + "</p><p>"
                    + escape(block.get("explanation", ""))
                    + "</p></li>"
                )
        sections.append(
            f"<section><h4>{i}. {escape(slide['title'])}</h4><ul>"
            + "".join(rows)
            + "</ul><pre>"
            + escape(json.dumps(slide.get("relationships", []), ensure_ascii=False))
            + "</pre></section>"
        )
    return "".join(sections)


def audit(root, first, fresh, ui, out):
    out.mkdir(parents=True, exist_ok=False)
    first_hash = read(first / "runtime/after/hashes.json")
    fresh_hash = read(fresh / "runtime/after/hashes.json")
    assert first_hash == fresh_hash
    for name, sha in first_hash.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha
    rows, decisions, pairs, html = [], [], [], []
    conditions = Counter()
    cost = {}
    cases = read(first / "cases.json")
    for case in cases:
        held = case["held_out"]
        run = fresh if held else first
        case = next(c for c in read(run / "cases.json") if c["id"] == case["id"])
        cells = []
        for mode in ("control", "after", "review"):
            folder = run / case["id"] / mode
            if not (folder / "report.json").exists():
                continue
            expected = read(
                run / "runtime" / ("after" if mode == "review" else mode) / "hashes.json"
            )
            snapshot_check(folder, expected)
            report = read(folder / "report.json")
            native = native_check(folder)
            calls = calls_for(folder)
            cost.setdefault(mode, Counter()).update(
                calls=calls["actual_calls"],
                input_tokens=calls["input_tokens"],
                output_tokens=calls["output_tokens"],
                wall_seconds=report["experiment_wall_ms"] / 1000,
                ollama_seconds=calls["ollama_total_seconds"],
            )
            conditions[mode] += native["pptx"]
            for attempt in sorted((folder / "semantic_review").glob("attempt_*")):
                decision = read(attempt / "decision.json")
                before, after = read(attempt / "before.json"), read(attempt / "after.json")
                if not decision["accepted"]:
                    assert before == after
                else:
                    candidate = read(attempt / "candidate_audit.json")
                    old = read(attempt / "before_audit.json")
                    assert len(candidate["diagnostics"]) < len(old["diagnostics"])
                    assert not any(decision.get("regressions", {}).values())
                decisions.append(
                    {"case": case["id"], "condition": mode, "attempt": attempt.name, **decision}
                )
            if mode == "review":
                historical = root / "outputs/semantic/experiment_02" / case["id"] / "B"
                initial = read(folder / "initial_plan.json")
                assert initial == read(historical / "semantic_review/plan.json")
                assert read(folder / "requirements.json") == read(historical / "requirements.json")
                pairs.append(
                    {
                        "case": case["id"],
                        "same_initial_plan": True,
                        "hash": digest(initial),
                        "same_requirements": True,
                    }
                )
            rows.append(
                {
                    "case": case["id"],
                    "held_out": held,
                    "condition": mode,
                    "path": folder.relative_to(root).as_posix(),
                    **native,
                    "calls": calls,
                    "requirements": report.get("requirements"),
                    "projection": report.get("conceptual_projection"),
                    "human_assessment": None,
                    "factual_score": None,
                }
            )
            if mode != "review":
                cells.append(f"<article><h3>{mode}</h3>" + content_html(folder) + "</article>")
        html.append(
            f"<h2>{escape(case['id'])}</h2><p>{escape(case['prompt'])}</p><div>"
            + "".join(cells)
            + "</div>"
        )
    ui_calls = calls_for(ui)
    development = []
    for folder in sorted((root / "outputs/conceptual").glob("experiment_*")) + [first, fresh, ui]:
        responses = []
        for response in folder.rglob("response.json"):
            if not (response.parent / "raw.txt").exists():
                continue
            data = read(response) or {}
            if data.get("eval_count"):
                responses.append(data)
        development.append(
            {
                "path": folder.relative_to(root).as_posix(),
                "calls": len(responses),
                "input_tokens": sum(r.get("prompt_eval_count", 0) for r in responses),
                "output_tokens": sum(r.get("eval_count", 0) for r in responses),
            }
        )
    result = {
        "selection": "Four known pairs and historical reviews from final_08; UTF-8 fresh pairs from final_11.",
        "runtime_identical": True,
        "rows": rows,
        "pptx_counts": conditions,
        "cost": cost,
        "paired_review": pairs,
        "decisions": decisions,
        "ui": {
            "path": ui.relative_to(root).as_posix(),
            "calls": ui_calls,
            "native": native_check(ui, "ui_export.sld", "ui_export.pptx"),
            "evidence": read(ui / "ui_evidence.json"),
        },
        "development": development,
        "development_totals": {
            key: sum(row[key] for row in development)
            for key in ("calls", "input_tokens", "output_tokens")
        },
        "human_assessment": None,
        "factual_score": None,
    }
    save_json(out / "audit.json", result)
    (out / "comparison.html").write_text(
        "<!doctype html><meta charset='utf-8'><title>Comparação de conteúdo</title>"
        "<style>body{font:16px system-ui;margin:2rem;color:#152332}div{display:grid;grid-template-columns:1fr 1fr;gap:2rem}"
        "article{background:#f3f6fa;padding:1rem}li{margin:1rem 0}code{font-size:12px}p{line-height:1.5}"
        "@media(max-width:900px){div{display:block}}</style><h1>Conteúdo antes/depois</h1>"
        "<p>Texto integral dos planos finais, incluindo falhas de exportação. Não é renderização PPTX nem avaliação factual.</p>"
        + "".join(html),
        "utf-8",
    )
    print(
        json.dumps({"pptx": conditions, "cost": cost, "development": result["development_totals"]})
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--known", required=True)
    parser.add_argument("--fresh", required=True)
    parser.add_argument("--ui", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    audit(root, *(Path(p).resolve() for p in (args.known, args.fresh, args.ui, args.out)))
