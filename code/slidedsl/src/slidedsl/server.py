from pathlib import Path
import hashlib
import json
import tempfile

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
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

app = FastAPI(title="SlideDSL — API local", version="1.1.0")


class SourcePayload(BaseModel):
    source: str


class IRPayload(BaseModel):
    ir: Presentation


class RelationPayload(IRPayload):
    slide: int
    relation: Relation


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
    diagnostics = validate_ir(deck) + check_design(deck)
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


app.mount("/assets", StaticFiles(directory=project_root() / "assets"), name="assets")
dist = project_root() / "editor/dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=dist, html=True), name="editor")
