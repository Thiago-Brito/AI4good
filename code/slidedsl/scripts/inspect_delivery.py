"""Auditar artefatos reais da demo e produzir manifesto sem dados pessoais."""

import hashlib
import json
from pathlib import Path

from slidedsl.benchmarking import instruction_coverage
from slidedsl.compiler import inspect_pptx
from slidedsl.ir import semantic_snapshot
from slidedsl.pipeline import validate_source
from slidedsl.serializer import to_dsl


def inspect():
    root = Path(__file__).resolve().parents[1]
    source = (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")
    result = validate_source(source)
    back = validate_source(to_dsl(result.ir))
    pptx = inspect_pptx(root / "outputs/apresentacao.pptx")
    coverage = instruction_coverage(result)
    assert (
        pptx["slide_count"] == 5
        and pptx["text_objects"] > 0
        and pptx["image_objects"] == 1
        and pptx["shape_objects"] > 0
    )
    assert semantic_snapshot(result.ir) == semantic_snapshot(back.ir)
    assert coverage["numerator"] == coverage["denominator"]
    (root / "outputs/pptx_inspection.json").write_text(
        json.dumps(pptx, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    artifacts = [
        "outputs/apresentacao.pptx",
        "outputs/ast.json",
        "outputs/deck.json",
        "outputs/validation.json",
        "assets/imagem_demo.png",
    ]
    report = {
        "inspection": pptx,
        "roundtrip_equivalent": True,
        "reference_coverage": coverage,
        "artifacts": [
            {
                "path": p,
                "bytes": (root / p).stat().st_size,
                "sha256": hashlib.sha256((root / p).read_bytes()).hexdigest(),
            }
            for p in artifacts
        ],
    }
    (root / "outputs/delivery.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"Auditado: {pptx['slide_count']} slides, {pptx['text_objects']} textos, {pptx['shape_objects']} formas, {pptx['image_objects']} imagem; rubrica {coverage['numerator']}/{coverage['denominator']} e roundtrip equivalente."
    )


if __name__ == "__main__":
    inspect()
