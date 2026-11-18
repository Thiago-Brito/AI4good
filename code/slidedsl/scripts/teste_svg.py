"""Teste PAGO do sem3, fora do pytest: diagramas SVG, IA sozinha (A) × SlideDSL (B).

A: o modelo recebe o pedido e responde com o código SVG inteiro.
B: o mesmo modelo escreve só o bloco ``etapas``/``grafico`` da SlideDSL Alto; o analisador
   LALR confere e o compilador (``svg_diagrams``) desenha o SVG.
Igual nas duas: modelo, temperatura, seed, texto do pedido, 1 reparo, tamanho da figura.
Depois roda ``scripts/conferir_svg.mjs`` em cada condição contra o gabarito congelado.

Executar de code/slidedsl:
  .venv/Scripts/python.exe scripts/teste_svg.py --ids fotossintese_etapas fotossintese_barras --seeds 42
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from slidedsl.alto import parse_alto
from slidedsl.local_settings import load_local_settings
from slidedsl.model_usage import RecordedModel
from slidedsl.models.ollama_model import OllamaTextModel
from slidedsl.models.openai_model import OpenAITextModel
from slidedsl.paths import project_root
from slidedsl.svg_diagrams import slide_svg

MODEL = "gpt-4.1-mini"
TEMPERATURE = 0.2
LIMIT_USD = 1.0
SIZES = {"etapas": (1200, 420), "ciclo": (1200, 700), "barras": (1200, 600)}

SYSTEM_A = """Você desenha diagramas para slides de apresentação.
Responda SOMENTE com o código de um SVG válido, sem explicação e sem bloco de código.
O SVG deve ter width="{w}" height="{h}" e viewBox="0 0 {w} {h}", fundo branco,
fonte Arial, texto em português legível (no mínimo 14 px), e todo o conteúdo pedido."""

SYSTEM_B = """Você escreve um único bloco da SlideDSL Alto, sem explicação e sem bloco de código.
Gramática:
  etapas  { titulo STRING item+ }        item: item "rótulo" "detalhe"
  ciclo   { titulo STRING item+ }
  grafico { titulo STRING unidade? barra+ }  barra: barra "rótulo" NUMERO   unidade: unidade "texto"
