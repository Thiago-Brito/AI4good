"""Teste 2 do TCC: o modelo escreve o programa python-pptx diretamente (grupo A, sem SlideDSL).

O grupo C (com SlideDSL) são as execuções do Teste 3 (modos json e gramatica), com o mesmo modelo,
servidor, pedidos, dossiês e sementes; o pareamento é por pedido e semente. Ver analise_teste2.py.

Protocolo do grupo A (docs/PLANO_TESTES_E_APK.md, Teste 2):
- mesmo pedido e mesmo dossiê do grupo C; 6 slides; temperatura 0,2; semente da execução;
- o programa é conferido (importações permitidas) e executado num diretório temporário,
  com `python -I` e limite de 60 s; o PPTX passa pelo verificador único (pptx_checks.py);
- até 2 correções (o mesmo limite de reparo do pipeline), devolvendo o erro de execução ou os
  bloqueios do verificador ao modelo.

Pré-requisito (outro terminal; contexto maior porque a correção reenvia o programa):
  D:\\android\\llama\\llama-server.exe -m D:\\android\\models\\Qwen3-4B-Instruct-2507-Q4_K_M.gguf ^
      -ngl 99 -c 16384 --port 8080 --jinja
Uso:
  .venv\\Scripts\\python scripts\\teste2_codigo.py --seeds 11,22 [--out outputs/teste2]
"""

from __future__ import annotations

import argparse
import ast
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
CONDITION = "codigo"
MAX_FIXES = 2
TEMPERATURE = 0.2
OUTPUT_TOKENS = 6144
ALLOWED_IMPORTS = {"pptx", "math", "datetime", "copy", "collections", "itertools", "textwrap",
                   "re", "string", "random"}
FORBIDDEN_NAMES = {"exec", "eval", "compile", "__import__", "open", "input", "breakpoint"}
METRICS = ["valido", "gerou_pptx", "executou_1a", "valido_1a", "chamadas", "reparos", "slides_pptx",
           "bloqueios", "avisos", "chars_visiveis", "tokens_entrada", "tokens_saida", "prefill_ms",
           "decode_ms", "wall_ms", "falha", "modelo", "commit"]

SYSTEM = "Você é um programador Python especialista na biblioteca python-pptx."
USER = """Escreva um programa Python, usando python-pptx, que crie uma apresentação de {n} slides \
em português sobre o pedido abaixo, usando os fatos fornecidos.

Pedido: {pedido}

Fatos (use-os no conteúdo e indique a fonte no slide em que forem usados):
{fatos}

Requisitos:
- exatamente {n} slides, formato 16:9 (prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5));
- títulos e textos claros, com todo o texto dentro das caixas e dentro do slide, sem caixas sobrepostas;
- salve o arquivo como "saida.pptx" no diretório atual;
- use apenas python-pptx e a biblioteca padrão (sem arquivos externos, imagens ou rede).

Responda só com o código, num único bloco ```python."""

FIX = """

Seu programa anterior:
```python
{codigo}
```

Problema encontrado: {problema}
Corrija e responda com o programa completo, num único bloco ```python."""


def facts_text(facts: dict) -> str:
    """Mesmos campos que o pipeline mostra ao modelo; trecho limitado a 200 caracteres (contexto)."""
    lines = []
    for fid, f in list(facts.items())[:32]:
        value = f" [valor: {f['value']}]" if f.get("value") else ""
        lines.append(f'{fid}{value}: {f["claim"]}\n   fonte: {f.get("source_title", "")}\n'
                     f'   trecho: "{f["quote"][:200]}"')
    return "\n".join(lines) or "(nenhum fato: não use números; use exemplos qualitativos)"


def extract_code(text: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.S)
    if blocks:
        return max(blocks, key=len).strip()
    return text.strip().removeprefix("```python").removeprefix("```").removesuffix("```").strip()


