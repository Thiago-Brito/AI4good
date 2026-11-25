"""Figura do artigo: os slides de uma apresentação da bancada do app, renderizados pelo compilador, em grade.

Uso: .venv/Scripts/python scripts/figura_deck.py <pasta da bancada> <run_id> <saida.png> [--colunas 3]
Ex.: scripts/figura_deck.py outputs/teste9_v077_lora06 sono_detalhado__gramatica_limites+frases__s11 fig.png
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image

from slidedsl.alto import AltoDeck
from slidedsl.alto_compile import build_alto
from slidedsl.ir_preview import render_deck
from slidedsl.motor_celular import _dossie

ROOT = Path(__file__).resolve().parents[1]
TEMAS = {"agua": "Ciclo da água", "sono": "Sono e estudos", "git": "Git", "solar": "Energia solar em casa"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("run")
    ap.add_argument("saida")
    ap.add_argument("--colunas", type=int, default=3)
    ap.add_argument("--escala", type=float, default=0.75)
    args = ap.parse_args(argv)
    base = Path(args.pasta) / args.run
    deck = AltoDeck.model_validate(json.loads(Path(f"{base}.deck.json").read_text("utf-8")))
    facts = json.loads(Path(f"{base}.facts.json").read_text("utf-8")).get("facts", {})
    tema = TEMAS[args.run.split("_")[0]]
    built = build_alto(deck, _dossie(tema, facts).fact_map() if facts else {}, ROOT)
    if not built.success():
        raise SystemExit(f"não compila: {[d.code for d in built.errors]}")
    with tempfile.TemporaryDirectory() as tmp:
        imgs = [Image.open(p).convert("RGB") for p in render_deck(built.validation.ir, Path(tmp), args.escala, ROOT)]
    w, h = imgs[0].size
    gap, cols = 16, args.colunas
    rows = -(-len(imgs) // cols)
    sheet = Image.new("RGB", (cols * w + (cols - 1) * gap, rows * h + (rows - 1) * gap), "white")
    for i, im in enumerate(imgs):
        r, c = divmod(i, cols)
        if r == rows - 1 and len(imgs) % cols:  # última linha incompleta fica centralizada
            c += (cols - len(imgs) % cols) / 2
        sheet.paste(im, (int(c * (w + gap)), r * (h + gap)))
    sheet.save(args.saida)
    print(args.saida, sheet.size, len(imgs), "slides")


if __name__ == "__main__":
    main()
