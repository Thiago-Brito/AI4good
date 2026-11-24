"""Análise do Teste 2: modelo escrevendo python-pptx (A) × pipeline SlideDSL (C, do Teste 3).

Pareamento por pedido e semente. Todo PPTX, de qualquer grupo, passa pelo mesmo verificador
(pptx_checks.py). Em C, um deck só conta se o compilador o aceitou E o verificador também.

Uso: .venv\\Scripts\\python scripts\\analise_teste2.py [--a outputs/teste2] [--c outputs/teste3]
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


def last_rows(path: Path) -> dict:
    rows = {}
    with path.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows[r["run_id"]] = r
    return rows


def num(v):
    return None if v in ("", None) else float(v)


def group_c(c_dir: Path, mode: str, n_slides: int, recompiled: Path | None = None) -> dict:
    out = {}
    for r in last_rows(c_dir / "results.csv").values():
        if r["condition"] != mode:
            continue
        pptx = (recompiled / r["run_id"] / "apresentacao.pptx" if recompiled
                else c_dir / "runs" / r["run_id"] / "deck" / "apresentacao.pptx")
        compiler_ok = r["valido"] == "True"
        check = check_pptx(pptx, n_slides) if compiler_ok and pptx.exists() else None
        out[(r["request_id"], r["seed"])] = {
            "gerou": check is not None,
            "valido": bool(check and check["valido"]),
            "estrito": bool(check and check["valido_estrito"]),
            "primeira": None,
            "tin": num(r["tokens_entrada"]), "tout": num(r["tokens_saida"]),
            "wall": num(r["wall_ms"]), "chamadas": num(r["chamadas"]),
            "chars": check["chars_visiveis"] if check else None,
            "estouros": len(check["estouros"]) if check else None,
            "bloqueios": check["bloqueios"] if check else [r["erros_bloqueio"] or "compilador recusou"],
        }
    return out


def group_a(a_dir: Path, n_slides: int) -> dict:
    out = {}
    for r in last_rows(a_dir / "results.csv").values():
        if r["status"] != "ok":
            continue
        pptx = a_dir / "runs" / r["run_id"] / "apresentacao.pptx"
        check = check_pptx(pptx, n_slides) if pptx.exists() else None
        out[(r["request_id"], r["seed"])] = {
            "gerou": check is not None,
            "valido": r["valido"] == "True",
            "estrito": bool(r["valido"] == "True" and check and check["valido_estrito"]),
            "primeira": r["valido_1a"] == "True",
            "tin": num(r["tokens_entrada"]), "tout": num(r["tokens_saida"]),
            "wall": num(r["wall_ms"]), "chamadas": num(r["chamadas"]),
            "chars": check["chars_visiveis"] if check else None,
            "estouros": len(check["estouros"]) if check else None,
            "bloqueios": (check["bloqueios"] if check else []) + ([r["falha"]] if r["falha"] else []),
        }
    return out


def summary(g: dict) -> dict:
    vals = list(g.values())
    n = len(vals)
    tin = [v["tin"] for v in vals]
    tout = [v["tout"] for v in vals]
    wall = [v["wall"] / 1000 for v in vals]
    n_valid = sum(v["valido"] for v in vals)
    n_strict = sum(v["estrito"] for v in vals)
    total_tokens = sum(a + b for a, b in zip(tin, tout))
    made = [v for v in vals if v["gerou"]]
    return {
        "execucoes": n, "gerou_pptx": len(made), "validos": n_valid, "validos_estritos": n_strict,
        "validos_1a": sum(bool(v["primeira"]) for v in vals) if vals and vals[0]["primeira"] is not None else None,
        "tokens_entrada": round(st.mean(tin)), "tokens_saida": round(st.mean(tout)),
        "tokens_saida_ic95": bootstrap_ci(tout), "tempo_s": round(st.mean(wall), 1),
        "tempo_ic95": bootstrap_ci(wall), "chamadas": round(st.mean(v["chamadas"] for v in vals), 1),
        "tokens_por_valido": round(total_tokens / n_valid) if n_valid else None,
        "tokens_por_valido_estrito": round(total_tokens / n_strict) if n_strict else None,
        "segundos_por_valido_estrito": round(sum(wall) / n_strict, 1) if n_strict else None,
        "chars_visiveis": round(st.mean(v["chars"] for v in made)) if made else None,
        "decks_com_estouro": sum(1 for v in made if v["estouros"]),
        "estouros_por_deck": round(st.mean(v["estouros"] for v in made), 2) if made else None,
    }


def paired(a: dict, c: dict) -> dict:
    keys = sorted(set(a) & set(c))
    res = {"pares": len(keys)}
    for field in ("valido", "estrito"):
        b = sum(1 for k in keys if a[k][field] and not c[k][field])
        cc = sum(1 for k in keys if c[k][field] and not a[k][field])
        res[f"mcnemar_{field}"] = {"so_A": b, "so_C": cc, "p": mcnemar_exact(b, cc)}
    for field in ("tout", "tin", "wall"):
        res[f"wilcoxon_{field}"] = wilcoxon([a[k][field] for k in keys], [c[k][field] for k in keys])
    res["wilcoxon_total"] = wilcoxon([a[k]["tin"] + a[k]["tout"] for k in keys],
                                     [c[k]["tin"] + c[k]["tout"] for k in keys])
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default=str(ROOT / "outputs" / "teste2"))
    ap.add_argument("--c", default=str(ROOT / "outputs" / "teste3"))
    ap.add_argument("--c-recompilado", default=str(ROOT / "outputs" / "teste3_recompilado"),
                    help="PPTX do grupo C recompilados com o código atual ('' para usar os originais)")
    ap.add_argument("--slides", type=int, default=6)
    args = ap.parse_args(argv)
    a = group_a(Path(args.a), args.slides)
    groups = {"A_codigo": a}
    recompiled = Path(args.c_recompilado) if args.c_recompilado else None
    for mode in ("gramatica", "json"):
        groups[f"C_{mode}"] = group_c(Path(args.c), mode, args.slides, recompiled)
        if recompiled:
            groups[f"C_{mode}_original"] = group_c(Path(args.c), mode, args.slides)
    out = {"grupos": {k: summary(v) for k, v in groups.items()},
           "pareado": {f"A_x_{k}": paired(a, v) for k, v in groups.items() if k != "A_codigo"},
           "falhas_A": {f"{k[0]}__s{k[1]}": v["bloqueios"] for k, v in sorted(a.items()) if not v["estrito"]},
           "c_recompilado": str(recompiled) if recompiled else None,
           "falhas_C": {f"{m}:{k[0]}__s{k[1]}": v["bloqueios"] for m in ("gramatica", "json")
                        for k, v in sorted(groups[f"C_{m}"].items()) if not v["valido"]}}
    path = Path(args.a) / "analise.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(out["grupos"], ensure_ascii=False, indent=1))
    print(json.dumps(out["pareado"], ensure_ascii=False, indent=1))
    print("salvo em", path)


if __name__ == "__main__":
    main()
