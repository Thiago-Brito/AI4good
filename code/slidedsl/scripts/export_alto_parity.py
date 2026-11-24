"""Exporta slides do corpus para a paridade do leitor Alto do app (mobile/app/src/pipeline/altoText.ts).

Para cada slide de um tipo que o app gera (imagem só com `buscar`, como o app escreve), grava o bloco impresso pelo printer Python e o
resultado do parser Python (`_parse_slide_text`) sobre esse mesmo texto. O teste do app lê o texto com
`altoToJson` + `jsonToSlide` e compara campo a campo. Python continua sendo a referência.

Uso: .venv\\Scripts\\python scripts\\export_alto_parity.py [--por-tipo 60]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
APP_KINDS = {"capa", "secao", "topicos", "etapas", "conclusao", "numeros", "comparacao",
             "linha_do_tempo", "citacao", "grafico", "imagem"}
OUT = ROOT / "mobile/app/test/fixtures/alto_slides.json"


def slide_fields(s) -> dict:
    return {
        "kind": s.kind, "title": s.title, "subtitle": s.subtitle, "author": s.author, "text": s.text,
        "unit": s.unit, "notes": s.notes, "caption": s.caption, "image_query": s.image_query,
        "items": [{"label": i.label, "detail": i.detail} for i in s.items],
        "values": [{"value": v.value, "label": v.label} for v in s.values],
        "sides": [{"name": d.name, "items": [{"label": i.label, "detail": i.detail} for i in d.items]}
                  for d in s.sides],
        "milestones": [{"date": m.date, "label": m.label, "detail": m.detail} for m in s.milestones],
        "bars": [{"label": b.label, "value": b.value} for b in s.bars],
        "sources": list(s.sources),
    }


def main(argv=None):
    from slidedsl.alto import parse_alto, print_slide
    from slidedsl.alto_generation import _parse_slide_text

    ap = argparse.ArgumentParser()
    ap.add_argument("--por-tipo", type=int, default=60)
    args = ap.parse_args(argv)
    files = sorted(ROOT.glob("examples/alto/*.slda")) + sorted(ROOT.glob("outputs/**/apresentacao.slda"))
    seen, cases, skipped = set(), [], {"tipo": 0, "imagem": 0, "erro": 0}
    for path in files:
        try:
            deck = parse_alto(path.read_text("utf-8"))
        except Exception:
            skipped["erro"] += 1
            continue
        for s in deck.slides:
            if s.kind not in APP_KINDS or s.cycle:
                skipped["tipo"] += 1
                continue
            if s.image_file or (s.image_query and s.kind != "imagem"):
                skipped["imagem"] += 1
                continue
            text = print_slide(s, indent="")
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            if sum(c["kind"] == s.kind for c in cases) >= args.por_tipo:
                continue
            cases.append({"kind": s.kind, "text": text,
                          "expected": slide_fields(_parse_slide_text(text, s.kind, "claro"))})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": "scripts/export_alto_parity.py", "cases": cases},
                              ensure_ascii=False, separators=(",", ":")), "utf-8")
    kinds = {}
    for c in cases:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print(json.dumps({"casos": len(cases), "por_tipo": kinds, "ignorados": skipped}, ensure_ascii=False))


if __name__ == "__main__":
    main()
