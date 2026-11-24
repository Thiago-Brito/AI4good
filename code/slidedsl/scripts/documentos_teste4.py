"""Gera os documentos do Teste 4 (celular) a partir dos dossiês fixos do benchmark.

Um documento .txt por tema, com os trechos literais já conferidos nos dossiês dos três níveis
(sem repetição), agrupados por fonte com título e endereço. Assim o celular recebe o mesmo
conteúdo usado nos testes do computador, e o que aparecer nos slides pode ser conferido contra ele.

Uso: .venv\\Scripts\\python scripts\\documentos_teste4.py [--out outputs/teste4/documentos]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    "solar": "Energia solar residencial",
    "git": "Git para iniciantes",
    "agua": "Ciclo da água",
    "sono": "Sono e desempenho nos estudos",
}


def build(theme: str, title: str) -> str:
    sources: dict[str, dict] = {}
    seen = set()
    for level in ("tema", "detalhado", "obrigatorio"):
        path = ROOT / "benchmark/dossies" / f"{theme}_{level}.json"
        if not path.exists():
            continue
        for fact in json.loads(path.read_text("utf-8")).get("facts", []):
            quote = " ".join(fact["quote"].split())
            if quote in seen:
                continue
            seen.add(quote)
            key = fact.get("url") or fact.get("source_title", "")
            src = sources.setdefault(key, {"title": fact.get("source_title", ""), "url": fact.get("url", ""),
                                           "quotes": []})
            src["quotes"].append(quote)
    lines = [title, "", "Documento de referência montado com trechos literais de fontes públicas.", ""]
    for n, src in enumerate(sources.values(), 1):
        lines.append(f"Fonte {n}: {src['title']}")
        if src["url"]:
            lines.append(src["url"])
        lines += [f"- {q}" for q in src["quotes"]]
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste4" / "documentos"))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for theme, title in THEMES.items():
        text = build(theme, title)
        path = out / f"{theme}.txt"
        path.write_text(text, "utf-8")
        print(path.name, len(text), "caracteres,", text.count("\n- "), "trechos")


if __name__ == "__main__":
    main()
