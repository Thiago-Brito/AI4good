"""Teste 1 do TCC: custo de representação do mesmo deck em cada formato (a IA não roda).

Para cada deck do corpus de paridade (`outputs/parity/<id>/`, gerado por scripts/export_parity.py)
que chega à IR, conta os tokens (tokenizador do Qwen3, sem tokens especiais) de:
  - alto:    SlideDSL Alto normalizada pelo printer (`print_alto`);
  - sld11:   SlideDSL 1.1 gerada pelo layout (`build_alto(...).dsl`);
  - json:    conteúdo do AltoDeck em JSON compacto, sem campos vazios/padrão;
  - pptx:    programa python-pptx gerado da IR, reproduzindo posição, tamanho, fonte, cor,
             negrito, alinhamento, fundo e notas — conferido executando o programa e comparando
             o PPTX resultante com a IR (formas, textos e posições); decks que não batem são
             excluídos e listados;
  - texto:   só as strings visíveis (régua).
Também conta os tokens das instruções de formato (gramática Alto, gramática 1.1, JSON Schema).

Saídas: outputs/teste1/format_cost.csv, outputs/teste1/resumo.json e outputs/teste1/tabela.md.
Uso: .venv\\Scripts\\python scripts\\format_cost.py [--tokenizer caminho/tokenizer.json]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
FORMATS = ["texto", "alto", "json", "sld11", "pptx"]
EMU_PX = 9525  # 1 px a 96 dpi


def compact(value):
    """Remove None, listas vazias e False para o JSON não pagar por campos ausentes."""
    if isinstance(value, dict):
        out = {k: compact(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v not in (None, [], {}, False, "")}
    if isinstance(value, list):
        return [compact(v) for v in value]
    return value


def visible_text(ir):
    return "\n".join(e["text"] for s in ir["slides"] for e in s["elements"]
                     if e["type"] == "text" and e.get("text"))


def pptx_program(ir, out_name="saida.pptx"):
    bg = "F6F8FC" if ir["theme"] == "claro" else "14233D"
    lines = [
        "from pptx import Presentation",
        "from pptx.util import Emu, Pt",
        "from pptx.dml.color import RGBColor",
        "from pptx.enum.shapes import MSO_SHAPE",
        "from pptx.enum.text import PP_ALIGN, MSO_ANCHOR",
        "prs = Presentation()",
        f"prs.slide_width = Emu({1280 * EMU_PX}); prs.slide_height = Emu({720 * EMU_PX})",
    ]
    shapes = {"rectangle": "RECTANGLE", "ellipse": "OVAL", "arrow": "DOWN_ARROW"}
    for scene in ir["slides"]:
        lines += ["s = prs.slides.add_slide(prs.slide_layouts[6])",
                  "s.background.fill.solid()",
                  f"s.background.fill.fore_color.rgb = RGBColor.from_string('{bg}')"]
        for e in sorted(scene["elements"], key=lambda e: e["z"]):
            box = ", ".join(f"Emu({round(e[k] * EMU_PX)})" for k in ("x", "y", "width", "height"))
            color = e["color"].lstrip("#") if e.get("color") else "000000"
            if e["type"] == "text":
                align = {"center": "CENTER", "right": "RIGHT"}.get(e.get("align"), "LEFT")
                lines += [
                    f"t = s.shapes.add_textbox({box}).text_frame",
                    "t.word_wrap = True",
                    f"t.vertical_anchor = MSO_ANCHOR.{'MIDDLE' if e.get('align') == 'center' else 'TOP'}",
                    f"p = t.paragraphs[0]; p.alignment = PP_ALIGN.{align}",
                    f"r = p.add_run(); r.text = {e['text']!r}",
                    f"r.font.size = Pt({e['font_size'] * 0.75:g}); r.font.name = {e['font_face']!r}",
                    f"r.font.color.rgb = RGBColor.from_string('{color}')",
                ]
                if e.get("bold"):
                    lines.append("r.font.bold = True")
            elif e["type"] == "image":
                lines.append(f"s.shapes.add_picture({e['file']!r}, {box})")
            else:
                kind = "ROUNDED_RECTANGLE" if e.get("rounded") else shapes[e["type"]]
                lines += [f"f = s.shapes.add_shape(MSO_SHAPE.{kind}, {box})",
                          f"f.fill.solid(); f.fill.fore_color.rgb = RGBColor.from_string('{color}')",
                          "f.line.fill.background()"]
        if scene.get("notes"):
            lines.append(f"s.notes_slide.notes_text_frame.text = {scene['notes']!r}")
    lines.append(f"prs.save({out_name!r})")
    return "\n".join(lines) + "\n"


def check_program(program, ir):
    """Executa o programa num diretório temporário e compara o PPTX com a IR."""
    from pptx import Presentation

    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "gera.py"
        script.write_text(program, "utf-8")
        run = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp, capture_output=True,
                             text=True, timeout=60)
        if run.returncode:
            return f"execução falhou: {run.stderr.strip().splitlines()[-1][:120]}"
        prs = Presentation(str(Path(tmp) / "saida.pptx"))
        if len(prs.slides) != len(ir["slides"]):
            return "número de slides difere"
        for slide, scene in zip(prs.slides, ir["slides"]):
            elems = sorted(scene["elements"], key=lambda e: e["z"])
            if len(slide.shapes) != len(elems):
                return f"slide {scene['number']}: {len(slide.shapes)} formas, IR {len(elems)}"
            for shape, e in zip(slide.shapes, elems):
                for attr, key in (("left", "x"), ("top", "y"), ("width", "width"),
                                  ("height", "height")):
                    if abs(getattr(shape, attr) - round(e[key] * EMU_PX)) > 1:
                        return f"slide {scene['number']}: posição de {e['id']} difere"
                if e["type"] == "text" and shape.text_frame.text != e["text"]:
                    return f"slide {scene['number']}: texto de {e['id']} difere"
    return ""


def bootstrap_ci(values, reps=5000, seed=20261123):
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def wilcoxon(a, b):
    """Wilcoxon pareado (bicaudal), aproximação normal com correção de empates."""
    diffs = [x - y for x, y in zip(a, b) if x != y]
    n = len(diffs)
    if n == 0:
        return {"n": 0, "W": 0.0, "z": 0.0, "p": 1.0}
    order = sorted(range(n), key=lambda i: abs(diffs[i]))
    ranks = [0.0] * n
    i, tie_term = 0, 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(diffs[order[j + 1]]) == abs(diffs[order[i]]):
            j += 1
        rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = rank
        t = j - i + 1
        tie_term += t ** 3 - t
        i = j + 1
    w_plus = sum(r for r, d in zip(ranks, diffs) if d > 0)
    mean = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - tie_term / 48
    z = (w_plus - mean) / math.sqrt(var)
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"n": n, "W": w_plus, "z": round(z, 3), "p": p}


def main(argv=None):
    from tokenizers import Tokenizer

    from slidedsl.alto import AltoDeck, print_alto
    from slidedsl.alto_compile import build_alto

    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default=r"D:\android\models\qwen3-tokenizer\tokenizer.json")
    ap.add_argument("--corpus", default=str(ROOT / "outputs" / "parity"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste1"))
    args = ap.parse_args(argv)
    tok = Tokenizer.from_file(args.tokenizer)
    tok_hash = hashlib.sha256(Path(args.tokenizer).read_bytes()).hexdigest()

    def count(text):
        return len(tok.encode(text, add_special_tokens=False).ids)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    instructions = {
        "alto": count((ROOT / "src/slidedsl/grammar/slidedsl_alto.lark").read_text("utf-8")),
        "sld11": count((ROOT / "src/slidedsl/grammar/slidedsl.lark").read_text("utf-8")),
        "json": count(json.dumps(AltoDeck.model_json_schema(), ensure_ascii=False)),
        "pptx": 0, "texto": 0,
    }
    rows, excluded, seen = [], [], set()
    for folder in sorted(Path(args.corpus).iterdir()):
        ir_path, deck_path = folder / "ir.json", folder / "deck.json"
        if not (ir_path.exists() and deck_path.exists()):
            continue
        ir = json.loads(ir_path.read_text("utf-8"))
        if not ir:
            continue
        deck = AltoDeck.model_validate(json.loads(deck_path.read_text("utf-8")))
        facts_path = folder / "facts.json"
        facts = json.loads(facts_path.read_text("utf-8")) if facts_path.exists() else {}
        alto = print_alto(deck)
        key = hashlib.sha256(alto.encode("utf-8")).hexdigest()
        if key in seen:  # o mesmo deck aparece em mais de uma pasta de teste
            excluded.append({"deck": folder.name, "motivo": "duplicado"})
            continue
        seen.add(key)
        built = build_alto(deck, facts or None)
        if not built.dsl:
            excluded.append({"deck": folder.name, "motivo": "sem SlideDSL 1.1"})
            continue
        if any(e["type"] == "image" for s in ir["slides"] for e in s["elements"]):
            excluded.append({"deck": folder.name, "motivo": "tem imagem (arquivo fora do corpus)"})
            continue
        program = pptx_program(ir)
        problem = check_program(program, ir)
        if problem:
            excluded.append({"deck": folder.name, "motivo": "exportador python-pptx: " + problem})
            continue
        texts = {
            "texto": visible_text(ir), "alto": alto,
            "json": json.dumps(compact(deck.model_dump(mode="json")), ensure_ascii=False,
                               separators=(",", ":")),
            "sld11": built.dsl, "pptx": program,
        }
        n = len(ir["slides"])
        row = {"deck": folder.name, "slides": n}
        for fmt in FORMATS:
            row[f"{fmt}_tokens"] = count(texts[fmt])
            row[f"{fmt}_por_slide"] = round(row[f"{fmt}_tokens"] / n, 2)
        rows.append(row)
    with (out / "format_cost.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = {"decks": len(rows), "slides": sum(r["slides"] for r in rows),
               "excluidos": excluded, "tokenizer_sha256": tok_hash,
               "instrucoes_tokens": instructions, "formatos": {}}
    base = [r["texto_por_slide"] for r in rows]
    for fmt in FORMATS:
        per = [r[f"{fmt}_por_slide"] for r in rows]
        ratio = [r[f"{fmt}_tokens"] / r["texto_tokens"] for r in rows]
        lo, hi = bootstrap_ci(per)
        rlo, rhi = bootstrap_ci(ratio)
        summary["formatos"][fmt] = {
            "media_por_slide": round(sum(per) / len(per), 1), "ic95": [round(lo, 1), round(hi, 1)],
            "multiplicador_medio": round(sum(ratio) / len(ratio), 2),
            "multiplicador_ic95": [round(rlo, 2), round(rhi, 2)],
            "wilcoxon_vs_alto": None if fmt == "alto" else wilcoxon(
                [r[f"{fmt}_por_slide"] for r in rows], [r["alto_por_slide"] for r in rows]),
        }
    (out / "resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
    lines = ["| Formato | Tokens/slide (média) | IC95% | Multiplicador vs texto | Instruções (tokens) |",
             "|---|---:|---:|---:|---:|"]
    for fmt in FORMATS:
        s = summary["formatos"][fmt]
        lines.append(f"| {fmt} | {s['media_por_slide']} | {s['ic95'][0]}–{s['ic95'][1]} | "
                     f"{s['multiplicador_medio']} ({s['multiplicador_ic95'][0]}–"
                     f"{s['multiplicador_ic95'][1]}) | {instructions[fmt]} |")
    (out / "tabela.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))
    print(f"decks={len(rows)} slides={summary['slides']} excluídos={len(excluded)}")
    _ = base


if __name__ == "__main__":
    main()
