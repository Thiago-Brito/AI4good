"""Analisa a avaliação cega (protocolo em docs/AVALIACAO_CEGA_PROTOCOLO.md).

Entrada: a pasta com as respostas exportadas da página (um JSON por avaliador, como o ArtifactData salva com
`out_dir`) e o gabarito privado outputs/avaliacao_cega/gabarito.json.
Saída: outputs/avaliacao_cega/resultado.json e um resumo no terminal.

Uso: .venv/Scripts/python scripts/avaliacao_cega_analisar.py outputs/avaliacao_cega/respostas
"""

from __future__ import annotations

import itertools
import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONDS = ["celular 0.6B LoRA", "celular 1.7B", "PC 4B", "externo GPT-4.1-mini"]
REP = {"nao": 0, "pouco": 1, "muito": 2}


def load(folder: Path):
    raters = []
    for f in sorted(folder.rglob("*.json")):
        doc = json.loads(f.read_text("utf-8"))
        body = doc.get("data", doc)  # aceita o arquivo do ArtifactData ou só o corpo
        if body.get("answers"):
            raters.append({"id": f.stem, "answers": body["answers"]})
    return raters


def krippendorff_ordinal(units: list[list[float]]) -> float | None:
    """Alfa ordinal (métrica de rank). units: valores de cada unidade (apresentação), um por avaliador."""
    values = sorted({v for u in units for v in u})
    if len(values) < 2:
        return None
    count = defaultdict(float)
    for u in units:
        for v in u:
            count[v] += 1
    def delta(a, b):
        lo, hi = sorted((a, b))
        inner = sum(count[v] for v in values if lo <= v <= hi)
        return (inner - (count[lo] + count[hi]) / 2) ** 2
    pairs = [u for u in units if len(u) >= 2]
    n = sum(len(u) for u in pairs)
    do = sum(sum(delta(a, b) for a, b in itertools.permutations(u, 2)) / (len(u) - 1) for u in pairs) / n
    de = sum(count[a] * count[b] * delta(a, b) for a in values for b in values) / (n * (n - 1))
    return None if de == 0 else 1 - do / de


def friedman(blocks: list[list[float]]) -> tuple[float, float]:
    """Estatística de Friedman (com empates por posto médio) e p pela qui-quadrado com k-1 gl."""
    k, n = len(blocks[0]), len(blocks)
    ranks = []
    for b in blocks:
        order = sorted(range(k), key=lambda i: b[i])
        r = [0.0] * k
        i = 0
        while i < k:
            j = i
            while j + 1 < k and b[order[j + 1]] == b[order[i]]:
                j += 1
            for t in range(i, j + 1):
                r[order[t]] = (i + j) / 2 + 1
            i = j + 1
        ranks.append(r)
    sums = [sum(r[c] for r in ranks) for c in range(k)]
    chi = 12 / (n * k * (k + 1)) * sum(s * s for s in sums) - 3 * n * (k + 1)
    # p da qui-quadrado com k-1 gl (k = 3: exp(-x/2); k = 4: 3 gl)
    if k == 3:
        p = math.exp(-chi / 2)
    elif k == 4:
        p = math.erfc(math.sqrt(chi / 2)) + math.sqrt(2 * chi / math.pi) * math.exp(-chi / 2)
    else:
        p = float("nan")
    return chi, p


def sign_test(diffs: list[float]) -> float:
    """p bilateral exato do teste do sinal (com 4 temas o Wilcoxon exato tem o mesmo piso de p = 0,125)."""
    pos, neg = sum(d > 0 for d in diffs), sum(d < 0 for d in diffs)
    m = pos + neg
    if m == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(m, i) for i in range(min(pos, neg) + 1)) / 2 ** m)


def main(folder: str):
    gab = {c: g for c, g in json.loads((ROOT / "outputs/avaliacao_cega/gabarito.json").read_text("utf-8"))["codigos"].items()
           if not c.startswith("ausente-")}
    pub = json.loads((ROOT / "outputs/avaliacao_cega/publicar/avaliacao.json").read_text("utf-8"))
    tema_of = {a["codigo"]: a["tema"] for a in pub["apresentacoes"]}
    raters = load(Path(folder))
    if not raters:
        raise SystemExit("Nenhuma resposta encontrada.")
    out = {"avaliadores": len(raters), "por_condicao": {}, "concordancia": {}, "testes": {}}
    for q in ("clareza", "utilidade"):
        units = [[float(r["answers"][c][q]) for r in raters if c in r["answers"]] for c in gab]
        out["concordancia"][q] = krippendorff_ordinal(units)
    for cond in CONDS:
        codes = [c for c, g in gab.items() if g["condicao"] == cond]
        ans = [r["answers"][c] for r in raters for c in codes if c in r["answers"]]
        out["por_condicao"][cond] = {
            "avaliacoes": len(ans),
            "clareza_media": round(st.mean(float(a["clareza"]) for a in ans), 2) if ans else None,
            "utilidade_media": round(st.mean(float(a["utilidade"]) for a in ans), 2) if ans else None,
            "erro_sim": sum(a["erro"] == "sim" for a in ans),
            "repeticao_muito": sum(a["repeticao"] == "muito" for a in ans),
            "repeticao_media_0a2": round(st.mean(REP[a["repeticao"]] for a in ans), 2) if ans else None,
            "segundos_mediana": st.median(a.get("segundos", 0) for a in ans) if ans else None,
            "erros_citados": [a["erro_qual"] for a in ans if a.get("erro") == "sim"],
        }
    # Unidade: média dos avaliadores por apresentação; blocos = temas.
    temas = sorted({tema_of[c] for c in gab})
    for q in ("clareza", "utilidade"):
        mean = {}
        for c in gab:
            vals = [float(r["answers"][c][q]) for r in raters if c in r["answers"]]
            mean[c] = st.mean(vals) if vals else None
        blocks = []
        for t in temas:
            row = [next((mean[c] for c, g in gab.items() if g["condicao"] == cond and tema_of[c] == t), None) for cond in CONDS]
            if None not in row:
                blocks.append(row)
        chi, p = friedman(blocks) if len(blocks) >= 2 else (None, None)
        idx = {c: i for i, c in enumerate(CONDS)}
        def diffs(a, b):  # por tema, só onde as duas condições existem
            return [round(r[idx[a]] - r[idx[b]], 2) for t in temas
                    for r in [[next((mean[c] for c, g in gab.items() if g["condicao"] == cond and tema_of[c] == t), None)
                               for cond in CONDS]] if r[idx[a]] is not None and r[idx[b]] is not None]
        out["testes"][q] = {"friedman_chi2": chi, "friedman_p": p, "temas_completos": len(blocks)}
        for nome, (a, b) in {"H1_externo_menos_lora": ("externo GPT-4.1-mini", "celular 0.6B LoRA"),
                             "H1_externo_menos_17b": ("externo GPT-4.1-mini", "celular 1.7B"),
                             "H2_lora_menos_17b": ("celular 0.6B LoRA", "celular 1.7B"),
                             "H3_pc4b_menos_17b": ("PC 4B", "celular 1.7B")}.items():
            d = diffs(a, b)
            out["testes"][q][nome] = d
            out["testes"][q][nome + "_p_sinal"] = sign_test(d)
    dst = ROOT / "outputs/avaliacao_cega/resultado.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), "utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "por_condicao"}, ensure_ascii=False, indent=1))
    for cond, v in out["por_condicao"].items():
        print(cond, {k: v[k] for k in v if k != "erros_citados"})
    print("->", dst)


if __name__ == "__main__":
    main(sys.argv[1])
