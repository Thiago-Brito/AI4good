"""Deterministic retention evidence, deliberately separate from semantic fulfillment."""

from collections import Counter
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .conceptual_planning import allocation_roles, conceptual_units, materialize_concepts
from .requirements import ContentRequirement, RequirementOrigin


class CoverageDiagnostic(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Literal["C001", "C002", "C003", "C004", "C005"]
    severity: Literal["AVISO", "INFORMACAO"]
    requirement: str | None
    origin: RequirementOrigin | None
    stage: Literal["requirements", "conceptual", "selection", "projection", "ir", "pptx"]
    evidence: dict
    message: str
    guidance: str


def records(data):
    result = {}
    for kind, group in (
        ("definition", "definitions"),
        ("entity", "entities"),
        ("step", "steps"),
        ("example", "examples"),
        ("claim", "claims"),
        ("criterion", "criteria"),
    ):
        result.update({f"{kind}_{i}": r for i, r in enumerate(data.get(group, []), 1)})
    if data.get("synthesis"):
        result["synthesis"] = data["synthesis"]
    return result


def validate_coverage(
    requirements, conceptual, outline, plan=None, ir=None, mapping=None, native=None
):
    """Audit exact fields at their own mapped paths, never search unrelated boxes for words."""
    reqs = [ContentRequirement.model_validate(r) for r in requirements]
    by_id = {r.id: r for r in reqs}
    content = records(conceptual)
    diagnostics = []

    def issue(code, req, stage, message, evidence, guidance):
        diagnostics.append(
            CoverageDiagnostic(
                code=code,
                severity="INFORMACAO" if code == "C005" else "AVISO",
                requirement=req.id if req else None,
                origin=req.origin if req else None,
                stage=stage,
                evidence=evidence,
                message=message,
                guidance=guidance,
            ).model_dump()
        )

    if len(by_id) != len(reqs):
        issue(
            "C004",
            None,
            "requirements",
            "IDs de requisitos duplicados.",
            {},
            "Corrija o contrato congelado.",
        )
    for ref, record in content.items():
        for rid in record.get("requirement_ids", []):
            if rid not in by_id:
                issue(
                    "C004",
                    None,
                    "conceptual",
                    "Registro aponta para requisito inexistente.",
                    {"record": ref, "target": rid},
                    "Associe somente IDs do contrato congelado.",
                )
        targets = [record["about"]] if "about" in record else record.get("based_on", [])
        for target in targets:
            if target not in content:
                issue(
                    "C004",
                    None,
                    "conceptual",
                    "Referência conceitual inexistente.",
                    {"record": ref, "target": target},
                    "Corrija about/based_on sem inventar registros.",
                )
    for si, slide in enumerate(outline.get("slides", []), 1):
        refs = slide.get("content_refs", [])
        for ref in refs:
            if ref not in content or refs.count(ref) > 1:
                issue(
                    "C004",
                    None,
                    "selection",
                    "Seleção contém ID inexistente ou duplicado.",
                    {"record": ref, "slide": si},
                    "Corrija a seleção usando IDs existentes únicos.",
                )
    # Broken references are reportable before projection, even if materialization cannot run.
    units = {}
    try:
        units = conceptual_units(conceptual)
    except (ValueError, KeyError):
        pass
    elements = {(s.number, e.id): e for s in ir.slides for e in s.elements} if ir else {}
    native_elements = (
        {
            (i, e["name"]): e.get("text")
            for i, slide in enumerate(native["slides"], 1)
            for e in slide["objects"]
        }
        if native
        else {}
    )
    evidence = []
    for si, slide in enumerate(outline.get("slides", [])):
        for ci in range(2 if slide.get("intent") == "comparison" else 1):
            for ri, ref in enumerate(slide.get("content_refs", [])):
                unit = units.get(ref)
                path = f"slides.{si}.columns.{ci}.content.{ri}"
                if not unit:
                    continue
                expected = {
                    "label": unit["label"],
                    "detail": unit["left" if ci == 0 else "right"]
                    if slide.get("intent") == "comparison"
                    else unit.get("detail", ""),
                    "explanation": ""
                    if slide.get("intent") == "comparison"
                    else unit.get("explanation", ""),
                    "role": unit["role"],
                    "sources": unit.get("sources", []),
                }
                actual = None
                if plan is not None:
                    try:
                        actual = plan["slides"][si]["columns"][ci]["content"][ri]
                    except (IndexError, KeyError):
                        pass
                projected = actual is not None and all(
                    actual.get(k, [] if k == "sources" else "") == v for k, v in expected.items()
                )
                witnesses, missing = [], []
                for field in ("label", "detail", "explanation"):
                    value = expected[field]
                    if not value:
                        continue
                    if (
                        field == "label"
                        and plan
                        and plan["slides"][si]["layout"] == "visual_sequence"
                    ):
                        value = f"{ri + 1}. {value}"
                    ids = [
                        key
                        for key, mapped in (mapping or {}).items()
                        if mapped == path + "." + field
                    ]
                    matches = [
                        key
                        for key in ids
                        if (si + 1, key) in elements
                        and elements[si + 1, key].type == "text"
                        and elements[si + 1, key].text == value
                    ]
                    witnesses += [
                        {"slide": si + 1, "element": key, "field": field, "text": value}
                        for key in matches
                    ]
                    if not matches:
                        missing.append(field)
                in_ir = projected and ir is not None and not missing
                in_pptx = (
                    in_ir
                    and native is not None
                    and all(
                        native_elements.get((w["slide"], w["element"])) == w["text"]
                        for w in witnesses
                    )
                )
                evidence.append(
                    {
                        "record": ref,
                        "slide": si + 1,
                        "path": path,
                        "projected": projected,
                        "in_ir": in_ir,
                        "in_pptx": in_pptx,
                        "elements": witnesses,
                        "missing_fields": missing,
                    }
                )
    rows = []
    for req in reqs:
        linked = [
            ref for ref, record in content.items() if req.id in record.get("requirement_ids", [])
        ]
        selected = [e for e in evidence if e["record"] in linked]
        scoped = [e for e in selected if req.slide is None or e["slide"] == req.slide]
        dropped = [ref for ref in linked if ref not in {e["record"] for e in scoped}]
        required = req.required and req.polarity == "include"
        if required and not linked:
            issue(
                "C001",
                req,
                "conceptual",
                "Requisito obrigatório sem registro associado.",
                {"records": []},
                "Produza conteúdo específico; a seleção não pode recuperar conteúdo ausente.",
            )
        if required and dropped:
            issue(
                "C002",
                req,
                "selection",
                "Registros associados não selecionados na seção solicitada.",
                {"records": dropped, "selected_slides": sorted({e["slide"] for e in selected})},
                "Reinclua registros existentes em slide compatível, conservando quantidade e geometria.",
            )
        stage = "pptx" if native is not None else "ir" if ir is not None else "projection"
        field = "in_pptx" if native is not None else "in_ir" if ir is not None else "projected"
        represented = [e for e in scoped if e[field]]
        retained = bool(linked) and not dropped and all(e[field] for e in scoped)
        if required and linked and plan is not None and not retained:
            issue(
                "C003",
                req,
                stage,
                "Evidência associada não preservada integralmente na saída examinada.",
                {"records": linked, "evidence": scoped},
                "Confira campos, seção e elementos emitidos; preserve a evidência literal.",
            )
        issue(
            "C005",
            req,
            stage,
            "Cumprimento semântico exige verificação independente.",
            {"records": linked, "represented": bool(represented), "polarity": req.polarity},
            "Inspecione completude, correção factual, relações e coerência; vínculos não comprovam cumprimento.",
        )
        rows.append(
            {
                **req.model_dump(),
                "associated": linked,
                "unselected": dropped,
                "slides": sorted({e["slide"] for e in scoped}),
                "evidence": scoped,
                "represented": bool(represented),
                "retained": retained,
                "semantic_verified": None,
            }
        )
    return {
        "protocol": "coverage-v1",
        "stage": "pptx"
        if native is not None
        else "ir"
        if ir is not None
        else "projection"
        if plan is not None
        else "selection",
        "requirements": rows,
        "records": evidence,
        "diagnostics": diagnostics,
        "associated_records": {
            ref: record.get("requirement_ids", []) for ref, record in content.items()
        },
        "unselected": [ref for ref in content if ref not in {e["record"] for e in evidence}],
        "represented_required": sum(
            r["represented"] for r in rows if r["required"] and r["polarity"] == "include"
        ),
        "required_count": sum(r["required"] and r["polarity"] == "include" for r in rows),
        "structural_retention_complete": all(
            r["retained"] for r in rows if r["required"] and r["polarity"] == "include"
        )
        and not any(d["code"] == "C004" for d in diagnostics),
        "semantic_verified": None,
        "factual_verified": False,
    }


def recover_selection(
    requirements, conceptual, outline, structural_requirements=(), *, enabled=True
):
    """Bounded append-only recovery of linked records; no model calls or layout changes."""
    from .reliability import evaluate_state, signatures
    from .semantic_planning import audit_semantics

    current = deepcopy(outline)
    plan, _ = materialize_concepts(conceptual, current)
    before = validate_coverage(requirements, conceptual, current, plan)
    state = evaluate_state(plan, len(current["slides"]), structural_requirements)
    attempts = []
    units = conceptual_units(conceptual)
    for row in before["requirements"] if enabled else []:
        if not row["required"] or row["polarity"] != "include":
            continue
        for ref in row["unselected"]:
            # A previous insertion may also have recovered this record for another requirement.
            report = validate_coverage(requirements, conceptual, current, plan)
            fresh = next(r for r in report["requirements"] if r["id"] == row["id"])
            if ref not in fresh["unselected"]:
                continue
            accepted = False
            for si, slide in enumerate(current["slides"]):
                if row["slide"] is not None and row["slide"] != si + 1:
                    continue
                if ref in slide["content_refs"]:
                    continue
                attempt = {
                    "requirement": row["id"],
                    "record": ref,
                    "slide": si + 1,
                    "accepted": False,
                }
                if (
                    len(slide["content_refs"]) >= 3
                    or units[ref]["role"] not in allocation_roles()[slide["intent"]]
                ):
                    attempts.append({**attempt, "reason": "capacity_or_role"})
                    continue
                candidate = deepcopy(current)
                candidate["slides"][si]["content_refs"].append(ref)
                try:
                    proposed, _ = materialize_concepts(conceptual, candidate)
                    new = evaluate_state(
                        proposed, len(candidate["slides"]), structural_requirements
                    )
                    old_q = Counter(
                        (d["code"], d["path"]) for d in audit_semantics(plan)["diagnostics"]
                    )
                    new_q = Counter(
                        (d["code"], d["path"]) for d in audit_semantics(proposed)["diagnostics"]
                    )
                    checks = validate_coverage(requirements, conceptual, candidate, proposed)
                    old_items, new_items = (
                        state["requirements"]["items"],
                        new["requirements"]["items"],
                    )
                    lost = any(v and not new_items.get(k) for k, v in old_items.items())
                    coverage_lost = any(
                        old["retained"] and not changed["retained"]
                        for old, changed in zip(
                            report["requirements"], checks["requirements"], strict=True
                        )
                    )
                    if (
                        not new["valid"]
                        or signatures(new) - signatures(state)
                        or new_q - old_q
                        or lost
                        or coverage_lost
                    ):
                        attempts.append(
                            {
                                **attempt,
                                "reason": "validation_regression",
                                "diagnostics": new["diagnostics"],
                                "semantic_diagnostics": audit_semantics(proposed)["diagnostics"],
                            }
                        )
                        continue
                    attempts.append(
                        {**attempt, "accepted": True, "reason": "retained_existing_record"}
                    )
                    current, plan, state = candidate, proposed, new
                    accepted = True
                    break
                except ValueError as exc:
                    attempts.append({**attempt, "reason": "invalid_contract", "error": str(exc)})
            if not accepted and not any(
                a["record"] == ref and a["requirement"] == row["id"] for a in attempts
            ):
                attempts.append(
                    {
                        "requirement": row["id"],
                        "record": ref,
                        "accepted": False,
                        "reason": "no_compatible_slide",
                    }
                )
    after = validate_coverage(requirements, conceptual, current, plan)
    return (
        current,
        plan,
        {
            "enabled": enabled,
            "calls": 0,
            "before": before,
            "after": after,
            "attempts": attempts,
            "accepted": sum(a["accepted"] for a in attempts),
            "rejected": sum(not a["accepted"] for a in attempts),
        },
    )
