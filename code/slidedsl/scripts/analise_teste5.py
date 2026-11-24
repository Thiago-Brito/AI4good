"""Análise da bancada do app (mobile/app/bench/app_bench.mjs): JSON Schema × SlideDSL Alto sob gramática.

Pareado por pedido e semente. Tempo no celular projetado pelas velocidades medidas no moto g(8) power lite
(docs/RESULTADOS_T4.md). Todo PPTX passa pelo verificador único (scripts/pptx_checks.py).

Uso: .venv\\Scripts\\python scripts\\analise_teste5.py [--dir outputs/teste5_app]
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analise_teste3 import mcnemar_exact  # noqa: E402
from format_cost import bootstrap_ci, wilcoxon  # noqa: E402
from pptx_checks import check_pptx  # noqa: E402

NUM = ["chamadas", "reparos", "falhas_chamada", "tokens_entrada", "tokens_saida", "prompt_processado",
       "slide_tokens_entrada", "slide_tokens_saida", "slide_prompt_processado", "pc_ms", "celular_min",
       "celular_slides_min", "slides_compilador"]


LIMITS = {"title": 80, "subtitle": 140, "author": 80, "text": 260, "unit": 40, "notes": 1500}
# (lista, campo, limite) — limites A005 do compilador (src/slidedsl/alto.py).
RECORD_LIMITS = [("items", "label", 48), ("items", "detail", 170), ("values", "value", 14),
                 ("values", "label", 170), ("milestones", "date", 16), ("milestones", "label", 36),
                 ("milestones", "detail", 90), ("bars", "label", 24)]


def truncated_fields(deck: dict) -> tuple[int, int]:
    """(campos no limite exato do compilador, campos de texto). Proxy de texto cortado pela gramática."""
    hit = total = 0

    def check(value, limit):
        nonlocal hit, total
        if value:
            total += 1
            hit += len(value) >= limit
    for s in deck.get("slides", []):
        for k, lim in LIMITS.items():
            check(s.get(k), lim)
        for key, field, limit in RECORD_LIMITS:
            for rec in s.get(key, []):
                check(rec.get(field), limit)
        for d in s.get("sides", []):
            check(d.get("name"), 40)
            for i in d.get("items", []):
                check(i.get("label"), 48)
                check(i.get("detail"), 80)
    return hit, total


def load(d: Path) -> dict:
    rows = {}
    with (d / "results.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            for k in NUM:
                r[k] = float(r[k]) if r.get(k) not in ("", None) else None
            r["ok"] = r["status"] == "success" and r["valido"] == "true"
            r["completo"] = r["ok"] and (r["slides_compilador"] or 0) == 0
            pptx = d / f"{r['run_id']}.pptx"
            chk = check_pptx(pptx, 5) if r["ok"] and pptx.exists() else None
            r["verificador"] = bool(chk and chk["valido_estrito"])
            deck = d / f"{r['run_id']}.deck.json"
            r["cortados"], r["campos"] = truncated_fields(json.loads(deck.read_text("utf-8"))) if deck.exists() else (0, 0)
            rows[r["run_id"]] = r
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "outputs" / "teste5_app"))
    args = ap.parse_args(argv)
    d = Path(args.dir)
    rows = load(d)
    modes = [m for m in ["json", "gramatica", "gramatica_limites"] if any(r["mode"] == m for r in rows.values())]
    by = {m: {(r["request_id"], r["seed"]): r for r in rows.values() if r["mode"] == m} for m in modes}
    keys = sorted(set.intersection(*(set(by[m]) for m in modes)))
    out = {"pares": len(keys), "modos": {}, "pareado": {}}
    for m in modes:
        rs = [by[m][k] for k in keys]
        mean = lambda f: round(st.mean(r[f] for r in rs if r[f] is not None), 2)  # noqa: E731
        out["modos"][m] = {
            "execucoes": len(rs), "validos": sum(r["ok"] for r in rs),
            "completos_sem_slide_do_compilador": sum(r["completo"] for r in rs),
            "verificador_estrito": sum(r["verificador"] for r in rs),
            "slides_do_compilador": int(sum(r["slides_compilador"] or 0 for r in rs)),
            **{f: mean(f) for f in NUM if f != "slides_compilador"},
            "celular_min_ic95": bootstrap_ci([r["celular_min"] for r in rs]),
            "celular_slides_min_ic95": bootstrap_ci([r["celular_slides_min"] for r in rs]),
            "campos_no_limite": f"{sum(r['cortados'] for r in rs)}/{sum(r['campos'] for r in rs)}",
            "falhas": [f"{r['run_id']}: {r['erro']}" for r in rs if not r["completo"]],
        }
    pairs = [(a, b) for i, a in enumerate(modes) for b in modes[i + 1:]]
    for ma, mb in pairs:
        res = out["pareado"].setdefault(f"{ma}_x_{mb}", {})
        res["slides_do_compilador_por_par"] = {
            "menos_em_" + mb: sum(1 for k in keys if (by[mb][k]["slides_compilador"] or 0) < (by[ma][k]["slides_compilador"] or 0)),
            "menos_em_" + ma: sum(1 for k in keys if (by[ma][k]["slides_compilador"] or 0) < (by[mb][k]["slides_compilador"] or 0))}
        for f in ["completo", "ok"]:
            b = sum(1 for k in keys if by[ma][k][f] and not by[mb][k][f])
            c = sum(1 for k in keys if by[mb][k][f] and not by[ma][k][f])
            res[f"mcnemar_{f}"] = {"so_" + ma: b, "so_" + mb: c, "p": mcnemar_exact(b, c)}
        for f in ["slides_compilador", "slide_tokens_saida", "slide_prompt_processado", "tokens_saida",
                  "celular_slides_min", "celular_min", "reparos"]:
            a = [by[ma][k][f] or 0 for k in keys]
            g = [by[mb][k][f] or 0 for k in keys]
            mean_a = st.mean(a)
            res[f"wilcoxon_{f}"] = {**wilcoxon(a, g), "media_" + ma: round(mean_a, 2), "media_" + mb: round(st.mean(g), 2),
                                    "variacao_%": round((st.mean(g) - mean_a) / mean_a * 100, 1) if mean_a else None}
    (d / "analise.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
