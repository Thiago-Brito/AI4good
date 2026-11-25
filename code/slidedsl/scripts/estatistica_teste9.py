"""Testes pareados da bancada T9 (versão congelada): McNemar exato nas apresentações completas e Wilcoxon
(aproximação normal) no tempo projetado.

Uso: .venv/Scripts/python scripts/estatistica_teste9.py [--versao v077]
Saída: outputs/teste9_<versao>_estatistica.json e um resumo no terminal.
"""

from __future__ import annotations

import argparse
import csv
import json
from math import comb, erf, sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELOS = {"lora06": "0.6B + LoRA", "q06": "0.6B", "q17": "1.7B"}


def carregar(versao: str, modelo: str) -> dict[str, dict]:
    with open(ROOT / f"outputs/teste9_{versao}_{modelo}/results.csv", encoding="utf-8") as f:
        return {r["run_id"]: r for r in csv.DictReader(f)}


def wilcoxon_p(a: list[float], b: list[float]) -> float:
    """Wilcoxon pareado bicaudal, aproximação normal com correção de empates (sem SciPy; n = 24)."""
    d = [x - y for x, y in zip(a, b) if x != y]
    n = len(d)
    if n == 0:
        return 1.0
    ordem = sorted(range(n), key=lambda i: abs(d[i]))
    postos, i = [0.0] * n, 0
    empates = 0.0
    while i < n:
        j = i
        while j + 1 < n and abs(d[ordem[j + 1]]) == abs(d[ordem[i]]):
            j += 1
        for k in range(i, j + 1):
            postos[ordem[k]] = (i + j) / 2 + 1
        t = j - i + 1
        empates += t ** 3 - t
        i = j + 1
    w = sum(r for r, x in zip(postos, d) if x > 0)
    media = n * (n + 1) / 4
    dp = sqrt(n * (n + 1) * (2 * n + 1) / 24 - empates / 48)
    z = (abs(w - media) - 0.5) / dp
    return 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))


def mcnemar_exato(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def comparar(a: dict, b: dict) -> dict:
    ids = sorted(set(a) & set(b))
    ca = [a[i]["slides_compilador"] == "0" for i in ids]
    cb = [b[i]["slides_compilador"] == "0" for i in ids]
    so_a = sum(x and not y for x, y in zip(ca, cb))
    so_b = sum(y and not x for x, y in zip(ca, cb))
    ta = [float(a[i]["celular_min"]) for i in ids]
    tb = [float(b[i]["celular_min"]) for i in ids]
    return {"pares": len(ids), "completas": [sum(ca), sum(cb)], "discordantes": [so_a, so_b],
            "mcnemar_p": mcnemar_exato(so_a, so_b), "tempo_medio": [sum(ta) / len(ta), sum(tb) / len(tb)],
            "wilcoxon_tempo_p": wilcoxon_p(ta, tb)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default="v077")
    args = ap.parse_args(argv)
    dados = {m: carregar(args.versao, m) for m in MODELOS}
    saida = {f"{x}_x_{y}": comparar(dados[x], dados[y]) for x, y in [("lora06", "q06"), ("lora06", "q17"), ("q06", "q17")]}
    (ROOT / f"outputs/teste9_{args.versao}_estatistica.json").write_text(json.dumps(saida, indent=1), "utf-8")
    for nome, r in saida.items():
        print(nome, json.dumps(r))


if __name__ == "__main__":
    main()
