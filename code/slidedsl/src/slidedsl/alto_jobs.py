"""Execuções do fluxo SlideDSL Alto para o editor: fila de 1, progresso e evidências."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
from threading import RLock
from uuid import uuid4

from .paths import project_root, replace_file

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
    replace_file(temp, path / "job.json")


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
    elif payload["provider"] == "openai":
        model.output_tokens = payload.get("max_output_tokens", 2048)
    return model


def _completo(payload, out, say, usage):
    """Fluxo completo do PC: pesquisa na internet/documentos, imagens, candidatos, lote."""
    from .alto_generation import create_presentation

    model = _model(payload)
    ok, message = model.available()
    if not ok:
        raise ValueError(f"Modelo indisponível: {message}")
    mode = payload.get("modo") or ("gramatica" if payload["provider"] == "llamacpp" else "json")
    return create_presentation(
        payload["pedido"],
        out,
        model,
        research_provider=None if payload["buscador"] == "nenhum" else payload["buscador"],
        langs=tuple(payload["idiomas"]),
        document_ids=payload.get("documentos"),
        sources_mode=payload.get("fontes"),
        n_slides=payload["slides"],
        theme=payload["tema"],
        mode=mode,
        candidates=payload["candidatos"],
        repair_max=payload["reparos"],
        images=payload["imagens"],
        batch=payload.get("lote", False),
        image_source=payload.get("imagens_fonte", "livres"),
        ai_profile=payload.get("imagens_ia_qualidade", "economica"),
        contact=payload.get("contato") or None,
        allow_without_facts=payload["permitir_sem_fatos"],
        progress=say,
        max_calls=payload.get("max_calls", 60),
        on_usage=usage,
    )


def _work(id: str, payload: dict):
    def usage(summary):
        with lock:
            jobs[id]["usage"] = summary
            _persist(jobs[id])

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
        from .pipeline import validate_source

        if payload.get("motor") == "celular":
            from .motor_celular import create_presentation_celular

            report = create_presentation_celular(
                payload["pedido"], out, modelo=payload["modelo_local"], n_slides=payload["slides"],
                document_ids=payload.get("documentos"), progress=say)
        else:
            report = _completo(payload, out, say, usage)
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
            "usage": None,
        }
        _persist(jobs[id])
    executor.submit(_work, id, payload)
    return read_job(id)


def _total_usage(out):
    """All attempts remain charged, including undone and failed revisions."""
    paths = [out / "uso.json", *(out / "versoes").glob("*/uso.json")]
    summaries = [json.loads(p.read_text("utf-8")) for p in paths if p.is_file()]
    if not summaries:
        return None
    result = dict(summaries[0])
    for key in ("calls", "max_calls", "failed_calls", "known_usage_calls", "unknown_usage_calls",
                "known_input_tokens", "known_output_tokens", "known_cached_input_tokens",
                "known_cost_usd", "text_cost_usd", "image_cost_usd", "image_calls", "unknown_image_cost"):
        result[key] = sum(s.get(key, 0) or 0 for s in summaries)
    result["cost_usd"] = (sum(s["cost_usd"] for s in summaries)
                          if all(s.get("cost_usd") is not None for s in summaries) else None)
    return result


def edit_job(id, payload):
    from .alto_edit import ajustar_alto, export_edit, refazer_slide
    from .model_usage import RecordedModel
    from .research import Dossier

    with lock:
        job = read_job(id)
        if job["state"] != "completed" or not job.get("result", {}).get("alto"):
            raise ValueError("Criação ainda não está pronta para edição.")
        if jobs.get(id, {}).get("editing"):
            raise RuntimeError("Já existe uma edição em andamento.")
        jobs[id] = job
        job["editing"] = True
        _persist(job)
    out = folder(id)
    revision = out / "versoes" / uuid4().hex
    action = payload["acao"]
    try:
        if action == "desfazer":
            history = job.get("history", [])
            if not history:
                raise ValueError("Não há versão anterior.")
            previous = json.loads((out / history[-1]).read_text("utf-8"))
            history.pop()
            job["result"] = previous
        else:
            facts = Dossier.load(out / "dossie.json").fact_map() if (out / "dossie.json").exists() else {}
            source = job["result"]["alto"]
            if action == "refazer":
                tracked = RecordedModel(_model(job["payload"]), revision, max_calls=2)
                outline = json.loads((out / "roteiro.json").read_text("utf-8")) if (out / "roteiro.json").exists() else None
                source = refazer_slide(source, payload["slide"], payload.get("instrucao") or "",
                                       facts, tracked, roteiro=outline)
            else:
                source = ajustar_alto(source, numero=payload["slide"],
                    tema=payload.get("tema"), foto_buscar=payload.get("foto_buscar"),
                    foto_arquivo=payload.get("foto_arquivo"), sem_foto=action == "sem_foto",
                    mover_para=payload.get("mover_para"), excluir=action == "excluir")
            built = export_edit(source, revision, facts)
            previous_path = revision / "anterior.json"
            previous_path.write_text(json.dumps(job["result"], ensure_ascii=False), "utf-8")
            job.setdefault("history", []).append(str(previous_path.relative_to(out)))
            if facts:
                Dossier.load(out / "dossie.json").save(revision / "dossie.json")
            result = deepcopy(job["result"])
            result.update(alto=source, source=built.dsl, ir=built.validation.ir.model_dump(mode="json"),
                folder=str(revision.relative_to(project_root())),
                diagnostics=[d.model_dump() for d in built.all_diagnostics], validation=built.report())
            result["report"].update(valid=True, pptx=str(revision / "apresentacao.pptx"), theme=built.deck.theme)
            job["result"] = result
    finally:
        with lock:
            job["usage"] = _total_usage(out) or job.get("usage")
            if job.get("result") and job.get("usage"):
                job["result"]["report"].update(usage=job["usage"], calls=job["usage"]["calls"])
            job["editing"] = False
            _persist(job)
    return read_job(id)
