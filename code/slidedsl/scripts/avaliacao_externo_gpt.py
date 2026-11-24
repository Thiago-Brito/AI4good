"""Condição externa da avaliação cega: GPT-4.1-mini escreve o PowerPoint direto (python-pptx), como um estudante
faria com uma IA comercial. Mesma entrada das condições do app: o pedido (nível detalhado), o documento-fonte e
5 slides. Reaproveita do Teste 2 a extração, a auditoria (só python-pptx e biblioteca padrão) e a execução
isolada do programa, com até 2 correções. O arquivo é mostrado como sai (LibreOffice -> PDF -> PNG).

Saída: outputs/avaliacao_cega/externo/<tema>/ (prompts, respostas, programas, apresentacao.pptx, slide_NN.png).
Uso: .venv/Scripts/python scripts/avaliacao_externo_gpt.py [--modelo gpt-4.1-mini] [--temas agua,sono,git,solar]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from teste2_codigo import FIX, SYSTEM, audit, execute, extract_code  # noqa: E402

SOFFICE = Path("C:/Program Files/LibreOffice/program/soffice.exe")
USER = """Escreva um programa Python, usando python-pptx, que crie uma apresentação de {n} slides \
em português sobre o pedido abaixo, usando o documento-fonte.

Pedido: {pedido}

Documento-fonte (use-o no conteúdo):
{documento}

Requisitos:
- exatamente {n} slides, formato 16:9 (prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5));
- títulos e textos claros, com todo o texto dentro das caixas e dentro do slide, sem caixas sobrepostas;
- salve o arquivo como "saida.pptx" no diretório atual;
- use apenas python-pptx e a biblioteca padrão (sem arquivos externos, imagens ou rede).

Responda só com o código, num único bloco ```python."""


def render(pptx: Path, folder: Path) -> list[Path]:
    import pypdfium2 as pdfium

    subprocess.run([str(SOFFICE), "--headless", "--convert-to", "pdf", "--outdir", str(folder), str(pptx)],
                   check=True, capture_output=True, timeout=180)
    pdf = pdfium.PdfDocument(str(folder / (pptx.stem + ".pdf")))
    paths = []
    for k in range(len(pdf)):
        image = pdf[k].render(scale=960 / pdf[k].get_width()).to_pil()
        path = folder / f"slide_{k + 1:02d}.png"
        image.save(path)
        paths.append(path)
    return paths


def main(argv=None):
    from slidedsl.local_settings import load_local_settings  # chave em .env, nunca impressa
    from slidedsl.models.openai_model import OpenAITextModel

    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="gpt-4.1-mini")
    ap.add_argument("--temas", default="agua,sono,git,solar")
    ap.add_argument("--slides", type=int, default=5)
    args = ap.parse_args(argv)
    load_local_settings()
    reqs = {r["id"]: r for r in json.loads((ROOT / "benchmark/format_requests.json").read_text("utf-8"))["requests"]}
    model = OpenAITextModel(args.modelo, output_tokens=6144)
    resumo = {}
    for tema in args.temas.split(","):
        folder = ROOT / "outputs/avaliacao_cega/externo" / tema
        folder.mkdir(parents=True, exist_ok=True)
        documento = (ROOT / "outputs/teste4/documentos" / f"{tema}.txt").read_text("utf-8")
        base = USER.format(n=args.slides, pedido=reqs[f"{tema}_detalhado"]["prompt"], documento=documento)
        user, pptx, problem, t0 = base, None, "", time.time()
        for attempt in range(3):
            raw = model.generate(SYSTEM, user, temperature=0.2, seed=11 + attempt)
            (folder / f"resposta_{attempt}.txt").write_text(raw, "utf-8")
            code = extract_code(raw)
            (folder / f"programa_{attempt}.py").write_text(code, "utf-8")
            problem = audit(code)
            out = None
            if not problem:
                problem, out = execute(code, folder, attempt)
            if out:
                pptx = folder / "apresentacao.pptx"
                pptx.write_bytes(Path(out).read_bytes())
                break
            user = base + FIX.format(codigo=code[:12000], problema=problem)
        usage = model.metadata.get("usage") or {}
        slides = [p.name for p in render(pptx, folder)] if pptx else []
        resumo[tema] = {"gerou": bool(pptx), "tentativas": attempt + 1, "slides": len(slides),
                        "falha": problem[:200], "segundos": round(time.time() - t0, 1), "ultima_chamada": usage}
        print(tema, resumo[tema], flush=True)
    (ROOT / "outputs/avaliacao_cega/externo/resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()
