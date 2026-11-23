"""Teste 3 (reduzido) do TCC: mecanismo de restrição da saída — json × gramatica × direto.

Mesmo modelo (Qwen3-4B-Instruct-2507 Q4_K_M no llama-server, GPU), mesmos pedidos e dossiês fixos,
ordem sorteada com semente registrada, execução retomável (src/slidedsl/experiment_runner.py).

Pré-requisito (outro terminal):
  D:\\android\\llama\\llama-server.exe -m D:\\android\\models\\Qwen3-4B-Instruct-2507-Q4_K_M.gguf ^
      -ngl 99 -c 8192 --port 8080 --jinja
Uso:
  .venv\\Scripts\\python scripts\\teste3_restricao.py [--seeds 11] [--out outputs/teste3]
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
MODES = ["json", "gramatica", "direto"]
METRICS = ["valido", "slides", "chamadas", "chamadas_slide", "reparos", "slides_1a_tentativa",
           "tokens_entrada", "tokens_saida", "prefill_ms", "decode_ms", "wall_ms", "erros_bloqueio",
           "modelo", "commit"]


def commit():
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "src"], cwd=ROOT, capture_output=True,
                               text=True, timeout=10).stdout.strip()
        return head + ("+alteracoes" if dirty else "")
    except Exception:
        return "desconhecido"


def make_executor(model_name, n_slides):
    from slidedsl.alto_generation import create_presentation
    from slidedsl.models.llamacpp_model import LlamaCppTextModel
    from slidedsl.research import Dossier

    head = commit()

    def run(run, folder):
        request = run.request
        dossier = Dossier.load(ROOT / "benchmark/dossies" / f"{request['id']}.json")
        model = LlamaCppTextModel(model_name, output_tokens=2048)
        ok, msg = model.available()
        if not ok:
            raise RuntimeError(msg)
        out = folder / "deck"
        try:
            report = create_presentation(request["prompt"], out, model, dossier=dossier,
                                         n_slides=n_slides, mode=run.condition, seed=run.seed,
                                         preview=False, research_provider=None, max_calls=60)
        except Exception as exc:  # deck inválido também é resultado; o relatório fica salvo
            path = out / "relatorio.json"
            report = json.loads(path.read_text("utf-8")) if path.exists() else {"valid": False}
            report.setdefault("exception", f"{type(exc).__name__}: {exc}"[:200])
        custo = json.loads((out / "custo.json").read_text("utf-8"))
        calls = [json.loads(x) for x in (out / "chamadas.jsonl").read_text("utf-8").splitlines()] \
            if (out / "chamadas.jsonl").exists() else []
        slide_calls = [c for c in calls if c["stage"] == "slide"]
        first = {c["slide"] for c in slide_calls if c["attempt"] == 0}
        repaired = {c["slide"] for c in slide_calls if c["attempt"] > 0}
        total = custo["total"]
        return {
            "valido": bool(report.get("valid")), "slides": n_slides, "chamadas": total["calls"],
            "chamadas_slide": len(slide_calls), "reparos": len([c for c in slide_calls if c["attempt"] > 0]),
            "slides_1a_tentativa": len(first - repaired),
            "tokens_entrada": total["input_tokens"], "tokens_saida": total["output_tokens"],
            "prefill_ms": total["prefill_ms"], "decode_ms": total["decode_ms"], "wall_ms": total["wall_ms"],
            "erros_bloqueio": ";".join(sorted({e.get("code", "?") for e in report.get("errors") or []}))
            or report.get("exception", ""),
            "modelo": model_name, "commit": head,
        }

    return run


def main(argv=None):
    from slidedsl.experiment_runner import load_requests, plan_runs, run_matrix

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="11")
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste3"))
    ap.add_argument("--model", default="Qwen3-4B-Instruct-2507-Q4_K_M")
    ap.add_argument("--slides", type=int, default=6)
    args = ap.parse_args(argv)
    data = load_requests(ROOT / "benchmark/format_requests.json")
    seeds = [int(s) for s in args.seeds.split(",")]
    runs = plan_runs(data["requests"], MODES, seeds, order_seed=data["order_seed"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "maquina.json").write_text(json.dumps({
        "plataforma": platform.platform(), "processador": platform.processor(),
        "python": platform.python_version(), "modelo": args.model, "seeds": seeds}, indent=2), "utf-8")
    counts = run_matrix(runs, make_executor(args.model, args.slides), out, metric_fields=METRICS,
                        progress=lambda m: print(m, flush=True))
    print(counts)


if __name__ == "__main__":
    main()
