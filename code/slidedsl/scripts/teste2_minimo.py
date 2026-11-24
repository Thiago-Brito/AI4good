"""Teste 2, condição C-mínimo: SlideDSL no mesmo formato do grupo A (uma chamada, deck inteiro).

Isola o efeito do formato do efeito do pipeline. Igual ao grupo A (teste2_codigo.py): mesmo modelo,
servidor, pedido, fatos (mesmo texto), 6 slides, temperatura 0,2, semente da execução, até 2
correções e o mesmo verificador de PPTX. Diferenças, que são a própria SlideDSL:
- o modelo escreve o deck inteiro em SlideDSL Alto, restrito pela gramática Alto convertida em GBNF;
- o prompt traz a gramática, um deck de exemplo e os limites de texto da linguagem;
- a correção devolve os erros do compilador (validação A0xx, layout, regras de design);
- o PPTX vem do compilador determinístico.
Regra fixada em 23/11/2026, antes de qualquer execução desta condição.

Uso (llama-server como no teste2_codigo.py):
  .venv\\Scripts\\python scripts\\teste2_minimo.py --seeds 11,22 [--out outputs/teste2_minimo]
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from teste2_codigo import MAX_FIXES, METRICS, OUTPUT_TOKENS, TEMPERATURE, facts_text  # noqa: E402

CONDITION = "alto_minimo"
SYSTEM = "Você escreve apresentações na linguagem SlideDSL Alto."
USER = """Escreva em SlideDSL Alto uma apresentação de {n} slides em português sobre o pedido abaixo, \
usando os fatos fornecidos.

Pedido: {pedido}

Fatos (cite os usados com `fontes F1, F2` no slide correspondente):
{fatos}

Requisitos:
- exatamente {n} slides, o primeiro do tipo capa; não use o tipo imagem; sem notas do apresentador;
- respeite os limites de texto da linguagem: {limites};
- o compilador calcula posições, fontes e cores: escreva só o conteúdo.

Gramática:
{gramatica}

Exemplo de deck:
{exemplo}

Responda só com o deck, começando por 'deck "'."""

FIX = """

Seu deck anterior:
{deck}

