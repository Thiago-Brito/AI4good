"""Ocupação de caixas úteis na IR; não mede tinta nem qualidade estética."""

from .geometry import area, box, intersection, union_area

OCCUPANCY_MINIMUM = 0.30


def content_occupancy(slide):
    titles = [e for e in slide.elements if e.role == "titulo"]
    top = max((e.y + e.height + 16 for e in titles), default=64)
    region = (64, min(top, 635), 1216, 636)
    relevant = [e for e in slide.elements if
                (e.type == "text" and e.role != "titulo" and (e.font_size or 0) >= 16)
                or e.type == "image" or "_card_" in e.id or "_cabecalho_" in e.id]
    clipped = [r for e in relevant if (r := intersection(box(e), region))]
    return round(union_area(clipped) / area(region), 4)
