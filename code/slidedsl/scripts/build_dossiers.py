"""Gera uma vez o dossiê fixo de cada pedido do TCC (F1 de docs/PLANO_TCC.md).

Uso (Windows):
    .venv\\Scripts\\python scripts\\build_dossiers.py --provider ollama --model qwen3:4b-instruct

Dossiês existentes não são refeitos (retomável). O uso do modelo na pesquisa fica em
outputs/dossies_uso/<id>/ (custo.json, uso_chamadas.jsonl) e não entra nos testes.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def build(
    requests_path: Path,
    out_dir: Path,
    usage_dir: Path,
    model,
    *,
    provider: str,
    fallback_wikipedia: bool,
    research_fn=None,
    progress=print,
) -> dict:
    from slidedsl.experiment_runner import load_requests
    from slidedsl.model_usage import RecordedModel

    if research_fn is None:
        from slidedsl.research import research as research_fn
    data = load_requests(requests_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8")) if manifest_path.exists() else {}
    for request in data["requests"]:
        target = out_dir / f"{request['id']}.json"
        if target.exists():
            progress(f"{request['id']}: já existe, mantido")
            continue
        usage = usage_dir / request["id"]
        if usage.exists():
            # Tentativa anterior interrompida: guardar ao lado, nunca sobrescrever.
            usage = usage.with_name(usage.name + "_" + datetime.now().strftime("%Y%m%d%H%M%S"))
        tracked = RecordedModel(model, usage, max_calls=60) if model is not None else None
        progress(f"{request['id']}: pesquisando")
        dossier = research_fn(
            request["prompt"],
            model=tracked,
            provider=provider,
            fallback_wikipedia=fallback_wikipedia,
            progress=lambda m, rid=request["id"]: progress(f"  {rid}: {m}"),
        )
        dossier.save(target)
        manifest[request["id"]] = {
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "provider": provider,
            "facts": len(dossier.facts),
            "sources": len(dossier.sources),
            "model": getattr(model, "metadata", {}).get("model_requested"),
            "usage_dir": str(usage.relative_to(ROOT)) if usage.is_relative_to(ROOT) else str(usage),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")
        if not dossier.facts:
            progress(f"  AVISO {request['id']}: dossiê sem fatos verificados")
    return manifest


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--requests", default=str(ROOT / "benchmark/format_requests.json"))
    p.add_argument("--out", default=str(ROOT / "benchmark/dossies"))
    p.add_argument("--usage-out", default=str(ROOT / "outputs/dossies_uso"))
    p.add_argument("--provider", default="ollama", choices=["ollama", "llamacpp", "openai"])
    p.add_argument("--model", default="qwen3:4b-instruct")
    p.add_argument(
        "--buscador", default="searxng", choices=["searxng", "wikipedia", "brave", "tavily"]
    )
    p.add_argument("--fallback-wikipedia", action="store_true")
    args = p.parse_args(argv)
    from slidedsl.alto_cli import _model

    model = _model(args.provider, args.model)
    ok, message = model.available()
    if not ok:
        raise SystemExit(message)
    build(
        Path(args.requests),
        Path(args.out),
        Path(args.usage_out),
        model,
        provider=args.buscador,
        fallback_wikipedia=args.fallback_wikipedia,
    )


if __name__ == "__main__":
    main()
