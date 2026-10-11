"""Ablations replay the exact same initial plan; criteria frozen before generation."""

import csv
import json
from pathlib import Path

from .evolution import generate_strategy
from .incremental import save_json, sha
from .models.ollama_model import OllamaTextModel
from .paths import project_root
from .reliability import run_reliability
from .requirements import Requirement


def evaluate_reliability(cases, out, *, model="qwen3:4b-instruct", repetitions=2, repair_max=2):
    if repetitions < 1:
        raise ValueError("Repetições devem ser positivas")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    # Validate all criteria before any model call; model never defines evaluation.
    ids = set()
    for case in cases:
        import re

        if not re.fullmatch(r"[a-zA-Z0-9_-]+", case["id"]) or case["id"] in ids:
            raise ValueError("IDs únicos e seguros são obrigatórios")
        ids.add(case["id"])
        for criterion in case["requirements"]:
            Requirement.model_validate(criterion)
    config = {
        "protocol": "reliability-paired-v1",
        "cases": cases,
        "model": model,
        "repetitions": repetitions,
        "repair_max": repair_max,
        "temperature": 0.1,
        "num_ctx": 8192,
        "num_predict": 4096,
        "strict": True,
        "initial_plan_shared": True,
        "source_hashes": {
            str(p.relative_to(project_root())): sha(p.read_text(encoding="utf-8"))
            for p in (project_root() / "src/slidedsl").rglob("*.py")
        },
    }
    save_json(out / "configuration.json", config)
    import shutil

    for name in config["source_hashes"]:
        destination = out / "sources_snapshot" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project_root() / name, destination)
    adapter = OllamaTextModel(model, context_length=8192, output_tokens=4096)
    rows, actual_calls = [], 0
    available, reason = adapter.available()
    save_json(
        out / "model.json", {"available": available, "reason": reason, "metadata": adapter.metadata}
    )
    if not available:
        result = {"status": "NAO_EXECUTADO", "reason": reason, "runs": [], "actual_calls": 0}
        save_json(out / "evaluation.json", result)
        return result
    modes = ["baseline", "validator", "deterministic", "slm"]
    for case in cases:
        for repeat in range(repetitions):
            folder = out / case["id"] / f"rep_{repeat + 1}"
            initial = generate_strategy(
                model,
                "C",
                case["prompt"],
                folder / "initial",
                slide_count=case["slides"],
                adapter=adapter,
                seed=42 + repeat,
            )
            actual_calls += len(initial["rounds"])
            plan_file = folder / "initial/plan.json"
            for mode in modes[repeat % 4 :] + modes[: repeat % 4]:
                if not plan_file.exists():
                    rows.append(
                        {
                            "case": case["id"],
                            "repeat": repeat + 1,
                            "mode": mode,
                            "status": "INITIAL_PLAN_INVALID",
                            "compile_success": False,
                            "requirements_met": 0,
                            "requirements_total": len(case["requirements"]),
                            "requirements_all_met": False,
                        }
                    )
                    continue
                raw = plan_file.read_bytes()
                result = run_reliability(
                    json.loads(raw),
                    case["prompt"],
                    folder / mode,
                    count=case["slides"],
                    requirements=case["requirements"],
                    mode=mode,
                    repair_max=repair_max,
                    adapter=adapter,
                    seed=42 + repeat,
                    model=model,
                )
                actual_calls += result["repair_calls"]
                initial_response = json.loads(
                    (folder / "initial/round_0/response.json").read_text(encoding="utf-8")
                )
                ds = result["diagnostics"]
                row = {
                    "case": case["id"],
                    "repeat": repeat + 1,
                    "mode": mode,
                    "status": "EXECUTADO",
                    "is_mock": result["is_mock"],
                    "seed": 42 + repeat,
                    "initial_plan_sha256": sha(raw.decode("utf-8")),
                    "compile_success": result["compile_success"],
                    "faithful": result["faithful"],
                    "requirements_met": result["requirements"]["numerator"],
                    "requirements_total": result["requirements"]["denominator"],
                    "requirements_all_met": result["requirements"]["all_met"],
                    "syntax_errors": sum(
                        d["code"].startswith(("P", "J")) and d["severity"] == "ERRO" for d in ds
                    ),
                    "semantic_errors": sum(
                        d["code"].startswith(("S", "L002", "L003", "L005"))
                        and d["severity"] == "ERRO"
                        for d in ds
                    ),
                    "geometry_errors": sum(
                        d["code"].startswith(("D", "V", "L004", "L006")) and d["severity"] == "ERRO"
                        for d in ds
                    ),
                    "requirement_errors": sum(d["code"] == "R001" for d in ds),
                    "visual_warnings": sum(
                        d["code"].startswith(("D", "V")) and d["severity"] == "AVISO" for d in ds
                    ),
                    "corrections": result["corrections"],
                    "successful_corrections": result["successful_corrections"],
                    "failed_corrections": result["failed_corrections"],
                    "calls_including_shared_initial": 1 + result["repair_calls"],
                    "output_tokens_including_shared_initial": initial_response.get("eval_count", 0)
                    + result["repair_output_tokens"],
                    "duration_ms_including_shared_initial": initial["duration_ms"]
                    + result["duration_ms"],
                    "path": str((folder / mode).relative_to(out)),
                }
                rows.append(row)
                save_json(
                    out / "evaluation.json",
                    {
                        "status": "EXECUTADO",
                        "runs": rows,
                        "actual_calls": actual_calls,
                        "limitation": "Ablação sobre planos idênticos, amostra exploratória; sem inferência estatística de generalização. Chamada inicial compartilhada, não somar custos das linhas.",
                    },
                )
    fields = sorted({key for row in rows for key in row})
    with (out / "evaluation.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return json.loads((out / "evaluation.json").read_text(encoding="utf-8"))
