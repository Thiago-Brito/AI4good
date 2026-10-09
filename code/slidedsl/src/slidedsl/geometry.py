import math
from typing import Iterable

from .ast_nodes import Position
from .ir import Element

Rect = tuple[float, float, float, float]


def box(e: Element) -> Rect:
    return e.x, e.y, e.x + e.width, e.y + e.height


def intersection(a: Rect, b: Rect) -> Rect | None:
    r = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return r if r[2] > r[0] and r[3] > r[1] else None


def area(r: Rect) -> float:
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def union_area(rects: Iterable[Rect]) -> float:
    """União exata de AABBs por varredura em X; sobreposição não soma duas vezes."""
    rects = [r for r in rects if area(r) > 0]
    xs = sorted({x for r in rects for x in (r[0], r[2])})
    total = 0.0
    for left, right in zip(xs, xs[1:]):
        intervals = sorted((r[1], r[3]) for r in rects if r[0] < right and r[2] > left)
        length = 0.0
        lo = hi = None
        for a, b in intervals:
            if lo is None:
                lo, hi = a, b
            elif a > hi:
                length += hi - lo
                lo, hi = a, b
            else:
                hi = max(hi, b)
        if lo is not None:
            length += hi - lo
        total += (right - left) * length
    return total


def distance(a: Rect, b: Rect) -> float:
    return math.hypot(max(a[0] - b[2], b[0] - a[2], 0), max(a[1] - b[3], b[1] - a[3], 0))


def bounds(elements: list[Element]) -> Rect:
    return (
        min(e.x for e in elements),
        min(e.y for e in elements),
        max(e.x + e.width for e in elements),
        max(e.y + e.height for e in elements),
    )


def resolve_position(
    p: Position, size: tuple[float, float], lookup: dict[str, Element]
) -> tuple[float, float]:
    if p.kind == "absolute":
        return p.x, p.y
    if p.kind == "corner":
        return 1280 - 64 - size[0], 64
    ref = lookup[p.reference]
    if p.kind == "below":
        return ref.x, ref.y + ref.height + p.margin
    return ref.x + ref.width + p.margin, ref.y


def aligned_position(a: Rect, b: Rect, axis: str) -> tuple[float, float]:
    x, y = a[0], a[1]
    if axis == "left":
        x = b[0]
    elif axis == "right":
        x = b[2] - (a[2] - a[0])
    elif axis == "center":
        x = (b[0] + b[2] - (a[2] - a[0])) / 2
    else:
        y = b[1]
    return x, y


def translate(elements: list[Element], x: float, y: float) -> None:
    r = bounds(elements)
    dx, dy = x - r[0], y - r[1]
    for e in elements:
        e.x += dx
        e.y += dy


def resize_group(elements: list[Element], width: float, height: float) -> None:
    r = bounds(elements)
    sx, sy = width / (r[2] - r[0]), height / (r[3] - r[1])
    for e in elements:
        e.x = r[0] + (e.x - r[0]) * sx
        e.y = r[1] + (e.y - r[1]) * sy
        e.width *= sx
        e.height *= sy
