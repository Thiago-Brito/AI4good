"""Condição "SlideDSL no PC" da avaliação cega: fluxo completo do PC (create_presentation) com o
Qwen3-4B-Instruct-2507 no llama.cpp (modo gramática, padrão do provedor), mesma entrada das outras condições:
pedido (nível detalhado), documento-fonte (fontes = documentos, sem internet, sem imagens) e 5 slides.

Pré-requisito: llama-server com o 4B em LLAMACPP_BASE_URL (padrão http://127.0.0.1:8080), contexto 8192.
Saída: outputs/avaliacao_cega/pc4b/<tema>/ (arquivos do fluxo completo: apresentacao.slda, .pptx, relatorio.json).
Uso: .venv/Scripts/python scripts/avaliacao_pc_4b.py [--temas agua,sono,git,solar]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv=None):
    from slidedsl.alto_generation import create_presentation
    from slidedsl.documents import add_document
    from slidedsl.models.llamacpp_model import LlamaCppTextModel

    ap = argparse.ArgumentParser()
    ap.add_argument("--temas", default="agua,sono,git,solar")
    ap.add_argument("--semente", type=int, default=11)
    # Avaliação cega v3 (assuntos novos): outra pasta de documentos, outro arquivo de pedidos e outra saída.
    ap.add_argument("--documentos", default="outputs/teste4/documentos")
    ap.add_argument("--pedidos", default="benchmark/format_requests.json")
    ap.add_argument("--saida", default="outputs/avaliacao_cega/pc4b")
    args = ap.parse_args(argv)
    reqs = {r["id"]: r for r in json.loads((ROOT / args.pedidos).read_text("utf-8"))["requests"]}
    resumo = {}
    for tema in args.temas.split(","):
        out = ROOT / args.saida / tema
        if args.semente != 11:  # regra do protocolo: até 3 sementes (11, 12, 13); fica a 1ª válida, falhas guardadas
            old = out.with_name(f"{tema}_s{args.semente - 1}_invalido")
            if out.exists() and not old.exists():
                out.rename(old)
        doc = add_document(f"{tema}.txt", (ROOT / args.documentos / f"{tema}.txt").read_bytes())
        model = LlamaCppTextModel("Qwen3-4B-Instruct-2507-Q4_K_M", output_tokens=2048, timeout=900)
        t0 = time.time()
        try:
            report = create_presentation(reqs[f"{tema}_detalhado"]["prompt"], out, model, research_provider=None,
                                         document_ids=[doc["id"]], sources_mode="documentos", n_slides=5,
                                         theme="claro", mode="gramatica", images=False, seed=args.semente,
                                         progress=lambda m: print("  >", m, flush=True))
            resumo[tema] = {"valido": report.get("valid"), "chamadas": report.get("calls"),
                            "segundos": round(time.time() - t0, 1)}
        except Exception as exc:  # registra e segue para o próximo tema
            resumo[tema] = {"erro": str(exc)[:300], "segundos": round(time.time() - t0, 1)}
        print(tema, resumo[tema], flush=True)
    name = "resumo.json" if args.semente == 11 else f"resumo_s{args.semente}.json"
    (ROOT / args.saida / name).write_text(json.dumps(resumo, ensure_ascii=False, indent=1), "utf-8")


if __name__ == "__main__":
    main()
