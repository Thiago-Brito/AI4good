"""Piloto pago pequeno pela API web; lê .env local e não imprime credenciais.

Executar da raiz do projeto: .venv/Scripts/python.exe scripts/piloto_openai.py
Até oito inferências, três slides, sem busca externa e sem geração de imagens.
Não é teste de regressão e nunca é chamado pelo pytest.
"""

import json
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from slidedsl.paths import project_root
from slidedsl.server import app


def main():
    root = project_root()
    output = root / "outputs/api_voz_mobile" / ("piloto_" + uuid4().hex[:12])
    output.mkdir(parents=True)
    with TestClient(app) as client:
        config = client.get("/api/providers").json()["openai"]
        if not config["configured"]:
            raise SystemExit("Configure OPENAI_API_KEY no .env local ou no ambiente.")
        response = client.post(
            "/api/criar",
            json={
                "pedido": "Organização do estudo para uma disciplina de programação",
                "provider": "openai",
                "model": config["default_model"],
                "slides": 3,
                "candidatos": 1,
                "reparos": 1,
                "buscador": "nenhum",
                "permitir_sem_fatos": True,
                "max_calls": 8,
                "max_output_tokens": 1500,
            },
        )
        response.raise_for_status()
        job = response.json()
        print("Execução:", job["id"], flush=True)
        deadline = time.monotonic() + 240
        seen = 0
        while time.monotonic() < deadline:
            job = client.get("/api/criar/" + job["id"]).json()
            for event in job["events"][seen:]:
                print(event["message"], flush=True)
            seen = len(job["events"])
            if job["state"] in {"failed", "completed"}:
                break
            time.sleep(0.5)
        (output / "job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2), "utf-8")
        manifest = {
            "job_id": job["id"],
            "state": job["state"],
            "usage": job.get("usage"),
            "evidence": str(output.relative_to(root)),
        }
        if job["state"] == "completed" and job["result"].get("ir"):
            result = client.post("/api/compile", json={"ir": job["result"]["ir"]})
            manifest["export_status"] = result.status_code
            if result.status_code == 200:
                (output / "export-editor.pptx").write_bytes(result.content)
            else:
                (output / "export-errors.json").write_text(result.text, "utf-8")
        else:
            manifest["error"] = job.get("error", "Execução não concluída no prazo.")
        (output / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8"
        )
        print(json.dumps(manifest, ensure_ascii=False), flush=True)
        return 0 if manifest.get("export_status") == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
