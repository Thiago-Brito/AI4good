from pathlib import Path
import hashlib
import json
import tempfile

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from starlette.background import BackgroundTask

from .compiler import compile_ir
from .design_rules import check_design
from .diagnostics import DSLException, failed
from .geometry import aligned_position, bounds, translate
from .ir import Presentation, Relation
from .paths import project_root
from .pipeline import validate_source
from .semantic import validate_ir
from .serializer import to_dsl
from .contextual import GenerationContext

app = FastAPI(title="SlideDSL — API local", version="1.1.0")


class SourcePayload(BaseModel):
    source: str


class IRPayload(BaseModel):
    ir: Presentation


class RelationPayload(IRPayload):
    slide: int
    relation: Relation


class GenerationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: str = Field(min_length=1, max_length=200)
    prompt: str = Field(min_length=1, max_length=12000)
    strategy: Literal["A", "B", "C", "D"] = "D"
    slides: int | None = Field(default=None, ge=1, le=12)
    strict: bool = True
    seed: int = 42
    reliability: bool = False
    repair_max: int = Field(default=2, ge=0, le=10)
    plan: dict | None = None
    requirements: list[dict] | None = None
    context: GenerationContext | None = None
    base_ir: Presentation | None = None
    current_ir: Presentation | None = None
    media_bindings: dict[str, str] = Field(default_factory=dict, max_length=12)
    base_source: str | None = Field(default=None, max_length=120000)


@app.get("/api/models")
def local_models():
    from .models.base import ModelError
    from .models.ollama_model import OllamaTextModel

    try:
        model = OllamaTextModel("", timeout=5)
        tags = model._request("GET", "/api/tags")
        return {
            "available": True,
            "models": [
                {"name": m["name"], "digest": m.get("digest")} for m in tags.get("models", [])
            ],
        }
    except ModelError as exc:
        return {"available": False, "models": [], "error": str(exc)}


@app.post("/api/generations", status_code=202)
def start_generation(payload: GenerationPayload):
    from .evolution import requested_count
    from .generation_jobs import submit_job

    try:
        if not payload.prompt.strip():
            raise ValueError("Escreva o pedido da apresentação.")
        requested_count(payload.prompt)  # Reject unsupported counts before queueing.
        if payload.plan is not None:
            from .planning import DeckPlan

            DeckPlan.model_validate(payload.plan)
            if payload.requirements is None:
                raise ValueError("Correção exige os critérios congelados da geração.")
        if (payload.base_ir is None) != (payload.current_ir is None):
            raise ValueError("Sincronização exige cena original e cena editada.")
        if payload.context is not None and payload.strategy not in {"C", "D"}:
            raise ValueError("Configurações contextuais exigem C ou D.")
        if payload.media_bindings:
            import re
            from .media import cached_assets

            catalog = {a["id"] for a in cached_assets()}
            for path, id in payload.media_bindings.items():
                match = re.fullmatch(r"slides\.(\d+)\.media\.(\d+)\.asset", path)
                if not match or id not in catalog or payload.plan is None:
                    raise ValueError("Seleção manual exige campo existente e imagem armazenada.")
                si, mi = map(int, match.groups())
                if si >= len(payload.plan["slides"]) or mi >= len(
                    payload.plan["slides"][si].get("media", [])
                ):
                    raise ValueError("Campo de imagem não existe no plano.")
        if payload.requirements is not None:
            from .requirements import Requirement

            for requirement in payload.requirements:
                Requirement.model_validate(requirement)
        return submit_job(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@app.get("/api/generations/{id}")
def generation_progress(id: str):
    import re
    from .generation_jobs import read_job

    if not re.fullmatch(r"[a-f0-9]{32}", id):
        raise HTTPException(404, detail="Geração não encontrada.")
    try:
        return read_job(id)
    except KeyError as exc:
        raise HTTPException(404, detail="Geração não encontrada.") from exc


class RequirementsPayload(IRPayload):
    requirements: list[dict]
    source: str | None = None


@app.post("/api/requirements/validate")
def validate_requirements(payload: RequirementsPayload):
    from .pipeline import ValidationResult
    from .requirements import evaluate_requirements
    from .parser import parse

    try:
        result = ValidationResult(ir=payload.ir, semantic_success=not validate_ir(payload.ir))
        if payload.source:
            result.ast = parse(payload.source)
            result.parse_success = True
        return evaluate_requirements(result, payload.requirements)
    except (ValueError, DSLException) as exc:
        raise HTTPException(422, detail=str(exc)) from exc


def normalize_ir(deck: Presentation):
    deck = deck.model_copy(deep=True)
    for s in deck.slides:
        s.elements.sort(key=lambda e: e.z)
        for z, e in enumerate(s.elements):
            e.z = z
            if e.color:
                e.color = e.color.upper()
    return deck


def report_ir(deck: Presentation):
    from .visual_validation import check_visual
    from .diagnostics import Diagnostic

    diagnostics = (
        validate_ir(deck)
        + check_design(deck)
        + [Diagnostic.model_validate(d) for d in check_visual(deck)]
    )
    return {"valid": not failed(diagnostics), "diagnostics": [d.model_dump() for d in diagnostics]}


@app.get("/api/health")
def health():
    return {"status": "ok", "schema_version": "1.1"}


@app.get("/api/local-demo")
def local_demo():
    root = project_root()
    manifest = root / "outputs/demo_local/latest.json"
    if not manifest.is_file():
        raise HTTPException(404, detail="Execute a demo local antes de abrir o resultado.")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        path = (root / data["source"]).resolve()
        if not path.is_relative_to((root / "outputs").resolve()) or path.suffix != ".sld":
            raise ValueError("Manifesto fora de outputs ou sem SlideDSL.")
        source = path.read_bytes()
        if hashlib.sha256(source).hexdigest() != data["sha256"]:
            raise ValueError("A apresentação mudou desde a publicação da demo.")
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    return {"source": source.decode("utf-8"), "path": data["source"]}


@app.post("/api/parse")
def parse_document(payload: SourcePayload):
    result = validate_source(payload.source)
    if not result.semantic_success:
        raise HTTPException(422, detail=result.report())
    return {"ir": result.ir.model_dump(), "report": result.report()}


@app.post("/api/validate")
def validate_document(payload: IRPayload):
    return report_ir(normalize_ir(payload.ir))


@app.post("/api/export")
def export_document(payload: IRPayload):
    deck = normalize_ir(payload.ir)
    errors = validate_ir(deck)
    if errors or any(e.width <= 0 or e.height <= 0 for s in deck.slides for e in s.elements):
        raise HTTPException(422, detail=report_ir(deck))
    source = to_dsl(deck)
    # Verifica exportação pela mesma cadeia antes de entregar código.
    result = validate_source(source)
    if not result.semantic_success:
        raise HTTPException(422, detail=result.report())
    return {"source": source}


@app.post("/api/compile")
def compile_document(payload: IRPayload):
    deck = normalize_ir(payload.ir)
    report = report_ir(deck)
    if not report["valid"]:
        raise HTTPException(422, detail=report)
    folder = project_root() / "outputs/editor"
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=folder, suffix=".pptx", delete=False) as f:
        target = Path(f.name)
    target.unlink()
    try:
        compile_ir(deck, target)
    except DSLException as exc:
        raise HTTPException(422, detail=[d.model_dump() for d in exc.diagnostics]) from exc
    except (OSError, RuntimeError) as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(503, detail=str(exc)) from exc
    return FileResponse(
        target,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename="apresentacao.pptx",
        background=BackgroundTask(target.unlink, missing_ok=True),
    )


