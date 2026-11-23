"""Revisões explícitas da r7: reparar slides recusados e revalidar fotos, sem ocultar originais."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil

import httpx

from comparar_alto_vs_sld import Budget, save_json
from testes_reais_r6 import PaidModel, carry_budget
from testes_reais_r7 import evidence, summarize
from slidedsl.alto import parse_alto
from slidedsl.alto_edit import export_edit, refazer_slide, slide_spans, replace_slide
from slidedsl.https import system_tls_context
from slidedsl.local_settings import load_local_settings
from slidedsl.media import photographic_candidate, resolve_asset
from slidedsl.model_usage import RecordedModel, pricing_for
from slidedsl.research import Dossier


def total_usage(parts):
    result = dict(parts[0])
    for key in ("calls", "max_calls", "failed_calls", "known_usage_calls", "unknown_usage_calls",
                "known_input_tokens", "known_output_tokens", "known_cached_input_tokens",
                "known_cost_usd", "text_cost_usd", "image_cost_usd", "image_calls", "unknown_image_cost"):
        result[key] = sum(p.get(key, 0) or 0 for p in parts)
    result["cost_usd"] = sum(p["cost_usd"] for p in parts) if all(p.get("cost_usd") is not None for p in parts) else None
    return result


def filter_photos(source, audit):
    deck = parse_alto(source)
    decisions = []
    for n, slide in enumerate(deck.slides, 1):
        if not slide.image_file:
            continue
        asset = resolve_asset(slide.image_file)
        entry = next((e for e in audit if e.get("slide") == n and "selected" in e), {})
        query = entry.get("query") or asset.get("query") or slide.image_query or ""
        item = {**asset, "query": query, "central_query": query, "people_request": slide.title or ""}
        approved = photographic_candidate(item)
        decisions.append({"slide": n, "title": asset["title"], "query": query, "approved": approved})
        if not approved:
            slide.image_file = None
            slide.image_query = query or slide.title
            source = replace_slide(source, n, slide)
    return source, decisions


def execute(run):
    load_local_settings()
    model_name = "gpt-5.4-mini"
    budget = Budget(pricing_for(model_name), limit=.6)
    original_ledger = json.loads((run / "orcamento.json").read_text("utf-8"))
    save_json(run / "orcamento_antes_revisoes.json", original_ledger)
    carry_budget(budget, run / "orcamento.json")
    budget.ledger_path = run / "orcamento.json"
    budget.persist()
    data = json.loads((run / "resultados.json").read_text("utf-8"))
    save_json(run / "resultados_antes_revisoes.json", data)
    data["attempts_before_revisions"] = deepcopy(data["runs"])
    with httpx.Client(timeout=300, verify=system_tls_context()) as client:
        for row in data["runs"]:
            name = row["name"]
            if name == "03_refeito":
                continue
            original = run / row["folder"]
            folder = run / (name + "_revisado")
            folder.mkdir(exist_ok=False)
            source = (original / "apresentacao.slda").read_bytes().decode("utf-8")
            facts = Dossier.load(original / "dossie.json").fact_map() if (original / "dossie.json").exists() else {}
            edits = ({1: "Encurte apenas o subtítulo para até 95 caracteres, mantendo o sentido e as notas.",
                      6: "Mude para tópicos com dois itens curtos. Preserve os números e os fatos documentais. "
                         "Explique a metodologia sem transformar datas em valores grandes."} if name == "01_documentos" else
                     {5: "Mude para tópicos com dois itens curtos, rótulos de até 24 caracteres e detalhes de até 90. "
                         "Preserve os números, as condições e as fontes. Ponha o restante nas notas."} if name == "02_docx" else {})
            if edits:
                tracked = RecordedModel(PaidModel(model_name, budget, folder, output_tokens=2400, client=client),
                    folder, max_calls=2 * len(edits), on_usage=lambda usage, f=folder: budget.note(f, usage))
                for number, instruction in edits.items():
                    print(f"{name}: refazer slide {number}", flush=True)
                    previous = source
                    source = refazer_slide(source, number, instruction, facts, tracked)
                    a, b = slide_spans(previous), slide_spans(source)
                    assert all(previous[slice(*x)].encode() == source[slice(*y)].encode()
                               for i, (x, y) in enumerate(zip(a, b)) if i != number - 1)
                save_json(folder / "instrucoes_reparo.json", edits)
            audit_path = original / "imagens.json"
            audit = json.loads(audit_path.read_text("utf-8")) if audit_path.exists() else []
            source, decisions = filter_photos(source, audit)
            save_json(folder / "revisao_fotos.json", decisions)
            export_edit(source, folder, facts or None)
            if facts:
                shutil.copyfile(original / "dossie.json", folder / "dossie.json")
            own_usage = json.loads((folder / "uso.json").read_text("utf-8")) if (folder / "uso.json").exists() else None
            row.update(folder=folder.name, error=None, usage=total_usage([row["usage"], own_usage]) if own_usage else row["usage"],
                       **evidence(folder, 8 if name.startswith(("01", "02")) else 6))
            save_json(folder / "uso_acumulado.json", row["usage"])
            save_json(run / "resultados.json", data)
            summarize(run)
        # The requested content edit starts from the corrected document deck.
        base = run / next(r["folder"] for r in data["runs"] if r["name"] == "01_documentos")
        folder = run / "03_refeito_revisado"
        folder.mkdir(exist_ok=False)
        source = (base / "apresentacao.slda").read_bytes().decode("utf-8")
        facts = Dossier.load(base / "dossie.json").fact_map()
        for filename in ("apresentacao.slda", "apresentacao.pptx", "contato.png"):
            shutil.copyfile(base / filename, folder / ("antes" + Path(filename).suffix))
        tracked = RecordedModel(PaidModel(model_name, budget, folder, output_tokens=2400, client=client),
            folder, max_calls=2, on_usage=lambda usage: budget.note(folder, usage))
        instruction = ("Transforme em comparação entre SLM sozinho e SLM + gramática. "
                       "Use dois itens curtos por lado, até 60 caracteres por detalhe. "
                       "Use somente os fatos fornecidos e cite F#. Não invente resultados nem vantagens medidas.")
        print("Refazendo slide 3 com comparação solicitada", flush=True)
        edited = refazer_slide(source, 3, instruction, facts, tracked)
        a, b = slide_spans(source), slide_spans(edited)
        preserved = all(source[slice(*x)].encode() == edited[slice(*y)].encode()
                        for i, (x, y) in enumerate(zip(a, b)) if i != 2)
        assert preserved
        save_json(folder / "preservacao.json", {"other_slides_byte_identical": preserved,
                                                "instruction": instruction})
        export_edit(edited, folder, facts)
        shutil.copyfile(base / "dossie.json", folder / "dossie.json")
        row = next(r for r in data["runs"] if r["name"] == "03_refeito")
        row.update(folder=folder.name, error=None, usage=tracked.summary(), **evidence(folder, 8))
        save_json(run / "resultados.json", data)
        summarize(run)
    print(f"Conhecido: {budget.spent:.8f}; limite com reservas: {budget.upper_bound:.8f}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    execute(parser.parse_args().run)
