"""Compara três fases existentes e inspeciona PPTX nativo; nenhuma rede/compilação."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from statistics import mean
import xml.etree.ElementTree as ET
import zipfile

from PIL import Image, ImageDraw

from slidedsl.alto import parse_alto
from slidedsl.compiler import inspect_pptx
from slidedsl.ir import Presentation
from slidedsl.layout_score import score_slide
from slidedsl.paths import project_root


def read(path):
    return json.loads(path.read_text("utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), "utf-8")


def phase_summary(folder, corpus):
    data = read(folder / "metricas.json")
    rows = data["slides"]
    photos, mixed, topic_rows, topics, rescored = 0, 0, 0, 0, []
    photo_choices = Counter()
    eligible = 0
    for source in sorted(corpus.glob("*.slda")):
        deck = parse_alto(source.read_text("utf-8"))
        ir = Presentation.model_validate(read(folder / source.stem / "ir.json"))
        history, previous_visual = [], None
        for original, slide in zip(deck.slides, ir.slides):
            row = next(r for r in rows if r["deck"] == source.stem and r["slide"] == slide.number)
            variant = row["variant"]
            if original.kind == "topicos":
                topics += 1
                topic_rows += variant == "rows" or (variant == "topicos" and
                              not any("_card_" in e.id for e in slide.elements))
            if original.kind == "imagem" and original.image_file:
                image = next(e for e in slide.elements if e.type == "image")
                choice = "photo50" if (image.x, image.y) == (664, 0) else "photo40"
                photo_choices[choice] += 1
                with Image.open(project_root() / original.image_file) as asset:
                    large_landscape = max(asset.size) >= 1000 and asset.width >= asset.height
                eligible += large_landscape
                photos += large_landscape and choice == "photo40"
            title = next((e for e in slide.elements if e.role == "titulo"), None)
            mark = next((e for e in slide.elements if "_marca_" in e.id), None)
            if original.kind not in {"capa", "secao", "citacao"}:
                mixed += bool(title and (title.align != "left" or (mark and mark.x != title.x)))
            visual = row.get("visual")
            rescored.append(score_slide(slide, variant, history[-1] if history else None,
                                        visual, previous_visual, history))
            history.append(variant)
            previous_visual = visual
    result = dict(pptx=sum(d["pptx"] for d in data["decks"]), decks=len(data["decks"]),
                  slides=len(rows), occupancy=mean(r["occupancy"] for r in rows),
                  range=[min(r["occupancy"] for r in rows), max(r["occupancy"] for r in rows)],
                  historical_score=mean(r["score"] for r in rows),
                  geometry_score_r5=mean(r["score"] for r in rescored),
                  photo40_eligible_violations=photos, eligible_photos=eligible,
                  photo_choices=dict(photo_choices), topic_rows=topic_rows, topics=topics,
                  topic_rows_fraction=topic_rows / topics, mixed_axis=mixed,
                  repeated=sum(r["repeated"] for r in rows),
                  variants_per_deck=mean(len({r["variant"] for r in rows if r["deck"] == d["deck"]})
                                         for d in data["decks"]),
                  diagnostics={c: sum(r[c] for r in rows) for c in ("A010", "A019", "D010", "A031")},
                  selected=dict(Counter(r["variant"] for r in rows)))
    result["criteria"] = dict(a=photos == 0, b=result["occupancy"] >= .58,
                              c=result["topic_rows_fraction"] <= .35, d=mixed == 0,
                              e=result["pptx"] == 16 and all(result["diagnostics"][c] == 0
                                                            for c in ("A010", "A019", "D010")))
    return result


def native_audit(folder):
    errors, counts = [], Counter()
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
          "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
    for path in sorted(folder.glob("*/apresentacao.pptx")):
        inspection = inspect_pptx(path)
        counts.update({k: inspection[k] for k in
                       ("slide_count", "text_objects", "image_objects", "shape_objects")})
        ir = read(path.parent / "ir.json")
        with zipfile.ZipFile(path) as archive:
            for slide in ir["slides"]:
                tree = ET.fromstring(archive.read(f"ppt/slides/slide{slide['number']}.xml"))
                shapes = {node.find(".//p:cNvPr", ns).get("name"): node
                          for node in tree.findall(".//p:sp", ns)}
                for e in slide["elements"]:
                    if e["type"] != "text":
                        continue
                    node = shapes.get(e["id"])
                    if node is None:
                        errors.append(f"{path.parent.name}: texto ausente {e['id']}")
                        continue
                    families = {n.get("typeface") for n in node.findall(".//a:latin", ns)}
                    sizes = {int(n.get("sz")) for n in node.findall(".//a:rPr", ns) if n.get("sz")}
                    if families != {e["font_face"]} or sizes != {100 * e["font_size"]}:
                        errors.append(f"{path.parent.name}: fonte diverge {e['id']}")
                    text = "\n".join("".join(p.itertext()) for p in node.findall(".//a:t", ns))
                    if " ".join(text.split()) != " ".join(e["text"].split()):
                        errors.append(f"{path.parent.name}: texto diverge {e['id']}")
    return dict(objects=dict(counts), errors=errors)


def compare(run, phase, base):
    out = run / "comparacao"
    out.mkdir(exist_ok=False)
    phases = {"r4-antes": base / "antes", "r4-final": base / "ciclo_3", "r5": run / phase}
    summaries = {label: phase_summary(folder, run / "corpus") for label, folder in phases.items()}
    for source in sorted((run / "corpus").glob("*.slda")):
        contacts = [Image.open(folder / source.stem / "contato.png").convert("RGB")
                    for folder in phases.values()]
        sheet = Image.new("RGB", (sum(im.width for im in contacts),
                                  max(im.height for im in contacts) + 40), "white")
        x = 0
        for label, im in zip(phases, contacts):
            sheet.paste(im, (x, 40))
            ImageDraw.Draw(sheet).text((x + 16, 12), label, fill="black")
            x += im.width
        sheet.save(out / f"{source.stem}.png")
        for im in contacts:
            im.close()
    write(out / "resumo.json", summaries)
    table = ["# Comparação offline — r4 antes | r4 final | r5", "",
             "89 slides em cada fase, incluindo capa/seção/citação. Prévia IR/Pillow, sem validação Office.", "",
             "| Critério / medida | r4-antes | r4-final | r5 |", "|---|---:|---:|---:|"]
    metrics = [
        ("(a) Foto grande paisagem/quadrada em photo40 (meta 0)", lambda s: s["photo40_eligible_violations"]),
        ("(b) Ocupação média (meta ≥0,58)", lambda s: f"{s['occupancy']:.4f}"),
        ("(c) Tópicos em rows (meta ≤35%)", lambda s: f"{s['topic_rows']}/{s['topics']} ({s['topic_rows_fraction']:.1%})"),
        ("(d) Conteúdo com eixo misto (meta 0)", lambda s: s["mixed_axis"]),
        ("(e) PPTX válidos", lambda s: f"{s['pptx']}/{s['decks']}"),
        ("(e) A010/A019/D010", lambda s: "/".join(str(s['diagnostics'][c]) for c in ("A010", "A019", "D010"))),
        ("Variantes/deck", lambda s: f"{s['variants_per_deck']:.3f}"),
        ("Repetição imediata", lambda s: s["repeated"]),
        ("Nota geométrica recalculada com r5", lambda s: f"{s['geometry_score_r5']:.4f}"),
    ]
    for label, fn in metrics:
        table.append("| " + " | ".join([label] + [str(fn(s)) for s in summaries.values()]) + " |")
    table += ["", "Notas históricas foram preservadas em resumo.json; pesos/platôs mudaram.",
              "A nota recalculada exclui preferência de conteúdo e aplica r5 às IR antigas;",
              "variantes r4-antes são inferidas, então ritmo/diversidade anteriores são aproximados.",
              "Ocupação usa o mesmo recorte/união nas três fases; photo40 r5 conta o viewport inteiro,",
              "incluindo barras do contain. Fotos visíveis são medidas separadamente no relatório.",
              "A031 não existia em r4-antes. A métrica não comprova preferência humana."]
    (out / "TABELA.md").write_text("\n".join(table) + "\n", "utf-8")
    audit = native_audit(run / phase)
    entries = read(run / "corpus.json")
    audit["corpus_unchanged"] = all(
        hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
        for entry in entries for path in (project_root() / entry["source"],
                                         run / "corpus" / (entry["name"] + ".slda")))
    audit.update(api_calls=0, cost_usd=0)
    write(run / "auditoria_final.json", audit)
    print(json.dumps(dict(summary=summaries, audit=audit), ensure_ascii=False, indent=2))
    if audit["errors"] or not audit["corpus_unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--base", type=Path, default=Path("outputs/design_r4/20261110-234240"))
    args = parser.parse_args()
    compare(args.run, args.phase, args.base)
