import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import time

import yaml

from .compiler import compile_ir
from .diagnostics import DSLException
from .generation import repair_prompt
from .geometry import area, bounds, box, distance, intersection
from .models.factory import create_model
from .paths import node_executable, project_root
from .pipeline import ValidationResult, validate_source
from .serializer import save_ir


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def layer_correctness(result: ValidationResult) -> bool:
    if not result.ir or len(result.ir.slides) < 4:
        return False
    elements = result.ir.slides[3].elements
    for image in (e for e in elements if e.type == "image"):
        for rect in (e for e in elements if e.type == "rectangle"):
            r = intersection(box(image), box(rect))
            if r and image.z > rect.z and 0 < area(r) < min(area(box(image)), area(box(rect))):
                return True
    return False


def instruction_coverage(result: ValidationResult) -> dict:
    rubric = yaml.safe_load((project_root() / "benchmark/rubric.yaml").read_text(encoding="utf-8"))
    checks = {x["id"]: False for x in rubric["items"]}
    checks["valid_commands"] = result.parse_success
    checks["unique_ids"] = result.semantic_success
    d = result.ir
    if d:
        checks.update(
            title=d.title == "Princípios de Design de Slides",
            theme=d.theme == "claro",
            slides=len(d.slides) == 5,
            canvas=(d.canvas.width, d.canvas.height) == (1280, 720),
        )
        if len(d.slides) >= 1:
            texts = [e for e in d.slides[0].elements if e.type == "text"]
            checks["cover"] = sum(abs(e.x + e.width / 2 - 640) <= 32 for e in texts) >= 2
        if len(d.slides) >= 2:
            s = d.slides[1]
            texts = [e for e in s.elements if e.type == "text"]
            shapes = [
                e
                for e in s.elements
                if e.type in {"rectangle", "ellipse"} and e.role != "background"
            ]
            checks["contrast_content"] = any(
                "contraste" in (e.text or "").casefold() for e in texts
            )
            checks["contrast_examples"] = len(texts) >= 2 and len({e.color for e in shapes}) >= 2
            checks["left_alignment"] = any(r.kind == "left" for r in s.relations)
        if len(d.slides) >= 3:
            s = d.slides[2]
            lookup = {e.id: e for e in s.elements}
            boxes = [bounds([lookup[id] for id in g.members]) for g in s.groups]
            checks["proximity_groups"] = any(
                distance(a, b) >= 64 for i, a in enumerate(boxes) for b in boxes[i + 1 :]
            )
        if len(d.slides) >= 4:
            s = d.slides[3]
            images = [
                e for e in s.elements if e.type == "image" and e.file == "assets/imagem_demo.png"
            ]
            checks["local_image"] = bool(images)

            def flatten(commands):
                return [
                    x for c in commands for x in (flatten(c.children) if c.op == "layout" else [c])
                ]

            commands = flatten(result.ast.slides[3].commands) if result.ast else []
            for image in images:
                indices = [
                    (i, c.op)
                    for i, c in enumerate(commands)
                    if c.id == image.id and c.op in {"back", "front"}
                ]
                checks["layer_actions"] = checks["layer_actions"] or any(
                    op == "back" and any(j > i and other == "front" for j, other in indices)
                    for i, op in indices
                )
            checks["final_layer"] = layer_correctness(result)
        if len(d.slides) >= 5:
            texts = [e for e in d.slides[4].elements if e.type == "text"]
            left = [e for e in texts if e.x + e.width / 2 < 640 and 200 <= e.y < 580]
            right = [e for e in texts if e.x + e.width / 2 >= 640 and 200 <= e.y < 580]
            checks["comparison_columns"] = (
                len(left) >= 4
                and len(right) >= 4
                and any("vantag" in e.text.casefold() for e in left)
                and any("limita" in e.text.casefold() for e in right)
            )
            checks["footer"] = any(e.y >= 580 for e in texts)
        checks["margins"] = all(
            e.x >= 64 and e.y >= 64 and e.x + e.width <= 1216 and e.y + e.height <= 656
            for s in d.slides
            for e in s.elements
            if e.role != "background"
        )
    numerator = sum(checks.values())
    denominator = len(checks)
    return {
        "numerator": numerator,
        "denominator": denominator,
        "fraction": numerator / denominator,
        "items": checks,
        "limitation": "Checklist geométrico e proxies lexicais; conteúdo/beleza precisam de avaliação humana.",
    }


