"""Audit saved real responses/scenes and recount reached-phase diagnostics."""

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

from slidedsl.compiler import inspect_pptx
from slidedsl.benchmarking import instruction_coverage
from slidedsl.evolution import apply_patch_response, assess_requirements
from slidedsl.incremental import save_json
from slidedsl.layouts import plan_to_dsl
from slidedsl.pipeline import validate_source
from slidedsl.parser import parse
from slidedsl.planning import DeckPlan


def audit(folder: Path) -> dict:
    evaluation = json.loads((folder / "evaluation.json").read_text(encoding="utf-8"))
    cfg = evaluation["configuration"]
    snapshots = folder / "sources_snapshot"
    if snapshots.is_dir():
        for name, expected in cfg["source_hashes"].items():
            assert hashlib.sha256((snapshots / name).read_bytes()).hexdigest() == expected, name
    rows, checks, responses, digests = [], [], 0, set()
    paired_initial = []
    for row in evaluation["runs"]:
        out = folder / row["path"]
        strategy = row["strategy"]
        report = json.loads(
            (
                out / ("evolution_report.json" if strategy in {"A", "B"} else "report.json")
            ).read_text(encoding="utf-8")
        )
        if report["status"] != "EXECUTADO":
            continue
        assert not report["is_mock"], f"Mock no conjunto real: {out}"
        all_diagnostics = []
        final_diagnostics = report["diagnostics"]
        reached_slides = 0
        if strategy in {"A", "B"}:
            rounds = [
                out / f"slides/slide_{s['number']:02d}/round_{r['round']}"
                for s in report["slides"]
                for r in s["rounds"]
            ]
            reached_slides = sum(s["rounds"][-1]["semantic_success"] for s in report["slides"])
        else:
            rounds = [out / f"round_{r['round']}" for r in report["rounds"]]
            if report["semantic_success"]:
                reached_slides = report["configuration"]["slide_count"]
        replay_plan = None
        for call in rounds:
            response_path, request_path = call / "response.json", call / "request.json"
            if not response_path.exists() or not (call / "raw.txt").exists():
                checks.append(
                    {"path": call.relative_to(folder).as_posix(), "transport_response": False}
                )
                continue
            request = json.loads(request_path.read_text(encoding="utf-8"))
            response = json.loads(response_path.read_text(encoding="utf-8"))
            raw = (call / "raw.txt").read_bytes()
            assert raw == response["message"]["content"].encode("utf-8"), str(call)
            assert request["model"] == cfg["model"]
            assert request["options"]["seed"] == row["seed"]
            assert request["options"]["temperature"] == cfg["options"]["temperature"]
            assert request["options"]["num_ctx"] == cfg["options"]["context_length"]
            assert request["options"]["num_predict"] == cfg["options"]["output_tokens"]
            if strategy != "A":
                assert isinstance(request.get("format"), dict)
            metrics = json.loads((call / "metrics.json").read_text(encoding="utf-8"))
            case = next(c for c in cfg["cases"] if c["id"] == row["case"])
            assert any(case["prompt"] in message["content"] for message in request["messages"]), (
                str(call)
            )
            if strategy in {"C", "D"} and (call / "plan.json").exists():
                if metrics.get("scope") == ["plan"]:
                    replay_plan = json.loads(raw)
                else:
                    replay_plan = apply_patch_response(
                        replay_plan, raw.decode("utf-8"), metrics["scope"]
                    )
                saved_plan = json.loads((call / "plan.json").read_text(encoding="utf-8"))
                assert replay_plan == saved_plan, f"Patch alterou campos não autorizados: {call}"
            all_diagnostics += metrics["diagnostics"]
            responses += 1
            checks.append(
                {
                    "path": call.relative_to(folder).as_posix(),
                    "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    "done": response.get("done"),
                    "done_reason": response.get("done_reason"),
                    "scope": metrics.get("scope"),
                    "valid": metrics["valid"],
                }
            )
        source_path = out / "presentation.sld"
        if not source_path.exists():
            source_path = out / "attempted.sld"
        case = next(c for c in cfg["cases"] if c["id"] == row["case"])
        source = source_path.read_text(encoding="utf-8") if source_path.exists() else None
        validation = validate_source(source) if source else None
        canonical_rubric = None
        canonical_title = None
        if case["original_design_rubric"] and validation:
            if strategy in {"A", "B"} and source_path.name == "attempted.sld":
                first = out / "slides/slide_01/round_0/slide.sld"
                canonical_title = parse(first.read_text(encoding="utf-8")).title
                if validation.ast:
                    validation.ast.title = canonical_title
                if validation.ir:
                    validation.ir.title = canonical_title
            canonical_rubric = instruction_coverage(validation)
        requirements = assess_requirements(validation, case["slides"], case["requirements"])
        assert requirements == report["requirements"]
        if strategy in {"C", "D"} and (out / "plan.json").exists():
            planned_source, _, _ = plan_to_dsl(
                DeckPlan.model_validate_json((out / "plan.json").read_text(encoding="utf-8"))
            )
            assert source == planned_source
        inspection = None
        if report["compile_success"]:
            assert report["valid"] and not any(d["severity"] == "ERRO" for d in final_diagnostics)
            assert validation and validation.success(cfg["options"]["strict"])
            inspection = inspect_pptx(out / "presentation.pptx")
            assert inspection["slide_count"] == case["slides"]
            for slide, native in zip(validation.ir.slides, inspection["slides"], strict=True):
                native_text = {o["name"]: o["text"] for o in native["objects"] if o["text"]}
                expected = {e.id: e.text for e in slide.elements if e.type == "text" and e.text}
                assert native_text == expected, str(out)
        digests.add(report["model_metadata"].get("model_digest"))
        counts = {
            "syntax_errors_final": sum(
                d["severity"] == "ERRO" and d["code"].startswith(("P", "J"))
                for d in final_diagnostics
            ),
            "semantic_errors_final": sum(
                d["severity"] == "ERRO" and d["code"].startswith(("S", "L002", "L003", "L005", "G"))
                for d in final_diagnostics
            ),
            "geometry_errors_final": sum(
                d["severity"] == "ERRO" and d["code"].startswith(("D", "L001", "L004"))
                for d in final_diagnostics
            )
            if reached_slides
            else None,
            "geometry_warnings_final": sum(
                d["severity"] == "AVISO" and d["code"].startswith("D") for d in final_diagnostics
            )
            if reached_slides
            else None,
            "all_round_error_codes": dict(
                Counter(d["code"] for d in all_diagnostics if d["severity"] == "ERRO")
            ),
            "design_slides_reached": reached_slides,
            "design_slides_potential": case["slides"],
        }
        rows.append(
            {
                **row,
                **counts,
                "pptx_inspection": inspection,
                "canonical_draft_title": canonical_title,
                "canonical_rubric_met": canonical_rubric["numerator"] if canonical_rubric else None,
                "canonical_rubric_total": canonical_rubric["denominator"]
                if canonical_rubric
                else None,
            }
        )
    summary = []
    for strategy in cfg["strategies"]:
        group = [r for r in rows if r["strategy"] == strategy]
        summary.append(
            {
                "strategy": strategy,
                "executed": len(group),
                "compiled": sum(r["compile_success"] for r in group),
                "requirements_met": sum(r["requirements_all_met"] for r in group),
                "syntax_errors_final": sum(r["syntax_errors_final"] for r in group),
                "semantic_errors_final": sum(r["semantic_errors_final"] for r in group),
                "geometry_errors_final": sum(r["geometry_errors_final"] or 0 for r in group),
                "geometry_warnings_final": sum(r["geometry_warnings_final"] or 0 for r in group),
                "design_slides_reached": sum(r["design_slides_reached"] for r in group),
                "design_slides_potential": sum(r["design_slides_potential"] for r in group),
                "corrections": sum(r["corrections"] for r in group),
                "duration_ms": sum(r["duration_ms"] or 0 for r in group),
            }
        )
    for case in cfg["cases"]:
        for rep in range(1, cfg["repetitions"] + 1):
            base = folder / "runs" / case["id"] / f"rep_{rep:02d}"
            c, d = base / "C/round_0/raw.txt", base / "D/round_0/raw.txt"
            if c.exists() and d.exists():
                paired_initial.append(
                    {
                        "case": case["id"],
                        "repeat": rep,
                        "identical_raw": c.read_bytes() == d.read_bytes(),
                    }
                )
    result = {
        "responses": responses,
        "digests": sorted(digests),
        "checks": checks,
        "runs": rows,
        "summary": summary,
        "paired_initial": paired_initial,
        "metric_note": "Design contado por slide alcançado; null significa nenhum slide alcançado. Erros finais e todos os códigos por rodada preservados separadamente.",
    }
    save_json(folder / "audit.json", result)
    flat = [
        {k: v for k, v in row.items() if k not in {"pptx_inspection", "all_round_error_codes"}}
        for row in rows
    ]
    if flat:
        with (folder / "audit.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(flat[0]))
            writer.writeheader()
            writer.writerows(flat)
    print(json.dumps({"responses": responses, "summary": summary}, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    audit(Path(sys.argv[1]))
