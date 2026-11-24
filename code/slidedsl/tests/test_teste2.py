"""Teste 2: conferência do programa gerado e verificador único de PPTX (offline)."""

import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pptx_checks import check_pptx  # noqa: E402
from teste2_codigo import audit, extract_code  # noqa: E402


def _deck(path, n=2, overlap=False, long_text=False, outside=False):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for i in range(n):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        box = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(5), Inches(1))
        box.text_frame.text = ("palavra " * 200) if long_text and i == 0 else f"Slide {i + 1}"
        box.text_frame.paragraphs[0].runs[0].font.size = Pt(24)
        if overlap and i == 0:
            other = slide.shapes.add_textbox(Inches(1.5), Inches(1.2), Inches(5), Inches(1))
            other.text_frame.text = "sobreposto"
        if outside and i == 0:
            far = slide.shapes.add_textbox(Inches(12), Inches(6), Inches(4), Inches(1))
            far.text_frame.text = "fora"
    prs.save(path)
    return path


def test_extract_code_takes_python_block():
    raw = "Aqui está:\n```python\nprint(1)\n```\nFim."
    assert extract_code(raw) == "print(1)"
    assert extract_code("print(2)") == "print(2)"


def test_audit_blocks_unsafe_programs():
    assert audit("from pptx import Presentation\nimport math\n") == ""
    assert "importação" in audit("import os\n")
    assert "importação" in audit("from subprocess import run\n")
    assert "não permitido" in audit("eval('1')\n")
    assert "sintaxe" in audit("def (:\n")


def test_check_accepts_clean_deck(tmp_path):
    r = check_pptx(_deck(tmp_path / "a.pptx", n=2), 2)
    assert r["valido"] and r["valido_estrito"]


def test_check_blocks_slide_count_overlap_and_outside(tmp_path):
    assert any(b.startswith("B1") for b in check_pptx(_deck(tmp_path / "b.pptx", n=3), 2)["bloqueios"])
    r = check_pptx(_deck(tmp_path / "c.pptx", overlap=True), 2)
    assert any(b.startswith("B4") for b in r["bloqueios"])
    r = check_pptx(_deck(tmp_path / "d.pptx", outside=True), 2)
    assert any(b.startswith("B3") for b in r["bloqueios"])


def test_measured_overflow_is_strict_level_only(tmp_path):
    r = check_pptx(_deck(tmp_path / "e.pptx", long_text=True), 2)
    assert r["valido"] and not r["valido_estrito"]
    assert r["estouros"] and r["estouros"][0].startswith("B5")


def test_unreadable_file(tmp_path):
    bad = tmp_path / "x.pptx"
    bad.write_bytes(b"nada")
    r = check_pptx(bad, 2)
    assert not r["abre"] and not r["valido"]
