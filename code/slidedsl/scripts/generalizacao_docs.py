"""T9 da noite de 26/11: as mudanças da noite em outros documentos, antes × depois, com o 4B local (llama-server ligado).

Lados: "antes" usa o código de D:/wt_antes (commit f12b102, git worktree); "depois", o código atual.
Documentos: outputs/noite26/docs/agua.txt (curto, sem seções) e outputs/noite26/docs/artigo.pdf (longo).
Métricas genéricas (sem gabarito): válido, fatos, chamadas, tempo, números do documento usados no texto visível e
números visíveis que não estão no documento (possível invenção).

Uso: .venv/Scripts/python scripts/generalizacao_docs.py --out outputs/noite26/generalizacao [--provider openai]
Obs.: o lado "antes" não gera o .pptx (a cópia antiga não tem node_modules do renderer); a validade vem do compilador.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDES = {"antes": Path("D:/wt_antes/code/slidedsl/src"), "depois": ROOT / "src"}
DOCS = {
    "agua": ("outputs/noite26/docs/agua.txt", "Ciclo da água para alunos do ensino fundamental, com as etapas e exemplos do documento"),
    "artigo": ("outputs/noite26/docs/artigo.pdf", "Apresente este trabalho para a banca: o problema, a proposta, a versão no celular, "
                                                  "os principais resultados e as limitações."),
}
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


def run(side: str, doc: str, out: Path, provider: str = "llamacpp") -> dict:
    path, pedido = DOCS[doc]
    folder = out / f"{doc}_{side}_{provider}"
    model = {"llamacpp": "qwen3-4b", "openai": "gpt-5.4-mini"}[provider]
    code = (f"import sys; sys.path.insert(0, r'{SIDES[side]}'); from slidedsl.cli import main; "
            f"sys.exit(main(['criar', {pedido!r}, '--provider', '{provider}', '--model', '{model}', '--documento', "
            f"r'{ROOT / path}', '--fontes', 'documentos', '--buscador', 'nenhum', '--slides', '6', '--out', r'{folder}']))")
    start = time.time()
    proc = subprocess.run([str(ROOT / ".venv/Scripts/python"), "-c", code], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=2400)
    report = json.loads((folder / "relatorio.json").read_text("utf-8")) if (folder / "relatorio.json").exists() else {}
    uso = json.loads((folder / "uso.json").read_text("utf-8")) if (folder / "uso.json").exists() else {}
    return {"lado": side, "documento": doc, "provider": provider, "custo_usd": uso.get("cost_usd"), "rc": proc.returncode, "segundos": round(time.time() - start, 1),
            "chamadas": report.get("calls"), "valida": report.get("valid"), "fatos": report.get("facts"),
            "erro": proc.stdout[-200:] if proc.returncode else None, "pasta": str(folder)}


def numbers_metrics(row: dict) -> dict:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "scripts"))
    from avaliar_documento import visible_text
    from slidedsl.alto import parse_alto
    from slidedsl.documents import extract_pdf

    slda = Path(row["pasta"]) / "apresentacao.slda"
    if not slda.exists():
        return {}
    text = visible_text(parse_alto(slda.read_text("utf-8")))
    path = ROOT / DOCS[row["documento"]][0]
    source = path.read_text("utf-8") if path.suffix == ".txt" else json.dumps(extract_pdf(path), ensure_ascii=False)
    doc_numbers = set(NUMBER.findall(source))
    shown = set(NUMBER.findall(text))
    return {"numeros_do_documento_usados": len(shown & doc_numbers), "numeros_fora_do_documento": sorted(shown - doc_numbers)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--provider", default="llamacpp", choices=["llamacpp", "openai"])
    args = ap.parse_args(argv)
    # O lado "antes" roda de outra pasta, sem .env: a chave e a tabela de preço vêm do .env deste projeto.
    sys.path.insert(0, str(ROOT / "src"))
    from slidedsl.local_settings import load_local_settings
    load_local_settings(ROOT / ".env")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for doc in DOCS:
        for side in SIDES:
            row = run(side, doc, out, args.provider)
            try:
                row |= numbers_metrics(row)
            except Exception as exc:
                row["metricas_erro"] = repr(exc)[:200]
            with open(out / "resultado.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
