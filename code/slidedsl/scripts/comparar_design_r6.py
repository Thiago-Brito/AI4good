"""Compara r5/r6 existentes, audita fontes/objetos e registra geometria; offline."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from comparar_design_r5 import native_audit, phase_summary
from slidedsl.alto_compile import build_alto


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), "utf-8")


def compare(run, baseline):
    out = run / "comparacao"
    out.mkdir(exist_ok=False)
    phases = {"r5": baseline / "ciclo_3", "r6": run / "ciclo_2"}
    summaries = {name: phase_summary(folder, run / "corpus") for name, folder in phases.items()}
    geometry, hashes, sources = [], {}, []
    for source in sorted((run / "corpus").glob("*.slda")):
        old = baseline / "corpus" / source.name
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        hashes[source.name] = dict(sha256=digest, equals_r5=old.read_bytes() == source.read_bytes())
        # Confirma que o refinamento de fallback de capa <600 px não mudou o
        # corpus já inspecionado no ciclo 2; não cria um terceiro ciclo visual.
        final = build_alto(source.read_text("utf-8"))
        stored = json.loads((run / "ciclo_2" / source.stem / "ir.json").read_text("utf-8"))
        assert final.validation.ir.model_dump(mode="json") == stored, source.name
        images = [Image.open(folder / source.stem / "contato.png").convert("RGB")
                  for folder in phases.values()]
        canvas = Image.new("RGB", (sum(im.width for im in images), max(im.height for im in images) + 40), "white")
        x = 0
        for label, image in zip(phases, images):
            canvas.paste(image, (x, 40))
            ImageDraw.Draw(canvas).text((x + 16, 10), label, fill="black", font_size=20)
            x += image.width
            image.close()
        canvas.save(out / f"{source.stem}.png")
        sources.append(f"- [{source.stem}]({source.stem}.png)")
        for slide in stored["slides"]:
            labels = [e for e in slide["elements"] if "_rotulo_" in e["id"]]
            details = [e for e in slide["elements"] if "_detalhe_" in e["id"]]
            cards = [e for e in slide["elements"] if "_card_" in e["id"]]
            if cards and len(labels) == len(cards):
                geometry.append(dict(deck=source.stem, slide=slide["number"],
                                     label_tops=[e["y"] for e in labels],
                                     detail_tops=[e["y"] for e in details],
                                     cards=[{k: e[k] for k in ("x", "y", "width", "height")} for e in cards]))
    write(out / "resumo.json", summaries)
    write(out / "geometria_cartoes.json", geometry)
    write(out / "corpus_sha256.json", hashes)
    write(out / "auditoria_pptx.json", native_audit(run / "ciclo_2"))
    rows = ["# Comparação r5 → r6", "", "Mesmos 16 decks/89 slides; sem inferência, prévia IR/Pillow.", "",
            "| Métrica | r5 | r6 |", "|---|---:|---:|"]
    for key in ("pptx", "occupancy", "topic_rows_fraction", "mixed_axis", "repeated",
                "variants_per_deck", "geometry_score_r5"):
        rows.append(f"| {key} | {summaries['r5'][key]:.4f} | {summaries['r6'][key]:.4f} |")
    rows += ["", "A nota geométrica caiu. Preferência explícita por cartões naturais/colunas é",
             "registrada em A030; não se alteraram notas para alegar melhora estética.", "",
             "Critérios (a)–(e) r5 preservados: " + str(summaries["r6"]["criteria"]), "", *sources, ""]
    (out / "INDICE.md").write_text("\n".join(rows), "utf-8")
    return summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=Path("outputs/design_r5/20261111-001430"))
    args = parser.parse_args()
    print(json.dumps(compare(args.run, args.baseline), ensure_ascii=True, indent=2))
