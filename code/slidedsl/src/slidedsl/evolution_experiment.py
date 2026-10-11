"""Reproducible A/B/C/D comparisons, separate from historical experiments."""

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

import httpx
from pydantic import Field

from .benchmarking import instruction_coverage
from .evolution import generate_strategy
from .incremental import save_json
from .paths import project_root
from .pipeline import validate_source
from .structured_slide import OutputModel


class Requirement(OutputModel):
    id: str
    slide: int = Field(ge=1, le=12)
    keywords: list[str] = Field(default_factory=list)
    two_columns: bool = False
    min_texts: int = 0


class RequestCase(OutputModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]+$")
    prompt: str = Field(min_length=1)
    slides: int = Field(ge=1, le=12)
    requirements: list[Requirement] = Field(default_factory=list)
    original_design_rubric: bool = False


def _write_results(out, cfg, rows):
    summary = []
    for strategy in cfg["strategies"]:
        group = [r for r in rows if r["strategy"] == strategy]
        executed = [r for r in group if r["status"] == "EXECUTADO"]
        summary.append(
            {
                "strategy": strategy,
                "attempted": len(group),
                "executed": len(executed),
                "generated": sum(r["generated_presentations"] for r in executed),
                "compiled": sum(r["compile_success"] for r in executed),
                "requirements_met": sum(r["requirements_all_met"] for r in executed),
                "syntax_errors": sum(r["syntax_errors"] for r in executed),
                "semantic_errors": sum(r["semantic_errors"] for r in executed),
                "geometry_errors": sum(r["geometry_errors"] or 0 for r in executed),
                "geometry_not_reached": sum(r["geometry_errors"] is None for r in executed),
                "corrections": sum(r["corrections"] for r in executed),
                "duration_ms": sum(r["duration_ms"] or 0 for r in executed),
                "statuses": dict(Counter(r["status"] for r in group)),
            }
        )
    result = {"configuration": cfg, "runs": rows, "summary": summary}
    save_json(out / "evaluation.json", result)
    if rows:
        with (out / "evaluation.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return result


def evaluate_strategies(
    model: str,
    cases: list[dict],
    out: Path,
    *,
    repetitions=5,
    strategies=None,
    resume=False,
    **options,
) -> dict:
    cases = [RequestCase.model_validate(case) for case in cases]
    strategies = strategies or ["A", "B", "C", "D"]
    if repetitions < 1 or not cases or len({c.id for c in cases}) != len(cases):
        raise ValueError("Pedidos únicos e ao menos uma repetição são obrigatórios.")
    if len(set(strategies)) != len(strategies) or not set(strategies) <= {"A", "B", "C", "D"}:
        raise ValueError("Estratégias únicas A, B, C, D.")
    options = {
        "temperature": 0.1,
        "context_length": 8192,
        "output_tokens": 4096,
        "strict": True,
        **options,
    }
    cfg = {
        "protocol": "evolution-v1",
        "model": model,
        "cases": [c.model_dump() for c in cases],
        "repetitions": repetitions,
        "strategies": strategies,
        "seed_base": 42,
        "options": options,
        "source_hashes": {
            name: hashlib.sha256((project_root() / "src/slidedsl" / name).read_bytes()).hexdigest()
            for name in (
                "evolution.py",
                "evolution_experiment.py",
                "planning.py",
                "layouts.py",
                "incremental.py",
                "structured_slide.py",
                "grammar/slidedsl.lark",
            )
        },
        "limitations": [
            "A/B geram um slide por chamada; C/D planejam o deck em uma chamada.",
            "B usa schema com coordenadas/IDs; C/D usam plano sem coordenadas/IDs.",
            "Mesmo modelo, parâmetros e pedido; prompts e número de chamadas diferem.",
            "A comparação não isola efeito da GLC; B/C mudam representação e layouts.",
            "C/D têm os mesmos prompts/schemas iniciais e diferem pela permissão de reparos; seeds não garantem respostas idênticas.",
            "Tempo inclui transporte, carregamento/cache, validação e compilação.",
            "Requisitos são proxies; PPTX compilado não implica correção completa.",
        ],
    }
    out = out.resolve()
    if out.exists():
        if (
            not resume
            or json.loads((out / "configuration.json").read_text(encoding="utf-8")) != cfg
        ):
            raise ValueError("Saída existente: --resume exige configuração/código idênticos.")
    else:
        out.mkdir(parents=True)
        save_json(out / "configuration.json", cfg)
        try:
            with httpx.Client(timeout=5, trust_env=False) as client:
                save_json(
                    out / "ollama_version.json",
                    client.get("http://127.0.0.1:11434/api/version").json(),
                )
                save_json(
                    out / "ollama_models.json", client.get("http://127.0.0.1:11434/api/tags").json()
                )
        except (httpx.HTTPError, ValueError) as exc:
            save_json(out / "availability.json", {"error": str(exc)})
    rows = []
    for rep in range(repetitions):
        # Rotate order to distribute cache/order effects; no concurrent model calls.
        ordered = strategies[rep % len(strategies) :] + strategies[: rep % len(strategies)]
        for case in cases:
            for strategy in ordered:
                folder = out / "runs" / case.id / f"rep_{rep + 1:02d}" / strategy
                report_path = folder / (
                    "evolution_report.json" if strategy in {"A", "B"} else "report.json"
                )
                if folder.exists():
                    if not report_path.is_file():
                        raise ValueError(f"Execução parcial preservada: {folder}; use nova saída.")
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                    if report["status"] != "NAO_EXECUTADO" and "finished_utc" not in report:
                        raise ValueError(f"Execução parcial preservada: {folder}; use nova saída.")
                else:
                    print(
                        f"Pedido {case.id}, repetição {rep + 1}, estratégia {strategy}", flush=True
                    )
                    report = generate_strategy(
                        model,
                        strategy,
                        case.prompt,
                        folder,
                        slide_count=case.slides,
                        seed=42 + rep,
                        requirements=[
                            r.model_dump(exclude_defaults=True) for r in case.requirements
                        ],
                        **options,
                    )
                source_path = folder / "presentation.sld"
                if not source_path.exists():
                    source_path = folder / "attempted.sld"
                rubric = None
                if case.original_design_rubric and source_path.exists():
                    rubric = instruction_coverage(
                        validate_source(source_path.read_text(encoding="utf-8"))
                    )
                    save_json(folder / "original_rubric.json", rubric)
                row = {
                    "case": case.id,
                    "repeat": rep + 1,
                    "strategy": strategy,
                    "model": model,
                    "seed": 42 + rep,
                    "path": folder.relative_to(out).as_posix(),
                    **{
                        key: report.get(key)
                        for key in (
                            "status",
                            "is_mock",
                            "generated_presentations",
                            "compile_success",
                            "syntax_errors",
                            "semantic_errors",
                            "generation_errors",
                            "geometry_errors",
                            "geometry_warnings",
                            "design_slides_reached",
                            "design_slides_potential",
                            "corrections",
                            "duration_ms",
                        )
                    },
                    "requirements_met": report["requirements"]["numerator"],
                    "requirements_total": report["requirements"]["denominator"],
                    "requirements_all_met": report["requirements"]["all_met"],
                    "original_rubric_met": rubric["numerator"] if rubric else None,
                    "original_rubric_total": rubric["denominator"] if rubric else None,
                    "model_digest": report["model_metadata"].get("model_digest"),
                }
                rows.append(row)
                _write_results(out, cfg, rows)
    return _write_results(out, cfg, rows)
