import pytest

from slidedsl.compiler import compile_source, inspect_pptx
from slidedsl.diagnostics import DSLException
from slidedsl.ir import semantic_snapshot
from slidedsl.pipeline import validate_source
from slidedsl.serializer import to_dsl


def test_five_editable_slides_and_layer_order(root, tmp_path):
    source = (root / "examples/cinco_slides.sld").read_text(encoding="utf-8")
    out = tmp_path / "pasta com espaços" / "apresentação.pptx"
    result = compile_source(source, out, root)
    report = inspect_pptx(out)
    assert report["slide_count"] == 5
    assert (
        report["text_objects"] >= 20
        and report["image_objects"] == 1
        and report["shape_objects"] >= 6
    )
    objects = report["slides"][3]["objects"]
    image_index = next(i for i, o in enumerate(objects) if o["kind"] == "pic")
    rect_index = next(i for i, o in enumerate(objects) if o["name"] == "decoracao_retangulo")
    assert image_index > rect_index
    assert result["out"] == str(out.resolve())


def test_compile_invalid_never_creates_file(root, tmp_path):
    out = tmp_path / "não criar.pptx"
    with pytest.raises(DSLException):
        compile_source(
            (root / "examples/negativo_id_duplicado.sld").read_text(encoding="utf-8"), out, root
        )
    assert not out.exists()


def test_demo_dsl_ir_roundtrip(root, tmp_path):
    d = validate_source((root / "examples/cinco_slides.sld").read_text(encoding="utf-8"), root)
    again = validate_source(to_dsl(d.ir), root)
    assert semantic_snapshot(again.ir) == semantic_snapshot(d.ir)
    compile_source(to_dsl(d.ir), tmp_path / "roundtrip.pptx", root)
