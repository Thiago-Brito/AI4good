"""Experimento PAGO, fora do pytest: 3 temas × A/B/B+img, teto global US$ 1.

Executar da raiz: .venv/Scripts/python.exe scripts/comparar_alto_vs_sld.py
Usa somente o .env local via carregador existente; não imprime configuração privada.
"""

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from statistics import mean
import shutil
import time

import httpx

from slidedsl.alto_compile import build_alto
from slidedsl.alto_generation import create_presentation
from slidedsl.compiler import compile_ir, inspect_pptx
from slidedsl.generation import generate_file, repair_prompt
from slidedsl.ir_preview import contact_sheet, render_deck
from slidedsl.https import system_tls_context
from slidedsl.local_settings import load_local_settings
from slidedsl.model_usage import RecordedModel, pricing_for
from slidedsl.models.base import GenerationLimitError
from slidedsl.models.openai_model import OpenAITextModel
from slidedsl.paths import project_root
from slidedsl.pipeline import validate_source
from slidedsl.repetition import THRESHOLD, repetition_pairs
from slidedsl.layout_metrics import content_occupancy

MODEL = "gpt-4.1-mini"
CONDITIONS = ("A", "B", "B+img", "B-lote")
THEMES = ("fotossintese", "git", "energia_solar", "historia_internet")
LIMIT_USD = 1.0
DIAGNOSTIC_TYPES = {
    "D001": "fora_da_area", "D002": "contraste", "D003": "hierarquia",
    "D004": "alinhamento", "D005": "proximidade", "D006": "hierarquia",
    "D007": "densidade", "D008": "sobreposicao_oclusao", "D009": "dimensao",
    "D010": "overflow", "A010": "layout", "A017": "repeticao",
}


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), "utf-8")


class Budget:
    """Soma execuções e reserva um teto conservador para chamadas sem uso."""

    def __init__(self, price, limit=LIMIT_USD):
        if price is None:
            raise ValueError("Tarifa datada ausente; experimento não iniciado.")
        self.price, self.limit = price, limit
        self.summaries = {}
        self.reserve_per_call = {}
        self.unpriced_calls = {}
        self.ledger_path = None

    @property
    def spent(self):
        return round(sum(s["known_cost_usd"] for s in self.summaries.values()), 10)

    @property
    def upper_bound(self):
        return self.spent + sum(
            count * self.reserve_per_call.get(folder, 0)
            for folder, count in self.unpriced_calls.items()
        )

    def persist(self):
        if self.ledger_path:
            save_json(self.ledger_path, {
                "limit_usd": self.limit, "known_cost_usd": self.spent,
                "cost_usd": None if any(self.unpriced_calls.values()) else self.spent,
                "cost_upper_bound_usd": self.upper_bound,
                "unpriced_calls": {str(k): v for k, v in self.unpriced_calls.items()},
                "reservation_per_call_usd": {str(k): v for k, v in self.reserve_per_call.items()},
            })

    def note(self, folder, summary):
        self.summaries[Path(folder)] = dict(summary)
        records = Path(folder) / "uso_chamadas.jsonl"
        if records.exists():
            self.unpriced_calls[Path(folder)] = sum(
                json.loads(line)["cost_usd"] is None
                for line in records.read_text("utf-8").splitlines()
            )
        else:
            pending = int((Path(folder) / "uso_em_andamento.json").exists())
            self.unpriced_calls[Path(folder)] = max(0, summary["unknown_usage_calls"] - pending)
        self.persist()
        # O callback inicial registra uma chamada pendente antes do HTTP.
        if not (Path(folder) / "uso_em_andamento.json").exists():
            self.check()

    def check(self):
        if self.upper_bound >= self.limit:
            raise GenerationLimitError("Orçamento global atingido; experimento interrompido.")
        if any(count and folder not in self.reserve_per_call
               for folder, count in self.unpriced_calls.items()):
            raise GenerationLimitError("Uso/custo desconhecido sem reserva; inferências bloqueadas.")

    def reservation(self, system, user, output_tokens, schema):
        # Limite superior conservador: bytes UTF-8 cobrem tokens de texto;
        # margem cobre envelopes de chat/schema. Não é medição de tokenização.
        incoming_bound = len((system + user + json.dumps(schema)).encode("utf-8")) + 4096
        return (
            incoming_bound * self.price["input"] + output_tokens * self.price["output"]
        ) / 1_000_000

    def before(self, system, user, output_tokens, schema, folder=None):
        self.check()
        reserve = self.reservation(system, user, output_tokens, schema)
        previous_reserve = self.reserve_per_call.get(Path(folder), 0) if folder else 0
        extension = self.unpriced_calls.get(Path(folder), 0) * max(0, reserve - previous_reserve) if folder else 0
        if self.upper_bound + extension + reserve > self.limit:
            raise GenerationLimitError("Saldo insuficiente para reservar a próxima chamada.")
        if folder is not None:
            folder = Path(folder)
            self.reserve_per_call[folder] = max(reserve, self.reserve_per_call.get(folder, 0))
            self.persist()


