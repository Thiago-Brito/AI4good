"""Verificador único de PPTX para o Teste 2 (o mesmo para todos os grupos).

Olha apenas o arquivo final, sem saber como ele foi produzido. Critérios que bloqueiam:
  B1 número de slides diferente do pedido;
  B2 slide sem nenhum texto visível;
  B3 forma fora da área do slide (tolerância de 1% da dimensão);
  B4 duas caixas com texto sobrepostas (interseção > 10% da menor caixa).
  B5 texto maior que a caixa, medido com as mesmas funções do compilador (text_metrics: largura
     de cada palavra pelo arquivo da fonte, quebra por palavra, entrelinha 1,2, margens da caixa),
     com 5% de tolerância. Fica num nível separado ("estrito"): o PowerPoint pode reduzir o texto
     de placeholders com ajuste automático, o que esta medição não reproduz.
Aviso (não bloqueia): W2 corpo de texto menor que 12 pt.
Tamanho não declarado: título de placeholder 44 pt, corpo de placeholder 32 pt, caixa de texto 18 pt;
fonte não declarada: Calibri (tema padrão do python-pptx).

Uso: python scripts/pptx_checks.py arquivo.pptx --slides 6
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
EMU_PT = 12700


def _font_pt(shape, run, paragraph):
    for size in (run.font.size if run is not None else None, paragraph.font.size):
        if size is not None:
            return size.pt
    if shape.is_placeholder:
        try:
            kind = str(shape.placeholder_format.type)
        except Exception:
            kind = ""
        return 44.0 if "TITLE" in kind else 32.0
    return 18.0


def _text_shapes(shapes):
    for shape in shapes:
        if shape.shape_type == 6:  # grupo
            yield from _text_shapes(shape.shapes)
        elif shape.has_text_frame and shape.text_frame.text.strip():
            yield shape


def _box(shape):
    if None in (shape.left, shape.top, shape.width, shape.height):
        return None
    return (shape.left, shape.top, shape.left + shape.width, shape.top + shape.height)


def _family(run, paragraph):
    from slidedsl.text_metrics import FAMILIES

    name = (run.font.name if run is not None else None) or paragraph.font.name or "Calibri"
    return name if name in FAMILIES else "Arial"


def _lines(text, width_px, size, bold, family):
    from slidedsl.text_metrics import text_width

    lines, current = 1, ""
    for word in text.split():
        proposed = current + " " + word if current else word
        if current and text_width(proposed, size, bold, family) > width_px:
            lines += 1
            current = word
        else:
            current = proposed
    return lines


def _overflow(shape):
    """Altura medida do texto contra a altura da caixa, em pt."""
    if None in (shape.width, shape.height):
        return False, 0.0, 0.0
    tf = shape.text_frame
    ml, mr = tf.margin_left, tf.margin_right
    mt, mb = tf.margin_top, tf.margin_bottom
    width_px = (shape.width - (91440 if ml is None else ml) - (91440 if mr is None else mr)) / 9525
    pad = ((45720 if mt is None else mt) + (45720 if mb is None else mb)) / EMU_PT
    height = shape.height / EMU_PT
    if width_px <= 0:
        return True, 0.0, height
    need = pad
    for p in tf.paragraphs:
        runs = [r for r in p.runs if r.text]
        r0 = runs[0] if runs else None
        size = _font_pt(shape, r0, p)
        bold = bool(r0 is not None and r0.font.bold)
        need += _lines(p.text, width_px, size, bold, _family(r0, p)) * size * 1.2
        need += (p.space_before.pt if p.space_before else 0) + (p.space_after.pt if p.space_after else 0)
    return need > height * 1.05, need, height


def check_pptx(path: Path, n_slides: int) -> dict:
    from pptx import Presentation

    out = {"abre": False, "slides": 0, "bloqueios": [], "estouros": [], "avisos": [],
           "valido": False, "valido_estrito": False, "chars_visiveis": 0, "caixas_texto": 0}
    try:
        prs = Presentation(str(path))
    except Exception as exc:
        out["bloqueios"].append(f"B0 arquivo não abre: {type(exc).__name__}")
        return out
    out["abre"] = True
    sw, sh = prs.slide_width, prs.slide_height
    out["slides"] = len(prs.slides)
    if len(prs.slides) != n_slides:
        out["bloqueios"].append(f"B1 {len(prs.slides)} slides, pedido {n_slides}")
    for i, slide in enumerate(prs.slides, 1):
        texts = list(_text_shapes(slide.shapes))
        out["caixas_texto"] += len(texts)
        out["chars_visiveis"] += sum(len(s.text_frame.text.strip()) for s in texts)
        if not texts:
            out["bloqueios"].append(f"B2 slide {i} sem texto")
        for shape in slide.shapes:
            b = _box(shape)
            if b and (b[0] < -0.01 * sw or b[1] < -0.01 * sh or b[2] > 1.01 * sw or b[3] > 1.01 * sh):
                out["bloqueios"].append(f"B3 slide {i}: '{shape.name}' fora do slide")
        boxes = [(s, _box(s)) for s in texts]
        for a in range(len(boxes)):
            for c in range(a + 1, len(boxes)):
                (sa, ba), (sc, bc) = boxes[a], boxes[c]
                if not ba or not bc:
                    continue
                w = min(ba[2], bc[2]) - max(ba[0], bc[0])
                h = min(ba[3], bc[3]) - max(ba[1], bc[1])
                if w <= 0 or h <= 0:
                    continue
                smaller = min((ba[2] - ba[0]) * (ba[3] - ba[1]), (bc[2] - bc[0]) * (bc[3] - bc[1]))
                if smaller and w * h / smaller > 0.10:
                    out["bloqueios"].append(f"B4 slide {i}: '{sa.name}' sobrepõe '{sc.name}'")
        for s in texts:
            over, need, height = _overflow(s)
            if over:
                out["estouros"].append(f"B5 slide {i}: '{s.name}' {need:.0f} pt de texto em {height:.0f} pt")
            for p in s.text_frame.paragraphs:
                for r in p.runs:
                    if r.text.strip() and _font_pt(s, r, p) < 12:
                        out["avisos"].append(f"W2 slide {i}: '{s.name}' com {_font_pt(s, r, p):.0f} pt")
                        break
    out["valido"] = not out["bloqueios"]
    out["valido_estrito"] = out["valido"] and not out["estouros"]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--slides", type=int, default=6)
    args = ap.parse_args(argv)
    print(json.dumps(check_pptx(Path(args.pptx), args.slides), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
