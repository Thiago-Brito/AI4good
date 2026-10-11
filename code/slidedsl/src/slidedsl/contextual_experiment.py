"""Small separate structural, media and source experiments; no invented human scores."""

from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import shutil

from .contextual import generate_contextual
from .documents import add_document
from .evolution import generate_strategy
from .incremental import save_json
from .media import cached_assets
from .paths import project_root
from .pipeline import validate_source
from .preview import render_optional
from .reliability import run_reliability
from .requirements import evaluate_requirements
from .resources import ResourceMonitor


def evaluate_contextual(out: Path, manifest: dict, model=None):
    out.mkdir(parents=True, exist_ok=False)
    model = model or manifest["model"]
    cases = deepcopy(manifest["cases"])
    for case in cases:
        print(f"Executando domínio: {case['id']}", flush=True)
        case["requirements"] = [
            {"id": "slides", "kind": "slides", "minimum": 2, "description": "Dois slides"},
            {"id": "margins", "kind": "margins", "description": "Margens de 64 pixels"},
            *[
                {
                    "id": f"topic{i + 1}",
                    "kind": "text",
                    "slide": i + 1,
                    "value": term,
                    "description": f"Proxy lexical declarado: {term}",
                }
                for i, term in enumerate(case["terms"])
            ],
        ]
    from importlib.metadata import version
    import platform

    save_json(
        out / "configuration.json",
        {
            **manifest,
            "model": model,
            "cases": cases,
            "runtime": {
                "python": platform.python_version(),
                "pypdf": version("pypdf"),
                "Pillow": version("Pillow"),
                "psutil": version("psutil"),
            },
        },
    )
    snapshot = out / "sources_snapshot"
    hashes = {}
    executed_files = list((project_root() / "src/slidedsl").rglob("*.py")) + list(
        (project_root() / "src/slidedsl/grammar").glob("*.lark")
    )
    executed_files += list((project_root() / "config").glob("*.yaml")) + [
        project_root() / "renderer/render.mjs",
        project_root() / "renderer/package-lock.json",
        project_root() / "pyproject.toml",
        project_root() / "requirements-lock.txt",
    ]
    for file in executed_files:
        relative = file.relative_to(project_root())
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        hashes[relative.as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    save_json(out / "source_hashes.json", hashes)
    rows = []

    def row(case, condition, report, checks, plan_hash=None):
        rows.append(
            {
                "case": case["id"],
                "domain": case["domain"],
                "condition": condition,
                "compile_success": report.get("compile_success", False),
                "valid": report.get("valid", False),
                "requirements_met": checks["numerator"],
                "requirements_total": checks["denominator"],
                "faithful_measured": bool(report.get("valid") and checks["all_met"]),
                "initial_plan_sha256": plan_hash,
                "attempts": len(report.get("attempts", [])),
                "duration_ms": report.get("duration_ms"),
                "visual_human": None,
                "factual_human": None,
                "clarity_human": None,
            }
        )
        save_json(out / "evaluation.json", {"protocol": manifest["protocol"], "rows": rows})

    for case in cases:
        folder = out / case["id"]
        folder.mkdir()
        monitor = ResourceMonitor()
        monitor.start()
        try:
            direct = generate_strategy(model, "A", case["prompt"], folder / "direct", slide_count=2)
        finally:
            save_json(folder / "direct_resources.json", monitor.finish())
        source = folder / "direct/presentation.sld"
        validation = validate_source(source.read_text("utf-8")) if source.exists() else None
        checks = evaluate_requirements(validation, case["requirements"])
        row(case, "direct", direct, checks)
        initial = generate_contextual(
            model,
            "C",
            case["prompt"],
            folder / "planned",
            context={"research": "off"},
            repair_max=0,
        )
        plan_file = folder / "planned/plan.json"
        if not plan_file.exists():
            row(case, "planned", initial, evaluate_requirements(None, case["requirements"]))
            continue
        plan = json.loads(plan_file.read_text("utf-8"))
        plan_hash = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
        for condition in ["baseline", "validator", "deterministic"]:
            report = run_reliability(
                plan,
                case["prompt"],
                folder / condition,
                count=2,
                requirements=case["requirements"],
                mode=condition,
                repair_max=2,
                allow_demo_repair=False,
            )
            row(case, condition, report, report["requirements"], plan_hash)
    assets = cached_assets()
    media_results = []
    if assets:
        plan = {
            "title": "Imagem licenciada",
            "theme": "claro",
            "slides": [
                {
                    "title": "Exploração lunar",
                    "layout": "text_image",
                    "columns": [
                        {
                            "heading": "",
                            "items": ["Imagem selecionada pelo usuário no catálogo local."],
                            "group": False,
                        }
                    ],
                    "decorations": [],
                    "relations": [],
                    "footer": "",
                    "media": [
                        {
                            "asset": assets[0]["asset"],
                            "query": "Apollo 11 moon",
                            "caption": "Arquivo licenciado",
                        }
                    ],
                }
            ],
        }
        for condition in ["selected", "pending"]:
            data = deepcopy(plan)
            if condition == "pending":
                data["slides"][0]["media"][0]["asset"] = ""
            result = run_reliability(
                data,
                "Plano fixo de imagem",
                out / f"media_{condition}",
                count=1,
                requirements=[],
                mode="baseline",
                repair_max=0,
            )
            media_results.append(
                {
                    "condition": condition,
                    "compile_success": result["compile_success"],
                    "diagnostics": result["diagnostics"],
                    "calls": 0,
                }
            )
    document = add_document(
        "reference_aurora.txt", (project_root() / "benchmark/reference_aurora.txt").read_bytes()
    )
    sources = []
    for mode in ["free", "restricted"]:
        request = "Crie um slide sobre o Projeto Aurora: objetivo, duração da fase piloto e registro da equipe. Use title_content com uma coluna, exatamente três itens curtos, heading vazio, sem rodapé, decorações ou imagens. Consulte o contexto fornecido e cite os IDs dos trechos quando usá-los."
        result = generate_contextual(
            model,
            "C",
            request,
            out / f"sources_{mode}",
            context={"documents": [document["id"]], "grounding": mode, "research": "off"},
            repair_max=0,
        )
        sources.append(
            {
                "mode": mode,
                "compile_success": result.get("compile_success"),
                "calls": result.get("calls"),
                "audit": result.get("source_audit"),
                "factual_human": None,
            }
        )
    responses = []
    for file in out.rglob("response.json"):
        data = json.loads(file.read_text("utf-8"))
        if data and "message" in data and "done" in data:
            responses.append(data)
    example = next(out.rglob("presentation.pptx"), None)
    rendering = (
        render_optional(example, out / "rendering")
        if example
        else {"rendered": False, "engine": "not_reached"}
    )
    result = {
        "protocol": manifest["protocol"],
        "rows": rows,
        "media": media_results,
        "sources": sources,
        "actual_http_calls": len(responses),
        "output_tokens": sum(r.get("eval_count", 0) for r in responses),
        "input_tokens": sum(r.get("prompt_eval_count", 0) for r in responses),
        "rendering": rendering,
        "human_evaluation_applied": False,
        "limitation": "Uma repetição por domínio; não isola GLC, estética, factualidade ou generalização.",
    }
    save_json(out / "evaluation.json", result)
    if rows:
        with (out / "evaluation.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return result