Para um fluxo use etapas e para um ciclo use ciclo, com os itens na ordem pedida. Para gráfico
de barras use grafico, com os números exatamente como pedidos (NUMERO sem unidade, ponto
decimal). Exemplo:
etapas {
  titulo "Do pedido ao slide"
  item "Pedido" "O estudante escreve o que quer"
  item "Compilador" "Calcula posição e fonte"
}"""


def strip_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:\w+)?\s*(.*?)```", text, re.S)
    return (match.group(1) if match else text).strip()


def check_svg(text: str) -> str | None:
    """Erro de XML/SVG ou None. Não olha geometria (isso é do conferidor)."""
    if "<svg" not in text:
        return "a resposta não contém <svg>"
    try:
        root = ET.fromstring(text[text.index("<svg"):text.rindex("</svg>") + 6])
    except (ValueError, ET.ParseError) as exc:
        return f"SVG inválido: {exc}"
    return None if root.tag.endswith("svg") else "a raiz não é <svg>"


RAW: list[tuple[str, str]] = []  # (sufixo, texto cru) da última execução, para auditoria


def run_a(model, spec, seed):
    w, h = SIZES[spec["tipo"]]
    system, user = SYSTEM_A.format(w=w, h=h), spec["pedido"]
    reply, error = "", None
    for attempt in range(2):
        reply = strip_fence(model.generate(system, user, temperature=TEMPERATURE, seed=seed,
                                           context={"stage": "A", "attempt": attempt}))
        RAW.append((f"tentativa{attempt}.txt", reply))
        error = check_svg(reply)
        if not error:
            return reply[reply.index("<svg"):reply.rindex("</svg>") + 6], attempt, None
        user = f"{spec['pedido']}\n\nSua resposta anterior falhou: {error}. Responda só com o SVG."
    return None, 1, error


def run_b(model, spec, seed):
    user = spec["pedido"]
    error = None
    for attempt in range(2):
        block = strip_fence(model.generate(SYSTEM_B, user, temperature=TEMPERATURE, seed=seed,
                                           context={"stage": "B", "attempt": attempt}))
        RAW.append((f"tentativa{attempt}.txt", block))
        try:
            deck = parse_alto(f'deck "teste" {{\n{block}\n}}')
            if len(deck.slides) != 1:
                raise ValueError("escreva exatamente um bloco")
            result = slide_svg(deck.slides[0])
            if result is None:
                raise ValueError("use etapas ou grafico")
            return result.svg, attempt, None, block
        except Exception as exc:  # erro do analisador ou do compilador vira reparo
            error = str(exc).splitlines()[0][:300]
            user = f"{spec['pedido']}\n\nSeu bloco anterior falhou: {error}. Corrija e responda só com o bloco."
    return None, 1, error, None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*", help="Pedidos a rodar (padrão: todos)")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--provider", choices=["openai", "ollama"], default="openai")
    parser.add_argument("--model", help="Padrão: gpt-4.1-mini (openai) ou qwen3:4b-instruct (ollama)")
    args = parser.parse_args()
    root = project_root()
    if Path.cwd().resolve() != root.resolve():
        raise SystemExit("Execute a partir de code/slidedsl.")
    load_local_settings()
    specs = json.loads((root / "experiments/svg/pedidos.json").read_text("utf-8"))["pedidos"]
    if args.ids:
        specs = [s for s in specs if s["id"] in args.ids]
    out = (args.out or root / "outputs/sem3/teste_svg" / datetime.now().strftime("%Y%m%d-%H%M")).resolve()
    if out.exists():
        raise SystemExit("A pasta de saída já existe; escolha outra.")
    name = args.model or (MODEL if args.provider == "openai" else "qwen3:4b-instruct")
    rows, models = [], {}
    for cond in ("A", "B"):
        (out / cond).mkdir(parents=True)
        client = (OpenAITextModel(name, output_tokens=6000) if args.provider == "openai"
                  else OllamaTextModel(name, output_tokens=6000))
        models[cond] = RecordedModel(client, out / cond / "uso", max_calls=200)
    gabarito = {}
    for spec in specs:
        for seed in args.seeds:
            fname = f"{spec['id']}_s{seed}.svg"
            gabarito[fname] = spec["gabarito"]
            for cond in ("A", "B"):
                spent = sum(m.summary()["known_cost_usd"] or 0 for m in models.values())
                if spent > LIMIT_USD:
                    raise SystemExit(f"Teto de US$ {LIMIT_USD} atingido ({spent:.4f}).")
                RAW.clear()
                if cond == "A":
                    svg, repairs, error = run_a(models[cond], spec, seed)
                    block = None
                else:
                    svg, repairs, error, block = run_b(models[cond], spec, seed)
                for suffix, text in RAW:
                    (out / cond / "cru").mkdir(exist_ok=True)
                    (out / cond / "cru" / fname.replace(".svg", f".{suffix}")).write_text(text, "utf-8")
                if svg:
                    (out / cond / fname).write_text(svg, "utf-8")
                if block:
                    (out / cond / fname.replace(".svg", ".slda")).write_text(block, "utf-8")
                rows.append({"condicao": cond, "pedido": spec["id"], "tipo": spec["tipo"],
                             "seed": seed, "gerou_svg": bool(svg), "reparos": repairs,
                             "erro": error, "arquivo": fname})
                print(f"{cond} {fname}: {'ok' if svg else 'FALHOU ' + str(error)}")
    (out / "gabarito.json").write_text(json.dumps(gabarito, ensure_ascii=False, indent=2), "utf-8")
    checks = {}
    for cond in ("A", "B"):
        target = out / cond / "conferencia.json"
        subprocess.run(["node", "scripts/conferir_svg.mjs", str(out / cond), str(out / "gabarito.json"),
                        str(target)], check=True)
        checks[cond] = json.loads(target.read_text("utf-8"))
    for row in rows:
        verdict = checks[row["condicao"]].get(row["arquivo"])
        row["correto"] = bool(verdict and verdict["correto"])
        row["problemas"] = verdict["problemas"] if verdict else ["sem SVG"]
    summary = {}
    for cond in ("A", "B"):
        mine = [r for r in rows if r["condicao"] == cond]
        usage = models[cond].summary()
        summary[cond] = {"diagramas": len(mine), "corretos": sum(r["correto"] for r in mine),
                         "custo_usd": usage["known_cost_usd"], "chamadas": usage["calls"],
                         "uso_desconhecido": usage["unknown_usage_calls"]}
    report = {"provedor": args.provider, "modelo": name, "temperatura": TEMPERATURE, "seeds": args.seeds,
              "resumo": summary, "linhas": rows}
    (out / "resultado.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    for cond, s in summary.items():
        print(f"{cond}: {s['corretos']}/{s['diagramas']} corretos, US$ {s['custo_usd'] or 0:.4f}, {s['chamadas']} chamadas")
    print(f"Resultados em {out}")


if __name__ == "__main__":
    main()
