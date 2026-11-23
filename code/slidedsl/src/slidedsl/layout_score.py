"""Heurísticas geométricas puras, sem validação psicofísica de beleza.

Pesos: ocupação .35, equilíbrio .20, alinhamento .15, regularidade .15,
ritmo .15. Média de potência p=-2; piso numérico 0.01 evita divisão por zero.
"""

import math
from statistics import pstdev

from .geometry import area, box, intersection, union_area

WEIGHTS = dict(ocupacao=.35, equilibrio=.20, alinhamento=.15, regularidade=.15, ritmo=.15)
BLOCKERS = {"A010", "A019", "D001", "D002", "D008", "D010"}


def occupancy(boxes, region):
    clipped = [r for b in boxes if (r := intersection(b, region))]
    return min(1., union_area(clipped) / max(1, area(region)))


def occupation_score(fraction):
    if .55 <= fraction <= .78:
        return 1.
    if fraction < .45:
        return max(0., .8 * (fraction / .45) ** 2)
    return max(0., min(1., .8 + 2 * (fraction - .45), (1 - fraction) / .22))


def balance(boxes, region, weights=None):
    if not boxes:
        return 0.
    weights = weights or [1.] * len(boxes)
    masses = [area(b) * w for b, w in zip(boxes, weights)]
    total = sum(masses)
    if total <= 0:
        return 0.
    cx = sum((b[0] + b[2]) / 2 * m for b, m in zip(boxes, masses)) / total
    cy = sum((b[1] + b[3]) / 2 * m for b, m in zip(boxes, masses)) / total
    rx, ry = (region[0] + region[2]) / 2, (region[1] + region[3]) / 2
    return max(0., 1 - math.hypot(cx - rx, cy - ry) /
               max(1, math.hypot(region[2] - region[0], region[3] - region[1]) / 2))


def alignment(boxes, tolerance=2):
    if len(boxes) < 2:
        return 1.
    def distinct(values):
        anchors = []
        for v in sorted(values):
            if not anchors or v - anchors[-1] > tolerance:
                anchors.append(v)
        return len(anchors)
    return 1 - (distinct([b[0] for b in boxes]) + distinct([b[1] for b in boxes]) - 2) / (2 * len(boxes))


def regularity(boxes):
    """Comparar irmãos, nunca misturar rótulos e descrições com papéis diferentes."""
    if len(boxes) < 2:
        return 1.
    widths = [b[2] - b[0] for b in boxes]
    heights = [b[3] - b[1] for b in boxes]
    ordered = sorted(boxes, key=lambda b: (b[1], b[0]))
    gaps = [max(0, b[0] - a[2]) if abs(a[1] - b[1]) <= 2 else max(0, b[1] - a[3])
            for a, b in zip(ordered, ordered[1:])]
    def cv(values):
        return pstdev(values) / max(1, sum(values) / len(values)) if values else 0
    return 1 / (1 + cv(widths) + cv(heights) + cv(gaps))


def rhythm(variant, previous, visual=None, previous_visual=None, history=()):
    if variant == previous:
        return .1
    if variant in history[-3:]:
        return .45
    if visual is not None and visual == previous_visual:
        return .55
    return 1.


def aggregate(scores):
    return sum(w * max(.01, scores[k]) ** -2 for k, w in WEIGHTS.items()) ** -.5


def useful_elements(slide):
    return [e for e in slide.elements if
            (e.type == "text" and e.role != "titulo" and (e.font_size or 0) >= 16)
            or e.type == "image" or "_card_" in e.id or "_cabecalho_" in e.id]


def score_slide(slide, variant, previous=None, visual=None, previous_visual=None, history=()):
    top = max((e.y + e.height + 16 for e in slide.elements if e.role == "titulo"), default=64)
    region = (64, min(top, 635), 1216, 636)
    elements = useful_elements(slide)
    clipped = [(e, r) for e in elements if (r := intersection(box(e), region))]
    boxes = [r for _, r in clipped]
    # Texto escuro/imagem > forma cheia > fio. Cores claras têm menor massa visual.
    from .design_rules import luminance
    weights = [1.2 if e.type == "image" else
               .8 + .4 * (1 - luminance(e.color or "#000000")) if e.type == "text" else
               .08 if e.height <= 8 else .65 for e, _ in clipped]
    groups = {}
    for e, r in clipped:
        key = (e.type, "rotulo" if "_rotulo_" in e.id else
               "detalhe" if "_detalhe_" in e.id else e.id.split("_")[1])
        groups.setdefault(key, []).append(r)
    fraction = occupancy(boxes, region)
    scores = dict(ocupacao=occupation_score(fraction), equilibrio=balance(boxes, region, weights),
                  alinhamento=alignment(boxes),
                  regularidade=sum(regularity(g) for g in groups.values()) / max(1, len(groups)),
                  ritmo=rhythm(variant, previous, visual, previous_visual, history))
    # Ganho marginal explícito: nº de variantes distintas após acrescentar a candidata.
    distinct = len(set(history) | {variant})
    diversity_bonus = .03 * distinct / max(1, len(history) + 1)
    return dict(variant=variant, visual=visual, occupancy=fraction, scores=scores,
                diversity_bonus=diversity_bonus, score=min(1., aggregate(scores) + diversity_bonus))


def content_preference(metrics, kind, items):
    """Cartões para mensagens curtas; linhas para leitura longa, antes do desempate."""
    result = dict(metrics)
    compact = (2 <= len(items) <= 3 and
               all(len(i.label) <= 36 and len(i.detail or "") <= 110 for i in items))
    bonus = .08 if kind == "topicos" and compact and metrics["variant"].startswith("cards") else 0.
    if kind == "conclusao" and metrics["variant"] == "actions_columns":
        bonus = .12
    result["content_bonus"] = bonus
    result["score"] = min(1., result["score"] + bonus)
    if kind == "topicos" and compact and metrics["variant"] == "rows":
        result["score"] = min(.70, result["score"])
    if kind == "conclusao" and metrics["variant"] == "actions_rows":
        result["score"] = min(.65, result["score"])
    return result


def choose(candidates, previous=None):
    """Ordem de entrada desempata; evita repetição se houver alternativa válida."""
    valid = [c for c in candidates if c["valid"]]
    pool = [c for c in valid if c["variant"] != previous] or valid or candidates
    return max(pool, key=lambda c: c["score"])
