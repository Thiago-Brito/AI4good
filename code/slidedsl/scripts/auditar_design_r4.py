"""Corpus congelado, PPTX editável, PNGs IR/Pillow e métricas; execução 100% offline."""

import argparse
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw

from slidedsl.alto_compile import build_alto
from slidedsl.compiler import compile_ir
from slidedsl.ir_preview import contact_sheet, render_deck
from slidedsl.layout_score import score_slide
from slidedsl.paths import project_root
from slidedsl.text_metrics import manifest


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), "utf-8")


def freeze(run):
    root = project_root()
    sources = [*sorted((root / "outputs/estilos").glob("*.slda")),
               *sorted((root / "outputs/comparacao_alto_sld/20261101-2227").glob("*_s42/apresentacao.slda")),
               *sorted((root / "examples/alto").glob("*.slda"))]
    corpus = run / "corpus"
    corpus.mkdir(parents=True, exist_ok=False)
    entries = []
    for i, source in enumerate(sources):
        name = f"{i:02d}_" + (source.parent.name if source.name == "apresentacao.slda" else source.stem)
        target = corpus / f"{name}.slda"
        shutil.copyfile(source, target)
        entries.append(dict(name=name, source=source.relative_to(root).as_posix(),
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    write_json(run / "corpus.json", entries)


def audit(run, phase):
    out = run / phase
    out.mkdir(parents=True, exist_ok=False)
    rows, decks = [], []
    for source in sorted((run / "corpus").glob("*.slda")):
        folder = out / source.stem
        folder.mkdir()
        result = build_alto(source.read_text("utf-8"))
        write_json(folder / "diagnosticos.json", result.report())
        if result.dsl:
            (folder / "compilado.sld").write_text(result.dsl, "utf-8")
        ir = result.validation.ir if result.validation else None
        pptx, failure = False, None
        if ir:
            write_json(folder / "ir.json", ir.model_dump())
            pngs = render_deck(ir, folder, scale=.45)
            contact_sheet(pngs, folder / "contato.png")
            if result.success():
                try:
                    compile_ir(ir, folder / "apresentacao.pptx")
                    pptx = True
                except (ValueError, RuntimeError) as exc:
                    failure = str(exc)
            previous, previous_visual = None, None
            history = []
            for slide, original in zip(ir.slides, result.deck.slides):
                diagnostic = next((d for d in result.diagnostics if d.code == "A030" and d.slide == slide.number), None)
                # Baseline: infere composição observável, sem alterar o compilador antigo.
                variant = (diagnostic.evidence["variant"] if diagnostic else
                           "cards" if any("_card_" in e.id for e in slide.elements) else original.kind)
                visual = diagnostic.evidence.get("visual") if diagnostic else variant
                metrics = score_slide(slide, variant, previous, visual, previous_visual, history)
                if diagnostic:
                    # Nota da seleção inclui preferência pelo conteúdo e diversidade.
                    metrics.update({k: diagnostic.evidence[k] for k in
                                    ("score", "scores", "occupancy")})
                dimensions = None
                if original.image_file:
                    with Image.open(project_root() / original.image_file) as asset:
                        dimensions = list(asset.size)
                title = next((e for e in slide.elements if e.role == "titulo"), None)
                mark = next((e for e in slide.elements if "_marca_" in e.id), None)
                content = original.kind not in {"capa", "secao", "citacao"}
                mixed_axis = bool(content and title and
                                  (title.align != "left" or (mark and mark.x != title.x)))
                ds = [d for d in result.all_diagnostics if d.slide == slide.number]
                row = dict(deck=source.stem, slide=slide.number, kind=original.kind, **metrics,
                           repeated=variant == previous, image_dimensions=dimensions,
                           mixed_axis=mixed_axis, recent_repeat=variant in history[-3:],
                           A010=sum(d.code == "A010" for d in ds), A019=sum(d.code == "A019" for d in ds),
                           A031=sum(d.code == "A031" for d in ds),
                           D010=sum(d.code == "D010" for d in ds))
                rows.append(row)
                previous, previous_visual = variant, visual
                history.append(variant)
        decks.append(dict(deck=source.stem, valid=result.success(), pptx=pptx, failure=failure))
        print(f"{phase}: {source.stem}: valid={result.success()} pptx={pptx}", flush=True)
    write_json(out / "metricas.json", dict(renderer="IR/Pillow (não comprova Office)", api_calls=0,
                                          cost_usd=0, fonts=manifest(), decks=decks, slides=rows))
    with (out / "metricas.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({**r, "scores": json.dumps(r["scores"])} for r in rows)
    return out


def summary(rows):
    return dict(slides=len(rows), score=sum(r["score"] for r in rows) / len(rows),
                occupancy=sum(r["occupancy"] for r in rows) / len(rows),
                range=[min(r["occupancy"] for r in rows), max(r["occupancy"] for r in rows)],
                variants=len({r["variant"] for r in rows}), repeated=sum(r["repeated"] for r in rows),
                **{c: sum(r[c] for r in rows) for c in ("A010", "A019", "A031", "D010")})


def compare(run, phase):
    out = run / "comparacao"
    out.mkdir(exist_ok=False)
    before = json.loads((run / "antes/metricas.json").read_text("utf-8"))
    after = json.loads((run / phase / "metricas.json").read_text("utf-8"))
    table = ["# Comparação offline — rodada 4", "", "Prévia IR/Pillow; PPTX editável gerado separadamente. Nota heurística, sem validação estética.", "",
             "| Deck | Fase | Nota | Ocupação (faixa) | Variantes | Repetições | A010/A019/A031 |",
             "|---|---|---:|---|---:|---:|---|"]
    summaries = []
    for deck in after["decks"]:
        name = deck["deck"]
        a, b = run / "antes" / name / "contato.png", run / phase / name / "contato.png"
        if a.exists() and b.exists():
            with Image.open(a) as left, Image.open(b) as right:
                sheet = Image.new("RGB", (left.width + right.width, max(left.height, right.height) + 32), "white")
                sheet.paste(left, (0, 32))
                sheet.paste(right, (left.width, 32))
                draw = ImageDraw.Draw(sheet)
                draw.text((16, 8), "ANTES", fill="black")
                draw.text((left.width + 16, 8), "DEPOIS", fill="black")
                sheet.save(out / f"{name}.png")
        for label, data in [("antes", before), (phase, after)]:
            rows = [r for r in data["slides"] if r["deck"] == name]
            if not rows:
                continue
            s = summary(rows)
            summaries.append(dict(deck=name, phase=label, **s))
            table.append(f"| {name} | {label} | {s['score']:.3f} | {s['occupancy']:.3f} ({s['range'][0]:.3f}–{s['range'][1]:.3f}) | {s['variants']} | {s['repeated']} | {s['A010']}/{s['A019']}/{s['A031']} |")
    write_json(out / "resumo.json", summaries)
    (out / "TABELA.md").write_text("\n".join(table) + "\n", "utf-8")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path)
    parser.add_argument("--phase", default="antes")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    run = args.run or Path("outputs/design_r4") / datetime.now().strftime("%Y%m%d-%H%M%S")
    if not args.run:
        run.mkdir(parents=True, exist_ok=False)
        freeze(run)
    print(compare(run, args.phase) if args.compare else audit(run, args.phase))
