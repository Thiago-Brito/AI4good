import jsonschema

from slidedsl.ir import Presentation, semantic_snapshot
from slidedsl.parser import parse
from slidedsl.semantic import analyze
from slidedsl.serializer import load_ir, save_ir, to_dsl


def test_json_and_dsl_roundtrip(compile_scene, tmp_path, root):
    d = compile_scene(
        'adicionar retangulo id a em (80,100) tamanho (100,60) cor #FF0000 adicionar texto id b "Oi" em abaixo de a com margem 24 tamanho (300,60) fonte 24 cor #14233D'
    )
    p = tmp_path / "ir.json"
    save_ir(d, p)
    assert load_ir(p) == d
    jsonschema.validate(d.model_dump(), Presentation.model_json_schema())
    again = analyze(parse(to_dsl(d)), root)
    assert semantic_snapshot(again) == semantic_snapshot(d)