O compilador recusou o deck: {problema}
Corrija e responda com o deck completo."""


def limits_text() -> str:
    from slidedsl.alto import LIMITS, TEXT_LIMITS

    names = {"title": "título", "subtitle": "subtítulo", "text": "texto", "label": "rótulo de item",
             "detail": "detalhe de item", "side": "nome de lado", "value": "valor", "caption": "legenda",
             "unit": "unidade", "date": "data"}
    chars = ", ".join(f"{names[k]} até {TEXT_LIMITS[k]} caracteres" for k in names)
    counts = ", ".join(f"{k} de {lo} a {hi} {attr}" for k, (attr, lo, hi) in LIMITS.items()
                       if k != "imagem")
    return f"{chars}; quantidades: {counts}"


def grammar_rules() -> str:
    from slidedsl.alto import grammar_text

    return "\n".join(line for line in grammar_text().splitlines()
                     if line.strip() and not line.lstrip().startswith(("//", "%")))


def problems(built) -> str:
    items = []
    for d in built.errors[:8]:
        where = f"slide {d.slide}: " if d.slide else ""
        path = (d.evidence or {}).get("path") if isinstance(d.evidence, dict) else None
        items.append(f"{where}{d.code} {d.message}" + (f" ({path})" if path else ""))
    return "; ".join(items) or "deck inválido"


def make_executor(model_name, n_slides, head):
    from pptx_checks import check_pptx
    from slidedsl.alto_compile import build_alto
    from slidedsl.compiler import compile_ir
    from slidedsl.gbnf import alto_gbnf
    from slidedsl.models.llamacpp_model import LlamaCppTextModel
    from slidedsl.research import Dossier

    grammar = alto_gbnf("start")
    example = (ROOT / "examples/alto/microsservicos.slda").read_text("utf-8")
    rules, limits = grammar_rules(), limits_text()

    def run(run, folder):
        request = run.request
        dossier = Dossier.load(ROOT / "benchmark/dossies" / f"{request['id']}.json")
        facts = dossier.fact_map()
        model = LlamaCppTextModel(model_name, output_tokens=OUTPUT_TOKENS, timeout=600)
        ok, msg = model.available()
        if not ok:
            raise RuntimeError(msg)
        base = USER.format(n=n_slides, pedido=request["prompt"], fatos=facts_text(facts),
                           limites=limits, gramatica=rules, exemplo=example)
        user, calls, problem, check, result = base, [], "", None, None
        first_valid = first_compiled = False
        t0 = time.perf_counter()
        for attempt in range(MAX_FIXES + 1):
            t = time.perf_counter()
            raw = model.generate(SYSTEM, user, temperature=TEMPERATURE, seed=run.seed + attempt,
                                 grammar=grammar)
            meta = model.metadata
            usage, timings = meta.get("usage") or {}, meta.get("timings") or {}
            calls.append({"attempt": attempt, "input_tokens": usage.get("prompt_tokens"),
                          "output_tokens": usage.get("completion_tokens"),
                          "prefill_ms": timings.get("prompt_ms"), "decode_ms": timings.get("predicted_ms"),
                          "wall_ms": (time.perf_counter() - t) * 1000,
                          "finish_reason": meta.get("finish_reason")})
            (folder / f"prompt_{attempt}.txt").write_text(user, "utf-8")
            (folder / f"deck_{attempt}.slda").write_text(raw, "utf-8")
            built = build_alto(raw, facts)
            problem = ""
            if built.deck is not None and len(built.deck.slides) != n_slides:
                problem = f"o deck tem {len(built.deck.slides)} slides; são exigidos {n_slides}"
            elif not built.success(False):
                problem = problems(built)
            if not problem:
                pptx = folder / f"saida_{attempt}.pptx"
                compile_ir(built.validation.ir, pptx)
                first_compiled = first_compiled or attempt == 0
                check = check_pptx(pptx, n_slides)
                (folder / f"verificacao_{attempt}.json").write_text(
                    json.dumps(check, ensure_ascii=False, indent=2), "utf-8")
                result = pptx
                if check["valido"]:
                    first_valid = attempt == 0
                    break
                problem = "o verificador encontrou: " + "; ".join(check["bloqueios"][:6])
            if meta.get("finish_reason") == "length":
                problem += " (a resposta foi cortada pelo limite de tokens; escreva textos mais curtos)"
            if attempt < MAX_FIXES:
                user = base + FIX.format(deck=raw[:12000], problema=problem)
        (folder / "chamadas.json").write_text(json.dumps(calls, indent=2), "utf-8")
        if result:
            shutil.copy(result, folder / "apresentacao.pptx")

        def total(key):
            vals = [c[key] for c in calls]
            return None if any(v is None for v in vals) else round(sum(vals), 3)

        return {
            "valido": bool(check and check["valido"] and not problem),
            "gerou_pptx": result is not None, "executou_1a": first_compiled, "valido_1a": first_valid,
            "chamadas": len(calls), "reparos": len(calls) - 1,
            "slides_pptx": check["slides"] if check else 0,
            "bloqueios": len(check["bloqueios"]) if check else "",
            "avisos": len(check["avisos"]) if check else "",
            "chars_visiveis": check["chars_visiveis"] if check else 0,
            "tokens_entrada": total("input_tokens"), "tokens_saida": total("output_tokens"),
            "prefill_ms": total("prefill_ms"), "decode_ms": total("decode_ms"),
            "wall_ms": round((time.perf_counter() - t0) * 1000, 1),
            "falha": problem[:300], "modelo": model_name, "commit": head,
        }

    return run


def main(argv=None):
    from slidedsl.experiment_runner import load_requests, plan_runs, run_matrix
    from teste3_restricao import commit

    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="11,22")
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste2_minimo"))
    ap.add_argument("--model", default="Qwen3-4B-Instruct-2507-Q4_K_M")
    ap.add_argument("--slides", type=int, default=6)
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    data = load_requests(ROOT / "benchmark/format_requests.json")
    requests = data["requests"]
    if args.only:
        requests = [r for r in requests if r["id"] in args.only.split(",")]
    seeds = [int(s) for s in args.seeds.split(",")]
    runs = plan_runs(requests, [CONDITION], seeds, order_seed=data["order_seed"])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    head = commit()
    (out / "maquina.json").write_text(json.dumps({
        "plataforma": platform.platform(), "processador": platform.processor(),
        "python": platform.python_version(), "modelo": args.model, "seeds": seeds,
        "temperatura": TEMPERATURE, "max_tokens": OUTPUT_TOKENS, "correcoes": MAX_FIXES,
        "commit": head}, indent=2), "utf-8")
    counts = run_matrix(runs, make_executor(args.model, args.slides, head), out, metric_fields=METRICS,
                        progress=lambda m: print(m, flush=True))
    print(counts)


if __name__ == "__main__":
    main()
