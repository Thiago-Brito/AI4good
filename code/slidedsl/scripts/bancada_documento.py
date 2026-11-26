"""Bancada da noite de 26/11 (T3): o mesmo documento e pedido em todos os modelos, avaliados por avaliar_documento.

Motores:
- celular:<id>  motor igual ao celular no PC (API em processo, como scripts/e2e_motor_celular.py), ids de
                config/modelos_locais.json; o motor liga o llama-server sozinho;
- pc:llamacpp   fluxo completo do PC com o llama-server já ligado (Qwen3 4B), modo gramática;
- pc:openai     fluxo completo do PC com o GPT-5.4-mini (pago; cerca de US$ 0,10 por execução, de uso.json).

Uso: .venv/Scripts/python scripts/bancada_documento.py --out outputs/noite26/bancada1 celular:qwen3-0.6b-lora pc:openai
Saída: <out>/resultado.jsonl (uma linha por motor) e as pastas de cada execução.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
DOC = ROOT / "outputs/diferencial_professor/diferencial_v2.md"
PEDIDO = ROOT / "outputs/criar/b8ae5384784247b285307924df7dfa00/pedido.txt"


def run_celular(model_id: str, slides: int, pedido: str) -> dict:
    from fastapi.testclient import TestClient

    from slidedsl.server import app

    client = TestClient(app)
    r = client.post("/api/documents", json={"name": DOC.name, "data_base64": base64.b64encode(DOC.read_bytes()).decode()})
    r.raise_for_status()
    r = client.post("/api/criar", json={"pedido": pedido, "model": model_id, "motor": "celular", "modelo_local": model_id,
                                        "slides": slides, "documentos": [r.json()["id"]], "fontes": "documentos",
                                        "buscador": "nenhum"})
    r.raise_for_status()
    job_id, start = r.json()["id"], time.time()
    while time.time() - start < 1800:
        job = client.get(f"/api/criar/{job_id}").json()
        if job.get("state") in {"completed", "failed"}:
            break
        time.sleep(3)
    result = job.get("result") or {}
    report = result.get("report") or {}
    return {"estado": job.get("state"), "erro": job.get("error"), "pasta": result.get("folder"),
            "chamadas": report.get("calls"), "segundos": report.get("seconds")}


def run_pc(provider: str, slides: int, pedido: str, out: Path) -> dict:
    model = {"openai": "gpt-5.4-mini", "llamacpp": "qwen3-4b"}[provider]
    folder = out / f"pc_{provider}"
    cmd = [str(ROOT / ".venv/Scripts/slidedsl.exe"), "criar", pedido, "--provider", provider, "--model", model,
           "--documento", str(DOC), "--fontes", "documentos", "--buscador", "nenhum", "--slides", str(slides),
           "--tema", "editorial", "--out", str(folder)]
    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    report = json.loads((folder / "relatorio.json").read_text("utf-8")) if (folder / "relatorio.json").exists() else {}
    uso = json.loads((folder / "uso.json").read_text("utf-8")) if (folder / "uso.json").exists() else {}
    return {"estado": "completed" if proc.returncode == 0 else "failed", "erro": proc.stdout[-300:] if proc.returncode else None,
            "pasta": str(folder), "chamadas": report.get("calls"), "segundos": round(time.time() - start, 1),
            "custo_usd": uso.get("cost_usd")}


def main(argv=None):
    from avaliar_documento import evaluate

    ap = argparse.ArgumentParser()
    ap.add_argument("motores", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--slides", type=int, default=8)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pedido = PEDIDO.read_text("utf-8").strip()
    gabarito = json.loads((ROOT / "benchmark/documento_diferencial.json").read_text("utf-8"))
    for motor in args.motores:
        kind, name = motor.split(":", 1)
        try:
            row = run_celular(name, args.slides, pedido) if kind == "celular" else run_pc(name, args.slides, pedido, out)
        except Exception as exc:  # um motor que falha não para a bancada
            row = {"estado": "failed", "erro": repr(exc)[:300]}
        if row.get("pasta") and (Path(row["pasta"]) / "apresentacao.slda").exists():
            row["avaliacao"] = evaluate(Path(row["pasta"]), gabarito)
        row["motor"] = motor
        with open(out / "resultado.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