class ExperimentModel(OpenAITextModel):
    def __init__(self, budget, audit_folder=None, experiment_seed=42, **kwargs):
        super().__init__(MODEL, **kwargs)
        self.budget = budget
        self.audit_folder = audit_folder
        self.experiment_seed = experiment_seed

    def generate(self, system_prompt, user_prompt, **kwargs):
        self.budget.before(
            system_prompt, user_prompt, self.output_tokens, kwargs.get("response_schema"),
            folder=self.audit_folder,
        )
        # Congela inclusive chamadas auxiliares e reparos nas três condições.
        kwargs.update(temperature=0.2, seed=self.experiment_seed)
        return super().generate(system_prompt, user_prompt, **kwargs)


def diagnostic_counts(diagnostics):
    by_code, by_type = {}, {}
    for d in diagnostics:
        severity = d["severity"]
        if severity not in {"ERRO", "AVISO"}:
            continue
        for target, key in (
            (by_code, d["code"]),
            (by_type, DIAGNOSTIC_TYPES.get(d["code"], d["code"])),
        ):
            target.setdefault(key, {"ERRO": 0, "AVISO": 0})[severity] += 1
    return by_code, by_type


def scene_metrics(ir):
    if ir is None:
        return {"slides_delivered": 0, "images": 0, "visible_characters": None,
                "repetition_pairs": None, "repetition_max_jaccard": None}, []
    blocks = [[e.text for e in s.elements if e.type == "text" and e.text
               and e.role != "titulo" and (e.font_size or 24) >= 16] for s in ir.slides]
    pairs = repetition_pairs(blocks)
    return {
        "slides_delivered": len(ir.slides),
        "images": sum(e.type == "image" for s in ir.slides for e in s.elements),
        "visible_characters": sum(len(e.text or "") for s in ir.slides for e in s.elements
                                  if e.type == "text"),
        "repetition_pairs": len(pairs),
        "repetition_max_jaccard": max((p["jaccard"] for p in pairs), default=0),
    }, pairs