@app.post("/api/relation")
def apply_relation(payload: RelationPayload):
    deck = normalize_ir(payload.ir)
    if validate_ir(deck):
        raise HTTPException(422, detail=report_ir(deck))
    slide = next((s for s in deck.slides if s.number == payload.slide), None)
    if slide is None:
        raise HTTPException(422, detail="Slide não existe.")
    r = payload.relation
    elements = {e.id: e for e in slide.elements}
    groups = {g.id: g for g in slide.groups}

    def objects(id):
        if id in elements:
            return [elements[id]]
        if id in groups:
            return [elements[m] for m in groups[id].members]
        raise HTTPException(422, detail="Referência não existe no mesmo slide.")

    target, reference = objects(r.target), objects(r.reference)
    if {e.id for e in target} & {e.id for e in reference}:
        raise HTTPException(
            422, detail="Relação exige conjuntos diferentes e sem sobreposição de IDs."
        )
    a, b = bounds(target), bounds(reference)
    if r.kind == "below":
        x, y = b[0], b[3] + r.margin
    elif r.kind == "right":
        x, y = b[2] + r.margin, b[1]
    else:
        x, y = aligned_position(a, b, "right" if r.kind == "align_right" else r.kind)
    translate(target, x, y)
    family = "position" if r.kind in {"below", "right"} else "alignment"
    slide.relations = [
        old
        for old in slide.relations
        if not (
            old.target == r.target
            and ("position" if old.kind in {"below", "right"} else "alignment") == family
        )
    ] + [r]
    return {"ir": deck.model_dump()}


@app.get("/api/examples/{name}")
def example(name: str):
    choices = {
        "cinco_slides": "cinco_slides.sld",
        "negativo_fora": "negativo_fora.sld",
        "operacoes": "operacoes.sld",
    }
    if name not in choices:
        raise HTTPException(404, detail="Exemplo não existe.")
    return {"source": (project_root() / "examples" / choices[name]).read_text(encoding="utf-8")}


