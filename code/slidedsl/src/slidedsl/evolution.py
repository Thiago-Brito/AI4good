"""A/B baselines and C/D planned generation, with bounded field-level repairs."""

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as SchemaValidationError
from pydantic import ValidationError

from .compiler import compile_source
from .ast_nodes import PresentationNode
from .diagnostics import Diagnostic, DSLException
from .incremental import error, generate_deck, save_json, sha
from .layouts import plan_to_dsl
from .models.base import ModelError
from .models.ollama_model import OllamaTextModel
from .pipeline import validate_source
from .parser import parse
from .printer import print_ast
from .planning import DeckPlan, plan_schema, plan_system


def requested_count(request: str, fallback=5) -> int:
    words = {
        "um": 1,
        "dois": 2,
        "três": 3,
        "tres": 3,
        "quatro": 4,
        "cinco": 5,
        "seis": 6,
        "sete": 7,
        "oito": 8,
        "nove": 9,
        "dez": 10,
    }
    match = re.search(r"\b(\d+|" + "|".join(words) + r")\s+slides?\b", request.casefold())
    if match:
        count = words.get(match[1]) or int(match[1])
        if not 1 <= count <= 12:
            raise ValueError("A geração suporta de 1 a 12 slides.")
        return count
    return fallback


def assess_requirements(validation, slide_count, requirements=None) -> dict:
    """Explicit structural/lexical proxies, evaluated independently of compilation."""
    deck = validation.ir if validation else None
    checks = {
        "slide_count": bool(deck and len(deck.slides) == slide_count),
        "unique_ids": bool(validation and validation.semantic_success),
        "titles": bool(
            deck
            and all(any(e.role == "titulo" and e.text for e in s.elements) for s in deck.slides)
        ),
        "body_content": bool(
            deck and all(any(e.role == "corpo" and e.text for e in s.elements) for s in deck.slides)
        ),
        "margins": bool(
            deck
            and all(
                e.x >= 64 and e.y >= 64 and e.x + e.width <= 1216 and e.y + e.height <= 656
                for s in deck.slides
                for e in s.elements
                if e.role != "background"
            )
        ),
    }
    for requirement in requirements or []:
        s = (
            next((s for s in deck.slides if s.number == requirement.get("slide")), None)
            if deck
            else None
        )
        text = " ".join(e.text or "" for e in s.elements).casefold() if s else ""
        ok = bool(s)
        if requirement.get("keywords"):
            ok = ok and any(word.casefold() in text for word in requirement["keywords"])
        if requirement.get("two_columns"):
            bodies = [e for e in s.elements if e.type == "text" and e.role == "corpo"] if s else []
            ok = ok and any(e.x < 640 for e in bodies) and any(e.x >= 640 for e in bodies)
        if "min_texts" in requirement:
            ok = ok and sum(e.type == "text" for e in s.elements) >= requirement["min_texts"]
        checks[requirement["id"]] = bool(ok)
    return {
        "items": checks,
        "numerator": sum(checks.values()),
        "denominator": len(checks),
        "all_met": all(checks.values()),
        "limitation": "Proxies estruturais/lexicais; não avaliam verdade factual ou beleza.",
    }


def _schema_at(schema, path):
    node = schema
    for token in path.split("."):
        while "$ref" in node:
            node = schema["$defs"][node["$ref"].split("/")[-1]]
        node = node["items"] if token.isdigit() else node["properties"][token]
    return deepcopy(node)


def repair_schema(paths: list[str]) -> dict:
    original = DeckPlan.model_json_schema()
    variants = [
        {
            "type": "object",
            "additionalProperties": False,
            "properties": {"path": {"const": path}, "value": _schema_at(original, path)},
            "required": ["path", "value"],
        }
        for path in paths
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "$defs": original.get("$defs", {}),
        "properties": {
            "edits": {
                "type": "array",
                "minItems": 1,
                "maxItems": len(paths),
                "items": {"anyOf": variants},
            }
        },
        "required": ["edits"],
    }


