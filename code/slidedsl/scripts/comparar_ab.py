"""Compara duas pastas de results.csv do experiment_runner (A/B pareado por request_id).

Uso: .venv/Scripts/python scripts/comparar_ab.py outputs/regressao_pc_ab/antes outputs/regressao_pc_ab/depois
"""
import csv
import statistics as st
import sys
from math import comb


def load(folder):
    with open(f"{folder}/results.csv", encoding="utf-8") as f:
        return {r["request_id"]: r for r in csv.DictReader(f)}


def resumo(d):
    ok = [r for r in d.values() if r["status"] == "ok"]
    m = lambda k: st.mean(float(r[k] or 0) for r in ok)
    return {"n": len(d), "validos": sum(r["valido"] == "True" for r in d.values()), "reparos": round(m("reparos"), 2),
            "slides_1a": round(m("slides_1a_tentativa"), 2), "tokens_entrada": round(m("tokens_entrada")),
            "tokens_saida": round(m("tokens_saida")), "tempo_s": round(m("wall_ms") / 1000, 1),
            "commit": sorted({r["commit"] for r in d.values()})}


a, b = load(sys.argv[1]), load(sys.argv[2])
print("antes ", resumo(a))
print("depois", resumo(b))
ids = sorted(set(a) & set(b))
so_a = sum(a[i]["valido"] == "True" and b[i]["valido"] != "True" for i in ids)
so_b = sum(b[i]["valido"] == "True" and a[i]["valido"] != "True" for i in ids)
n = so_a + so_b
p = 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) for k in range(min(so_a, so_b) + 1)) / 2 ** n)
print(f"discordantes: só antes {so_a}, só depois {so_b}, McNemar p = {p:.3f}")
for i in ids:
    if a[i]["valido"] != b[i]["valido"]:
        print(" ", i, "antes", a[i]["valido"], a[i]["erros_bloqueio"][:80], "| depois", b[i]["valido"], b[i]["erros_bloqueio"][:80])
