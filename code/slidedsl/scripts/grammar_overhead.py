"""Microbenchmark do custo da gramática no llama-server (Teste 3): ms por token com e sem GBNF.

Mesmo prompt N vezes em cada condição (alternadas), aquecimento descartado; mede
predicted_ms / predicted_n e prompt_ms dos `timings`. Host como parâmetro (PC ou celular).
Uso: .venv\\Scripts\\python scripts\\grammar_overhead.py [--host http://127.0.0.1:8080] [--n 20]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PROMPT = ("Escreva um slide de tópicos na SlideDSL Alto sobre energia solar residencial, com título e "
          "três itens (rótulo e detalhe), em português.")


def main(argv=None):
    from slidedsl.gbnf import alto_gbnf

    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="http://127.0.0.1:8080")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste3" / "grammar_overhead.json"))
    args = ap.parse_args(argv)
    grammar = alto_gbnf("topicos")
    rows = []
    with httpx.Client(timeout=300, trust_env=False) as client:
        def one(with_grammar, i):
            payload = {"messages": [{"role": "user", "content": PROMPT}], "max_tokens": 256,
                       "temperature": 0, "seed": 1000 + i, "stream": False}
            if with_grammar:
                payload["grammar"] = grammar
            data = client.post(args.host + "/v1/chat/completions", json=payload).json()
            t = data.get("timings") or {}
            return {"gramatica": with_grammar, "i": i, "predicted_n": t.get("predicted_n"),
                    "predicted_ms": t.get("predicted_ms"), "prompt_ms": t.get("prompt_ms"),
                    "ms_por_token": (t["predicted_ms"] / t["predicted_n"]) if t.get("predicted_n") else None}

        one(False, -1)
        one(True, -1)  # aquecimento descartado
        for i in range(args.n):
            for g in (False, True):
                rows.append(one(g, i))
                time.sleep(1)
    summary = {}
    for g in (False, True):
        vals = [r["ms_por_token"] for r in rows if r["gramatica"] == g and r["ms_por_token"]]
        summary["com_gramatica" if g else "sem_gramatica"] = {
            "n": len(vals), "ms_por_token_mediana": round(statistics.median(vals), 3),
            "ms_por_token_media": round(statistics.mean(vals), 3),
            "tokens_por_s_mediana": round(1000 / statistics.median(vals), 2)}
    a, b = summary["sem_gramatica"], summary["com_gramatica"]
    summary["acrescimo_mediana_pct"] = round(100 * (b["ms_por_token_mediana"] / a["ms_por_token_mediana"] - 1), 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"host": args.host, "resumo": summary, "execucoes": rows},
                                         ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
