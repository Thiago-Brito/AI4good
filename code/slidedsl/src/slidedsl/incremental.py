"""One model request per slide, with explicit repairs and immutable evidence."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import csv
import json
from pathlib import Path
import platform
import re
import time

from pydantic import ValidationError

from .ast_nodes import PresentationNode
from .compiler import compile_source
from .diagnostics import DSLException
from .models.base import ModelError
from .models.ollama_model import OllamaTextModel
from .paths import project_root
from .parser import parse
from .pipeline import validate_source
from .printer import print_ast
from .structured_slide import SlideOutput, json_to_dsl


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def error(code: str, message: str, **evidence) -> dict:
    return {"code": code, "severity": "ERRO", "message": message, "evidence": evidence}


def parameters(
    model, mode, request, repair_max, temperature, seed, context_length, output_tokens, strict=False
):
    if mode not in {"direct", "json"} or repair_max not in {0, 1, 2}:
        raise ValueError("Use modo direct/json e zero a dois reparos.")
    if not 0 <= temperature <= 1 or context_length < 4096 or output_tokens < 512:
        raise ValueError("Temperatura 0..1, contexto >=4096 e saída >=512.")
    system = (project_root() / f"prompts/incremental_{mode}.txt").read_text(encoding="utf-8")
    schema = SlideOutput.model_json_schema() if mode == "json" else None
    if schema is not None:
        system += "\nSchema JSON obrigatório:\n" + json.dumps(schema, ensure_ascii=False)
    return {
        "protocol": "incremental-v1",
        "model": model,
        "mode": mode,
        "request": request,
        "slide_count": 5,
        "repair_max": repair_max,
        "temperature": temperature,
        "seed": seed,
        "num_ctx": context_length,
        "num_predict": output_tokens,
        "strict": strict,
        "system_prompt": system,
        "system_sha256": sha(system),
        "schema": schema,
        "schema_sha256": sha(json.dumps(schema, sort_keys=True)),
        "grammar_sha256": hashlib.sha256(
            (project_root() / "src/slidedsl/grammar/slidedsl.lark").read_bytes()
        ).hexdigest(),
        "acceptance": "complete + parser + semantics + design (strict flag controls warnings); no manual fallback",
    }


def slide_prompt(request: str, number: int, previous: list[str], mode: str) -> str:
    focus = re.search(
        rf"Slide\s+{number}\s*:\s*(.*?)(?=Slide\s+\d+\s*:|$)", request, re.IGNORECASE | re.DOTALL
    )
    return (
        f"Pedido integral do usuário:\n{request}\n\n"
        f"Gere apenas o slide {number} de 5 correspondente ao pedido. "
        "Não repita os outros slides. Crie conteúdo informativo e elementos concretos.\n"
        + ("REQUISITO DESTE SLIDE: " + focus.group(1).strip() + "\n" if focus else "")
        + (
            f"No programa individual use somente slide {number}; a montagem valida a numeração local.\n"
            if mode == "direct"
            else "O JSON representa apenas este slide.\n"
        )
        + "Títulos já produzidos: "
        + json.dumps(previous, ensure_ascii=False)
    )


def generate_deck(
    model: str,
    mode: str,
    request: str,
    out: Path,
    *,
    repair_max=2,
    temperature=0.1,
    seed=42,
    context_length=8192,
    output_tokens=4096,
    strict=False,
    adapter=None,
) -> dict:
    cfg = parameters(
        model, mode, request, repair_max, temperature, seed, context_length, output_tokens, strict
    )
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    save_json(out / "configuration.json", cfg)
    (out / "request.txt").write_text(request, encoding="utf-8")
    (out / "system.txt").write_text(cfg["system_prompt"], encoding="utf-8")
    adapter = adapter or OllamaTextModel(
        model, context_length=context_length, output_tokens=output_tokens
    )
    available, reason = adapter.available()
    save_json(out / "model_show.json", getattr(adapter, "model_show", None))
    report = {
        "model": model,
        "mode": mode,
        "is_mock": adapter.metadata.get("provider") != "ollama",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "status": "EXECUTADO" if available else "NAO_EXECUTADO",
        "availability": reason,
        "configuration": cfg,
        "model_metadata": dict(adapter.metadata),
        "slides": [],
        "complete": False,
        "parse_success": False,
        "semantic_success": False,
        "valid": False,
        "compile_success": False,
        "compile_error": None,
        "design_errors": None,
        "design_warnings": None,
        "corrections": 0,
    }
    save_json(out / "report.json", report)
    if not available:
        return report
    started = time.perf_counter()
    accepted, titles = [], []
    for number in range(1, 6):
        base_prompt = slide_prompt(request, number, titles, mode)
        current = base_prompt
        slide_record = {"number": number, "accepted": False, "rounds": [], "selected_round": None}
        for round_number in range(repair_max + 1):
            folder = out / f"slides/slide_{number:02d}/round_{round_number}"
            folder.mkdir(parents=True, exist_ok=False)
            (folder / "system.txt").write_text(cfg["system_prompt"], encoding="utf-8")
            (folder / "user.txt").write_text(current, encoding="utf-8")
            call_started = time.perf_counter()
            try:
                raw = adapter.generate(
                    cfg["system_prompt"],
                    current,
                    temperature=temperature,
                    seed=seed,
                    response_schema=cfg["schema"],
                )
            except ModelError as exc:
                save_json(folder / "request.json", adapter.last_request)
                record = {
                    "round": round_number,
                    "transport_error": str(exc),
                    "complete": False,
                    "parse_success": False,
                    "semantic_success": False,
                    "valid": False,
                    "diagnostics": [error("G001", str(exc))],
                }
                save_json(folder / "metrics.json", record)
                slide_record["rounds"].append(record)
                break
            (folder / "raw.txt").write_bytes(raw.encode("utf-8"))
            save_json(folder / "request.json", adapter.last_request)
            save_json(folder / "response.json", adapter.last_response)
            metadata = dict(adapter.metadata)
            complete = (
                bool(raw.strip())
                and bool((adapter.last_response or {}).get("done"))
                and metadata.get("done_reason") == "stop"
            )
            diagnostics = (
                []
                if complete
                else [
                    error(
                        "G002",
                        "Resposta vazia, truncada ou sem término confirmado.",
                        done_reason=metadata.get("done_reason"),
                        content_chars=len(raw),
                    )
                ]
            )
            source, validation, normalization = None, None, None
            try:
                source = json_to_dsl(raw) if mode == "json" else raw
                if mode == "direct":
                    try:
                        original_ast = parse(raw)
                        save_json(folder / "original_ast.json", original_ast.model_dump())
                        if len(original_ast.slides) == 1 and original_ast.slides[0].number in {
                            1,
                            number,
                        }:
                            normalization = {
                                "original_slide_number": original_ast.slides[0].number,
                                "validation_slide_number": 1,
                                "assembly_slide_number": number,
                                "changes": "somente numeração e impressão canônica; conteúdo e comandos preservados",
                            }
                            original_ast.slides[0].number = 1
                            source = print_ast(original_ast)
                    except DSLException:
                        pass  # Original invalid syntax goes unchanged to authoritative validation.
                (folder / "slide.sld").write_bytes(source.encode("utf-8"))
                validation = validate_source(source)
                diagnostics += [d.model_dump() for d in validation.diagnostics]
                if validation.ast:
                    save_json(folder / "ast.json", validation.ast.model_dump())
                    if (
                        len(validation.ast.slides) != 1
                        or validation.ast.slides[0].number != 1
                        or validation.ast.theme != "claro"
                    ):
                        diagnostics.append(
                            error(
                                "G003",
                                "Cada solicitação deve gerar tema claro e exatamente slide 1.",
                            )
                        )
                if validation.ir:
                    save_json(folder / "ir.json", validation.ir.model_dump())
                    elements = [e for s in validation.ir.slides for e in s.elements]
                    if (
                        not any(
                            e.type == "text" and e.role == "titulo" and e.text for e in elements
                        )
                        or len(elements) < 2
                    ):
                        diagnostics.append(
                            error(
                                "G004",
                                "O slide deve conter título textual e pelo menos dois elementos.",
                            )
                        )
            except (ValidationError, ValueError) as exc:
                diagnostics.append(
                    error("J001", "JSON não atende ao schema restrito.", detail=str(exc))
                )
            valid = (
                complete
                and validation is not None
                and validation.success(strict)
                and not any(d["severity"] == "ERRO" for d in diagnostics)
            )
            record = {
                "round": round_number,
                "duration_ms": (time.perf_counter() - call_started) * 1000,
                "raw_sha256": sha(raw),
                "source_sha256": sha(source) if source is not None else None,
                "normalization": normalization,
                "user_sha256": sha(current),
                "metadata": metadata,
                "complete": complete,
                "parse_success": bool(validation and validation.parse_success),
                "parser_reached": validation is not None,
                "json_schema_success": source is not None if mode == "json" else None,
                "semantic_success": bool(validation and validation.semantic_success),
                "valid": valid,
                "design_errors": sum(
                    d["code"].startswith("D") and d["severity"] == "ERRO" for d in diagnostics
                )
                if validation and validation.semantic_success
                else None,
                "design_warnings": sum(
                    d["code"].startswith("D") and d["severity"] == "AVISO" for d in diagnostics
                )
                if validation and validation.semantic_success
                else None,
                "diagnostics": diagnostics,
            }
            save_json(folder / "diagnostics.json", diagnostics)
            save_json(folder / "metrics.json", record)
            slide_record["rounds"].append(record)
            print(
                f"{model} {mode} slide {number}/5 rodada {round_number}: {'válido' if valid else ','.join(d['code'] for d in diagnostics)}",
                flush=True,
            )
            if valid:
                slide_record.update(accepted=True, selected_round=round_number)
                node = validation.ast.slides[0].model_copy(deep=True)
                node.number = number
                accepted.append(node)
                titles.append(
                    next(
                        e.text
                        for e in validation.ir.slides[0].elements
                        if e.type == "text" and e.role == "titulo"
                    )
                )
                break
            current = (
                base_prompt
                + "\nCorrija sua resposta anterior integralmente, mantendo apenas este slide.\nResposta anterior:\n"
                + raw
                + "\nDiagnósticos explícitos:\n"
                + json.dumps(diagnostics, ensure_ascii=False)
                + "\nAs correções têm prioridade sobre o exemplo. Não repita os mesmos valores inválidos.\n"
                + "\n".join(
                    f"Elemento {d.get('element')}: altura precisa ser >= {int(d['evidence']['estimated_height']) + 17}, ou reduza texto/amplie largura."
                    for d in diagnostics
                    if d["code"] == "D010" and "estimated_height" in d.get("evidence", {})
                )
                + "\nRetorne somente "
                + ("SlideDSL." if mode == "direct" else "JSON conforme o schema.")
            )
        report["slides"].append(slide_record)
        save_json(out / "report.json", report)
    finals = [s["rounds"][-1] for s in report["slides"]]
    report.update(
        complete=all(r["complete"] for r in finals),
        parse_success=all(r["parse_success"] for r in finals),
        semantic_success=all(r["semantic_success"] for r in finals),
        corrections=sum(max(0, len(s["rounds"]) - 1) for s in report["slides"]),
        initial_complete=all(s["rounds"][0]["complete"] for s in report["slides"]),
        initial_parse_success=all(s["rounds"][0]["parse_success"] for s in report["slides"]),
        initial_semantic_success=all(s["rounds"][0]["semantic_success"] for s in report["slides"]),
    )
    if len(accepted) == 5:
        source = print_ast(PresentationNode(title=titles[0], theme="claro", slides=accepted))
        (out / "presentation.sld").write_text(source, encoding="utf-8")
        validation = validate_source(source)
        save_json(out / "ast.json", validation.ast.model_dump() if validation.ast else None)
        save_json(out / "ir.json", validation.ir.model_dump() if validation.ir else None)
        save_json(out / "diagnostics.json", validation.report(strict))
        report["valid"] = validation.success(strict)
        report["design_errors"] = sum(
            d.code.startswith("D") and d.severity == "ERRO" for d in validation.diagnostics
        )
        report["design_warnings"] = sum(
            d.code.startswith("D") and d.severity == "AVISO" for d in validation.diagnostics
        )
        if report["valid"]:
            try:
                compilation = compile_source(source, out / "presentation.pptx", strict=strict)
                report["compile_success"] = True
                save_json(out / "pptx_inspection.json", compilation)
            except (OSError, RuntimeError, DSLException) as exc:
                report["compile_error"] = str(exc)
        report["source_sha256"] = sha(source)
    report["duration_ms"] = (time.perf_counter() - started) * 1000
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    save_json(out / "report.json", report)
    return report


def publish_demo(out: Path, report: dict):
    if not report["compile_success"] or report["is_mock"]:
        raise ValueError("Só uma apresentação real compilada pode ser publicada como demo.")
    source = (out.resolve() / "presentation.sld").relative_to(project_root())
    save_json(
        project_root() / "outputs/demo_local/latest.json",
        {
            "source": source.as_posix(),
            "sha256": hashlib.sha256((project_root() / source).read_bytes()).hexdigest(),
        },
    )


def evaluate_incremental(
    models, modes, request, out: Path, *, repetitions=5, resume=False, **options
):
    if (
        repetitions < 1
        or not models
        or not modes
        or len(set(models)) != len(models)
        or len(set(modes)) != len(modes)
    ):
        raise ValueError("Modelos/modos únicos e ao menos uma repetição são obrigatórios.")
    cfg = {
        "models": models,
        "modes": modes,
        "request": request,
        "repetitions": repetitions,
        "runs": [
            parameters(
                m,
                mode,
                request,
                options.get("repair_max", 2),
                options.get("temperature", 0.1),
                42 + rep,
                options.get("context_length", 8192),
                options.get("output_tokens", 4096),
                options.get("strict", False),
            )
            for m in models
            for mode in modes
            for rep in range(repetitions)
        ],
    }
    out = out.resolve()
    if out.exists():
        if (
            not resume
            or json.loads((out / "configuration.json").read_text(encoding="utf-8")) != cfg
        ):
            raise ValueError(
                "Diretório existente: retome somente com --resume e a configuração idêntica."
            )
    else:
        out.mkdir(parents=True)
        save_json(out / "configuration.json", cfg)
    rows = []
    for model in models:
        for mode in modes:
            for rep in range(repetitions):
                folder = (
                    out
                    / "runs"
                    / model.replace(":", "_").replace("/", "_")
                    / mode
                    / f"rep_{rep + 1:02d}"
                )
                if folder.exists():
                    report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
                    if report["status"] != "NAO_EXECUTADO" and "finished_utc" not in report:
                        raise ValueError(
                            f"Execução parcial preservada em {folder}; use outro diretório, sem sobrescrever."
                        )
                else:
                    report = generate_deck(model, mode, request, folder, seed=42 + rep, **options)
                rows.append(
                    {
                        "model": model,
                        "mode": mode,
                        "repeat": rep + 1,
                        "path": str(folder.relative_to(out)),
                        **{
                            k: report.get(k)
                            for k in (
                                "status",
                                "is_mock",
                                "complete",
                                "initial_complete",
                                "initial_parse_success",
                                "initial_semantic_success",
                                "parse_success",
                                "semantic_success",
                                "valid",
                                "compile_success",
                                "design_errors",
                                "design_warnings",
                                "corrections",
                                "duration_ms",
                            )
                        },
                    }
                )
                save_json(out / "runs.json", rows)
    summary = []
    for model in models:
        for mode in modes:
            group = [r for r in rows if r["model"] == model and r["mode"] == mode]
            summary.append(
                {
                    "model": model,
                    "mode": mode,
                    "repetitions": len(group),
                    **{
                        key: sum(bool(r[key]) for r in group)
                        for key in (
                            "initial_complete",
                            "initial_parse_success",
                            "initial_semantic_success",
                            "complete",
                            "parse_success",
                            "semantic_success",
                            "valid",
                            "compile_success",
                        )
                    },
                    "corrections": sum(r["corrections"] for r in group),
                    "statuses": dict(Counter(r["status"] for r in group)),
                }
            )
    result = {"configuration": cfg, "runs": rows, "summary": summary}
    save_json(out / "evaluation.json", result)
    with (out / "evaluation.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Avaliação incremental real",
        "",
        "Validade inclui parser, semântica e erros fatais de design. Avisos são registrados. JSON sempre passa pela SlideDSL.",
        "",
        "| Modelo | Modo | N | Completa inicial/final | Parse inicial/final | Semântica inicial/final | Válida final | PPTX | Correções |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        lines.append(
            f"| {r['model']} | {r['mode']} | {r['repetitions']} | {r['initial_complete']}/{r['complete']} | {r['initial_parse_success']}/{r['parse_success']} | {r['initial_semantic_success']}/{r['semantic_success']} | {r['valid']} | {r['compile_success']} | {r['corrections']} |"
        )
    (out / "RESULTADOS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result
