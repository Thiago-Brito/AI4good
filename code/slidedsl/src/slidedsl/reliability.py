"""Requirement-aware D, isolated from the historical A/B/C/D protocol."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import time

from .compiler import compile_source
from .design_rules import load_rules
from .evolution import (
    _validate_plan,
    apply_patch_response,
    generate_strategy,
    repair_schema,
    requested_count,
)
from .incremental import save_json, sha
from .layouts import plan_to_dsl
from .models.ollama_model import OllamaTextModel
from .requirements import evaluate_requirements, extract_requirements
from .visual_validation import check_visual


def evaluate_state(data, count, requirements, strict=True):
    plan, validation, mapping, diagnostics = _validate_plan(data, count)
    if validation and validation.ir:
        diagnostics += check_visual(validation.ir, mapping)
    checks = evaluate_requirements(validation, requirements, plan)
    blocking = set(load_rules()["strict_codes"]) if strict else set()
    errors = [
        d
        for d in diagnostics
        if d["severity"] == "ERRO" or (d["severity"] == "AVISO" and d["code"] in blocking)
    ]
    return {
        "plan": plan,
        "validation": validation,
        "mapping": mapping,
        "diagnostics": diagnostics,
        "errors": errors,
        "requirements": checks,
        "valid": bool(validation and validation.success(strict) and not errors),
    }


def summary(state):
    v = state["validation"]
    semantic = bool(v and v.semantic_success) and not any(
        d["code"].startswith(("S", "L002", "L003", "L005", "G005")) for d in state["errors"]
    )
    geometric = not any(
        d["code"].startswith(("D", "V", "L001", "L004", "L006")) for d in state["errors"]
    )
    return {
        "syntax": bool(v and v.parse_success),
        "semantics": semantic,
        "geometry": geometric if semantic else None,
        "requirements": state["requirements"],
        "diagnostics": state["diagnostics"],
        "visual_quality": {
            "assessed_by_humans": False,
            "rendered": False,
            "method": "D001–D010: AABB, contraste e estimativa de texto; não mede glifos",
        },
    }


def signatures(state):
    return Counter(
        (d["code"], d.get("slide"), d.get("evidence", {}).get("path")) for d in state["errors"]
    )


def accept_candidate(before, after):
    """Reject new blockers and any lost requirement; require measurable progress."""
    if signatures(after) - signatures(before):
        return False, "new_errors"
    old, new = before["requirements"]["items"], after["requirements"]["items"]
    if any(met and not new.get(key) for key, met in old.items()):
        return False, "lost_requirement"
    if len(after["errors"]) >= len(before["errors"]) and sum(new.values()) <= sum(old.values()):
        return False, "no_progress"
    return True, "accepted"


def deterministic_candidate(data, state):
    """Only explicit missing requirements authorize additions; no phantom references."""
    result, edits = deepcopy(data), []
    for d in state["errors"]:
        path = d.get("evidence", {}).get("path", "")
        if d["code"] == "L001" and path and path.endswith(".columns"):
            index = int(path.split(".")[1])
            slide = result["slides"][index]
            requires_two = any(
                (r["kind"] == "columns" and r["slide"] == index + 1)
                or (r["kind"] == "original" and r["value"] == "comparison_columns" and index == 4)
                for r in state["requirements"]["details"]
            )
            if (
                len(slide["columns"]) == 1
                and slide["layout"] in {"two_columns", "comparison"}
                and not requires_two
            ):
                slide["layout"] = "title_content"
                edits.append(f"slides.{index}.layout")
    for req in state["requirements"]["details"]:
        if req["met"]:
            continue
        kind, number = req["kind"], req["slide"]
        if kind == "original":
            known = {
                "contrast_examples": ("shapes", 2),
                "local_image": ("images", 4),
                "layer_actions": ("layers", 4),
                "final_layer": ("layers", 4),
            }
            if req["value"] not in known:
                continue
            kind, number = known[req["value"]]
        if not number or number > len(result.get("slides", [])):
            continue
        slide = result["slides"][number - 1]
        path = f"slides.{number - 1}.decorations"
        if kind == "shapes":
            shapes = [d for d in slide["decorations"] if d["kind"] != "image"]
            minimum = 2 if req["kind"] == "original" else req["minimum"]
            # Existing colors are preserved. Ambiguous recoloring is delegated.
            for _ in range(max(0, minimum - len(shapes))):
                if len(slide["decorations"]) >= 4:
                    break
                used = {d["color"] for d in shapes}
                color = next(
                    (c for c in ["primaria", "destaque", "secundaria"] if c not in used), "primaria"
                )
                slot = "right" if any(d["slot"] == "left" for d in slide["decorations"]) else "left"
                decoration = {"kind": "rectangle", "slot": slot, "color": color}
                slide["decorations"].append(decoration)
                shapes.append(decoration)
                edits.append(path)
        elif (
            kind == "images"
            and not any(d["kind"] == "image" for d in slide["decorations"])
            and len(slide["decorations"]) < 4
        ):
            layering = (
                any(
                    r["slide"] == number and r["kind"] == "layers"
                    for r in state["requirements"]["details"]
                )
                or req["kind"] == "original"
            )
            slide["decorations"].append(
                {"kind": "image", "slot": "overlay" if layering else "right", "color": "primaria"}
            )
            edits.append(path)
        elif kind == "layers":
            images = [i for i, d in enumerate(slide["decorations"], 1) if d["kind"] == "image"]
            rectangles = [d for d in slide["decorations"] if d["kind"] == "rectangle"]
            if images and rectangles:
                key = f"d{images[0]}"
                ops = [r["kind"] for r in slide["relations"] if r["target"] == key]
                if not ("back" in ops and "front" in ops[ops.index("back") + 1 :]):
                    slide["relations"] += [
                        {"kind": "back", "target": key, "reference": ""},
                        {"kind": "front", "target": key, "reference": ""},
                    ]
                    edits.append(f"slides.{number - 1}.relations")
    return result, sorted(set(edits))


def preserve_good_fields(before, candidate, paths, state):
    """Array patches for missing decorations may append, never replace existing objects."""
    missing_paths = {r["path"] for r in state["requirements"]["details"] if not r["met"]}
    for path in paths:
        if path.endswith(".decorations") and path in missing_paths:
            a, b = before, candidate
            for token in path.split("."):
                a = a[int(token)] if isinstance(a, list) else a[token]
                b = b[int(token)] if isinstance(b, list) else b[token]
            if b[: len(a)] != a:
                return False
        if path.endswith(".columns") and path in missing_paths:
            a, b = before, candidate
            for token in path.split("."):
                a = a[int(token)] if isinstance(a, list) else a[token]
                b = b[int(token)] if isinstance(b, list) else b[token]
            if len(b) < len(a) or any(
                old["heading"] != new["heading"]
                or new["items"][: len(old["items"])] != old["items"]
                for old, new in zip(a, b)
            ):
                return False
        if (
            path.endswith(".relations")
            and path in missing_paths
            and not any(
                (d.get("evidence", {}).get("path") or "").startswith(path) for d in state["errors"]
            )
        ):
            a, b = before, candidate
            for token in path.split("."):
                a = a[int(token)] if isinstance(a, list) else a[token]
                b = b[int(token)] if isinstance(b, list) else b[token]
            if b[: len(a)] != a:
                return False
    # Unaffected fields are already protected by apply_patch_response's path schema.
    return True


def run_reliability(
    data,
    request,
    out,
    *,
    count,
    requirements,
    mode="slm",
    repair_max=2,
    adapter=None,
    model="qwen3:4b-instruct",
    strict=True,
    seed=42,
    temperature=0.1,
    event_callback=None,
):
    if mode not in {"baseline", "validator", "deterministic", "slm"} or not 0 <= repair_max <= 10:
        raise ValueError("Modo inválido ou limite fora de 0..10.")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    save_json(out / "requirements.json", requirements)
    save_json(out / "initial_plan.json", data)
    state = evaluate_state(data, count, requirements, strict)
    initial = summary(state)
    attempts, seen, calls, tokens = [], {sha(json.dumps(data, sort_keys=True))}, 0, 0
    deterministic_rejected = False
    adapter = adapter or OllamaTextModel(model)
    for i in range(repair_max if mode in {"deterministic", "slm"} else 0):
        if state["valid"] and state["requirements"]["all_met"]:
            break
        folder = out / f"repair_{i + 1}"
        folder.mkdir()
        save_json(folder / "before.json", data)
        save_json(folder / "before_validation.json", summary(state))
        candidate, paths = deterministic_candidate(data, state)
        if deterministic_rejected:
            candidate = deepcopy(data)
        method, reason, after = "deterministic", None, None
        if candidate == data:
            if mode == "deterministic":
                break
            paths = sorted(
                {
                    d.get("evidence", {}).get("path")
                    for d in state["errors"] + state["requirements"]["diagnostics"]
                }
                - {None}
            )
            if not paths:
                break
            method = "slm"
            try:
                schema = repair_schema(paths)
                system = (
                    "Corrija somente caminhos autorizados; preserve o restante. Para decoração ausente, apenas acrescente, preservando as existentes. JSON:\n"
                    + json.dumps(schema, ensure_ascii=False)
                )
                prompt = (
                    "Pedido:\n"
                    + request
                    + "\nCritérios fixos:\n"
                    + json.dumps(requirements, ensure_ascii=False)
                    + "\nPlano:\n"
                    + json.dumps(data, ensure_ascii=False)
                    + "\nDiagnósticos:\n"
                    + json.dumps(
                        state["errors"] + state["requirements"]["diagnostics"], ensure_ascii=False
                    )
                )
                (folder / "system.txt").write_text(system, encoding="utf-8")
                (folder / "user.txt").write_text(prompt, encoding="utf-8")
                calls += 1
                raw = adapter.generate(
                    system, prompt, response_schema=schema, seed=seed, temperature=temperature
                )
                (folder / "raw.txt").write_bytes(raw.encode("utf-8"))
                response = getattr(adapter, "last_response", None) or {}
                tokens += response.get("eval_count", 0)
                save_json(folder / "request.json", getattr(adapter, "last_request", None))
                save_json(folder / "response.json", response)
                if (
                    not response.get("done")
                    or response.get("done_reason", adapter.metadata.get("done_reason")) != "stop"
                ):
                    raise ValueError("Resposta incompleta")
                candidate = apply_patch_response(data, raw, paths)
            except (ValueError, KeyError, IndexError, RuntimeError) as exc:
                candidate, reason = deepcopy(data), f"invalid_patch: {exc}"
            except Exception as exc:
                # A schema rejection is recorded; current state remains untouched.
                candidate, reason = deepcopy(data), f"rejected_patch: {exc}"
        candidate_hash = sha(json.dumps(candidate, sort_keys=True))
        if reason is None and candidate_hash in seen:
            reason = "repeated_or_unchanged_patch"
        seen.add(candidate_hash)
        if reason is None and not preserve_good_fields(data, candidate, paths, state):
            reason = "changed_existing_elements"
        if reason is None:
            after = evaluate_state(candidate, count, requirements, strict)
            accepted, reason = accept_candidate(state, after)
        else:
            accepted = False
        save_json(folder / "candidate.json", candidate)
        save_json(folder / "candidate_validation.json", summary(after) if after else None)
        if accepted:
            data, state = candidate, after
        record = {
            "attempt": i + 1,
            "method": method,
            "paths": paths,
            "accepted": accepted,
            "reason": reason,
            "candidate_sha256": candidate_hash,
            "before": initial if not attempts else attempts[-1]["after"],
            "after": summary(state),
        }
        attempts.append(record)
        if method == "deterministic" and not accepted:
            deterministic_rejected = True
        elif accepted:
            deterministic_rejected = False
        save_json(folder / "after.json", data)
        save_json(folder / "attempt.json", record)
        if event_callback:
            event_callback(
                {
                    "stage": "repair",
                    "round": i + 1,
                    "paths": paths,
                    "message": reason,
                    "diagnostics": state["errors"] + state["requirements"]["diagnostics"],
                }
            )
        if reason == "repeated_or_unchanged_patch" or (
            method == "deterministic" and not accepted and mode == "deterministic"
        ):
            break
    report = {
        "protocol": "reliability-v1",
        "mode": mode,
        "initial": initial,
        **summary(state),
        "requirements": state["requirements"],
        "diagnostics": state["diagnostics"] + state["requirements"]["diagnostics"],
        "valid": state["valid"],
        "faithful": state["valid"] and state["requirements"]["all_met"],
        "attempts": attempts,
        "corrections": len(attempts),
        "successful_corrections": sum(a["accepted"] for a in attempts),
        "failed_corrections": sum(not a["accepted"] for a in attempts),
        "repair_calls": calls,
        "repair_output_tokens": tokens,
        "compile_success": False,
        "compile_error": None,
        "is_mock": adapter.metadata.get("provider") != "ollama",
    }
    save_json(out / "plan.json", data)
    if state["plan"]:
        source, mapping, _ = plan_to_dsl(state["plan"])
        (out / "presentation.sld").write_text(source, encoding="utf-8")
        save_json(out / "element_paths.json", mapping)
        if state["validation"].ir:
            save_json(out / "ir.json", state["validation"].ir.model_dump())
        if state["valid"]:
            try:
                save_json(
                    out / "pptx_inspection.json",
                    compile_source(source, out / "presentation.pptx", strict=strict),
                )
                report["compile_success"] = True
            except (ValueError, RuntimeError, OSError) as exc:
                report["compile_error"] = str(exc)
    report["duration_ms"] = (time.perf_counter() - started) * 1000
    save_json(out / "report.json", report)
    return report


def generate_reliable(
    model,
    strategy,
    request,
    out,
    *,
    requirements=None,
    repair_max=2,
    slide_count=None,
    adapter=None,
    event_callback=None,
    **options,
):
    if not 0 <= repair_max <= 10:
        raise ValueError("Limite de correções fora de 0..10")
    if strategy not in {"C", "D"}:
        return generate_strategy(
            model,
            strategy,
            request,
            out,
            slide_count=slide_count,
            adapter=adapter,
            event_callback=event_callback,
            **options,
        )
    count = requested_count(request) if slide_count is None else slide_count
    criteria = requirements if requirements is not None else extract_requirements(request, count)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / "requirements.json", criteria)  # freeze before the initial model call
    adapter = adapter or OllamaTextModel(
        model,
        context_length=options.get("context_length", 8192),
        output_tokens=options.get("output_tokens", 4096),
    )
    initial = generate_strategy(
        model,
        "C",
        request,
        out / "initial",
        slide_count=count,
        adapter=adapter,
        event_callback=event_callback,
        **options,
    )
    plan_file = out / "initial/plan.json"
    if not plan_file.exists():
        initial.update(
            protocol="reliability-v1",
            requirements=evaluate_requirements(None, criteria),
            faithful=False,
            limitation="Plano inicial ilegível; preservado sem reparo localizado seguro.",
        )
        save_json(out / "report.json", initial)
        return initial
    report = run_reliability(
        json.loads(plan_file.read_text(encoding="utf-8")),
        request,
        out / "validated",
        count=count,
        requirements=criteria,
        mode="slm" if strategy == "D" else "validator",
        repair_max=repair_max,
        adapter=adapter,
        model=model,
        event_callback=event_callback,
        strict=options.get("strict", True),
        seed=options.get("seed", 42),
        temperature=options.get("temperature", 0.1),
    )
    import shutil

    for name in [
        "presentation.sld",
        "presentation.pptx",
        "plan.json",
        "ir.json",
        "element_paths.json",
    ]:
        path = out / "validated" / name
        if path.exists():
            shutil.copyfile(path, out / name)
    response = json.loads((out / "initial/round_0/response.json").read_text(encoding="utf-8")) or {}
    report.update(
        status=initial["status"],
        availability=initial["availability"],
        model_metadata=initial["model_metadata"],
        calls=1 + report["repair_calls"],
        output_tokens=response.get("eval_count", 0) + report["repair_output_tokens"],
        duration_ms=initial["duration_ms"] + report["duration_ms"],
        configuration=initial["configuration"],
    )
    save_json(out / "report.json", report)
    return report
