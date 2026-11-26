"""Resumo de uma bancada (resultado.jsonl de bancada_documento.py) com os tokens de cada execução.

Uso: .venv/Scripts/python scripts/resumo_bancada.py <pasta da bancada> [...]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tokens_chamadas import resumo  # noqa: E402

for pasta in sys.argv[1:]:
    for linha in (Path(pasta) / "resultado.jsonl").read_text("utf-8").splitlines():
        r = json.loads(linha)
        a = r.get("avaliacao") or {}
        t = resumo(Path(r["pasta"])) if r.get("pasta") else {"total": {}, "etapas": {}}
        print(json.dumps({"motor": r["motor"], "estado": r["estado"], "s": r.get("segundos"), **{k: a.get(k) for k in a if k != "execucao"},
                          "tokens": t["total"], "leitura": t["etapas"].get("document_extract")}, ensure_ascii=False))