def execute(condition, theme, brief_path, folder, budget, client=None, seed=42):
    folder.mkdir()
    brief = brief_path.read_text("utf-8")
    frozen = folder / "brief.txt"
    # Os bytes enviados por generate_file devem coincidir com a string do Alto,
    # inclusive no Windows, onde write_text converteria LF em CRLF.
    frozen.write_bytes(brief.encode("utf-8"))
    model = ExperimentModel(budget, audit_folder=folder,
                            experiment_seed=seed,
                            output_tokens={"A": 7000, "B-lote": 6000}.get(condition, 2200), client=client)
    started = time.monotonic()
    error, diagnostics, ir, valid, repairs = None, [], None, False, 0
    pptx = folder / "apresentacao.pptx"
    def callback(summary):
        budget.note(folder, summary)

    stop = False
    try:
        if condition == "A":
            tracked = RecordedModel(model, folder, max_calls=3, on_usage=callback)
            metadata = generate_file(
                provider="openai", model=MODEL, prompt_file=frozen,
                out=folder / "apresentacao.sld", repair_max=2,
                temperature=0.2, seed=seed, adapter=tracked,
            )
            repairs = metadata["repair_rounds"]
            result = validate_source((folder / "apresentacao.sld").read_text("utf-8"))
            valid, ir = result.success(), result.ir
            diagnostics = [d.model_dump() for d in result.diagnostics]
            if valid:
                compile_ir(ir, pptx)
        else:
            report = create_presentation(
                brief, folder, model, n_slides=5, research_provider=None,
                candidates=1, repair_max=1, images=condition == "B+img", batch=condition == "B-lote",
                temperature=0.2, seed=seed, max_calls=16, preview=False,
                allow_without_facts=True, on_usage=callback,
                progress=lambda message: print(f"{theme}/{condition}: {message}", flush=True),
            )
            valid = report["valid"]
    except Exception as exc:
        error = {"type": type(exc).__name__, "message": str(exc)}
        stop = isinstance(exc, GenerationLimitError)
        if hasattr(exc, "diagnostics"):
            diagnostics = [d.model_dump() for d in exc.diagnostics]
        else:
            diagnostics = [{"code": "MODEL_ERROR", "severity": "ERRO", "message": str(exc)}]
    # Reabre os artefatos finais também no caso de compilação/validação malsucedida.
    if condition != "A" and (folder / "apresentacao.slda").exists():
        built = build_alto((folder / "apresentacao.slda").read_text("utf-8"))
        ir = built.validation.ir if built.validation else None
        diagnostics = [d.model_dump() for d in built.all_diagnostics]
        candidates_path = folder / "candidatos.json"
        if candidates_path.exists():
            candidates = json.loads(candidates_path.read_text("utf-8"))
            diagnostics += [d for c in candidates for d in c["diagnostics"]
                            if d["code"] in {"A017", "A018", "A020", "A022"}]
        valid = valid and built.success()
    usage_path = folder / "uso.json"
    usage = json.loads(usage_path.read_text("utf-8")) if usage_path.exists() else {}
    records_path = folder / "uso_chamadas.jsonl"
    records = [json.loads(line) for line in records_path.read_text("utf-8").splitlines()
               ] if records_path.exists() else []
    if condition != "A":
        repairs = sum((r.get("attempt") or 0) > 0 for r in records)
    elif error and not (folder / "apresentacao.meta.json").exists():
        repairs = max(0, len(records) - 1)
    metrics, pairs = scene_metrics(ir)
    metrics["slides_in_ir"] = metrics["slides_delivered"]
    metrics["slides_delivered"] = 0
    metrics["images_in_ir"] = metrics["images"]
    metrics["images"] = 0  # incluídas = objetos no PPTX efetivamente exportado
    save_json(folder / "repeticao.json", {"threshold": THRESHOLD, "pairs": pairs})
    save_json(folder / "diagnosticos.json", diagnostics)
    preview_error = None
    if ir is not None:
        save_json(folder / "ir.json", ir.model_dump())
        save_json(folder / "design_audit.json", {
            "body_minimum_pt": 16, "label_minimum_pt": 20, "title_minimum_pt": 32,
            "body_violations": [e.id for s in ir.slides for e in s.elements
                                if e.type == "text" and e.role == "corpo" and e.font_size < 16],
            "content_occupancy": [{"slide": s.number, "fraction": content_occupancy(s)} for s in ir.slides],
            "photos": [{"slide": s.number, "file": e.file} for s in ir.slides
                       for e in s.elements if e.type == "image"],
        })
        try:
            paths = render_deck(ir, folder / "pngs", scale=0.75)
            if paths:
                contact_sheet(paths, folder / "contato.png")
        except Exception as exc:
            preview_error = type(exc).__name__ + ": " + str(exc)
    codes, types = diagnostic_counts(diagnostics)
    inspection = inspect_pptx(pptx) if pptx.exists() else None
    if inspection:
        save_json(folder / "inspecao_pptx.json", inspection)
        metrics["slides_delivered"] = inspection["slide_count"]
        metrics["images"] = inspection["image_objects"]
    row = {
        "condition": condition, "theme": theme, "model": MODEL, "temperature": 0.2,
        "seed": seed, "brief_sha256": hashlib.sha256(brief.encode("utf-8")).hexdigest(),
        "calls": usage.get("calls", 0),
        "input_tokens": usage.get("known_input_tokens") if not usage.get("unknown_usage_calls", 1) else None,
        "output_tokens": usage.get("known_output_tokens") if not usage.get("unknown_usage_calls", 1) else None,
        "cached_input_tokens": sum(r["cached_input_tokens"] for r in records)
        if records and all(r["cached_input_tokens"] is not None for r in records) else None,
        "cost_usd": usage.get("cost_usd"), "known_cost_usd": usage.get("known_cost_usd"),
        "unknown_usage_calls": usage.get("unknown_usage_calls"),
        "known_input_tokens": usage.get("known_input_tokens"),
        "known_output_tokens": usage.get("known_output_tokens"),
        "known_cached_input_tokens": usage.get("known_cached_input_tokens"),
        "generation_seconds": round(time.monotonic() - started, 3),
        "valid": valid, "repair_rounds": repairs,
        "errors": sum(d["severity"] == "ERRO" for d in diagnostics),
        "warnings": sum(d["severity"] == "AVISO" for d in diagnostics),
        "diagnostics_by_code": codes, "diagnostics_by_type": types,
        "slides_requested": 5, **metrics,
        "pptx_generated": pptx.exists(), "pptx_slides": inspection["slide_count"] if inspection else 0,
        "preview_renderer": "ir_preview/Pillow (IR, não renderiza PPTX)" if ir else None,
        "preview_error": preview_error, "error": error, "folder": folder.name,
    }
    save_json(folder / "metricas.json", row)
    return row, stop


