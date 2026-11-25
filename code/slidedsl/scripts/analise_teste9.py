"""Teste 9: bancada do app 0.7.4 contra as linhas de base do T7/T8 (mesmos 12 pedidos × sementes 11 e 22,
`gramatica_limites+frases`, 5 slides, `mobile/app/bench/app_bench.mjs`).

O 0.7.3/0.7.4 mudou o roteiro (vê todos os fatos), a distribuição de fatos por slide, os itens já escritos no
pedido de cada slide, a gramática (só caracteres medidos), o bloqueio de número inventado em números/gráfico e
o corte de texto no limite (docs/TESTE_TCC_DOCUMENTO_LONGO.md, ROADMAP.md).

Métricas por modelo (as mesmas para o antes e o depois, calculadas por este script):
- válidas e completas (nenhum slide do compilador); slides do compilador; slides de seção (conteúdo vazio);
- reparos por apresentação; tokens de saída; tempo projetado no celular (do results.csv);
- textos repetidos no deck: textos visíveis com mais de 25 caracteres iguais a outro do mesmo deck (normalizados);
- pares de slides parecidos: Jaccard de palavras de conteúdo ≥ 0,3 entre slides de conteúdo (sem a capa);
- fatos citados no deck (distintos) e fatos aceitos na leitura; vocabulário visível (palavras distintas).

Uso: .venv/Scripts/python scripts/analise_teste9.py
"""

from __future__ import annotations

import csv
import itertools
import json
import re
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PARES = {
    "0.6B LoRA": ("teste8_lora", "teste9_v074_lora06"),
    "0.6B": ("teste7_06b_dica", "teste9_v074_q06"),
    "1.7B": ("teste6_17b_dica", "teste9_v074_q17"),
}
STOP = set("a o as os um uma de do da dos das em no na nos nas para por com sem e ou que se ao à é como mais "
           "seu sua seus suas pelo pela este esta isso".split())


def textos(slide: dict) -> list[str]:
    out = [slide.get(k) for k in ("title", "subtitle", "text", "caption", "unit")]
    for it in slide.get("items") or []:
        out += [it.get("label"), it.get("detail")]
    for side in slide.get("sides") or []:
        out.append(side.get("name"))
        for it in side.get("items") or []:
            out += [it.get("label"), it.get("detail")]
    for m in slide.get("milestones") or []:
        out += [m.get("label"), m.get("detail")]
    for v in slide.get("values") or []:
        out.append(v.get("label"))
    for b in slide.get("bars") or []:
        out.append(b.get("label"))
    return [t for t in out if t]


def norm(t: str) -> str:
    return re.sub(r"[^\w]+", " ", t.lower()).strip()


def palavras(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-zà-ú]{4,}", t.lower()) if w not in STOP}


def deck_metricas(deck: dict) -> dict:
    slides = deck["slides"]
    todos = [t for s in slides for t in textos(s)]
    longos = [norm(t) for t in todos if len(t) > 25]
    repetidos = sum(1 for t in longos if longos.count(t) > 1)
    conteudo = [palavras(" ".join(textos(s))) for s in slides[1:]]
    pares = sum(1 for a, b in itertools.combinations(conteudo, 2) if a | b and len(a & b) / len(a | b) >= 0.3)
    secoes = sum(1 for s in slides if s["kind"] == "secao")
    citados = {f for s in slides for f in s.get("sources") or []}
    return {"repetidos": repetidos, "longos": len(longos), "pares": pares, "secoes": secoes,
            "citados": len(citados), "vocab": {w for t in todos for w in re.findall(r"[a-zà-ú]+", t.lower())},
            "itens": sum(len(s.get("items") or []) for s in slides[1:]) / max(1, len(slides) - 1)}


def bancada(pasta: Path) -> dict:
    linhas = list(csv.DictReader((pasta / "results.csv").open(encoding="utf-8")))
    decks = {p.name.split(".deck.json")[0]: json.loads(p.read_text("utf-8")) for p in pasta.glob("*.deck.json")}
    ms = [deck_metricas(decks[r["run_id"]]) for r in linhas if r["run_id"] in decks]
    num = lambda k: [float(r[k]) for r in linhas if r[k] not in ("", None)]
    vocab = set().union(*(m["vocab"] for m in ms)) if ms else set()
    return {
        "apresentacoes": len(linhas),
        "validas": sum(r["valido"] == "true" for r in linhas),
        "completas": sum(r["valido"] == "true" and float(r["slides_compilador"] or 0) == 0 for r in linhas),
        "slides_compilador": int(sum(num("slides_compilador"))),
        "slides_secao": sum(m["secoes"] for m in ms),
        "reparos_por_apresentacao": round(st.mean(num("reparos")), 2),
        "textos_repetidos": f"{sum(m['repetidos'] for m in ms)}/{sum(m['longos'] for m in ms)}",
        "pares_slides_parecidos": sum(m["pares"] for m in ms),
        "fatos_citados_por_deck": round(st.mean(m["citados"] for m in ms), 2),
        "fatos_aceitos": round(st.mean(num("fatos")), 2),
        "itens_por_slide": round(st.mean(m["itens"] for m in ms), 2),
        "vocabulario": len(vocab),
        "tokens_saida": round(st.mean(num("tokens_saida"))),
        "celular_min": round(st.mean(num("celular_min")), 1),
    }


def main():
    resultado = {}
    for modelo, (antes, depois) in PARES.items():
        resultado[modelo] = {"antes": bancada(OUT / antes), "depois": bancada(OUT / depois)}
    (OUT / "teste9_resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), "utf-8")
    chaves = list(next(iter(resultado.values()))["antes"])
    print("| | " + " | ".join(f"{m} antes | {m} 0.7.4" for m in resultado) + " |")
    print("|---" * (1 + 2 * len(resultado)) + "|")
    for k in chaves:
        print(f"| {k} | " + " | ".join(f"{v['antes'][k]} | {v['depois'][k]}" for v in resultado.values()) + " |")


if __name__ == "__main__":
    main()
