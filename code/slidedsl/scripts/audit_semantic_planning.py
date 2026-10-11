"""Audit saved bytes, paired plans, native objects and review decisions offline."""

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import zipfile

from evaluate_semantic_planning import audit_calls, digest
from slidedsl.compiler import inspect_pptx
from slidedsl.connections import anchored_connections
from slidedsl.incremental import save_json
from slidedsl.ir import Presentation


def audit(folder, out):
    out.mkdir(parents=True, exist_ok=False)
    report = json.loads((folder / "evaluation.json").read_text("utf-8"))
    rows, rollback, native_count = [], [], 0
    for row in report["rows"]:
        case, condition = row["case"], row["condition"]
        base = folder / case / condition
        ir_path, pptx = base / "ir.json", base / "presentation.pptx"
        if pptx.exists():
            native_count += 1
            ir = Presentation.model_validate_json(ir_path.read_text("utf-8"))
            native = inspect_pptx(pptx)
            with zipfile.ZipFile(pptx) as archive:
                for scene, slide in zip(ir.slides, native["slides"], strict=True):
                    texts = {o["name"]: o["text"] for o in slide["objects"]}
                    for element in scene.elements:
                        if element.type == "text":
                            assert texts[element.id] == element.text, element.id
                    xml = archive.read(slide["xml"]).decode("utf-8")
                    assert xml.count("<p:cxnSp>") == len(anchored_connections(scene))
        attempts = list((base / "semantic_review").glob("attempt_*"))
        for attempt in attempts:
            before = json.loads((attempt / "before.json").read_text("utf-8"))
            after = json.loads((attempt / "after.json").read_text("utf-8"))
            decision = json.loads((attempt / "decision.json").read_text("utf-8"))
            if not decision["accepted"]:
                assert before == after
            new_flags, new_blockers = [], []
            if (attempt / "candidate_audit.json").exists():
                old = json.loads((attempt / "before_audit.json").read_text("utf-8"))
                candidate = json.loads((attempt / "candidate_audit.json").read_text("utf-8"))
                prior = {(d["code"], d["path"]) for d in old["diagnostics"]}
                new_flags = [
                    d for d in candidate["diagnostics"] if (d["code"], d["path"]) not in prior
                ]
            if (attempt / "validation.json").exists():
                val = json.loads((attempt / "validation.json").read_text("utf-8"))
                old_errors = {
                    (d["code"], d.get("evidence", {}).get("path")) for d in val["before"]["errors"]
                }
                new_blockers = [
                    d
                    for d in val["candidate"]["errors"]
                    if (d["code"], d.get("evidence", {}).get("path")) not in old_errors
                ]
            rollback.append(
                {
                    "case": case,
                    "attempt": attempt.name,
                    **decision,
                    "new_flags": new_flags,
                    "new_blockers": new_blockers,
                    "before_equals_after": before == after,
                }
            )
        reqs = row.get("requirements") or {}
        terms = row.get("declared_terms") or {}
        rows.append(
            {
                "case": case,
                "condition": condition,
                "json": row.get("json_valid"),
                "pptx": row.get("pptx_strict"),
                "recognized_met": reqs.get("numerator"),
                "recognized_total": reqs.get("denominator"),
                "terms_met": sum(terms.values()),
                "terms_total": len(terms),
                "body_min": row.get("minimum_body_font"),
                "flags": sum((row.get("semantic_flags") or {}).values()),
                "attempts": len(attempts),
                "accepted": sum(a["accepted"] for a in row.get("review_attempts", [])),
                "conceptual_accuracy": None,
            }
        )
    for pair in report["paired_initial"]:
        case = pair["case"]
        initial = json.loads((folder / case / "C/initial_plan.json").read_text("utf-8"))
        assert pair["B_initial_hash"] == pair["C_initial_hash"] == digest(initial)
        if (folder / "reuse.json").exists():
            from slidedsl.paths import project_root

            origin = (
                project_root() / json.loads((folder / "reuse.json").read_text("utf-8"))["origin"]
            )
            original = json.loads(
                (origin / case / "B/semantic_review/plan.json").read_text("utf-8")
            )
            assert original == initial
            assert (origin / case / "B/requirements.json").read_bytes() == (
                folder / case / "C/requirements.json"
            ).read_bytes()
            for condition in ("A", "B"):
                for name in ("plan.json", "presentation.sld", "presentation.pptx", "ir.json"):
                    copied = folder / case / condition / name
                    if copied.exists():
                        assert (
                            copied.read_bytes() == (origin / case / condition / name).read_bytes()
                        )
    calls = audit_calls(folder)
    assert len(rollback) == calls["actual_calls"]
    result = {
        "rows": rows,
        "calls": calls,
        "paired_plans": report["paired_initial"],
        "native_pptx_checked": native_count,
        "rollback": rollback,
        "factual_accuracy": None,
        "human_assessment": None,
        "audit_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "decision_counts": Counter(r["reason"] for r in rollback),
    }
    save_json(out / "audit.json", result)
    with (out / "audit.csv").open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "native_pptx": native_count,
                "review_calls": calls["actual_calls"],
                "decisions": result["decision_counts"],
                "new_flags": [
                    {
                        "case": r["case"],
                        "attempt": r["attempt"],
                        "flags": [(d["code"], d["path"]) for d in r["new_flags"]],
                    }
                    for r in rollback
                ],
            },
            ensure_ascii=False,
        )
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    audit(Path(args.folder), Path(args.out))
