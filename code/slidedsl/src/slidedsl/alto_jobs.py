"""Execuções do fluxo SlideDSL Alto para o editor: fila de 1, progresso e evidências."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
from threading import RLock
from uuid import uuid4

from .paths import project_root

executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="slidedsl-alto")
lock = RLock()
jobs: dict[str, dict] = {}


def folder(id: str):
    return project_root() / "outputs/criar" / id


def _persist(job):
    path = folder(job["id"])
    path.mkdir(parents=True, exist_ok=True)
    temp = path / "job.tmp.json"
    temp.write_text(json.dumps(job, ensure_ascii=False, default=str), "utf-8")
    temp.replace(path / "job.json")


def read_job(id: str) -> dict:
    with lock:
        if id in jobs:
            return deepcopy(jobs[id])
    path = folder(id) / "job.json"
    if not path.is_file():
        raise KeyError(id)
    job = json.loads(path.read_text("utf-8"))
    if job["state"] in {"queued", "running"}:
        job.update(state="failed", error="Servidor reiniciado durante a geração; gere novamente.")
    return job


def _model(payload):
    from .models.factory import create_model

    model = create_model(payload["provider"], payload["model"])
    if payload["provider"] == "ollama":
        model.context_length = 8192
        model.output_tokens = 2048
        model.metadata.update(num_ctx=8192, num_predict=2048)
    return model


def _work(id: str, payload: dict):
    def say(message: str):
        with lock:
            jobs[id]["events"].append(
                {"message": str(message)[:300], "at": datetime.now(timezone.utc).isoformat()}
            )
            _persist(jobs[id])

    with lock:
        jobs[id]["state"] = "running"
        _persist(jobs[id])
    out = folder(id)
    try:
        from .alto_generation import create_presentation
        from .pipeline import validate_source

        model = _model(payload)
        ok, message = model.available()
        if not ok:
            raise ValueError(f"Modelo indisponível: {message}")
        mode = payload.get("modo") or ("gramatica" if payload["provider"] == "llamacpp" else "json")
        report = create_presentation(
            payload["pedido"],
            out,
            model,
            research_provider=None if payload["buscador"] == "nenhum" else payload["buscador"],
            langs=tuple(payload["idiomas"]),
            n_slides=payload["slides"],
            theme=payload["tema"],
            mode=mode,
            candidates=payload["candidatos"],
            repair_max=payload["reparos"],
            images=payload["imagens"],
            contact=payload.get("contato") or None,
            allow_without_facts=payload["permitir_sem_fatos"],
            progress=say,
        )
        result = {"report": report, "folder": str(out.relative_to(project_root()))}
        dossier = out / "dossie.json"
        if dossier.is_file():
            data = json.loads(dossier.read_text("utf-8"))
            result["facts"] = [
                {k: f[k] for k in ("id", "claim", "kind", "value", "url", "source_title")}
                for f in data.get("facts", [])
            ]
        if (out / "apresentacao.slda").is_file():
            result["alto"] = (out / "apresentacao.slda").read_text("utf-8")
        if (out / "apresentacao.sld").is_file():
            source = (out / "apresentacao.sld").read_text("utf-8")
            validation = validate_source(source)
            result.update(
                source=source,
                ir=validation.ir.model_dump(mode="json") if validation.ir else None,
                diagnostics=[d.model_dump() for d in validation.diagnostics],
            )
        if (out / "validacao.json").is_file():
            result["validation"] = json.loads((out / "validacao.json").read_text("utf-8"))
        with lock:
            jobs[id].update(state="completed", result=result)
            _persist(jobs[id])
    except Exception as exc:  # o erro vai para a interface e para job.json
        with lock:
            jobs[id].update(state="failed", error=str(exc))
            _persist(jobs[id])


def submit(payload: dict) -> dict:
    with lock:
        if any(j["state"] in {"queued", "running"} for j in jobs.values()):
            raise RuntimeError("Já existe uma criação em andamento; aguarde terminar.")
        id = uuid4().hex
        jobs[id] = {
            "id": id,
            "state": "queued",
            "events": [],
            "result": None,
            "error": None,
            "payload": payload,
        }
        _persist(jobs[id])
    executor.submit(_work, id, payload)
    return read_job(id)