def audit(code: str) -> str:
    """Conferência estática antes de executar: sintaxe, importações e nomes perigosos."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"erro de sintaxe na linha {exc.lineno}: {exc.msg}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mods = [(node.module or "").split(".")[0]]
        else:
            mods = []
        bad = [m for m in mods if m not in ALLOWED_IMPORTS]
        if bad:
            return f"importação não permitida: {', '.join(bad)} (use só python-pptx e math)"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"uso não permitido de {node.id}"
    return ""


def execute(code: str, folder: Path, attempt: int) -> tuple[str, Path | None]:
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "gera.py"
        script.write_text(code, "utf-8")
        try:
            run = subprocess.run([sys.executable, "-I", str(script)], cwd=tmp, capture_output=True,
                                 text=True, timeout=60, encoding="utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            return "o programa excedeu 60 s", None
        (folder / f"stdout_{attempt}.txt").write_text(run.stdout + "\n--stderr--\n" + run.stderr,
                                                      "utf-8")
        if run.returncode:
            tail = [x for x in run.stderr.strip().splitlines() if x.strip()]
            return "erro de execução: " + " | ".join(tail[-3:])[:600], None
        made = Path(tmp) / "saida.pptx"
        if not made.exists():
            return "o programa terminou sem criar saida.pptx", None
        dest = folder / f"saida_{attempt}.pptx"
        shutil.copy(made, dest)
        return "", dest


def make_executor(model_name, n_slides, head):
    from pptx_checks import check_pptx
    from slidedsl.models.llamacpp_model import LlamaCppTextModel
    from slidedsl.research import Dossier

    def run(run, folder):
        request = run.request
        dossier = Dossier.load(ROOT / "benchmark/dossies" / f"{request['id']}.json")
        model = LlamaCppTextModel(model_name, output_tokens=OUTPUT_TOKENS, timeout=600)
        ok, msg = model.available()
        if not ok:
            raise RuntimeError(msg)
        base = USER.format(n=n_slides, pedido=request["prompt"], fatos=facts_text(dossier.fact_map()))
        user, calls, code = base, [], ""
        result, problem, check = None, "", None
        first_exec = first_valid = False
        t0 = time.perf_counter()
        for attempt in range(MAX_FIXES + 1):
            t = time.perf_counter()
            raw = model.generate(SYSTEM, user, temperature=TEMPERATURE, seed=run.seed + attempt)
            meta = model.metadata
            usage, timings = meta.get("usage") or {}, meta.get("timings") or {}
            calls.append({"attempt": attempt, "input_tokens": usage.get("prompt_tokens"),
                          "output_tokens": usage.get("completion_tokens"),
                          "prefill_ms": timings.get("prompt_ms"), "decode_ms": timings.get("predicted_ms"),
                          "wall_ms": (time.perf_counter() - t) * 1000,
                          "finish_reason": meta.get("finish_reason")})
            (folder / f"prompt_{attempt}.txt").write_text(user, "utf-8")
            (folder / f"resposta_{attempt}.txt").write_text(raw, "utf-8")
            code = extract_code(raw)
            (folder / f"programa_{attempt}.py").write_text(code, "utf-8")
            problem = audit(code)
            pptx = None
            if not problem:
                problem, pptx = execute(code, folder, attempt)
            if pptx:
                if attempt == 0:
                    first_exec = True
                check = check_pptx(pptx, n_slides)
                (folder / f"verificacao_{attempt}.json").write_text(
                    json.dumps(check, ensure_ascii=False, indent=2), "utf-8")
                result = pptx
                if check["valido"]:
                    first_valid = attempt == 0
                    problem = ""
                    break
                problem = "o verificador encontrou: " + "; ".join(check["bloqueios"][:6])
            if meta.get("finish_reason") == "length":
                problem += " (a resposta foi cortada pelo limite de tokens; escreva um programa mais curto)"
            if attempt < MAX_FIXES:
                user = base + FIX.format(codigo=code[:12000], problema=problem)
        (folder / "chamadas.json").write_text(json.dumps(calls, indent=2), "utf-8")
        if result:
            shutil.copy(result, folder / "apresentacao.pptx")

        def total(key):
            vals = [c[key] for c in calls]
            return None if any(v is None for v in vals) else round(sum(vals), 3)

        return {
            "valido": bool(check and check["valido"] and not problem),
            "gerou_pptx": result is not None, "executou_1a": first_exec, "valido_1a": first_valid,
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
    ap.add_argument("--out", default=str(ROOT / "outputs" / "teste2"))
    ap.add_argument("--model", default="Qwen3-4B-Instruct-2507-Q4_K_M")
    ap.add_argument("--slides", type=int, default=6)
    ap.add_argument("--only", default="", help="ids de pedido separados por vírgula (teste rápido)")
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
