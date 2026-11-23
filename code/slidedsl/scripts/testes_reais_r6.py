"""Lote PAGO r6: seis decks novos, sem pesquisa/IA de imagens, teto US$ 0,50.

Executar somente com autorização explícita. --summarize recompõe índice/galeria offline.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

from comparar_alto_vs_sld import Budget, save_json
from slidedsl.alto_compile import build_alto
from slidedsl.alto_generation import create_presentation
from slidedsl.compiler import inspect_pptx
from slidedsl.https import system_tls_context
from slidedsl.ir_preview import _font, contact_sheet, render_deck
from slidedsl.local_settings import load_local_settings
from slidedsl.model_usage import pricing_for
from slidedsl.models.base import GenerationLimitError
from slidedsl.models.openai_model import OpenAITextModel
from slidedsl.paths import project_root

JOBS = [
    ("claro", "energia_solar", "Energia solar residencial para quem pensa em instalar painéis em casa"),
    ("editorial", "reciclagem", "Reciclagem no dia a dia para alunos do ensino médio"),
    ("vibrante", "fotossintese", "Como funciona a fotossíntese, para alunos do 7º ano"),
    ("natural", "horta", "Cuidados básicos com hortas caseiras em apartamento"),
    ("escuro", "git", "Introdução ao Git para estudantes de programação"),
    ("noturno", "internet", "Breve história da internet para adolescentes"),
]


def select_model():
    """Só consulta a configuração em memória; nunca exibe valores do .env."""
    requested = "gpt-5.4-mini"
    if pricing_for(requested):
        return requested, None
    for model in (os.environ.get("SLIDEDSL_OPENAI_MODEL"), "gpt-4.1-mini"):
        if model and pricing_for(model):
            return model, "gpt-5.4-mini sem tarifa configurada; fallback autorizado pelo plano."
    raise ValueError("Sem tarifa datada para o modelo solicitado ou fallback; nenhuma chamada iniciada.")


class PaidModel(OpenAITextModel):
    def __init__(self, model, budget, folder, **kwargs):
        super().__init__(model, **kwargs)
        self.budget, self.folder = budget, folder

    def generate(self, system_prompt, user_prompt, **kwargs):
        self.budget.before(system_prompt, user_prompt, self.output_tokens,
                           kwargs.get("response_schema"), folder=self.folder)
        return super().generate(system_prompt, user_prompt, **kwargs)


def summarize(output):
    data = json.loads((output / "resultados.json").read_text("utf-8"))
    reviews_path = output / "revisoes.json"
    reviews = json.loads(reviews_path.read_text("utf-8")) if reviews_path.exists() else {}
    ledger = json.loads((output / "orcamento.json").read_text("utf-8"))
    lines = ["# Decks reais — rodada 6", "", f"Modelo: {data['model']}. {data['fallback'] or ''}", "",
             "Seis slides por pedido, seed 42, um candidato, até um reparo; pesquisa desligada.",
             "Imagens licenciadas Commons, sem geração de imagens por IA. Prévia IR/Pillow; não Office.", "",
             "| Deck | Estilo | Válido | Fotos | Chamadas | Tokens E/S/cache | USD | PPTX | Folha |",
             "|---|---|---|---:|---:|---|---:|---|---|"]
    tile_height = 830 if any((output / r["folder"] / "ir.json").exists() for r in data["runs"]) else 420
    gallery = Image.new("RGB", (1800, tile_height * 2), "#e2e8f0")
    draw = ImageDraw.Draw(gallery)
    for i, row in enumerate(data["runs"]):
        folder = row["folder"]
        if not (output / folder / "ir.json").exists():
            failure = Image.new("RGB", (800, 450), "#fff7f7")
            note = ImageDraw.Draw(failure)
            note.text((30, 30), f"{row['style']} — SEM DECK", fill="#991b1b", font=_font(21, True, 1))
            note.text((30, 100), "Falha antes da geração dos slides.", fill="black", font=_font(17, False, 1))
            note.text((30, 150), "HTTP 401: autenticação recusada" if "HTTP 401" in (row.get("error") or "")
                      else "Consulte diagnosticos.json", fill="black", font=_font(17, False, 1))
            note.text((30, 230), "Este painel registra a falha; não é um slide gerado.", fill="black", font=_font(14, False, 1))
            failure.save(output / folder / "contato.png")
        usage = row["usage"]
        tokens = "/".join(str(usage.get(k, "?")) for k in
                          ("known_input_tokens", "known_output_tokens", "known_cached_input_tokens"))
        if usage.get("unknown_usage_calls"):
            tokens = f"desconhecidos (parcial {tokens})"
        price = usage.get("cost_usd")
        cost = f"{price:.8f}" if price is not None else "desconhecido"
        pptx = f"[abrir]({folder}/apresentacao.pptx)" if row["valid"] else "—"
        lines.append(f"| {row['theme']} | {row['style']} | {'sim' if row['valid'] else 'não'} | "
                     f"{row['photos']} | {usage.get('calls', 0)} | {tokens} | {cost} | {pptx} | "
                     f"[abrir]({folder}/contato.png) |")
        x, y = (i % 3) * 600, (i // 3) * tile_height
        draw.text((x + 16, y + 10), row["style"], fill="black", font=_font(18, True, 1))
        with Image.open(output / folder / "contato.png") as sheet:
            sheet.thumbnail((584, tile_height - 48))
            gallery.paste(sheet, (x + 8, y + 40))
    lines += ["", f"Gasto conhecido: US$ {ledger['known_cost_usd']:.8f}; "
              f"total exato: {ledger['cost_usd'] if ledger['cost_usd'] is not None else 'desconhecido'}. "
              f"Limite com reservas: US$ {ledger['cost_upper_bound_usd']:.8f} ≤ US$ 0,50.", "",
              "[Galeria dos seis estilos](galeria.png)", "", "## Inspeção visual", ""]
    for row in data["runs"]:
        lines += [f"### {row['style']} — {row['theme']}", "",
                  reviews.get(row["style"], "Aguardando inspeção visual; não declarar qualidade validada."), ""]
        if row.get("error"):
            lines += [f"Falha registrada: {row['error']}", ""]
    lines += ["Sem pesquisa factual: conteúdo não foi verificado contra fontes. Seed não garante determinismo remoto.",
              "Validade estrutural/editabilidade e inspeção do executor não equivalem a avaliação humana cega ou Office.", ""]
    (output / "INDICE.md").write_text("\n".join(lines), "utf-8")
    gallery.save(output / "galeria.png")


def carry_budget(budget, ledger_path):
    """Retomada acumula o mesmo teto; nunca zera reservas das tentativas anteriores."""
    ledger = json.loads(ledger_path.read_text("utf-8"))
    budget.reserve_per_call.update({Path(k): v for k, v in ledger["reservation_per_call_usd"].items()})
    for folder in budget.reserve_per_call:
        budget.note(folder, json.loads((folder / "uso.json").read_text("utf-8")))
    if budget.upper_bound + 1e-9 < ledger["cost_upper_bound_usd"]:
        raise ValueError("Retomada reduziria a reserva anterior; execução bloqueada.")


def execute(output, previous_ledger=None):
    load_local_settings()
    model_name, fallback = select_model()
    budget = Budget(pricing_for(model_name), limit=.50)
    output.mkdir(parents=True, exist_ok=False)
    budget.ledger_path = output / "orcamento.json"
    if previous_ledger:
        carry_budget(budget, previous_ledger)
    budget.persist()
    data = dict(model=model_name, fallback=fallback, seed=42, slides=6,
                research=False, image_source="livres", ai_images=False,
                previous_ledger=str(previous_ledger) if previous_ledger else None, runs=[])
    save_json(output / "resultados.json", data)
    (output.parent / "ULTIMO.txt").write_text(output.relative_to(project_root()).as_posix(), "utf-8")
    print(f"Modelo selecionado: {model_name}; teto global US$ 0,50.", flush=True)
    with httpx.Client(timeout=300, verify=system_tls_context()) as client:
        for number, (style, theme, request) in enumerate(JOBS, 1):
            folder = output / f"{number:02d}_{style}_{theme}"
            folder.mkdir()
            # Estimativa explícita antes do deck; cada chamada também precisa reservar saldo.
            estimate = 10 * budget.reservation("x" * 8000, request, 2200, None)
            row = dict(style=style, theme=theme, folder=folder.name, valid=False,
                       photos=0, error=None, estimate_usd=estimate, usage={})
            try:
                budget.check()
                if budget.upper_bound + estimate > budget.limit:
                    raise GenerationLimitError("Deck não iniciado: estimativa excede saldo global.")
                adapter = PaidModel(model_name, budget, folder, output_tokens=2200, client=client)
                report = create_presentation(
                    request, folder, adapter, n_slides=6, theme=style, candidates=1,
                    repair_max=1, max_calls=16, images=True, image_source="livres",
                    research_provider=None, allow_without_facts=True, preview=False,
                    seed=42, temperature=.2, on_usage=lambda usage, f=folder: budget.note(f, usage),
                    progress=lambda message, s=style: print(f"{s}: {message}", flush=True),
                )
                row["valid"] = report["valid"] and (folder / "apresentacao.pptx").exists()
            except Exception as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
            usage_path = folder / "uso.json"
            if usage_path.exists():
                row["usage"] = json.loads(usage_path.read_text("utf-8"))
                budget.note(folder, row["usage"])
            else:
                # Deck não iniciado: estado distinto de tentativa com uso ausente.
                row["usage"] = dict(calls=0, started=False, cost_usd=None, known_cost_usd=0,
                                    unknown_usage_calls=0)
                save_json(usage_path, row["usage"])
            diagnostics = []
            if (folder / "apresentacao.slda").exists():
                built = build_alto((folder / "apresentacao.slda").read_text("utf-8"))
                diagnostics = [d.model_dump() for d in built.all_diagnostics]
                if built.validation and built.validation.ir:
                    ir = built.validation.ir
                    save_json(folder / "ir.json", ir.model_dump())
                    contact_sheet(render_deck(ir, folder / "pngs", .6), folder / "contato.png")
            if row["valid"]:
                inspection = inspect_pptx(folder / "apresentacao.pptx")
                row["photos"] = inspection["image_objects"]
                row["valid"] = inspection["slide_count"] == 6
            if row["error"]:
                diagnostics.append(dict(code="RUN_ERROR", severity="ERRO", message=row["error"]))
            save_json(folder / "diagnosticos.json", diagnostics)
            if not (folder / "contato.png").exists():
                sheet = Image.new("RGB", (800, 450), "white")
                ImageDraw.Draw(sheet).text((30, 30), f"{style}: falha, sem slides gerados", fill="black")
                sheet.save(folder / "contato.png")
            data["runs"].append(row)
            save_json(output / "resultados.json", data)
            summarize(output)
            print(f"{style}: valido={row['valid']}; chamadas={row['usage'].get('calls', 0)}; "
                  f"conhecido={budget.spent:.8f}; reservado={budget.upper_bound:.8f}", flush=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summarize", type=Path)
    parser.add_argument("--carry-budget", type=Path, help="Ledger anterior incluído no mesmo teto de US$ 0,50.")
    args = parser.parse_args()
    if args.summarize:
        summarize(args.summarize)
    else:
        execute(project_root() / "outputs/testes_reais" / datetime.now().strftime("%Y%m%d-%H%M"),
                args.carry_budget)


if __name__ == "__main__":
    main()