def aggregate(rows):
    groups = {}
    for condition in CONDITIONS:
        selected = [r for r in rows if r["condition"] == condition]
        if not selected:
            continue
        sums = {}
        for key in ("calls", "input_tokens", "output_tokens", "cached_input_tokens", "cost_usd",
                    "errors", "warnings", "repair_rounds", "generation_seconds"):
            sums[key] = sum(r[key] for r in selected) if all(r[key] is not None for r in selected) else None
        delivered = sum(r["pptx_slides"] for r in selected if r["valid"] and r["pptx_generated"])
        groups[condition] = {
            "runs": len(selected), "valid": sum(r["valid"] for r in selected),
            "pptx": sum(r["pptx_generated"] for r in selected), "valid_slides": delivered,
            "totals": sums,
            "means": {key: value / len(selected) if value is not None else None for key, value in sums.items()},
            "cost_per_valid_slide": sums["cost_usd"] / delivered
            if delivered and sums["cost_usd"] is not None else None,
            "mean_images": mean(r["images"] for r in selected),
        }
    a_cost = groups.get("A", {}).get("totals", {}).get("cost_usd")
    for condition in CONDITIONS[1:]:
        if condition in groups:
            cost = groups[condition]["totals"]["cost_usd"]
            groups[condition]["saving_vs_A"] = 1 - cost / a_cost if a_cost and cost is not None else None
    return groups


def number(value, digits=6):
    return "desconhecido" if value is None else f"{value:.{digits}f}"


def repetition_statistics(rows):
    """Média e faixa de lotes de quatro temas, um lote por seed; falhas têm custo."""
    result = {}
    for condition in CONDITIONS:
        selected = [r for r in rows if r['condition'] == condition]
        batches = []
        for seed in sorted({r['seed'] for r in selected}):
            batch = [r for r in selected if r['seed'] == seed]
            cost = sum(r['cost_usd'] for r in batch) if all(r['cost_usd'] is not None for r in batch) else None
            slides = sum(r['pptx_slides'] for r in batch if r['valid'] and r['pptx_generated'])
            batches.append(dict(seed=seed, runs=len(batch), cost_usd=cost,
                input_tokens=sum(r['input_tokens'] for r in batch) if all(r['input_tokens'] is not None for r in batch) else None,
                output_tokens=sum(r['output_tokens'] for r in batch) if all(r['output_tokens'] is not None for r in batch) else None,
                cached_input_tokens=sum(r['cached_input_tokens'] for r in batch) if all(r['cached_input_tokens'] is not None for r in batch) else None,
                valid_rate=sum(r['valid'] for r in batch) / len(batch),
                cost_per_valid_slide=cost / slides if cost is not None and slides else None))
        if batches:
            result[condition] = {'batches': batches, 'statistics': {key: {
                'mean': mean(b[key] for b in batches), 'min': min(b[key] for b in batches),
                'max': max(b[key] for b in batches)} if all(b[key] is not None for b in batches) else None
                for key in ('cost_usd', 'input_tokens', 'output_tokens', 'cached_input_tokens', 'valid_rate', 'cost_per_valid_slide')}}
    return result


