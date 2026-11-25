"""Ponta a ponta pela API do PC com o motor do celular: documento → criar → refazer → mover → desfazer.

Usa o servidor FastAPI em processo (TestClient), o llama-server que o motor do celular liga sozinho e o código
do app (bench/motor_pc.mjs). Saída: outputs/e2e_motor_celular/<data>/relatorio.json e os PPTX de cada passo.

Uso: .venv/Scripts/python scripts/e2e_motor_celular.py [--documento arquivo.pdf] [--modelo qwen3-0.6b-lora]
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main(argv=None):
    from fastapi.testclient import TestClient

    from slidedsl.server import app

    ap = argparse.ArgumentParser()
    ap.add_argument("--documento", default=str(ROOT / "../../academy/papers/artigo-overleaf/samplepaper.pdf"))
    ap.add_argument("--pedido", default="Apresente este trabalho para a banca: o problema, a proposta, a versão no "
                                        "celular, os principais resultados e as limitações.")
    ap.add_argument("--modelo", default="qwen3-0.6b-lora")
    ap.add_argument("--slides", type=int, default=5)
    args = ap.parse_args(argv)
    out = ROOT / "outputs/e2e_motor_celular" / datetime.now().strftime("%Y%m%d-%H%M")
    out.mkdir(parents=True, exist_ok=True)
    client, passos = TestClient(app), []

    def esperar(job_id, limite=900):
        inicio = time.time()
        while time.time() - inicio < limite:
            job = client.get(f"/api/criar/{job_id}").json()
            if job.get("state") in {"completed", "failed"}:
                return job
            time.sleep(2)
        raise TimeoutError("job não terminou")

    def guardar(nome, job):
        result = job.get("result") or {}
        pptx = (result.get("report") or {}).get("pptx") or result.get("pptx")
        if pptx and Path(pptx).exists():
            shutil.copy(pptx, out / f"{nome}.pptx")
        slides = len((result.get("ir") or {}).get("slides") or [])
        passos.append({"passo": nome, "state": job.get("state"), "erro": job.get("error"), "slides": slides, "pptx": bool(pptx)})
        print(nome, job.get("state"), slides, "slides", job.get("error") or "", flush=True)

    doc = Path(args.documento)
    r = client.post("/api/documents", json={"name": doc.name, "data_base64": base64.b64encode(doc.read_bytes()).decode()})
    r.raise_for_status()
    doc_id = r.json()["id"]
    r = client.post("/api/criar", json={"pedido": args.pedido, "model": args.modelo, "motor": "celular",
                                        "modelo_local": args.modelo, "slides": args.slides, "documentos": [doc_id],
                                        "fontes": "documentos", "buscador": "nenhum"})
    r.raise_for_status()
    job_id = r.json()["id"]
    job = esperar(job_id)
    guardar("criar", job)
    (out / "job_criar.json").write_text(json.dumps(job, ensure_ascii=False, indent=1, default=str), "utf-8")
    for nome, edit in [("refazer_slide2", {"acao": "refazer", "slide": 2, "instrucao": "deixe mais simples"}),
                       ("mover_3_para_2", {"acao": "ajustar", "slide": 3, "mover_para": 2}),
                       ("desfazer", {"acao": "desfazer"})]:
        r = client.post(f"/api/criar/{job_id}/editar", json=edit)
        if r.status_code >= 400:
            passos.append({"passo": nome, "http": r.status_code, "erro": r.text[:300]})
            print(nome, "HTTP", r.status_code, r.text[:200], flush=True)
            continue
        guardar(nome, r.json() if r.json().get("state") in {"completed", "failed"} else esperar(job_id))
    (out / "relatorio.json").write_text(json.dumps({"documento": doc.name, "modelo": args.modelo, "passos": passos},
                                                   ensure_ascii=False, indent=1), "utf-8")
    print("->", out)
    return 0 if all(p.get("erro") in (None, "") and not p.get("http") for p in passos) else 1


if __name__ == "__main__":
    sys.exit(main())
