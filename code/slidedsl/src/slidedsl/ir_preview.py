"""Prévia PNG aproximada da IR (Pillow), sem PowerPoint/LibreOffice.

Serve para inspeção rápida, comparação entre candidatos e crítica por modelo de visão.
Não prova fidelidade do Office: fontes e quebras podem diferir levemente.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .ir import Presentation
from .paths import project_root

BACKGROUND = {"claro": "#F6F8FC", "escuro": "#14233D"}
FALLBACK_FONTS = {
    False: ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"],
    True: ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
}


def _font(size_pt: int, bold: bool, scale: float):
    from .text_metrics import font_file

    metric = font_file(bold)
    candidates = [metric] + [Path(p) for p in FALLBACK_FONTS[bold]]
    for path in candidates:
        if path and Path(path).is_file():
            # DejaVu é ~9% mais larga que Arial; compensa para aproximar as quebras.
            factor = 1 if path == metric else 0.91
            return ImageFont.truetype(str(path), max(6, round(size_pt * 96 / 72 * scale * factor)))
    return ImageFont.load_default()


def _wrap(draw, text, font, width):
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            proposal = f"{current} {word}".strip()
            if current and draw.textlength(proposal, font=font) > width:
                lines.append(current)
                current = word
            else:
                current = proposal
        lines.append(current)
    return lines


def render_slide(deck: Presentation, index: int, scale: float = 1.0, root: Path | None = None):
    root = root or project_root()
    slide = deck.slides[index]
    image = Image.new("RGB", (round(1280 * scale), round(720 * scale)), BACKGROUND[deck.theme])
    draw = ImageDraw.Draw(image)
    for e in sorted(slide.elements, key=lambda e: e.z):
        box = [e.x * scale, e.y * scale, (e.x + e.width) * scale, (e.y + e.height) * scale]
        if e.type == "rectangle":
            if e.rounded:
                draw.rounded_rectangle(box, radius=12 * scale, fill=e.color)
            else:
                draw.rectangle(box, fill=e.color)
        elif e.type == "ellipse":
            draw.ellipse(box, fill=e.color)
        elif e.type == "arrow":
            x0, y0, x1, y1 = box
            mid = (x0 + x1) / 2
            draw.polygon(
                [
                    (x0 + (x1 - x0) * 0.3, y0),
                    (x0 + (x1 - x0) * 0.7, y0),
                    (x0 + (x1 - x0) * 0.7, (y0 + y1) / 2),
                    (x1, (y0 + y1) / 2),
                    (mid, y1),
                    (x0, (y0 + y1) / 2),
                    (x0 + (x1 - x0) * 0.3, (y0 + y1) / 2),
                ],
                fill=e.color,
            )
        elif e.type == "image":
            try:
                with Image.open(root / e.file) as src:
                    src = src.convert("RGB")
                    w, h = round(e.width * scale), round(e.height * scale)
                    src.thumbnail((w, h))
                    image.paste(
                        src,
                        (round(box[0] + (w - src.width) / 2), round(box[1] + (h - src.height) / 2)),
                    )
            except OSError:
                draw.rectangle(box, outline="#94A3B8", width=2)
        elif e.type == "text":
            font = _font(e.font_size or 24, e.bold, scale)
            pad = 6 * scale
            lines = _wrap(draw, e.text or "", font, (e.width * scale) - 2 * pad)
            line_h = (e.font_size or 24) * 96 / 72 * 1.2 * scale
            total = line_h * len(lines)
            y = box[1] + pad
            if e.align == "center":
                y = box[1] + max(pad, ((box[3] - box[1]) - total) / 2)
            for line in lines:
                width = draw.textlength(line, font=font)
                x = box[0] + pad
                if e.align == "center":
                    x = box[0] + ((box[2] - box[0]) - width) / 2
                elif e.align == "right":
                    x = box[2] - pad - width
                draw.text((x, y), line, font=font, fill=e.color)
                y += line_h
    return image


def render_deck(deck: Presentation, out_dir: Path, scale: float = 0.75, root: Path | None = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for index in range(len(deck.slides)):
        path = out_dir / f"slide_{index + 1:02d}.png"
        render_slide(deck, index, scale, root).save(path)
        paths.append(path)
    return paths


def contact_sheet(paths: list[Path], out: Path, columns: int = 2):
    images = [Image.open(p) for p in paths]
    w, h = images[0].size
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new(
        "RGB", (columns * w + (columns + 1) * 16, rows * h + (rows + 1) * 16), "#94A3B8"
    )
    for k, im in enumerate(images):
        sheet.paste(im, (16 + (k % columns) * (w + 16), 16 + (k // columns) * (h + 16)))
    sheet.save(out)
    return out
