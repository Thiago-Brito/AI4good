from slidedsl.design_rules import check_design, contrast, load_rules


def codes(deck):
    return {d.code for d in check_design(deck) if d.severity != "INFORMAÇÃO"}


def test_d001_outside(compile_scene):
    assert "D001" in codes(
        compile_scene("adicionar retangulo id a em (1400,0) tamanho (50,50) cor #000000")
    )


def test_d001_boundary_pass(compile_scene):
    assert "D001" not in codes(
        compile_scene("adicionar retangulo id a em (1230,670) tamanho (50,50) cor #000000")
    )


def test_d002_contrast(compile_scene):
    assert contrast("#000000", "#FFFFFF") == 21
    d = compile_scene(
        'adicionar retangulo id fundo em (0,0) tamanho (1280,720) cor #FFFFFF adicionar texto id a "A" em (80,80) tamanho (100,100) fonte 24 cor #EEEEEE'
    )
    assert "D002" in codes(d)
    d.slides[0].elements[1].color = "#000000"
    assert "D002" not in codes(d)


def test_d002_indeterminate_image(compile_scene, root, tmp_path):
    # O mesmo comportamento para imagem ou elipse sem retângulo sólido integral.
    d = compile_scene(
        'adicionar elipse id e em (80,80) tamanho (300,300) cor #FFFFFF adicionar texto id a "A" em (100,100) tamanho (100,100) fonte 24 cor #000000'
    )
    info = [x for x in check_design(d) if x.code == "D002"]
    assert info[0].severity == "INFORMAÇÃO" and info[0].evidence["status"] == "INDETERMINADO"


def test_d003_title_theme(compile_scene):
    d = compile_scene(
        'adicionar texto id titulo "A" em (80,80) tamanho (500,100) fonte 30 cor #14233D'
    )
    assert "D003" in codes(d)
    d.slides[0].elements[0].font_size = 42
    assert "D003" not in codes(d)
    d.slides[0].elements[0].role = None
    d.slides[0].elements[0].color = "#000000"
    assert "D003" not in codes(d)


def test_d004_declared_alignment_drift(compile_scene):
    d = compile_scene(
        "adicionar retangulo id a em (80,80) tamanho (100,100) cor #FFFFFF adicionar retangulo id b em (200,240) tamanho (100,100) cor #000000 alinhar b com a pela esquerda"
    )
    assert "D004" not in codes(d)
    d.slides[0].elements[1].x = 82
    assert "D004" not in codes(d)
    d.slides[0].elements[1].x = 82.1
    assert "D004" in codes(d)


def test_d005_group_gap(compile_scene):
    d = compile_scene(
        "adicionar retangulo id a em (80,80) tamanho (100,100) cor #FFFFFF adicionar retangulo id b em (400,80) tamanho (100,100) cor #000000 agrupar [a,b] como g"
    )
    assert "D005" in codes(d)
    d.slides[0].elements[1].x = 300
    assert "D005" not in codes(d)


def test_d006_hierarchy(compile_scene):
    d = compile_scene(
        'adicionar texto id titulo "A" em (80,80) tamanho (500,100) fonte 24 cor #14233D adicionar texto id corpo "B" em (80,200) tamanho (500,100) fonte 30 cor #14233D'
    )
    assert "D006" in codes(d)


def test_d007_density_excludes_background(compile_scene):
    d = compile_scene("adicionar retangulo id fundo em (0,0) tamanho (1280,720) cor #FFFFFF")
    assert "D007" not in codes(d)
    d.slides[0].elements[0].role = None
    assert "D007" in codes(d)


def test_d008_true_occlusion_and_front(compile_scene):
    base = 'adicionar texto id a "A" em (80,80) tamanho (100,100) fonte 24 cor #000000 adicionar retangulo id b em (80,80) tamanho (100,100) cor #FFFFFF'
    assert "D008" in codes(compile_scene(base))
    assert "D008" not in codes(compile_scene(base + " trazer a para frente"))


def test_d008_union_and_threshold(compile_scene):
    d = compile_scene(
        'adicionar texto id a "A" em (0,0) tamanho (100,100) fonte 24 cor #000000 adicionar retangulo id b em (0,0) tamanho (20,100) cor #FFFFFF adicionar retangulo id c em (0,0) tamanho (20,100) cor #FFFFFF papel decoracao'
    )
    assert "D008" not in {x.code for x in check_design(d) if x.element == "a"}
    d.slides[0].elements[1].width = 21
    occlusion = [x for x in check_design(d) if x.code == "D008" and x.element == "a"][0]
    assert occlusion.evidence["fraction"] == 0.21


def test_d008_decorative_target_not_warned(compile_scene):
    d = compile_scene(
        'adicionar retangulo id decoracao em (80,80) tamanho (100,100) cor #FFFFFF adicionar texto id a "A" em (80,80) tamanho (100,100) fonte 24 cor #000000'
    )
    assert "D008" not in codes(d)


def test_d009_ir_invalid_dimension(compile_scene):
    d = compile_scene("adicionar retangulo id a em (80,80) tamanho (100,100) cor #FFFFFF")
    d.slides[0].elements[0].width = 0
    assert "D009" in codes(d)


def test_d010_approximate_overflow(compile_scene):
    d = compile_scene(
        'adicionar texto id a "Uma frase muito grande para caber em caixa pequena" em (80,80) tamanho (20,20) fonte 40 cor #000000'
    )
    diag = [x for x in check_design(d) if x.code == "D010"][0]
    assert diag.severity == "AVISO" and "estimativa" in diag.message


def test_configurable_threshold(compile_scene):
    d = compile_scene('adicionar texto id a "A" em (80,80) tamanho (100,100) fonte 24 cor #EEEEEE')
    cfg = load_rules()
    cfg["contrast_minimum"] = 1
    assert "D002" not in {x.code for x in check_design(d, cfg)}
