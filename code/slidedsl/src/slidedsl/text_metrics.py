"""Local Arial measurements plus word wrapping; Office rendering remains a separate check."""

from functools import lru_cache
import hashlib
import math
import logging
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


FAMILIES = {
    "Arial": ("arial.ttf", "arialbd.ttf"),
    "Calibri": ("calibri.ttf", "calibrib.ttf"),
    "Cambria": ("cambria.ttc", "cambriab.ttf"),
    "Georgia": ("georgia.ttf", "georgiab.ttf"),
    "Trebuchet MS": ("trebuc.ttf", "trebucbd.ttf"),
    "Verdana": ("verdana.ttf", "verdanab.ttf"),
}
FALLBACKS = set()


@lru_cache(maxsize=32)
def font_file(family="Arial", bold=False):
    # Compatibilidade com chamadores anteriores: font_file(False).
    if isinstance(family, bool):
        bold, family = family, "Arial"
    if family not in FAMILIES:
        FALLBACKS.add((family, bool(bold)))
        logging.getLogger(__name__).warning("Fonte %s ausente: Arial com margem de 10%%.", family)
        return font_file("Arial", bold)
    filename = FAMILIES.get(family, FAMILIES["Arial"])[bool(bold)]
    display = family + (" Bold" if bold else "")
    candidates = [f"C:/Windows/Fonts/{filename}", f"/Library/Fonts/{display}.ttf",
                  f"/Library/Fonts/Microsoft/{display}.ttf",
                  f"/System/Library/Fonts/Supplemental/{display}.ttf",
                  f"/usr/share/fonts/truetype/msttcorefonts/{filename}",
                  f"/usr/share/fonts/truetype/msttcorefonts/{display.replace(' ', '_')}.ttf"]
    if family == "Arial":
        candidates += FONT_CANDIDATES[bool(bold)]
    found = next((Path(p) for p in candidates if Path(p).is_file()), None)
    if found:
        return found
    if family != "Arial":
        FALLBACKS.add((family, bool(bold)))
        logging.getLogger(__name__).warning("Fonte %s ausente: Arial com margem de 10%%.", display)
        return font_file("Arial", bold)
    return None


@lru_cache(maxsize=256)
def local_font(size, bold, family="Arial"):
    path = font_file(family, bold)
    if path is None:
        return None
    try:
        return ImageFont.truetype(str(path), round(size * 96 / 72 * 4))
    except OSError:
        return None


@lru_cache(maxsize=32)
def x_height_ratio(family="Arial"):
    """Altura raster do glifo x a 1000 px, relativa a Arial (mesmo tamanho).

    Medimos normal, inclusive para títulos: a compensação é da família, não do peso.
    Fontes ausentes seguem o fallback registrado por font_file.
    """
    reference, target = font_file("Arial"), font_file(family)
    if reference is None or target is None:
        return 1.
    def height(path):
        bounds = ImageFont.truetype(str(path), 1000).getbbox("x", anchor="ls")
        return bounds[3] - bounds[1]
    return height(target) / height(reference)


def optical_size(nominal, family="Arial", minimum=0, effective_minimum=0):
    """Compensa altura-x, arredonda a 1 pt e preserva pisos nominal e efetivo."""
    ratio = x_height_ratio(family)
    return max(minimum, round(nominal / ratio), math.ceil(effective_minimum / ratio))


@lru_cache(maxsize=32768)
def text_width(value, size, bold=False, family="Arial"):
    font = local_font(size, bold, family)
    return (
        font.getlength(value) / 4 * (1.14 if (family, bool(bold)) in FALLBACKS else 1.04)
        if font
        else len(value) * size * 96 / 72 * (0.65 if bold else 0.58)
    )


@lru_cache(maxsize=32768)
def text_height(value, width, size, bold=False, family="Arial"):
    available = max(1, width - 16)
    lines = 0
    for paragraph in value.split("\n"):
        current = ""
        lines += 1
        for word in paragraph.split():
            proposed = current + " " + word if current else word
            if current and text_width(proposed, size, bold, family) > available:
                lines += 1
                current = word
            else:
                current = proposed
    measured = math.ceil(lines * size * 96 / 72 * 1.2 + 18)
    return (max(legacy_height(value, width, size), measured)
            if family == "Arial" or local_font(size, bold, family) is None else measured)


def manifest():
    files = {p for family in FAMILIES for bold in (False, True)
             if (p := font_file(family, bold)) is not None}
    return {
        "method": (
            "local family/Pillow + word wrapping + 4% width margin"
            if files
            else "conservative character widths + word wrapping"
        ),
        "fonts": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},
        "office_measurement": False,
        "fallbacks": sorted(FALLBACKS),
        "x_height_ratios": {family: x_height_ratio(family) for family in FAMILIES},
    }
