"""Soma tokens e tempo das chamadas de uma execução (chamadas.jsonl), por etapa: medida de custo no celular.

No celular o tempo é dominado pelos tokens gerados (decodificação) e, depois, pelos tokens de entrada (prefill).
Uso: .venv/Scripts/python scripts/tokens_chamadas.py <pasta> [<pasta> ...]
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def resumo(pasta: Path) -> dict:
    etapas = defaultdict(lambda: {"chamadas": 0, "entrada": 0, "saida": 0})
    for linha in (pasta / "chamadas.jsonl").read_text("utf-8").splitlines():
        if not linha.strip():
            continue
        c = json.loads(linha)
        u = c.get("usage") or c
        e = etapas[c.get("stage", "?")]
        e["chamadas"] += 1
        e["entrada"] += int(u.get("prompt_tokens") or u.get("input_tokens") or 0)
        e["saida"] += int(u.get("completion_tokens") or u.get("output_tokens") or 0)
    total = {k: sum(e[k] for e in etapas.values()) for k in ("chamadas", "entrada", "saida")}
    return {"pasta": pasta.name, "total": total, "etapas": dict(etapas)}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(json.dumps(resumo(Path(p)), ensure_ascii=False))