def apply_patch_response(data: dict, raw: str, paths: list[str]) -> dict:
    patch = json.loads(raw)
    Draft202012Validator(repair_schema(paths)).validate(patch)
    result, seen = deepcopy(data), set()
    for edit in patch["edits"]:
        path = edit["path"]
        if path in seen:
            raise ValueError("Reparo contém caminhos duplicados.")
        seen.add(path)
        tokens = path.split(".")
        obj = result
        for token in tokens[:-1]:
            obj = obj[int(token)] if isinstance(obj, list) else obj[token]
        key = int(tokens[-1]) if isinstance(obj, list) else tokens[-1]
        obj[key] = edit["value"]
    return result


def _validate_plan(data, count):
    try:
        plan = DeckPlan.model_validate(data)
    except ValidationError as exc:
        return (
            None,
            None,
            {},
            [
                error("J001", item["msg"], path=".".join(map(str, item["loc"])))
                for item in exc.errors(include_url=False)
            ],
        )
    source, mapping, diagnostics = plan_to_dsl(plan)
    if len(plan.slides) != count:
        diagnostics.append(
            Diagnostic(
                code="G005",
                severity="ERRO",
                message=f"Pedido exige {count} slides.",
                evidence={"path": "slides"},
            )
        )
    validation = validate_source(source)
    ds = [d.model_dump() for d in [*diagnostics, *validation.diagnostics]]
    for d in ds:
        if "path" not in d.get("evidence", {}) and d.get("element") in mapping:
            d["evidence"]["path"] = mapping[d["element"]]
    return plan, validation, mapping, ds


def _metric_counts(diagnostics, reached):
    return {
        "syntax_errors": sum(
            d["code"].startswith(("P", "J")) and d["severity"] == "ERRO" for d in diagnostics
        ),
        "semantic_errors": sum(
            d["code"].startswith(("S", "L002", "L003", "L005", "G003", "G004", "G005"))
            and d["severity"] == "ERRO"
            for d in diagnostics
        ),
        "generation_errors": sum(d["code"] in {"G001", "G002"} for d in diagnostics),
        "geometry_errors": sum(
            d["code"].startswith(("D", "L001", "L004")) and d["severity"] == "ERRO"
            for d in diagnostics
        )
        if reached
        else None,
        "geometry_warnings": sum(
            d["code"].startswith("D") and d["severity"] == "AVISO" for d in diagnostics
        )
        if reached
        else None,
    }


