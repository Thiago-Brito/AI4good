"""Análise do Teste 3 (outputs/teste3/results.csv): validade e custo por modo de restrição.

Validade: proporção por modo e McNemar exato (binomial) par a par, pareado por pedido e semente.
Custo: média e IC95% bootstrap de tokens de saída, tempo de geração (decode) e tempo total; Friedman
(aproximação qui-quadrado) entre os 3 modos e Wilcoxon pareado de dois em dois, só nos pares em que
ambos os modos geraram o deck (válido ou não), sem inventar valores.
Uso: .venv\\Scripts\\python scripts\\analise_teste3.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from format_cost import bootstrap_ci, wilcoxon  # noqa: E402

MODES = ["json", "gramatica", "direto"]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def friedman(blocks):
    """blocks: lista de [v_modo1, v_modo2, v_modo3]; devolve (Q, p) com gl = k-1."""
    k, n = len(blocks[0]), len(blocks)
    rank_sums = [0.0] * k
    for row in blocks:
        order = sorted(range(k), key=lambda i: row[i])
        ranks = [0.0] * k
        i = 0
        while i < k:
            j = i
            while j + 1 < k and row[order[j + 1]] == row[order[i]]:
                j += 1
            for t in range(i, j + 1):
                ranks[order[t]] = (i + j) / 2 + 1
            i = j + 1
        for m in range(k):
            rank_sums[m] += ranks[m]
    q = 12 / (n * k * (k + 1)) * sum(r * r for r in rank_sums) - 3 * n * (k + 1)
    p = math.exp(-q / 2) if k == 3 else None  # qui-quadrado com 2 gl: P(X>q) = e^{-q/2}
    return round(q, 3), p


def main():
    rows = list(csv.DictReader((ROOT / "outputs/teste3/results.csv").open(encoding="utf-8")))
    last = {}
    for r in rows:  # última linha por execução
        last[r["run_id"]] = r
    data = {}
    for r in last.values():
        key = (r["request_id"], r["seed"])
        data.setdefault(key, {})[r["condition"]] = r
    out = {"execucoes": len(last), "por_modo": {}, "mcnemar": {}, "friedman": {}, "wilcoxon": {}}
    for m in MODES:
        rs = [d[m] for d in data.values() if m in d]
        ok = [r for r in rs if r["status"] == "ok"]
        valid = [r for r in ok if r["valido"] == "True"]

        def nums(key, sel=ok):
            return [float(r[key]) for r in sel if r.get(key) not in ("", None, "None")]

        entry = {"execucoes": len(rs), "concluidas": len(ok), "validas": len(valid),
                 "taxa_validade": round(len(valid) / len(rs), 3) if rs else None,
                 "slides_1a_tentativa_media": round(sum(nums("slides_1a_tentativa")) / len(ok), 2) if ok else None,
                 "reparos_media": round(sum(nums("reparos")) / len(ok), 2) if ok else None}
        for key in ("tokens_saida", "tokens_entrada", "decode_ms", "wall_ms"):
            v = nums(key)
            if v:
                lo, hi = bootstrap_ci(v)
                entry[key] = {"media": round(sum(v) / len(v), 1), "ic95": [round(lo, 1), round(hi, 1)]}
        out["por_modo"][m] = entry
    for a, b in combinations(MODES, 2):
        pairs = [(d[a], d[b]) for d in data.values() if a in d and b in d]
        va = [x["valido"] == "True" for x, _ in pairs]
        vb = [y["valido"] == "True" for _, y in pairs]
        only_a = sum(x and not y for x, y in zip(va, vb))
        only_b = sum(y and not x for x, y in zip(va, vb))
        out["mcnemar"][f"{a}_vs_{b}"] = {"n": len(pairs), "so_" + a: only_a, "so_" + b: only_b,
                                        "p_exato": round(mcnemar_exact(only_a, only_b), 4)}
        for key in ("tokens_saida", "decode_ms", "wall_ms"):
            both = [(float(x[key]), float(y[key])) for x, y in pairs
                    if x["status"] == y["status"] == "ok" and x.get(key) not in ("", "None")
                    and y.get(key) not in ("", "None")]
            if both:
                out["wilcoxon"][f"{key}:{a}_vs_{b}"] = wilcoxon([p[0] for p in both], [p[1] for p in both])
    for key in ("tokens_saida", "decode_ms", "wall_ms"):
        blocks = [[float(d[m][key]) for m in MODES] for d in data.values()
                  if all(m in d and d[m]["status"] == "ok" and d[m].get(key) not in ("", "None")
                         for m in MODES)]
        if len(blocks) >= 2:
            q, p = friedman(blocks)
            out["friedman"][key] = {"n": len(blocks), "Q": q, "p": p}
    target = ROOT / "outputs/teste3/analise.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
