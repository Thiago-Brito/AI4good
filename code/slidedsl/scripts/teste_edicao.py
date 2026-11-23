"""Teste de edição localizada de um slide na SlideDSL Alto (TCC, 23/11/2026).

1. Gera 4 decks base localmente (Qwen3 4B via Ollama, dossiês fixos, 6 slides, semente 11).
2. Em cada deck aplica, no slide 3:
   - 3 edições por IA (`refazer_slide`): texto mais curto; troca para comparação; linguagem simples;
   - 3 edições determinísticas (`ajustar_alto`): tema, mover para a posição 5, excluir.
3. Mede: validade após a edição, localidade (fonte fora do bloco e IR dos demais slides idênticas),
   tipo resultante, tokens e tempo (RecordedModel), comparados com o custo de gerar o deck base.

Retomável: decks base e edições já feitos são reaproveitados. Uso:
    .venv\\Scripts\\python scripts\\teste_edicao.py
"""

from __future__ import annotations

import csv
import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REQUESTS = ["solar_detalhado", "git_detalhado", "agua_detalhado", "sono_detalhado"]
AI_EDITS = {
    "texto_curto": "Reescreva este slide com frases mais curtas e diretas, mantendo o assunto.",
    "virar_comparacao": "Transforme este slide em uma comparação entre duas opções do mesmo assunto.",
    "linguagem_simples": "Adapte a linguagem deste slide para alunos do ensino fundamental.",
}
DET_EDITS = {"tema_escuro": {"tema": "escuro"}, "mover_para_5": {"mover_para": 5},
             "excluir": {"excluir": True}}
SLIDE = 3
OUT = ROOT / "outputs" / "teste_edicao"
# Rodada: v2 = antes da restrição de tipo em refazer_slide; v3 = depois (23/11/2026).
RODADA = sys.argv[1] if len(sys.argv) > 1 else "v2"
EDITS = OUT / ("edicoes" if RODADA == "v2" else f"edicoes_{RODADA}")


def ir_slides(source, facts):
    from slidedsl.alto_compile import build_alto

    built = build_alto(source, facts)
    ir = built.validation.ir if built.validation else None
    errors = [d.code for d in built.all_diagnostics if d.severity == "ERRO"]
    if ir is None:
        return None, errors
    slides = []
    for s in ir.model_dump(mode="json")["slides"]:
        s = dict(s)
        s.pop("number", None)
        slides.append(json.dumps(s, sort_keys=True, ensure_ascii=False))
    return slides, errors


def texts(slide_json):
    data = json.loads(slide_json)
    return sorted(e.get("text", "") for e in data.get("elements", []) if e.get("type") == "text")


def outside_span(source, number):
    from slidedsl.alto_edit import slide_spans

    a, b = slide_spans(source)[number - 1]
    return source[:a], source[b:]


SEEDS = (11, 22, 33)


def base_deck(rid, model_factory, dossier_cls):
    """Primeiro deck válido entre as sementes; devolve (pasta, tentativas)."""
    from slidedsl.alto_generation import create_presentation

    request = next(r for r in json.loads((ROOT / "benchmark/format_requests.json").read_text("utf-8"))
                   ["requests"] if r["id"] == rid)
    folder = None
    for attempt, seed in enumerate(SEEDS, 1):
        folder = OUT / "base" / f"{rid}_s{seed}"
        if not (folder / "relatorio.json").exists():
            dossier = dossier_cls.load(ROOT / "benchmark/dossies" / f"{rid}.json")
            folder.parent.mkdir(parents=True, exist_ok=True)
            try:
                create_presentation(request["prompt"], folder, model_factory(), dossier=dossier,
                                    n_slides=6, seed=seed, preview=False, research_provider=None,
                                    max_calls=80)
            except Exception:
                pass
        if (folder / "relatorio.json").exists() and json.loads(
                (folder / "relatorio.json").read_text("utf-8")).get("valid"):
            return folder, attempt
    return folder, len(SEEDS)


