"""Local Arial measurements plus word wrapping; Office rendering remains a separate check."""

from functools import lru_cache
import hashlib
import math
from pathlib import Path

from PIL import ImageFont

from .layouts import text_height as legacy_height


@lru_cache(maxsize=32)
def local_font(size, bold):
    path = Path("C:/Windows/Fonts") / ("arialbd.ttf" if bold else "arial.ttf")
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
    files = [Path("C:/Windows/Fonts") / name for name in ["arial.ttf", "arialbd.ttf"]]
    return {
        "method": "local Arial/Pillow + word wrapping + 4% width margin"
        if all(p.is_file() for p in files)
        else "conservative character widths + word wrapping",
        "fonts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},
        "office_measurement": False,
    }