def generate_strategy(
    model: str,
    strategy: str,
    request: str,
    out: Path,
    *,
    slide_count=None,
    temperature=0.1,
    seed=42,
    context_length=8192,
    output_tokens=4096,
    strict=True,
    requirements=None,
    adapter=None,
    event_callback=None,
) -> dict:
    if strategy not in {"A", "B", "C", "D"}:
        raise ValueError("Estratégia deve ser A, B, C ou D.")
    count = requested_count(request) if slide_count is None else slide_count
    schema = plan_schema(count)
    if (
        not request.strip()
        or not 0 <= temperature <= 1
        or context_length < 4096
        or output_tokens < 512
    ):
        raise ValueError("Pedido obrigatório; temperatura 0..1, contexto >=4096, saída >=512.")
    if strategy in {"A", "B"}:
        report = generate_deck(
            model,
            "direct" if strategy == "A" else "json",
            request,
            out,
            repair_max=0,
            temperature=temperature,
            seed=seed,
            context_length=context_length,
            output_tokens=output_tokens,
            strict=strict,
            adapter=adapter,
            slide_count=count,
            event_callback=event_callback,
        )
        diagnostics = [d for s in report["slides"] for r in s["rounds"] for d in r["diagnostics"]]
        source_path = out / "presentation.sld"
        if not source_path.exists():
            # Assess rejected drafts too; compilation and requirement coverage are independent.
            nodes = []
            first_title, first_theme = None, None
            for number in range(1, count + 1):
                path = out / f"slides/slide_{number:02d}/round_0/slide.sld"
                if not path.exists():
                    break
                try:
                    ast = parse(path.read_text(encoding="utf-8"))
                except DSLException:
                    break
                if len(ast.slides) != 1:
                    break
                if not nodes:
                    first_title, first_theme = ast.title, ast.theme
                node = ast.slides[0].model_copy(deep=True)
                node.number = number
                nodes.append(node)
            if len(nodes) == count:
                source_path = out / "attempted.sld"
                source_path.write_text(
                    print_ast(PresentationNode(title=first_title, theme=first_theme, slides=nodes)),
                    encoding="utf-8",
                )
        validation = (
            validate_source(source_path.read_text(encoding="utf-8"))
            if source_path.exists()
            else None
        )
        report.update(
            strategy=strategy,
            protocol="evolution-v1",
            diagnostics=diagnostics,
            generated_presentations=int(report.get("complete", False)),
            design_slides_reached=sum(
                s["rounds"][-1]["semantic_success"] for s in report["slides"]
            ),
            design_slides_potential=count,
            **_metric_counts(
                diagnostics, any(s["rounds"][-1]["semantic_success"] for s in report["slides"])
            ),
            requirements=assess_requirements(validation, count, requirements),
        )
        save_json(out / "evolution_report.json", report)
        return report
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    adapter = adapter or OllamaTextModel(
        model, context_length=context_length, output_tokens=output_tokens
    )
    system = plan_system() + "\nSchema:\n" + json.dumps(schema, ensure_ascii=False)
    cfg = {
        "protocol": "evolution-v1",
        "strategy": strategy,
        "model": model,
        "request": request,
        "slide_count": count,
        "temperature": temperature,
        "seed": seed,
        "num_ctx": context_length,
        "num_predict": output_tokens,
        "strict": strict,
        "repair_max": 2 if strategy == "D" else 0,
        "schema": schema,
        "system_sha256": sha(system),
        "requirements": requirements or [],
    }
    save_json(out / "configuration.json", cfg)
    (out / "request.txt").write_text(request, encoding="utf-8")
    available, reason = adapter.available()
    report = {
        "protocol": "evolution-v1",
        "strategy": strategy,
        "model": model,
        "is_mock": adapter.metadata.get("provider") != "ollama",
        "status": "EXECUTADO" if available else "NAO_EXECUTADO",
        "availability": reason,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "configuration": cfg,
        "model_metadata": dict(adapter.metadata),
        "rounds": [],
        "corrections": 0,
        "complete": False,
        "valid": False,
        "compile_success": False,
        "compile_error": None,
        "generated_presentations": 0,
        "diagnostics": [],
        "parse_success": False,
        "semantic_success": False,
    }
    save_json(out / "model_show.json", getattr(adapter, "model_show", None))
    save_json(out / "report.json", report)
    current, call_schema, call_system = (
        f"Pedido integral:\n{request}\nExatamente {count} slides.",
        schema,
        system,
    )
    data, validation, plan, mapping, selected_source = None, None, None, {}, None
    paths = []
    for round_number in range(cfg["repair_max"] + 1) if available else []:
        folder = out / f"round_{round_number}"
        folder.mkdir()
        if event_callback:
            event_callback(
                {
                    "stage": "planning" if round_number == 0 else "repair",
                    "round": round_number,
                    "message": "Planejando conteúdo"
                    if not round_number
                    else "Corrigindo apenas campos indicados",
                    "paths": paths if round_number else [],
                }
            )
        (folder / "system.txt").write_text(call_system, encoding="utf-8")
        (folder / "user.txt").write_text(current, encoding="utf-8")
        diagnostics, complete = [], False
        call_started = time.perf_counter()
        try:
            raw = adapter.generate(
                call_system,
                current,
                temperature=temperature,
                seed=seed,
                response_schema=call_schema,
            )
            (folder / "raw.txt").write_bytes(raw.encode("utf-8"))
            complete = (
                bool(raw.strip())
                and bool((adapter.last_response or {}).get("done"))
                and adapter.metadata.get("done_reason") == "stop"
            )
            if not complete:
                diagnostics.append(error("G002", "Resposta truncada ou sem conclusão confirmada."))
            if round_number and data is not None:
                candidate = apply_patch_response(data, raw, paths)
            else:
                candidate = json.loads(raw)
            if not isinstance(candidate, dict):
                raise ValueError("O plano deve ser um objeto JSON.")
            data = candidate
            plan, validation, mapping, ds = _validate_plan(data, count)
            diagnostics += ds
            if plan:
                selected_source, _, _ = plan_to_dsl(plan)
                (folder / "presentation.sld").write_text(selected_source, encoding="utf-8")
                save_json(folder / "plan.json", plan.model_dump())
            if validation:
                if validation.ast:
                    save_json(folder / "ast.json", validation.ast.model_dump())
                if validation.ir:
                    save_json(folder / "ir.json", validation.ir.model_dump())
            save_json(folder / "element_paths.json", mapping)
        except ModelError as exc:
            diagnostics.append(error("G001", str(exc)))
        except (ValueError, KeyError, IndexError, SchemaValidationError) as exc:
            diagnostics.append(
                error("J001", "Resposta ou patch não atende ao contrato.", detail=str(exc))
            )
        save_json(folder / "request.json", getattr(adapter, "last_request", None))
        save_json(folder / "response.json", getattr(adapter, "last_response", None))
        valid = (
            complete
            and validation is not None
            and validation.success(strict)
            and not any(d["severity"] == "ERRO" for d in diagnostics)
        )
        record = {
            "round": round_number,
            "complete": complete,
            "valid": valid,
            "diagnostics": diagnostics,
            "duration_ms": (time.perf_counter() - call_started) * 1000,
            "metadata": dict(adapter.metadata),
            "scope": paths if round_number and data is not None else ["plan"],
        }
        report["rounds"].append(record)
        report["diagnostics"] = diagnostics
        report["corrections"] = round_number
        save_json(folder / "metrics.json", record)
        save_json(out / "report.json", report)
        if event_callback:
            event_callback({"stage": "validation", **record})
        if valid:
            report["valid"] = True
            break
        if any(d["code"] == "G001" for d in diagnostics):
            break
        paths = sorted(
            {
                d.get("evidence", {}).get("path")
                for d in diagnostics
                if d["severity"] == "ERRO" or (strict and d["severity"] == "AVISO")
            }
            - {None}
        )
        # Unknown fields are removed locally only by an explicit plan-wide repair,
        # never by silently discarding user/model content.
        try:
            patch_schema = repair_schema(paths) if paths and data is not None else None
        except (KeyError, TypeError):
            patch_schema = None
        if patch_schema:
            call_schema = patch_schema
            call_system = (
                "Corrija apenas os campos autorizados. Retorne edits com path e value. "
                + "Preserve conteúdo correto e requisitos do pedido. Schema:\n"
                + json.dumps(call_schema, ensure_ascii=False)
            )
            current = (
                f"Pedido integral:\n{request}\nPlano atual:\n"
                + json.dumps(data, ensure_ascii=False)
                + "\nDiagnósticos específicos:\n"
                + json.dumps(diagnostics, ensure_ascii=False)
                + "\nCaminhos autorizados: "
                + json.dumps(paths)
            )
        else:
            if data is not None and validation is not None:
                break  # No safely localizable change: do not regenerate a valid deck.
            data = None
            paths = ["plan"]
            call_schema, call_system = schema, system
            current = (
                f"Corrija a estrutura JSON completa (plano ilegível). Pedido:\n{request}\n"
                + json.dumps(diagnostics, ensure_ascii=False)
            )
    report["complete"] = bool(report["rounds"] and report["rounds"][-1]["complete"])
    report["generated_presentations"] = int(report["complete"])
    report["plan_available"] = plan is not None
    report["parse_success"] = bool(validation and validation.parse_success)
    report["semantic_success"] = bool(validation and validation.semantic_success)
    report["design_slides_reached"] = count if report["semantic_success"] else 0
    report["design_slides_potential"] = count
    report.update(_metric_counts(report["diagnostics"], report["semantic_success"]))
    report["requirements"] = assess_requirements(validation, count, requirements)
    if selected_source and plan is not None:
        (out / "presentation.sld").write_text(selected_source, encoding="utf-8")
        save_json(out / "plan.json", plan.model_dump())
        save_json(out / "element_paths.json", mapping)
        if validation and validation.ir:
            save_json(out / "ir.json", validation.ir.model_dump())
    if report["valid"]:
        try:
            inspection = compile_source(selected_source, out / "presentation.pptx", strict=strict)
            save_json(out / "pptx_inspection.json", inspection)
            report["compile_success"] = True
        except (DSLException, OSError, RuntimeError) as exc:
            report["compile_error"] = str(exc)
    report["duration_ms"] = (time.perf_counter() - started) * 1000
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save_json(out / "report.json", report)
    return report