def main():
    from slidedsl.alto import parse_alto
    from slidedsl.alto_edit import ajustar_alto, refazer_slide
    from slidedsl.model_usage import RecordedModel
    from slidedsl.models.ollama_model import OllamaTextModel
    from slidedsl.research import Dossier

    def model_factory():
        m = OllamaTextModel("qwen3:4b-instruct", context_length=8192, output_tokens=4096)
        ok, msg = m.available()
        if not ok:
            raise SystemExit(msg)
        return m

    OUT.mkdir(parents=True, exist_ok=True)
    rows_path = OUT / f"edicoes_{RODADA}.csv"
    done = set()
    if rows_path.exists():
        with rows_path.open(encoding="utf-8", newline="") as f:
            done = {(r["deck"], r["edicao"]) for r in csv.DictReader(f)}
    fields = ["deck", "edicao", "tipo_edicao", "status", "valido", "outros_slides_ir_iguais",
              "fonte_fora_igual", "slide_mudou", "tipo_antes", "tipo_depois", "chamadas",
              "tokens_entrada", "tokens_saida", "wall_ms", "base_chamadas", "base_tokens_entrada",
              "base_tokens_saida", "base_wall_ms", "base_valido", "base_tentativas", "tipo_pedido_cumprido", "erro"]
    new_file = not rows_path.exists()
    with rows_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            writer.writeheader()
        for rid in REQUESTS:
            t0 = time.perf_counter()
            try:
                folder, tries = base_deck(rid, model_factory, Dossier)
            except Exception as exc:  # registra e segue
                writer.writerow({"deck": rid, "edicao": "base", "status": "erro",
                                 "erro": f"{type(exc).__name__}: {exc}"[:300]})
                f.flush()
                continue
            report = json.loads((folder / "relatorio.json").read_text("utf-8"))
            custo = json.loads((folder / "custo.json").read_text("utf-8"))["total"]
            source = (folder / "apresentacao.slda").read_text("utf-8")
            facts = Dossier.load(folder / "dossie.json").fact_map()
            base_ir, _ = ir_slides(source, facts)
            base_kinds = [s.kind for s in parse_alto(source).slides]
            common = {"deck": rid, "base_chamadas": custo["calls"],
                      "base_tokens_entrada": custo["input_tokens"],
                      "base_tokens_saida": custo["output_tokens"], "base_wall_ms": custo["wall_ms"],
                      "base_valido": report.get("valid"), "base_tentativas": tries,
                      "tipo_antes": base_kinds[SLIDE - 1]}
            print(f"{rid}: base válido={report.get('valid')} tentativas={tries} "
                  f"em {time.perf_counter() - t0:.0f}s")
            if not report.get("valid"):
                writer.writerow(dict(common, edicao="base", status="base_invalida"))
                f.flush()
                continue
            for name, instruction in AI_EDITS.items():
                if (rid, name) in done:
                    continue
                edit_dir = EDITS / rid / name
                row = dict(common, edicao=name, tipo_edicao="ia")
                try:
                    if edit_dir.exists():
                        edit_dir = edit_dir.with_name(name + f"_{int(time.time())}")
                    tracked = RecordedModel(model_factory(), edit_dir, max_calls=2)
                    new = refazer_slide(source, SLIDE, instruction, facts, tracked)
                    (edit_dir / "apresentacao.slda").write_text(new, "utf-8")
                    slides, errors = ir_slides(new, facts)
                    total = json.loads((edit_dir / "custo.json").read_text("utf-8"))["total"]
                    before, after = outside_span(source, SLIDE), outside_span(new, SLIDE)
                    row.update(
                        status="ok", valido=slides is not None and not errors,
                        outros_slides_ir_iguais=slides is not None and all(
                            slides[i] == base_ir[i] for i in range(len(base_ir)) if i != SLIDE - 1),
                        fonte_fora_igual=before == after,
                        slide_mudou=slides is not None and slides[SLIDE - 1] != base_ir[SLIDE - 1],
                        tipo_depois=parse_alto(new).slides[SLIDE - 1].kind,
                        tipo_pedido_cumprido=(parse_alto(new).slides[SLIDE - 1].kind == "comparacao")
                        if name == "virar_comparacao" else "",
                        chamadas=total["calls"], tokens_entrada=total["input_tokens"],
                        tokens_saida=total["output_tokens"], wall_ms=total["wall_ms"])
                except Exception as exc:
                    (OUT / "erros").mkdir(exist_ok=True)
                    (OUT / "erros" / f"{rid}_{name}.txt").write_text(traceback.format_exc(), "utf-8")
                    row.update(status="erro", erro=f"{type(exc).__name__}: {exc}"[:300])
                writer.writerow(row)
                f.flush()
                print(f"  {name}: {row.get('status')} válido={row.get('valido')} "
                      f"local={row.get('outros_slides_ir_iguais')} tipo={row.get('tipo_depois')}")
            for name, kwargs in DET_EDITS.items():
                if (rid, name) in done:
                    continue
                row = dict(common, edicao=name, tipo_edicao="deterministica", chamadas=0)
                try:
                    t = time.perf_counter()
                    new = ajustar_alto(source, numero=SLIDE, **kwargs)
                    slides, errors = ir_slides(new, facts)
                    wall = round((time.perf_counter() - t) * 1000, 1)
                    kinds = [s.kind for s in parse_alto(new).slides]
                    if name == "tema_escuro":
                        same = slides is not None and all(texts(a) == texts(b)
                                                          for a, b in zip(slides, base_ir))
                    elif name == "mover_para_5":
                        order = base_kinds[:SLIDE - 1] + base_kinds[SLIDE:]
                        order.insert(4, base_kinds[SLIDE - 1])
                        same = kinds == order and slides is not None and sorted(
                            map(lambda s: json.dumps(texts(s)), slides)) == sorted(
                            map(lambda s: json.dumps(texts(s)), base_ir))
                    else:
                        same = slides is not None and len(slides) == len(base_ir) - 1
                    row.update(status="ok", valido=slides is not None and not errors,
                               outros_slides_ir_iguais=same, tipo_depois="",
                               tokens_entrada=0, tokens_saida=0, wall_ms=wall)
                except Exception as exc:
                    row.update(status="erro", erro=f"{type(exc).__name__}: {exc}"[:300])
                writer.writerow(row)
                f.flush()
                print(f"  {name}: {row.get('status')} válido={row.get('valido')} "
                      f"preservado={row.get('outros_slides_ir_iguais')}")


if __name__ == "__main__":
    main()
