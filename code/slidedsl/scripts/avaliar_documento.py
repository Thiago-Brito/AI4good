"""Avalia uma apresentação gerada a partir de um documento contra um gabarito (noite de 26/11).

Mede, no texto visível do .slda (títulos, subtítulos, itens, valores, lados; não as notas):
- válida: o .slda compila sem erro;
- seções cobertas: cada seção do gabarito tem ao menos um termo presente;
- números presentes: quantos números-chave aparecem;
- invertidas: frases que contradizem o documento (lista do gabarito), contando só fora de pergunta.

Uso: .venv/Scripts/python scripts/avaliar_documento.py <pasta ou .slda> [...] [--gabarito benchmark/documento_diferencial.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def visible_text(deck) -> str:
    parts = []
    for s in deck.slides:
        parts += [s.title or "", getattr(s, "subtitle", "") or "", getattr(s, "text", "") or ""]
        for i in getattr(s, "items", []) or []:
            parts += [i.label or "", i.detail or ""]
        for v in getattr(s, "values", []) or []:
            parts += [v.value or "", v.label or ""]
        for side in getattr(s, "sides", []) or []:
            parts.append(side.name if hasattr(side, "name") else "")
            for i in getattr(side, "items", []) or []:
                parts += [i.label or "", i.detail or ""]
    return plain("\n".join(p for p in parts if p))


def evaluate(path: Path, gabarito: dict) -> dict:
    from slidedsl.alto import parse_alto
    from slidedsl.alto_compile import build_alto

    slda = path if path.suffix == ".slda" else path / "apresentacao.slda"
    deck = parse_alto(slda.read_text("utf-8"))
    fact_map = {}
    dossie = slda.parent / "dossie.json"
    if dossie.is_file():
        from slidedsl.research import Dossier
        fact_map = Dossier.load(dossie).fact_map()
    built = build_alto(deck, fact_map, ROOT)
    text = visible_text(deck)
    lines = text.splitlines()
    secoes = {nome: any(plain(t) in text for t in termos) for nome, termos in gabarito["secoes"].items()}
    numeros = [n for n in gabarito["numeros"] if plain(n) in text]
    invertidas = [frase for frase in gabarito["invertidas"]
                  if any(plain(frase) in ln and "?" not in ln and "pergunta" not in ln for ln in lines)]
    return {"execucao": str(slda.parent.name), "valida": not [d for d in built.errors if d.code not in ("A007", "A012")],
            "slides": len(deck.slides), "secoes": f"{sum(secoes.values())}/{len(secoes)}",
            "secoes_faltando": [k for k, v in secoes.items() if not v],
            "numeros": f"{len(numeros)}/{len(gabarito['numeros'])}",
            "numeros_faltando": [n for n in gabarito["numeros"] if n not in numeros], "invertidas": invertidas}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("caminhos", nargs="+")
    ap.add_argument("--gabarito", default=str(ROOT / "benchmark/documento_diferencial.json"))
    args = ap.parse_args(argv)
    gabarito = json.loads(Path(args.gabarito).read_text("utf-8"))
    for c in args.caminhos:
        print(json.dumps(evaluate(Path(c), gabarito), ensure_ascii=False))


if __name__ == "__main__":
    main()
