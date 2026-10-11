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
        report = generate_strategy(
            payload["model"],
            payload["strategy"],
            payload["prompt"],
            out,
            slide_count=payload.get("slides"),
            strict=payload["strict"],
            seed=payload["seed"],
            event_callback=event,
        )
        source_path = out / "presentation.sld"
        source = source_path.read_text(encoding="utf-8") if source_path.exists() else None
        validation = validate_source(source) if source else None
        result = {
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
