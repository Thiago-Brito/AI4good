"""Referência independente do porte TS. Não altera o compilador Python.

Executar da raiz: .venv/Scripts/python.exe scripts/export_parity.py
"""

# ruff: noqa: E402 -- o script roda também sem instalação editável do projeto.
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from PIL import Image, ImageFont
import yaml
from slidedsl.alto import parse_alto
from slidedsl.alto_compile import build_alto
from slidedsl import text_metrics as tm

PACKAGE = ROOT / "packages/slidedsl-core"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def facts_in(folder):
    for name in ("dossie.json", "relatorio.json"):
        path = folder / name
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for key in ("dossier", "dossie", "research"):
            if isinstance(data, dict) and key in data:
                data = data[key]
        facts = data.get("facts", data.get("fatos", {})) if isinstance(data, dict) else {}
        if isinstance(facts, list):
            facts = {f["id"]: f for f in facts if isinstance(f, dict) and "id" in f}
        if facts:
            return facts
    return {}


def font_data(characters):
    # Rasterização exata do Python: round(pt*96/72*4), avanços em 1/64 px,
    # /4 e margem 1.04 (1.14 no fallback). Exportamos também ajustes de pares;
    # a tabela grande preserva a precisão dos avanços de cada glifo.
    result = {
        "method": "Pillow/FreeType getlength, kerning ligado; round ties-to-even(pt*96/72*4); /4; margem 1.04 ou 1.14",
        "families": {},
    }
    chars = sorted(characters | {chr(i) for i in range(256)} | set("—–“”‘’•…€"))
    for family in tm.FAMILIES:
        weights = {}
        for bold in (False, True):
            path = tm.font_file(family, bold)
            if path is None:
                weights[str(int(bold))] = {"missing": True}
                continue
            font = ImageFont.truetype(str(path), 16384)
            advances = {c: font.getlength(c) / 16384 for c in chars}
            # Todos os pares: cobre também textos novos fora do corpus.
            kern = {}
            for a in chars:
                for b in chars:
                    delta = font.getlength(a + b) / 16384 - advances[a] - advances[b]
                    if abs(delta) > 1e-9:
                        kern[a + b] = delta
            weights[str(int(bold))] = {
                "advances": advances,
                "kerning": kern,
                "font": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "margin": 1.14 if (family, bold) in tm.FALLBACKS else 1.04,
                "layout_engine": int(font.layout_engine),
            }
            weights[str(int(bold))]["pairs"] = list(kern)
            # FreeType BASIC (Windows) arredonda cada avanço para px inteiros;
            # não é legítimo escalar uma medição única para todos os tamanhos.
            # Tabelas por raster preservam hinting e kerning também no RAQM.
            raster_tables = {}
            for size in range(10, 97):
                raster = round(size * 96 / 72 * 4)
                actual = tm.local_font(size, bold, family)
                char_widths = {c: actual.getlength(c) for c in chars}
                raster_tables[str(raster)] = {
                    "advances": [
                        int(char_widths[c]) if char_widths[c].is_integer() else char_widths[c]
                        for c in chars
                    ],
                    "kerning": [
                        actual.getlength(pair) - char_widths[pair[0]] - char_widths[pair[1]]
                        for pair in kern
                    ],
                }
            weights[str(int(bold))]["rasters"] = raster_tables
        result["families"][family] = {
            "x_height_ratio": tm.x_height_ratio(family),
            "weights": weights,
        }
    result["characters"] = chars
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-fonts", action="store_true")
    args = parser.parse_args()
    target = ROOT / "outputs/parity"
    paths = sorted((ROOT / "examples/alto").glob("*.slda"))
    denied = []

    def onerror(error):
        denied.append({"path": str(Path(error.filename).relative_to(ROOT)), "reason": str(error)})

    for folder, dirs, files in os.walk(ROOT / "outputs", onerror=onerror):
        # Exported JSON has no Alto sources. Skip only our own output.
        if Path(folder) == target:
            dirs[:] = []
            continue
        if "apresentacao.slda" in files:
            paths.append(Path(folder) / "apresentacao.slda")
    entries, characters = [], set()
    for path in paths:
        relative = path.relative_to(ROOT).as_posix()
        ident = hashlib.sha256(relative.encode()).hexdigest()[:12]
        row = {"id": ident, "source": relative}
        try:
            deck = parse_alto(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            entries.append({**row, "status": "parser_error", "reason": str(exc)})
            continue
        try:
            facts = facts_in(path.parent)
            images = {}
            for slide in deck.slides:
                if not slide.image_file:
                    continue
                try:
                    with Image.open(ROOT / slide.image_file) as image:
                        entry = {"width": image.width, "height": image.height}
                    media = ROOT / "outputs/media/assets" / (Path(slide.image_file).stem + ".json")
                    if media.is_file():
                        entry["metadata"] = json.loads(media.read_text(encoding="utf-8"))
                    images[slide.image_file] = entry
                except OSError:
                    images[slide.image_file] = {"missing": True}
            result = build_alto(deck, facts, ROOT)
            ir = (
                result.validation.ir.model_dump(mode="json")
                if result.validation and result.validation.ir
                else None
            )
            values = {
                "deck": deck.model_dump(mode="json"),
                "facts": facts,
                "images": images,
                "ir": ir,
                "diagnostics": [
                    {"code": d.code, "severity": d.severity} for d in result.all_diagnostics
                ],
            }
            for name, value in values.items():
                write(target / ident / (name + ".json"), value)
            characters.update(json.dumps(values["deck"], ensure_ascii=False))
            features = {"kind:" + s.kind for s in deck.slides} | {"style:" + deck.theme}
            if ir:
                features |= {
                    "font:" + e["font_face"]
                    for s in ir["slides"]
                    for e in s["elements"]
                    if e["type"] == "text"
                }
                features |= {"layout:" + s.kind for s in deck.slides}
            features |= {"image"} if images else set()
            entries.append(
                {
                    **row,
                    "status": "exported",
                    "has_ir": ir is not None,
                    "features": sorted(features),
                }
            )
        except Exception as exc:
            entries.append({**row, "status": "export_error", "reason": repr(exc)})
    # Cobertura gulosa determinística; depois exemplos e casos com/sem IR.
    available = [r for r in entries if r["status"] == "exported"]
    selected, covered = [], set()
    while available and len(selected) < 25:
        best = max(available, key=lambda r: len(set(r["features"]) - covered))
        if set(best["features"]) <= covered:
            break
        selected.append(best)
        available.remove(best)
        covered.update(best["features"])
    for row in available:
        if len(selected) >= 25:
            break
        if row["source"].startswith("examples/") or not row["has_ir"]:
            selected.append(row)
    for row in selected:
        destination = PACKAGE / "test/fixtures" / row["id"]
        destination.mkdir(parents=True, exist_ok=True)
        for name in ("deck", "facts", "images", "ir", "diagnostics"):
            shutil.copyfile(target / row["id"] / (name + ".json"), destination / (name + ".json"))
    manifest = {
        "entries": entries,
        "unreadable_directories": denied,
        "fixtures": [r["id"] for r in selected],
        "coverage": sorted(covered),
    }
    write(target / "manifest.json", manifest)
    write(
        PACKAGE / "test/fixtures/manifest.json", {"entries": selected, "coverage": sorted(covered)}
    )
    for name in ("design_rules", "themes"):
        write(
            PACKAGE / "src/data" / (name + ".json"),
            yaml.safe_load((ROOT / "config" / (name + ".yaml")).read_text(encoding="utf-8")),
        )
    if not args.skip_fonts:
        (PACKAGE / "src/data/font_metrics.json").write_text(
            json.dumps(font_data(characters), ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    texts = [
        "Ação, evidência e comparação.",
        "AVATAR To Wa fi ffi ffl",
        "Planejamento de uma equipe em 2026.",
        "“Dados” — análise; € 1.000,00",
        "Primeira linha\nSegunda linha",
    ]
    cases = [
        {
            "text": text,
            "family": family,
            "bold": bold,
            "size": size,
            "box": width,
            "width": tm.text_width(text, size, bold, family),
            "height": tm.text_height(text, width, size, bold, family),
        }
        for family in tm.FAMILIES
        for bold in (False, True)
        for size, width in ((12, 160), (20, 300), (26, 560), (42, 800), (54, 1152))
        for text in texts
    ]
    write(PACKAGE / "test/data/text_metrics.json", cases)
    print(
        json.dumps(
            {
                "exported": sum(r["status"] == "exported" for r in entries),
                "excluded": sum(r["status"] != "exported" for r in entries),
                "fixtures": len(selected),
                "unreadable": len(denied),
            }
        )
    )


if __name__ == "__main__":
    main()
