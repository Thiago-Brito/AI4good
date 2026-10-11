"""Local generation jobs: bounded queue, persistent evidence and polling progress."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from threading import RLock
from uuid import uuid4

from .evolution import generate_strategy
from .incremental import save_json
from .models.ollama_model import OllamaTextModel
from .paths import project_root
from .pipeline import validate_source

executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="slidedsl-slm")
lock = RLock()
jobs = {}


def _persist(job):
    folder = project_root() / "outputs/generation_jobs" / job["id"]
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / "job.tmp.json"
    save_json(temp, job)
    temp.replace(folder / "job.json")


def read_job(id):
    with lock:
        if id in jobs:
            return deepcopy(jobs[id])
    path = project_root() / "outputs/generation_jobs" / id / "job.json"
    if not path.is_file():
        raise KeyError(id)
    job = json.loads(path.read_text(encoding="utf-8"))
    if job["state"] in {"queued", "running"}:
        job.update(
            state="failed",
            error="Servidor reiniciado; execução parcial preservada. Gere novamente.",
        )
    return job


def _work(id, payload):
    def event(data):
        with lock:
            jobs[id]["events"].append(data)
            _persist(jobs[id])

    with lock:
        jobs[id]["state"] = "running"
        _persist(jobs[id])
    out = project_root() / "outputs/generation_jobs" / id / "run"
    try:
        if payload.get("plan") is not None:
            from .reliability import run_reliability

            if payload.get("media_bindings"):
                from .media import cached_assets

                catalog = {a["id"]: a for a in cached_assets()}
                before = deepcopy(payload["plan"])
                for path, id in payload["media_bindings"].items():
                    fields = path.split(".")
                    payload["plan"]["slides"][int(fields[1])]["media"][int(fields[3])]["asset"] = (
                        catalog[id]["asset"]
                    )
                out.parent.mkdir(parents=True, exist_ok=True)
                save_json(
                    out.parent / "manual_media.json",
                    {
                        "before": before,
                        "after": payload["plan"],
                        "bindings": payload["media_bindings"],
                    },
                )

            report = run_reliability(
                payload["plan"],
                payload["prompt"],
                out,
                count=len(payload["plan"]["slides"]),
                requirements=payload["requirements"],
                model=payload["model"],
                repair_max=payload["repair_max"],
                strict=payload["strict"],
                seed=payload["seed"],
                event_callback=event,
                allow_demo_repair=payload.get("context") is None
                or "imagem_demo.png" in payload["prompt"],
            )
        elif payload.get("context") is not None:
            from .contextual import generate_contextual

            report = generate_contextual(
                payload["model"],
                payload["strategy"],
                payload["prompt"],
                out,
                context=payload["context"],
                repair_max=payload["repair_max"],
                strict=payload["strict"],
                seed=payload["seed"],
                event_callback=event,
            )
        else:
            report = generate_strategy(
                payload["model"],
                payload["strategy"],
                payload["prompt"],
                out,
                slide_count=payload.get("slides"),
                strict=payload["strict"],
                seed=payload["seed"],
                event_callback=event,
                reliability=payload.get("reliability", False),
                repair_max=payload.get("repair_max", 2),
            )
        source_path = out / "presentation.sld"
        source = source_path.read_text(encoding="utf-8") if source_path.exists() else None
        validation = validate_source(source) if source else None
        generated_ir = validation.ir.model_dump() if validation and validation.ir else None
        if payload.get("current_ir") is not None and (
            payload["current_ir"] != payload["base_ir"] or not report.get("valid")
        ):
            from .edits import merge_manual, merged_source
            from .ir import Presentation
            from .requirements import evaluate_requirements
            from .compiler import compile_ir

            save_json(out / "candidate_report.json", report)
            if generated_ir is None or not report.get("valid"):
                merged = deepcopy(payload["current_ir"])
                edits = [{"conflict": "Candidato inválido; cena editada preservada integralmente."}]
                generated_ir = payload["base_ir"]
            else:
                merged, edits = merge_manual(
                    payload["base_ir"], payload["current_ir"], generated_ir
                )
            save_json(
                out / "manual_merge.json",
                {
                    "edits": edits,
                    "base": payload["base_ir"],
                    "current": payload["current_ir"],
                    "candidate": generated_ir,
                    "merged": merged,
                },
            )
            report["manual_edits"] = edits
            source = merged_source(
                Presentation.model_validate(merged), source or payload.get("base_source")
            )
            source_path.write_text(source, encoding="utf-8")
            validation = validate_source(source)
            if any(edit.get("conflict") for edit in edits):
                report.update(compile_success=False, manual_conflict=True)
                (out / "presentation.pptx").unlink(missing_ok=True)
            else:
                try:
                    compile_ir(validation.ir, out / "presentation.pptx", strict=payload["strict"])
                    report["compile_success"] = True
                except Exception as exc:
                    report.update(compile_success=False, compile_error=str(exc))
            report["requirements"] = evaluate_requirements(validation, payload["requirements"])
            from .visual_validation import check_visual
            from .design_rules import load_rules
            from .reliability import summary

            diagnostics = [d.model_dump() for d in validation.diagnostics]
            if validation.ir:
                diagnostics += check_visual(validation.ir)
            strict_codes = set(load_rules()["strict_codes"]) if payload["strict"] else set()
            errors = [
                d
                for d in diagnostics
                if d["severity"] == "ERRO"
                or (d["severity"] == "AVISO" and d["code"] in strict_codes)
            ]
            report["candidate_valid"] = report.get("valid")
            report.update(
                summary(
                    {
                        "validation": validation,
                        "errors": errors,
                        "diagnostics": diagnostics,
                        "requirements": report["requirements"],
                    }
                )
            )
            report["valid"] = validation.success(payload["strict"]) and not errors
            report["faithful"] = report["compile_success"] and report["requirements"]["all_met"]
            save_json(out / "ir.json", merged)
            save_json(out / "report.json", report)
        if payload.get("context") is not None and payload.get("plan") is not None:
            from .contextual import source_audit
            from .documents import retrieve

            context = payload["context"]
            chunks = (
                retrieve(context["documents"], payload["prompt"] + " " + context["theme"])
                if context["grounding"] != "free"
                else []
            )
            final_plan = json.loads((out / "plan.json").read_text("utf-8"))
            audit = source_audit(final_plan, chunks, context["grounding"] == "restricted")
            from .media import cached_assets

            catalog = {a["id"]: a for a in cached_assets()}
            allowed = {catalog[id]["asset"] for id in context["assets"] if id in catalog}
            used = []
            for number, slide in enumerate(final_plan["slides"], 1):
                for media in slide.get("media", []):
                    if media.get("asset") and media["asset"] not in allowed:
                        audit["issues"].append(
                            {
                                "slide": number,
                                "code": "M003",
                                "message": "Imagem fora da seleção autorizada",
                            }
                        )
                    used.extend(a for a in catalog.values() if a["asset"] == media.get("asset"))
                if "imagem_demo.png" not in payload["prompt"] and any(
                    d["kind"] == "image" for d in slide["decorations"]
                ):
                    audit["issues"].append(
                        {
                            "slide": number,
                            "code": "M003",
                            "message": "Imagem demonstrativa não solicitada",
                        }
                    )
            report["images"] = used
            report.update(source_audit=audit, settings=context)
            save_json(out / "source_audit.json", audit)
            if audit["issues"]:
                report.update(compile_success=False, faithful=False, source_conflict=True)
                (out / "presentation.pptx").unlink(missing_ok=True)
            save_json(out / "report.json", report)
        result = {
            "request": payload["prompt"],
            "generated_ir": generated_ir,
            "plan": json.loads((out / "plan.json").read_text(encoding="utf-8"))
            if (out / "plan.json").exists()
            else None,
            "source": source,
            "ir": validation.ir.model_dump() if validation and validation.ir else None,
            "report": {
                key: report.get(key)
                for key in (
                    "status",
                    "is_mock",
                    "compile_success",
                    "valid",
                    "diagnostics",
                    "corrections",
                    "requirements",
                    "duration_ms",
                    "availability",
                    "compile_error",
                    "faithful",
                    "attempts",
                    "calls",
                    "visual_quality",
                    "syntax",
                    "semantics",
                    "geometry",
                    "images",
                    "image_searches",
                    "source_audit",
                    "settings",
                    "manual_edits",
                    "manual_conflict",
                    "source_conflict",
                )
            },
            "path": out.relative_to(project_root()).as_posix(),
        }
        with lock:
            jobs[id].update(state="completed", result=result)
            _persist(jobs[id])
    except Exception as exc:
        with lock:
            jobs[id].update(state="failed", error=f"Geração interrompida: {exc}")
            _persist(jobs[id])


def submit_job(payload):
    adapter = OllamaTextModel(payload["model"])
    available, reason = adapter.available()
    if not available:
        raise ValueError(reason)
    with lock:
        if sum(job["state"] in {"queued", "running"} for job in jobs.values()) >= 2:
            raise RuntimeError("Já há duas gerações em andamento. Aguarde uma delas terminar.")
        id = uuid4().hex
        jobs[id] = {"id": id, "state": "queued", "events": [], "result": None, "error": None}
        _persist(jobs[id])
        executor.submit(_work, id, payload)
        return read_job(id)
