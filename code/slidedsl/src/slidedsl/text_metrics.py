"""Local Arial measurements plus word wrapping; Office rendering remains a separate check."""

from functools import lru_cache
import hashlib
import math
from pathlib import Path

from PIL import ImageFont

from .layouts import text_height as legacy_height

# Arial no Windows/macOS; Liberation Sans tem as mesmas métricas no Linux.
FONT_CANDIDATES = {
    False: [
        "C:/Windows/Fonts/arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    ],
    True: [
        "C:/Windows/Fonts/arialbd.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/liberation-sans/LiberationSans-Bold.ttf",
    ],
}


def font_file(bold):
    return next((Path(p) for p in FONT_CANDIDATES[bool(bold)] if Path(p).is_file()), None)


@lru_cache(maxsize=32)
def local_font(size, bold):
    path = font_file(bold)
    if path is None:
        return None
    try:
        return ImageFont.truetype(str(path), round(size * 96 / 72 * 4))
    except OSError:
        return None


def text_width(value, size, bold=False):
    font = local_font(size, bold)
    return (
        font.getlength(value) / 4 * 1.04
        if font
        else len(value) * size * 96 / 72 * (0.65 if bold else 0.58)
    )


def text_height(value, width, size, bold=False):
    available = max(1, width - 16)
    lines = 0
    for paragraph in value.split("\n"):
        current = ""
        lines += 1
        for word in paragraph.split():
            proposed = current + " " + word if current else word
            if current and text_width(proposed, size, bold) > available:
                lines += 1
                current = word
            else:
                current = proposed
    return max(legacy_height(value, width, size), math.ceil(lines * size * 96 / 72 * 1.2 + 18))


def manifest():
    files = [p for p in (font_file(False), font_file(True)) if p is not None]
    return {
        "method": (
            "local Arial/Pillow + word wrapping + 4% width margin"
            if len(files) == 2
            else "conservative character widths + word wrapping"
        ),
        "fonts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},
        "office_measurement": False,
    }
