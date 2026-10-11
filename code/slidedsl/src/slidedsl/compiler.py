import os
from pathlib import Path
import subprocess
import tempfile
import zipfile
import re
from uuid import uuid4
import xml.etree.ElementTree as ET

from .design_rules import check_design, load_rules
from .diagnostics import DSLException, failed
from .ir import Presentation
from .paths import node_executable, project_root
from .pipeline import validate_source
from .semantic import validate_ir
from .serializer import save_ir


def inspect_pptx(path: Path) -> dict:
    ns = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    }
    with zipfile.ZipFile(path) as z:
        names = sorted(
            [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)],
            key=lambda n: int(re.search(r"slide(\d+)\.xml", n)[1]),
        )
        slides = []
        for name in names:
            xml = ET.fromstring(z.read(name))
            tree = xml.find("p:cSld/p:spTree", ns)
            objects = []
            for obj in tree:
                label = obj.find(".//p:cNvPr", ns)
                if label is None:
                    continue
                objects.append(
                    {
                        "name": label.get("name"),
                        "kind": obj.tag.split("}")[-1],
                        "text": "".join(t.text or "" for t in obj.findall(".//a:t", ns)),
                    }
                )
            slides.append({"xml": name, "objects": objects})
        return {
            "slide_count": len(names),
            "slides": slides,
            "text_objects": sum(bool(o["text"]) for s in slides for o in s["objects"]),
            "image_objects": sum(o["kind"] == "pic" for s in slides for o in s["objects"]),
            "shape_objects": sum(
                o["kind"] == "sp" and not o["text"] for s in slides for o in s["objects"]
            ),
        }


def compile_ir(deck: Presentation, out: Path, root: Path | None = None, *, strict=False) -> dict:
    root = (root or project_root()).resolve()
    diagnostics = validate_ir(deck, root) + check_design(deck)
    if failed(diagnostics, set(load_rules()["strict_codes"]) if strict else None):
        raise DSLException(diagnostics)
    out = out.expanduser().resolve()
    if out.suffix.lower() != ".pptx":
        raise ValueError("A saída deve ter extensão .pptx.")
    tmp_root = project_root() / "outputs/tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="compile_") as temp:
        temp = Path(temp)
        ir_path, result_path = temp / "scene.json", temp / "deck.pptx"
        save_ir(deck, ir_path)
        command = [
            node_executable(),
            str(project_root() / "renderer/render.mjs"),
            str(ir_path),
            str(result_path),
            str(root),
        ]
        result = subprocess.run(
            command, shell=False, capture_output=True, text=True, encoding="utf-8", timeout=120
        )
        if result.returncode:
            raise RuntimeError(f"Renderer falhou: {result.stderr.strip()}")
        from .connections import anchor_pptx

        anchor_pptx(result_path, deck)
        inspection = inspect_pptx(result_path)
        if inspection["slide_count"] != len(deck.slides):
            raise RuntimeError("PPTX gerado não preservou a quantidade de slides.")
        out.parent.mkdir(parents=True, exist_ok=True)
        # A move from TemporaryDirectory retains its private Windows DACL.
        # Create the staging file under the delivery folder to inherit its access,
        # then publish atomically. The PowerPoint bytes remain unchanged.
        staging = out.with_name(f".{out.name}.{uuid4().hex}.tmp")
        try:
            staging.write_bytes(result_path.read_bytes())
            os.replace(staging, out)
        finally:
            staging.unlink(missing_ok=True)
    return {
        "out": str(out),
        "inspection": inspection,
        "diagnostics": [d.model_dump() for d in diagnostics],
    }


def compile_source(source: str, out: Path, root: Path | None = None, *, strict=False) -> dict:
    validation = validate_source(source, root)
    if not validation.success(strict):
        raise DSLException(validation.diagnostics)
    return compile_ir(validation.ir, out, root, strict=strict)