def write_results(output, rows, budget, aborted):
    summary = aggregate(rows)
    repeated = repetition_statistics(rows)
    save_json(output / "resultados.json", {
        "protocol": "docs/PLANO_CODEX_COMPARACAO.md", "model": MODEL,
        "temperature": 0.2, "seeds": sorted({r['seed'] for r in rows}), "limit_usd": budget.limit,
        "known_total_cost_usd": budget.spent,
        "total_cost_usd": None if any(budget.unpriced_calls.values()) else budget.spent,
        "total_cost_upper_bound_usd": budget.upper_bound, "aborted": aborted,
        "summary": summary, "repetition_statistics": repeated, "runs": rows,
    })
    if rows:
        with (output / "resultados.csv").open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                             for k, v in row.items()} for row in rows)
    lines = [
        "# Comparação Alto × SlideDSL detalhada", "",
        "Protocolo e fontes registrados em `refs/COMPARACAO_ALTO_SLD.md`.",
        f"Modelo {MODEL}; temperatura 0,2; seeds {sorted({r['seed'] for r in rows})}, fixas em todas as chamadas de cada execução.",
        "Mesmos bytes do brief em cada condição; hashes registrados. Sem pesquisa factual.",
        "A: generate_file, até dois reparos; B/B+img: um candidato, um reparo por slide.",
        "B mantém extração padrão de tópicos do pedido. B+img só consulta Commons.",
        "Limites de saída: A 7.000 tokens/chamada, B/B+img 2.200, B-lote 6.000 na chamada em lote.",
        "B-lote: roteiro + uma chamada para todos os slides; reparo individual só do slide reprovado.",
        "Todos os reparos e chamadas auxiliares entram no uso; cache é parte da entrada.",
        f"Gasto conhecido total: **US$ {number(budget.spent, 8)}**, teto US$ {budget.limit:.2f}.",
        f"Teto conservador incluindo tentativas sem uso: **US$ {number(budget.upper_bound, 8)}**; não é gasto medido.",
        "Custo total é desconhecido se houver tentativa sem uso; sua reserva nunca é contabilizada como custo zero.",
        "Se houver `custos_anteriores.json`, o total global inclui tentativas anteriores e o diagnóstico de rede; a tabela compara só o novo lote.",
        f"Interrupção por orçamento/uso desconhecido: {aborted}.", "",
        "## Totais por condição", "",
        "| Condição | Execuções | Entrada | Saída | Cache | USD | Válidos | PPTX | ERRO/AVISO | USD/slide válido |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for condition, group in summary.items():
        t = group["totals"]
        lines.append(f"| {condition} | {group['runs']} | {t['input_tokens']} | {t['output_tokens']} | "
                     f"{t['cached_input_tokens']} | {number(t['cost_usd'])} | {group['valid']} | "
                     f"{group['pptx']} | {t['errors']}/{t['warnings']} | {number(group['cost_per_valid_slide'])} |")
    lines += ["", "## Médias por execução", "",
              "| Condição | Chamadas | Entrada | Saída | USD | Segundos | Reparos |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for condition, group in summary.items():
        m = group["means"]
        lines.append(f"| {condition} | {number(m['calls'], 2)} | {number(m['input_tokens'], 2)} | "
                     f"{number(m['output_tokens'], 2)} | {number(m['cost_usd'])} | "
                     f"{number(m['generation_seconds'], 2)} | {number(m['repair_rounds'], 2)} |")
    lines += ["", "Economia de custo total, fórmula `1 - custo_condição / custo_A` (negativo = aumento):"]
    for condition in CONDITIONS[1:]:
        if condition in summary:
            saving = summary[condition]["saving_vs_A"]
            lines.append(f"- {condition}: {number(saving * 100 if saving is not None else None, 2)}%.")
    lines += ["", "## Valores individuais", "",
              "| Tema/condição | Chamadas | Entrada/saída/cache | USD | Válido | ERRO/AVISO | Slides/PPTX | Imagens | Caracteres | Repetições |",
              "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['theme']}/{r['condition']} | {r['calls']} | {r['input_tokens']}/{r['output_tokens']}/{r['cached_input_tokens']} | "
                     f"{number(r['cost_usd'])} | {r['valid']} | {r['errors']}/{r['warnings']} | "
                     f"{r['slides_delivered']}/{'sim' if r['pptx_generated'] else 'não'} | {r['images']} | "
                     f"{r['visible_characters']} | {r['repetition_pairs']} |")
    lines += ["", "## Diagnósticos finais por execução", ""]
    for r in rows:
        lines.append(f"- {r['folder']}: `{json.dumps(r['diagnostics_by_type'], ensure_ascii=False)}`; "
                     f"falha: `{json.dumps(r['error'], ensure_ascii=False)}`.")
    lines += ["", "## Renderização e observações visuais", "",
              "PPTX: renderer PptxGenJS compartilhado por todas as condições; ZIP inspecionado.",
              "PNGs: `ir_preview/Pillow`, derivados da IR, em `<execução>/pngs/`; folhas em `<execução>/contato.png`.",
              "Essas prévias não renderizam nem comprovam a aparência do PPTX final no Office.",
              "Sem IR válida não há PNGs: essa ausência é falha observada, não pontuação visual zero.",
              "Inspeção visual qualitativa do executor registrada após a geração; avaliação humana cega não realizada.",
              "", "## Limitações", "",
              f"{len({r['theme'] for r in rows})} temas, {len({r['seed'] for r in rows})} repetições por condição, um modelo; não generalizar nem inferir significância.",
              "Os briefs são iguais, mas prompts de sistema, schemas, limites de saída, contextos e reparos diferem.",
              "Portanto, esta comparação mede os fluxos completos; não isola causalmente só a DSL ou a gramática.",
              "A não tem busca de imagem. B+img depende da rede/licenças/relevância lexical e pode virar tópicos.",
              "Sem fontes factuais e sem avaliação humana de conteúdo: validade sintática não demonstra correção ou beleza.",
              "Jaccard usa tokens normalizados, limiar 0,72 e mínimo quatro tokens; não mede repetição semântica.",
              "Na escrita usa rótulos/detalhes; na comparação usa blocos de texto da IR, excluindo títulos e fonte <16 pt em todas as condições.",
              "Caracteres contam todo texto visível da IR; slides sem PPTX são cenas planejadas, não slides entregues ao usuário.",
              "Custo por slide válido considera somente slides de PPTX exportados de execuções válidas; inclui custo das falhas no numerador.",
              "Tempos incluem inferência, rede de mídia, validação, compilação e prévias; não isolam latência do modelo.",
              "Diagnósticos da tabela são finais; estados anteriores e reparos permanecem nos arquivos de auditoria.",
              "Seed é parâmetro solicitado, não garantia de determinismo do serviço remoto.", ""]
    lines += ["", "## Média e faixa por repetição (soma dos quatro temas por seed)", "",
              "| Condição | Entrada | Saída | Cache | USD | Taxa válidos | USD/slide válido |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for condition, group in repeated.items():
        values = []
        for key in ('input_tokens', 'output_tokens', 'cached_input_tokens', 'cost_usd', 'valid_rate', 'cost_per_valid_slide'):
            stat = group['statistics'][key]
            digits = 2 if 'tokens' in key or key == 'valid_rate' else 8
            values.append(f"{number(stat['mean'], digits)} ({number(stat['min'], digits)}–{number(stat['max'], digits)})" if stat else 'desconhecido')
        lines.append('| ' + condition + ' | ' + ' | '.join(values) + ' |')
    lines += ['', 'Rodada 1 (n=1): A teve 1/3 válidos; rodada 2, 4/4 sem mudança no caminho de A. '
              'A validade era instável; não atribuir a diferença ao compilador Alto.', '']
    (output / "RELATORIO.md").write_text("\n".join(lines), "utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resume", type=Path, help="Lote interrompido; copia evidências para nova pasta.")
    parser.add_argument("--carry-budget", type=Path, help="Ledger anterior, incluído no mesmo teto global.")
    parser.add_argument("--out", type=Path, help="Nova pasta de resultados dentro de outputs/.")
    parser.add_argument("--limit-usd", type=float, default=LIMIT_USD)
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=CONDITIONS)
    parser.add_argument("--themes", nargs="+", choices=THEMES, default=THEMES)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42])
    args = parser.parse_args()
    root = project_root()
    if Path.cwd().resolve() != root.resolve():
        raise SystemExit("Execute a partir de code/slidedsl.")
    load_local_settings()
    if not 0 < args.limit_usd <= LIMIT_USD:
        raise ValueError("Limite deve ser positivo e não exceder US$ 1.")
    budget = Budget(pricing_for(MODEL), limit=args.limit_usd)
    output = (args.out or (root / "outputs/comparacao_alto_sld" /
                          datetime.now().strftime("%Y%m%d-%H%M"))).resolve()
    if not output.is_relative_to((root / "outputs").resolve()):
        raise ValueError("Saída deve ficar em outputs/.")
    output.mkdir(parents=True, exist_ok=False)
    budget.ledger_path = output / "orcamento.json"
    client = httpx.Client(timeout=300, verify=system_tls_context())
    rows, aborted = [], False
    try:
        if args.carry_budget:
            ledger_path = args.carry_budget.resolve()
            if not ledger_path.is_relative_to((root / "outputs").resolve()):
                raise ValueError("Ledger deve vir de outputs/.")
            ledger = json.loads(ledger_path.read_text("utf-8"))
            budget.reserve_per_call.update({Path(k): v for k, v in ledger["reservation_per_call_usd"].items()})
            for folder in budget.reserve_per_call:
                budget.note(folder, json.loads((folder / "uso.json").read_text("utf-8")))
            save_json(output / "custos_anteriores.json", {
                "source": str(ledger_path), "known_cost_usd": budget.spent,
                "cost_upper_bound_usd": budget.upper_bound,
                "folders": [str(p) for p in budget.reserve_per_call],
            })
        if args.resume:
            source = args.resume.resolve()
            if not source.is_relative_to((root / "outputs/comparacao_alto_sld").resolve()):
                raise ValueError("Retomada deve vir de outputs/comparacao_alto_sld.")
            old = json.loads((source / "resultados.json").read_text("utf-8"))
            save_json(output / "retomada.json", {"source": str(source), "new_api_repetitions": False})
            for previous in old["runs"]:
                target = output / previous["folder"]
                shutil.copytree(source / previous["folder"], target)
                usage = json.loads((target / "uso.json").read_text("utf-8"))
                # Reconstrói o envelope da chamada A interrompida a partir dos
                # bytes efetivamente enviados, preservados nas rodadas anteriores.
                if usage["cost_usd"] is None and previous["condition"] == "A":
                    last = max(target.glob("apresentacao.round*.raw.txt"))
                    round_number = int(last.name.split(".round")[1].split(".")[0])
                    validation = json.loads((target / f"apresentacao.round{round_number}.validation.json").read_text("utf-8"))
                    user = repair_prompt((target / "brief.txt").read_text("utf-8"),
                                         last.read_text("utf-8"), validation["diagnostics"])
                    budget.reserve_per_call[target] = budget.reservation(
                        (root / "prompts/system_dsl.txt").read_text("utf-8"), user, 7000, None
                    )
                budget.note(target, usage)
                previous.update({key: usage.get(key) for key in (
                    "known_input_tokens", "known_output_tokens", "known_cached_input_tokens"
                )})
                if previous["error"] and previous["condition"] == "A":
                    failed = [{"code": "MODEL_ERROR", "severity": "ERRO",
                               "message": "Falha de inferência após a última rodada concluída; custo desconhecido."}]
                    previous["errors"] = 1
                    previous["diagnostics_by_code"], previous["diagnostics_by_type"] = diagnostic_counts(failed)
                    save_json(target / "diagnosticos.json", failed)
                    raw_paths = sorted(target.glob("apresentacao*.raw.txt"))
                    if raw_paths:
                        partial = validate_source(raw_paths[-1].read_text("utf-8"))
                        save_json(target / "ultima_rodada_concluida.validacao.json", partial.report())
                        if partial.ir:
                            save_json(target / "ultima_rodada_concluida.ir.json", partial.ir.model_dump())
                            paths = render_deck(partial.ir, target / "pngs", scale=.75)
                            contact_sheet(paths, target / "contato.png")
                            previous.update(preview_source="última rodada concluída, execução final falhou",
                                            preview_renderer="ir_preview/Pillow (IR parcial, não PPTX)",
                                            slides_in_ir=len(partial.ir.slides))
                save_json(target / "metricas.json", previous)
                rows.append(previous)
        jobs = [(seed, theme, condition) for seed in args.seeds for theme in args.themes for condition in args.conditions]
        for seed, theme, condition in jobs:
                if any(r["theme"] == theme and r["condition"] == condition and r["seed"] == seed for r in rows):
                    continue
                budget.check()
                folder = output / f"{theme}_{condition.replace('+', '_')}_s{seed}"
                row, stop = execute(
                    condition, theme, root / f"experiments/comparacao/briefs/{theme}.txt",
                    folder, budget,
                    client=client, seed=seed,
                )
                rows.append(row)
                print(f"{folder.name}: válido={row['valid']}; custo={row['cost_usd']}; "
                      f"total={budget.spent}", flush=True)
                if stop:
                    aborted = True
                    return 1
    except GenerationLimitError:
        aborted = True
        return 1
    finally:
        client.close()
        write_results(output, rows, budget, aborted)
        print("Relatório:", output / "RELATORIO.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