def evaluate(raw: str, folder: Path, *, design: bool, root: Path) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "raw.txt").write_bytes(raw.encode("utf-8"))
    (folder / "program.sld").write_bytes(raw.encode("utf-8"))
    result = validate_source(raw, root, design=design)
    write_json(folder / "diagnostics.json", result.report())
    write_json(
        folder / "parser_log.json",
        {
            "accepted_entire_output": result.parse_success,
            "diagnostics": [d.model_dump() for d in result.diagnostics if d.code.startswith("P")],
        },
    )
    if result.ast:
        write_json(folder / "ast.json", result.ast.model_dump())
    if result.ir:
        save_ir(result.ir, folder / "ir.json")
    compiled = False
    compile_ms = None
    compile_error = None
    if result.semantic_success and len(result.ir.slides) == 5:
        start = time.perf_counter()
        try:
            report = compile_ir(result.ir, folder / "deck.pptx", root)
            compiled = (
                report["inspection"]["slide_count"] == 5
                and report["inspection"]["text_objects"] > 0
            )
            write_json(folder / "pptx_inspection.json", report["inspection"])
        except (DSLException, RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
            compile_error = str(exc)
        compile_ms = (time.perf_counter() - start) * 1000
    metric = {
        "parse_success": result.parse_success,
        "semantic_success": result.semantic_success,
        "compile_success": compiled,
        "instruction_coverage": instruction_coverage(result),
        "layer_correctness": layer_correctness(result),
        "design_errors": sum(
            d.code.startswith("D") and d.severity == "ERRO" for d in result.diagnostics
        )
        if design
        else None,
        "design_warnings": sum(
            d.code.startswith("D") and d.severity == "AVISO" for d in result.diagnostics
        )
        if design
        else None,
        "design_counts": {
            f"D{n:03}": sum(
                d.code == f"D{n:03}" and d.severity != "INFORMAÇÃO" for d in result.diagnostics
            )
            for n in range(1, 11)
        }
        if design
        else None,
        "compile_ms": compile_ms,
        "compile_error": compile_error,
        "valid": result.success(),
        "diagnostics": [d.model_dump() for d in result.diagnostics],
    }
    write_json(folder / "metrics.json", metric)
    return metric


def run_benchmark(
    models: list[str], repetitions: int, out: Path, *, conditions=None, adapters=None, resume=False
) -> dict:
    if repetitions < 1:
        raise ValueError("Repetições devem ser positivas.")
    conditions = conditions or ["A", "B", "C"]
    if not set(conditions) <= {"A", "B", "C"}:
        raise ValueError("Condições permitidas: A,B,C.")
    if (out / "benchmark.json").exists():
        raise FileExistsError(
            "Benchmark já existe; use outro diretório para preservar as tentativas."
        )
    if (out / "configuration.json").exists() and not resume:
        raise FileExistsError("Execução interrompida encontrada; use --resume ou outro diretório.")
    root = project_root()
    out.mkdir(parents=True, exist_ok=True)
    system_bytes = (root / "prompts/system_dsl.txt").read_bytes()
    user_bytes = (root / "benchmark/prompts/tarefa_cinco_slides.txt").read_bytes()
    system, user = system_bytes.decode("utf-8"), user_bytes.decode("utf-8")
    config = yaml.safe_load((root / "config/models.yaml").read_text(encoding="utf-8"))
    shutil_config = {
        "models": config,
        "rubric": yaml.safe_load((root / "benchmark/rubric.yaml").read_text(encoding="utf-8")),
    }
    if resume:
        for name, expected in [
            ("system_prompt.txt", system_bytes),
            ("user_prompt.txt", user_bytes),
        ]:
            if (out / name).read_bytes() != expected:
                raise ValueError("Resume exige os mesmos bytes dos prompts.")
        if json.loads((out / "configuration.json").read_text(encoding="utf-8")) != shutil_config:
            raise ValueError("Resume exige a mesma configuração e rubrica.")
    (out / "system_prompt.txt").write_bytes(system_bytes)
    (out / "user_prompt.txt").write_bytes(user_bytes)
    write_json(out / "configuration.json", shutil_config)
    version = subprocess.run(
        [node_executable(), "--version"], capture_output=True, text=True, timeout=10
    ).stdout.strip()
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "runtime": {"python": platform.python_version(), "node": version, "os": platform.system()},
        "repetitions_requested": repetitions,
        "conditions": conditions,
        "system_sha256": hashlib.sha256(system_bytes).hexdigest(),
        "user_sha256": hashlib.sha256(user_bytes).hexdigest(),
        "paired_AB": True,
        "models": {},
        "attempts": [],
        "resumed": resume,
    }
    for model_id in models:
        cfg = config["models"].get(model_id)
        if cfg is None:
            if model_id.startswith(("ollama:", "openai:", "mock:")):
                provider, actual_model = model_id.split(":", 1)
                cfg = {
                    "provider": provider,
                    "temperature": 0,
                    "seed": None,
                    "explicit_substitution": True,
                    "model": actual_model,
                }
            else:
                report["models"][model_id] = {
                    "status": "NAO_EXECUTADO",
                    "reason": "Modelo não configurado; use provider:ID para substituição explícita.",
                }
                continue
        provider = cfg["provider"]
        actual_model = cfg.get("model", model_id)
        model = (adapters or {}).get(model_id) or create_model(provider, actual_model)
        available, reason = model.available()
        status = {
            "status": "EXECUTADO" if available else "NAO_EXECUTADO",
            "reason": reason,
            "provider": provider,
            "is_mock": provider == "mock",
            "configuration": cfg,
            "metadata": dict(model.metadata),
            "successful_responses": 0,
            "generation_failures": 0,
            "reused_completed_repetitions": 0,
        }
        report["models"][model_id] = status
        if not available:
            continue
        slug = re.sub(r"[^a-zA-Z0-9_.-]", "_", model_id)
        for repeat in range(1, repetitions + 1):
            repetition_folder = out / "attempts" / slug / f"rep_{repeat:02}"
            saved_paths = [repetition_folder / c / "attempt.json" for c in conditions]
            if resume and all(p.is_file() for p in saved_paths):
                saved_rows = [json.loads(p.read_text(encoding="utf-8")) for p in saved_paths]
                for condition, row in zip(conditions, saved_rows):
                    if (row["model"], row["repeat"], row["condition"]) != (
                        model_id,
                        repeat,
                        condition,
                    ):
                        raise ValueError("Identidade da tentativa salva não confere.")
                    raw_path = repetition_folder / condition / "round_0" / "raw.txt"
                    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != row["raw_sha256"]:
                        raise ValueError("Hash da resposta salva não confere.")
                    metadata = row["rounds"][0].get("metadata", {})
                    for key in ["model_digest", "thinking", "num_ctx", "num_predict"]:
                        if key in metadata and metadata[key] != model.metadata.get(key):
                            raise ValueError(
                                f"Resume incompatível com parâmetro/modelo salvo: {key}."
                            )
                report["attempts"].extend(saved_rows)
                status["successful_responses"] += 1
                status["reused_completed_repetitions"] += 1
                continue
            if repetition_folder.exists():
                raise FileExistsError(
                    "Repetição parcial existente; preserve-a fora de attempts antes de retomar."
                )
            try:
                start = time.perf_counter()
                raw = model.generate(
                    system, user, temperature=cfg["temperature"], seed=cfg.get("seed")
                )
                duration = (time.perf_counter() - start) * 1000
                status["successful_responses"] += 1
            except RuntimeError as exc:
                status["generation_failures"] += 1
                report["attempts"].append(
                    {
                        "model": model_id,
                        "repeat": repeat,
                        "status": "FALHA_PROVEDOR",
                        "reason": str(exc),
                    }
                )
                continue
            for condition in conditions:
                folder = out / "attempts" / slug / f"rep_{repeat:02}" / condition
                metrics = evaluate(raw, folder / "round_0", design=condition != "A", root=root)
                first = dict(metrics)
                rounds = [
                    {
                        "round": 0,
                        "generation_ms": duration,
                        "prompt": user,
                        "metadata": dict(model.metadata),
                        **metrics,
                    }
                ]
                repair_rounds = 0
                if condition == "C":
                    previous = raw
                    for round in range(1, 3):
                        actionable = [
                            d for d in metrics["diagnostics"] if d["severity"] in {"ERRO", "AVISO"}
                        ]
                        if not actionable:
                            break
                        prompt = repair_prompt(user, previous, actionable)
                        try:
                            start = time.perf_counter()
                            repaired = model.generate(
                                system, prompt, temperature=cfg["temperature"], seed=cfg.get("seed")
                            )
                            ms = (time.perf_counter() - start) * 1000
                        except RuntimeError as exc:
                            rounds.append(
                                {
                                    "round": round,
                                    "status": "FALHA_PROVEDOR",
                                    "reason": str(exc),
                                    "prompt": prompt,
                                }
                            )
                            break
                        metrics = evaluate(
                            repaired, folder / f"round_{round}", design=True, root=root
                        )
                        rounds.append(
                            {
                                "round": round,
                                "generation_ms": ms,
                                "prompt": prompt,
                                "metadata": dict(model.metadata),
                                **metrics,
                            }
                        )
                        repair_rounds += 1
                        previous = repaired
                row = {
                    "model": model_id,
                    "condition": condition,
                    "repeat": repeat,
                    "status": "RESPONDEU",
                    "is_mock": provider == "mock",
                    "duration_ms": duration,
                    "raw_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                    "repair_rounds": repair_rounds,
                    "success_after_repair": metrics["valid"] if condition == "C" else None,
                    "first_attempt": first,
                    "final_attempt": metrics,
                    "rounds": rounds,
                }
                report["attempts"].append(row)
                write_json(folder / "attempt.json", row)
            status["metadata"] = dict(model.metadata)
        if status["successful_responses"] == 0:
            status["status"] = "FALHA_PROVEDOR"
            status["reason"] = "Todas as chamadas falharam; métricas de geração não calculadas."
    # Taxas incluem respostas do modelo; falhas de transporte têm contagem separada.
    summary = []
    for model_id in report["models"]:
        for condition in conditions:
            rows = [
                r
                for r in report["attempts"]
                if r.get("model") == model_id
                and r.get("condition") == condition
                and r["status"] == "RESPONDEU"
            ]
            if rows:
                summary.append(
                    {
                        "model": model_id,
                        "condition": condition,
                        "n": len(rows),
                        "is_mock": rows[0]["is_mock"],
                        "parse_rate_first": sum(r["first_attempt"]["parse_success"] for r in rows)
                        / len(rows),
                        "semantic_rate_first": sum(
                            r["first_attempt"]["semantic_success"] for r in rows
                        )
                        / len(rows),
                        "compile_rate_first": sum(
                            r["first_attempt"]["compile_success"] for r in rows
                        )
                        / len(rows),
                        "compile_rate_final": sum(
                            r["final_attempt"]["compile_success"] for r in rows
                        )
                        / len(rows),
                        "coverage_first_mean": sum(
                            r["first_attempt"]["instruction_coverage"]["fraction"] for r in rows
                        )
                        / len(rows),
                        "duration_ms_mean": sum(r["duration_ms"] for r in rows) / len(rows),
                    }
                )
    report["summary"] = summary
    write_json(out / "benchmark.json", report)
    fields = [
        "model",
        "condition",
        "repeat",
        "status",
        "is_mock",
        "parse_success",
        "semantic_success",
        "compile_success",
        "coverage_numerator",
        "coverage_denominator",
        "design_errors",
        "design_warnings",
        "layer_correctness",
        "duration_ms",
        "compile_ms",
        "repair_rounds",
        "success_after_repair",
    ]
    with (out / "benchmark.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for model_id, state in report["models"].items():
            if state["status"] == "NAO_EXECUTADO":
                writer.writerow(
                    {
                        "model": model_id,
                        "status": "NAO_EXECUTADO",
                        "is_mock": state.get("is_mock", False),
                    }
                )
        for row in report["attempts"]:
            if row["status"] != "RESPONDEU":
                writer.writerow({k: row.get(k) for k in fields})
                continue
            m = row["first_attempt"]
            cov = m["instruction_coverage"]
            writer.writerow(
                {
                    **{k: row.get(k) for k in fields},
                    **{k: m.get(k) for k in fields if k in m},
                    "coverage_numerator": cov["numerator"],
                    "coverage_denominator": cov["denominator"],
                }
            )
    with (out / "attempts.jsonl").open("w", encoding="utf-8") as f:
        for row in report["attempts"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    lines = [
        "# Análise do benchmark",
        "",
        f"Solicitadas {repetitions} repetições por modelo disponível. Mock é exclusivamente teste de infraestrutura.",
        "",
        "| Modelo | Estado | Motivo |",
        "|---|---|---|",
    ]
    lines += [f"| {m} | {s['status']} | {s['reason']} |" for m, s in report["models"].items()]
    lines += [
        "",
        "| Modelo | Condição | n | Parse inicial | Compila inicial | Compila final | Cobertura inicial |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    lines += [
        f"| {s['model']} | {s['condition']} | {s['n']} | {s['parse_rate_first']:.3f} | {s['compile_rate_first']:.3f} | {s['compile_rate_final']:.3f} | {s['coverage_first_mean']:.3f} |"
        for s in summary
    ]
    lines += [
        "",
        "A/B reutilizam exatamente a mesma primeira resposta (par pareado); B apenas observa design. C recebe no máximo dois reparos. O backend sempre rejeita erros geométricos fatais; A não mede avisos de design.",
        "Taxas usam somente tentativas que receberam texto, incluindo textos inválidos. Falhas de transporte são registradas separadamente. Não inferir melhora sem comparações reais. Proxies de conteúdo não substituem avaliação humana; amostra pequena, tokenizadores e infraestrutura diferentes.",
    ]
    examples = [
        (r["model"], r["condition"], d)
        for r in report["attempts"]
        if r["status"] == "RESPONDEU"
        for d in r["first_attempt"]["diagnostics"]
    ][:8]
    lines += ["", "## Amostras de diagnósticos iniciais", ""]
    lines += [
        f"- {m}/{c}: {d['code']} ({d['severity']}), slide {d['slide']}, elemento {d['element']}: {d['message']}"
        for m, c, d in examples
    ] or ["Sem saídas recebidas com diagnósticos para exemplificar."]
    (out / "ANALISE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [(m, s) for m, s in report["models"].items() if s["status"] != "EXECUTADO"]
    if missing:
        (out / "RESULTADOS_PENDENTES.md").write_text(
            "# Resultados pendentes\n\n"
            + "\n".join(f"- {m}: {s['reason']}" for m, s in missing)
            + "\n\nNão há médias/taxas inventadas para modelos sem resposta. Rode novamente em outro diretório após configurar os provedores.\n",
            encoding="utf-8",
        )
    return report
