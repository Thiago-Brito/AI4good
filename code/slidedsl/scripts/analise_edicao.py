"""Análise do teste de edição localizada (scripts/teste_edicao.py), a partir dos arquivos salvos.

Localidade: a IR de cada slide não editado é comparada com a do deck base, ignorando apenas
`source_line`/`source_column` (posição no texto-fonte, que muda quando o slide editado muda de
tamanho). Em "mover", ignoram-se também o prefixo `sN_` dos ids e o elemento de número de página,
que mudam por construção. Conteúdo: itens, valores, lados e fontes do slide antes/depois.

Uso: .venv\\Scripts\\python scripts\\analise_edicao.py v2 v3
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "outputs" / "teste_edicao"
SLIDE = 3


def norm_slides(source, facts, drop_numbering=False):
    from slidedsl.alto_compile import build_alto

    built = build_alto(source, facts)
    if not built.validation or not built.validation.ir:
        return None
    result = []
    for s in built.validation.ir.model_dump(mode="json")["slides"]:
        elems = []
        for e in s["elements"]:
            e = {k: v for k, v in e.items() if k not in ("source_line", "source_column")}
            if drop_numbering:
                if "_pagina_" in e["id"]:
                    continue
                e["id"] = re.sub(r"^s\d+_", "", e["id"])
            elems.append(e)
        s = {k: v for k, v in s.items() if k not in ("number", "elements")}
        s["elements"] = elems
        result.append(json.dumps(s, sort_keys=True, ensure_ascii=False))
    return result


def slide_texts(slides):
    """Textos visíveis de cada slide, sem o número de página (conteúdo, não variante visual)."""
    return [sorted(e["text"] for e in json.loads(s)["elements"]
                   if e.get("type") == "text" and e.get("text") and "_pagina_" not in e["id"])
            for s in slides]


def content_size(slide):
    return {"itens": len(slide.items), "valores": len(slide.values),
            "lados": sum(len(x.items) for x in slide.sides), "etapas": len(slide.milestones),
            "fontes": len(slide.sources)}


def main(rounds):
    from slidedsl.alto import parse_alto
    from slidedsl.research import Dossier

    report = {}
    for rnd in rounds:
        rows = list(csv.DictReader((OUT / f"edicoes_{rnd}.csv").open(encoding="utf-8")))
        edits_dir = OUT / ("edicoes" if rnd == "v2" else f"edicoes_{rnd}")
        bases = {p.name.rsplit("_s", 1)[0]: p for p in sorted((OUT / "base").glob("*_s*"))
                 if (p / "relatorio.json").exists()
                 and json.loads((p / "relatorio.json").read_text("utf-8")).get("valid")}
        per = []
        for r in rows:
            if r["tipo_edicao"] != "ia" or r["status"] != "ok":
                if r["tipo_edicao"] == "ia":
                    per.append({"deck": r["deck"], "edicao": r["edicao"], "ok": False})
                continue
            base = bases[r["deck"]]
            facts = Dossier.load(base / "dossie.json").fact_map()
            src_base = (base / "apresentacao.slda").read_text("utf-8")
            folders = sorted((edits_dir / r["deck"]).glob(r["edicao"] + "*"))
            src_new = (folders[-1] / "apresentacao.slda").read_text("utf-8")
            a, b = norm_slides(src_base, facts), norm_slides(src_new, facts)
            sa, sb = parse_alto(src_base).slides[SLIDE - 1], parse_alto(src_new).slides[SLIDE - 1]
            ca, cb = content_size(sa), content_size(sb)
            per.append({
                "deck": r["deck"], "edicao": r["edicao"], "ok": b is not None,
                "local": b is not None and all(a[i] == b[i] for i in range(len(a)) if i != SLIDE - 1),
                "local_texto": b is not None and all(
                    x == y for i, (x, y) in enumerate(zip(slide_texts(a), slide_texts(b)))
                    if i != SLIDE - 1),
                "fonte_fora_igual": r["fonte_fora_igual"] == "True",
                "tipo_antes": sa.kind, "tipo_depois": sb.kind,
                "tipo_ok": (sb.kind == "comparacao") if r["edicao"] == "virar_comparacao"
                else sb.kind == sa.kind,
                "conteudo_antes": sum(ca.values()) - ca["fontes"],
                "conteudo_depois": sum(cb.values()) - cb["fontes"],
                "fontes_antes": ca["fontes"], "fontes_depois": cb["fontes"],
                "tokens_in": int(r["tokens_entrada"]), "tokens_out": int(r["tokens_saida"]),
                "wall_ms": float(r["wall_ms"]),
                "base_tokens_in": int(r["base_tokens_entrada"]),
                "base_tokens_out": int(r["base_tokens_saida"]), "base_wall_ms": float(r["base_wall_ms"]),
            })
        # Determinísticas: mover com ids/página normalizados.
        moves = []
        for r in rows:
            if r["edicao"] != "mover_para_5" or r["status"] != "ok":
                continue
            from slidedsl.alto_edit import ajustar_alto

            base = bases[r["deck"]]
            facts = Dossier.load(base / "dossie.json").fact_map()
            src = (base / "apresentacao.slda").read_text("utf-8")
            a = norm_slides(src, facts, drop_numbering=True)
            b = norm_slides(ajustar_alto(src, numero=SLIDE, mover_para=5), facts, drop_numbering=True)
            expected = a[:SLIDE - 1] + a[SLIDE:]
            expected.insert(4, a[SLIDE - 1])
            moves.append((b == expected, slide_texts(b) == slide_texts(expected)))
        ok = [x for x in per if x["ok"]]
        n = len(per)

        def mean(key, rows=ok):
            return round(sum(x[key] for x in rows) / len(rows), 1) if rows else None

        report[rnd] = {
            "edicoes_ia": n, "validas": len(ok),
            "locais_ir": sum(x["local"] for x in ok),
            "locais_texto": sum(x["local_texto"] for x in ok),
            "fonte_fora_igual": sum(x["fonte_fora_igual"] for x in ok),
            "tipo_cumprido": sum(x["tipo_ok"] for x in ok),
            "viraram_secao": sum(x["tipo_depois"] == "secao" for x in ok),
            "conteudo_preservado": sum(x["conteudo_depois"] >= min(2, x["conteudo_antes"]) for x in ok),
            "fontes_mantidas": sum(x["fontes_depois"] >= x["fontes_antes"] for x in ok),
            "tokens_in_medio": mean("tokens_in"), "tokens_out_medio": mean("tokens_out"),
            "wall_ms_medio": mean("wall_ms"),
            "base_tokens_in_medio": mean("base_tokens_in"), "base_tokens_out_medio": mean("base_tokens_out"),
            "base_wall_ms_medio": mean("base_wall_ms"),
            "mover_ir_igual": f"{sum(m[0] for m in moves)}/{len(moves)}",
            "mover_texto_igual": f"{sum(m[1] for m in moves)}/{len(moves)}",
            "deterministicas": [
                {"edicao": r["edicao"], "deck": r["deck"], "valido": r["valido"],
                 "preservado": r["outros_slides_ir_iguais"], "wall_ms": r["wall_ms"]}
                for r in rows if r["tipo_edicao"] == "deterministica"],
            "por_edicao": per,
        }
    out = OUT / "analise.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    for rnd, r in report.items():
        print(rnd, {k: v for k, v in r.items() if k not in ("por_edicao", "deterministicas")})


if __name__ == "__main__":
    main(sys.argv[1:] or ["v2"])
