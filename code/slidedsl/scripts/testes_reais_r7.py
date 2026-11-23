"""Rodada 7 PAGA, autorizada pelo plano: teto global US$ 0,60, sem imagens por IA."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import httpx
from PIL import Image, ImageDraw

from comparar_alto_vs_sld import Budget, save_json
from testes_reais_r6 import JOBS, PaidModel, carry_budget
from slidedsl.alto import parse_alto, number_tokens
from slidedsl.alto_compile import build_alto
from slidedsl.alto_edit import export_edit, refazer_slide, slide_spans
from slidedsl.alto_generation import create_presentation
from slidedsl.alto_quality import visible_text
from slidedsl.compiler import inspect_pptx
from slidedsl.documents import add_document
from slidedsl.https import system_tls_context
from slidedsl.ir_preview import _font, contact_sheet, render_deck
from slidedsl.local_settings import load_local_settings
from slidedsl.model_usage import RecordedModel, pricing_for
from slidedsl.paths import project_root
from slidedsl.research import Dossier


def make_docx(article, target):
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    root = ET.Element(f"{{{ns}}}document")
    body = ET.SubElement(root, f"{{{ns}}}body")
    for paragraph in article.split("\n\n"):
        p = ET.SubElement(body, f"{{{ns}}}p")
        if paragraph.startswith("#"):
            props = ET.SubElement(p, f"{{{ns}}}pPr")
            ET.SubElement(props, f"{{{ns}}}pStyle", {f"{{{ns}}}val": "Heading1"})
        run = ET.SubElement(p, f"{{{ns}}}r")
        ET.SubElement(run, f"{{{ns}}}t").text = paragraph.lstrip("# ")
    with ZipFile(target, "w") as archive:
        archive.writestr("word/document.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True))
        archive.writestr("[Content_Types].xml", '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')


def evidence(folder, expected):
    dossier = Dossier.load(folder / "dossie.json") if (folder / "dossie.json").exists() else None
    facts = dossier.fact_map() if dossier else {}
    row = dict(valid=False, photos=0, document_facts_used=0)
    source_path = folder / "apresentacao.slda"
    if not source_path.exists():
        panel = Image.new("RGB", (800, 450), "#fff7f7")
        ImageDraw.Draw(panel).text((30, 60), "FALHA — nenhum deck gerado. Veja diagnosticos.json.",
                                    fill="black", font=_font(18, False, 1))
        panel.save(folder / "contato.png")
        return row
    source = source_path.read_bytes().decode("utf-8")
    deck = parse_alto(source)
    built = build_alto(source, facts or None)
    save_json(folder / "diagnosticos.json", built.report())
    if built.validation and built.validation.ir:
        ir = built.validation.ir
        save_json(folder / "ir.json", ir.model_dump())
        contact_sheet(render_deck(ir, folder / "pngs", .6), folder / "contato.png")
    if not (folder / "contato.png").exists():
        panel = Image.new("RGB", (800, 450), "#fff7f7")
        ImageDraw.Draw(panel).text((30, 60), "FALHA DE VALIDAÇÃO — sem PPTX. Veja diagnosticos.json.",
                                    fill="black", font=_font(18, False, 1))
        panel.save(folder / "contato.png")
    used = {ref for slide in deck.slides for ref in slide.sources if ref in facts}
    mapping = [{"id": ref, **facts[ref]} for ref in sorted(used, key=lambda x: int(x[1:]))]
    save_json(folder / "fatos_usados.json", mapping)
    row["document_facts_used"] = sum(f["url"].startswith("documento:") for f in mapping)
    row["facts"] = len(facts)
    audit = []
    for n, slide in enumerate(deck.slides, 1):
        # All facts, not just cited facts; citation-specific warnings remain in diagnostics.
        all_text = " ".join(f["claim"] + " " + f["quote"] for f in facts.values())
        absent = sorted(number_tokens(visible_text(slide)) - number_tokens(all_text)) if facts else []
        audit.append({"slide": n, "text": visible_text(slide), "sources": slide.sources,
                      "numbers_without_fact": absent,
                      "names_review": "Revisão manual obrigatória; sem prova semântica automática."})
    save_json(folder / "auditoria_factual.json", audit)
    pptx = folder / "apresentacao.pptx"
    if pptx.exists():
        inspection = inspect_pptx(pptx)
        save_json(folder / "inspecao_pptx.json", inspection)
        row.update(valid=built.success() and inspection["slide_count"] == expected,
                   photos=inspection["image_objects"])
    return row


def summarize(output):
    data = json.loads((output / "resultados.json").read_text("utf-8"))
    ledger = json.loads((output / "orcamento.json").read_text("utf-8"))
    reviews = json.loads((output / "revisoes.json").read_text("utf-8")) if (output / "revisoes.json").exists() else {}
    lines = ["# Testes reais — rodada 7", "", "Modelo gpt-5.4-mini; um candidato, até um reparo. "
             "Imagens Commons, sem imagens por IA. Prévia IR/Pillow, sem validação Office.", "",
             "| Deck | Válido | Fatos documentais usados | Fotos | Chamadas | USD | Artefatos |",
             "|---|---|---:|---:|---:|---:|---|"]
    gallery = Image.new("RGB", (1800, 1840), "#e2e8f0")
    draw = ImageDraw.Draw(gallery)
    for i, row in enumerate(data["runs"]):
        folder, usage = row["folder"], row["usage"]
        cost = usage.get("cost_usd")
        cost_text = f"{cost:.8f}" if cost is not None else "desconhecido"
        lines.append(f"| {row['name']} | {'sim' if row['valid'] else 'não'} | {row['document_facts_used']} | "
                     f"{row['photos']} | {usage.get('calls', 0)} | {cost_text} | "
                     f"[folha]({folder}/contato.png) · [SLDA]({folder}/apresentacao.slda) · [PPTX]({folder}/apresentacao.pptx) |")
        x, y = (i % 3) * 600, (i // 3) * 920
        draw.text((x + 12, y + 10), row["name"], fill="black", font=_font(18, True, 1))
        with Image.open(output / folder / "contato.png") as sheet:
            sheet.thumbnail((584, 860))
            gallery.paste(sheet, (x + 8, y + 45))
    lines += ["", f"Gasto conhecido: US$ {ledger['known_cost_usd']:.8f}. Total exato: "
              f"{ledger['cost_usd'] if ledger['cost_usd'] is not None else 'desconhecido'}. "
              f"Limite com reservas: US$ {ledger['cost_upper_bound_usd']:.8f} ≤ US$ 0,60.",
              "", "[Galeria](galeria.png)", "", "## Inspeção visual e factual", ""]
    for row in data["runs"]:
        lines += [f"### {row['name']}", "", reviews.get(row["name"], "Aguardando abertura da folha; qualidade não validada."), ""]
        if row.get("error"):
            lines += [f"Falha: {row['error']}", ""]
    lines += ["O arquivo fatos_usados.json relaciona F# a documento/trecho. auditoria_factual.json "
              "registra números ausentes. Os decks de Git/horta/internet não tiveram pesquisa factual.",
              "Filtros de foto são lexicais e podem rejeitar fotos úteis ou aceitar coincidências.", ""]
    (output / "INDICE.md").write_text("\n".join(lines), "utf-8")
    gallery.save(output / "galeria.png")


def execute(output, previous=None, only=None, base_deck=None):
    load_local_settings()
    model_name = "gpt-5.4-mini"
    budget = Budget(pricing_for(model_name), limit=.60)
    output.mkdir(parents=True, exist_ok=False)
    budget.ledger_path = output / "orcamento.json"
    if previous:
        carry_budget(budget, previous)
    budget.persist()
    data = dict(model=model_name, ai_images=False, limit_usd=.60, runs=[])
    save_json(output / "resultados.json", data)
    (output.parent / "ULTIMO.txt").write_text(output.relative_to(project_root()).as_posix(), "utf-8")
    inputs = output / "inputs"
    inputs.mkdir()
    root = project_root()
    article = root / "docs/artigo/ARTIGO_CIENTIFICO_SLIDEDSL.md"
    docx = inputs / "artigo.docx"
    make_docx(article.read_text("utf-8"), docx)
    request = "Apresentação do meu TCC SlideDSL para a banca"
    cases = [("01_documentos", request, "auto", 8, [article, root / "README.md"]),
             ("02_docx", request, "auto", 8, [docx]),
             ("03_refeito", request, "auto", 8, [])]
    cases += [(f"{n:02d}_{topic}", brief, style, 6, []) for n, (style, topic, brief) in enumerate(
        [JOBS[4], JOBS[3], JOBS[5]], 4)]
    if only:
        cases = [c for c in cases if c[0] in only]
    auth_failure = False
    with httpx.Client(timeout=300, verify=system_tls_context()) as client:
        for name, brief, theme, count, paths in cases:
            folder = output / name
            folder.mkdir()
            print(f"Iniciando {name}; gasto conhecido US$ {budget.spent:.8f}", flush=True)
            error = None
            try:
                adapter = PaidModel(model_name, budget, folder, output_tokens=2400, client=client)
                if name == "03_refeito":
                    original = base_deck or output / "01_documentos"
                    facts = Dossier.load(original / "dossie.json").fact_map()
                    source = (original / "apresentacao.slda").read_bytes().decode("utf-8")
                    for filename in ("apresentacao.slda", "apresentacao.pptx", "contato.png"):
                        shutil.copyfile(original / filename, folder / ("antes" + Path(filename).suffix))
                    tracked = RecordedModel(adapter, folder, max_calls=2,
                        on_usage=lambda usage, f=folder: budget.note(f, usage))
                    edited = refazer_slide(source, 3,
                        "Transforme em comparação entre SLM sozinho e SLM + gramática. "
                        "Use somente o que os fatos documentais sustentam, sem resultados inventados.",
                        facts, tracked, roteiro=json.loads((original / "roteiro.json").read_text("utf-8")))
                    before, after = slide_spans(source), slide_spans(edited)
                    preserved = all(source[slice(*a)].encode() == edited[slice(*b)].encode()
                                    for i, (a, b) in enumerate(zip(before, after)) if i != 2)
                    save_json(folder / "preservacao.json", {"other_slides_byte_identical": preserved})
                    if not preserved:
                        raise ValueError("Outros slides foram alterados.")
                    shutil.copyfile(original / "dossie.json", folder / "dossie.json")
                    export_edit(edited, folder, facts)
                else:
                    ids = [add_document(p.name, p.read_bytes())["id"] for p in paths]
                    create_presentation(brief, folder, adapter, n_slides=count, theme=theme,
                        document_ids=ids, sources_mode="documentos" if ids else None,
                        research_provider=None, images=True, image_source="livres", repair_max=1,
                        candidates=1, max_calls=45, allow_without_facts=not ids,
                        seed=42, temperature=.2, preview=False,
                        on_usage=lambda usage, f=folder: budget.note(f, usage),
                        progress=lambda message, n=name: print(f"{n}: {message}", flush=True))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                auth_failure = "HTTP 401" in error
                save_json(folder / "diagnosticos.json", {"error": error})
            usage_path = folder / "uso.json"
            usage = json.loads(usage_path.read_text("utf-8")) if usage_path.exists() else {
                "calls": 0, "known_cost_usd": 0, "cost_usd": None, "unknown_usage_calls": 0}
            if usage_path.exists():
                budget.note(folder, usage)
            else:
                save_json(usage_path, usage)
            row = dict(name=name, folder=name, error=error, usage=usage, **evidence(folder, count))
            data["runs"].append(row)
            save_json(output / "resultados.json", data)
            summarize(output)
            print(f"{name}: válido={row['valid']}; chamadas={usage['calls']}; teto reservado={budget.upper_bound:.8f}", flush=True)
            if auth_failure:
                break
    return auth_failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summarize", type=Path)
    parser.add_argument("--carry-budget", type=Path)
    parser.add_argument("--clean-key-retry", action="store_true")
    parser.add_argument("--only", nargs="+")
    parser.add_argument("--base-deck", type=Path)
    args = parser.parse_args()
    if args.summarize:
        summarize(args.summarize)
        return
    inherited = bool(os.environ.get("OPENAI_API_KEY"))
    output = project_root() / "outputs/testes_reais" / (datetime.now().strftime("%Y%m%d-%H%M") + "_r7")
    if output.exists():
        output = output.with_name(datetime.now().strftime("%Y%m%d-%H%M%S") + "_r7")
    auth_failure = execute(output, args.carry_budget, args.only, args.base_deck)
    if auth_failure:
        print(f"HTTP 401. Chave herdada presente no processo: {inherited}. Nenhum valor exibido.", flush=True)
        if inherited and not args.clean_key_retry:
            env = dict(os.environ)
            env.pop("OPENAI_API_KEY", None)
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                "--clean-key-retry", "--carry-budget", str(output / "orcamento.json")], env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            if result.returncode:
                raise SystemExit(result.returncode)
        else:
            print("Autenticação recusada; lote parado conforme o plano.", flush=True)
    print(f"Evidências: {output}", flush=True)


if __name__ == "__main__":
    main()