class ImageSearchPayload(BaseModel):
    provider: Literal["openverse", "commons", "nasa"] = "openverse"
    query: str = Field(min_length=1, max_length=200)
    offline: bool = False


class ImageSelectionPayload(BaseModel):
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewed: bool = False


@app.post("/api/images/search")
def image_search(payload: ImageSearchPayload):
    from .media import search_images

    try:
        return search_images(payload.provider, payload.query, offline=payload.offline)
    except Exception as exc:
        raise HTTPException(
            503, detail=f"Busca indisponível; geração offline continua disponível: {exc}"
        ) from exc


@app.post("/api/images/select")
def image_select(payload: ImageSelectionPayload):
    from .media import cache_image

    try:
        return cache_image(payload.id, reviewed=payload.reviewed)
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, detail=f"Download indisponível: {exc}") from exc


@app.get("/api/images/cache")
def image_cache():
    from .media import cached_assets

    return {"results": cached_assets()}


class DocumentPayload(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    data_base64: str = Field(max_length=2_800_000)


class LocalImagePayload(DocumentPayload):
    author: str = Field(default="", max_length=200)
    license_note: str = Field(min_length=1, max_length=300)
    rights_confirmed: bool = False


@app.post("/api/images/local", status_code=201)
def add_local_image(payload: LocalImagePayload):
    import base64
    from .media import local_image

    try:
        return local_image(
            payload.name,
            base64.b64decode(payload.data_base64, validate=True),
            author=payload.author,
            license_note=payload.license_note,
            rights_confirmed=payload.rights_confirmed,
        )
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@app.post("/api/documents", status_code=201)
def add_reference(payload: DocumentPayload):
    import base64
    from .documents import add_document

    try:
        return add_document(payload.name, base64.b64decode(payload.data_base64, validate=True))
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@app.delete("/api/documents/{id}")
def remove_reference(id: str):
    from .documents import delete_document

    try:
        delete_document(id)
        return {
            "deleted": True,
            "note": "Trechos já usados permanecem nos trabalhos; exclua os trabalhos para remover essas cópias.",
        }
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@app.delete("/api/generations/{id}")
def remove_generation(id: str):
    import re
    import shutil
    from .generation_jobs import jobs, lock

    if not re.fullmatch(r"[a-f0-9]{32}", id):
        raise HTTPException(422, detail="Identificador inválido.")
    with lock:
        if id in jobs and jobs[id]["state"] in {"running", "queued"}:
            raise HTTPException(409, detail="Aguarde o trabalho terminar antes de excluir.")
        path = (project_root() / "outputs/generation_jobs" / id).resolve()
        if not path.is_relative_to((project_root() / "outputs/generation_jobs").resolve()):
            raise HTTPException(422, detail="Caminho inválido.")
        if path.exists():
            shutil.rmtree(path)
        jobs.pop(id, None)
    return {"deleted": True}


@app.delete("/api/images/cache/{id}")
def remove_image(id: str):
    from .media import safe_id, store_root

    try:
        safe_id(id)
        # Explicit deletion; callers are told existing presentations may require re-selection.
        (project_root() / "assets/media" / f"{id}.png").unlink(missing_ok=True)
        (store_root() / "assets" / f"{id}.json").unlink(missing_ok=True)
        (store_root() / "candidates" / f"{id}.json").unlink(missing_ok=True)
        for cache in (store_root() / "searches").glob("*.json"):
            entries = json.loads(cache.read_text("utf-8"))
            cache.write_text(json.dumps([i for i in entries if i["id"] != id]), "utf-8")
        return {
            "deleted": True,
            "note": "Apresentações que usam esse arquivo precisam selecionar uma imagem novamente.",
        }
    except (ValueError, OSError) as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@app.middleware("http")
async def bounded_local_requests(request, call_next):
    from fastapi.responses import JSONResponse
    from urllib.parse import urlsplit

    origin = request.headers.get("origin")
    same_origin = origin and urlsplit(origin).netloc == request.headers.get("host")
    development_origin = origin in {
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    } and request.url.hostname in {"127.0.0.1", "localhost"}
    if origin and not (same_origin or development_origin):
        return JSONResponse({"detail": "Origem externa bloqueada."}, status_code=403)
    if request.method in {"POST", "PUT", "PATCH"}:
        data, size = [], 0
        async for part in request.stream():
            size += len(part)
            if size > 4 * 1024 * 1024:
                return JSONResponse({"detail": "Solicitação maior que 4 MiB."}, status_code=413)
            data.append(part)
        request._body = b"".join(data)
    return await call_next(request)


app.mount("/assets", StaticFiles(directory=project_root() / "assets"), name="assets")
dist = project_root() / "editor/dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=dist, html=True), name="editor")
