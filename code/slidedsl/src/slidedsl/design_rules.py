import math
from itertools import combinations
from pathlib import Path

import yaml

from .diagnostics import Diagnostic
from .geometry import area, bounds, box, distance, intersection, union_area
from .ir import Element, Presentation
from .paths import project_root


def load_rules(path: Path | None = None) -> dict:
    return yaml.safe_load(
        (path or project_root() / "config/design_rules.yaml").read_text(encoding="utf-8")
    )


def luminance(color: str) -> float:
    values = [int(color[n : n + 2], 16) / 255 for n in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(a: str, b: str) -> float:
    low, high = sorted([luminance(a), luminance(b)])
    return (high + 0.05) / (low + 0.05)


def known_background(text: Element, elements: list[Element], default: str) -> str | None:
    r = box(text)
    for e in sorted(elements, key=lambda e: e.z, reverse=True):
        if e.z >= text.z or e.type == "text" or not intersection(r, box(e)):
            continue
        if e.type != "rectangle" or intersection(r, box(e)) != r:
            return None
        return e.color
    return default


def estimated_overflow(e: Element, cfg: dict) -> dict:
    width = max(0, e.width - 2 * cfg["text_padding"])
    height = max(0, e.height - 2 * cfg["text_padding"])
    font_px = (e.font_size or 24) * 96 / 72
    capacity = max(1, math.floor(width / (cfg["character_width_factor"] * font_px)))
    lines = sum(max(1, math.ceil(len(line) / capacity)) for line in (e.text or "").split("\n"))
    needed = lines * font_px * cfg["line_height_factor"]
    return {
        "estimated_lines": lines,
        "estimated_height": needed,
        "available_height": height,
        "characters_per_line": capacity,
        "approximation": "AABB; largura média de caracteres; não mede glifos",
    }


def check_design(deck: Presentation, config: dict | None = None) -> list[Diagnostic]:
    cfg = config or load_rules()
    theme = yaml.safe_load((project_root() / "config/themes.yaml").read_text(encoding="utf-8"))[
        deck.theme
    ]
    ds = []
    for s in deck.slides:

        def emit(
            code, message, e=None, evidence=None, suggestion="Revise a composição.", info=False
        ):
            ds.append(
                Diagnostic(
                    code=code,
                    severity="INFORMAÇÃO" if info else cfg["severities"][code],
                    message=message,
                    slide=s.number,
                    element=e.id if e else None,
                    line=e.source_line if e else None,
                    column=e.source_column if e else None,
                    evidence={
                        **({"x": e.x, "y": e.y, "width": e.width, "height": e.height} if e else {}),
                        **(evidence or {}),
                    },
                    suggestion=suggestion,
                )
            )

        valid = [e for e in s.elements if e.width > 0 and e.height > 0]
        by_id = {e.id: e for e in valid}
        group_map = {g.id: g for g in s.groups}

        def object_box(id):
            if id in by_id:
                return box(by_id[id])
            if id in group_map and all(m in by_id for m in group_map[id].members):
                return bounds([by_id[m] for m in group_map[id].members])
            return None

        for e in s.elements:
            if e.width <= 0 or e.height <= 0:
                emit(
                    "D009",
                    "Largura ou altura não positiva.",
                    e,
                    suggestion="Defina dimensões maiores que zero.",
                )
                continue
            if e.x < 0 or e.y < 0 or e.x + e.width > 1280 or e.y + e.height > 720:
                emit(
                    "D001",
                    "Elemento sai do canvas 1280×720.",
                    e,
                    suggestion="Mova ou redimensione o elemento para dentro da tela.",
                )
            if e.type == "text":
                bg = known_background(e, valid, theme["colors"]["fundo"])
                if bg is None:
                    emit(
                        "D002",
                        "Contraste INDETERMINADO: fundo contém imagem, elipse ou cores parciais.",
                        e,
                        {"status": "INDETERMINADO"},
                        "Use fundo sólido conhecido para medir contraste.",
                        info=True,
                    )
                elif e.color:
                    ratio = contrast(e.color, bg)
                    if ratio < cfg["contrast_minimum"]:
                        emit(
                            "D002",
                            "Contraste abaixo do mínimo configurado.",
                            e,
                            {"ratio": ratio, "minimum": cfg["contrast_minimum"], "background": bg},
                            "Aumente a diferença de luminância entre texto e fundo.",
                        )
                if e.role == "titulo":
                    actual = (e.font_size, e.color, e.font_face)
                    expected = (
                        theme["fonts"]["titulo"],
                        theme["colors"]["texto"],
                        theme["font_face"],
                    )
                    if actual != expected:
                        emit(
                            "D003",
                            "Título diverge da fonte/tamanho/cor do tema.",
                            e,
                            {"actual": actual, "expected": expected, "role_origin": e.role_origin},
                            "Use os tokens titulo e texto do tema ou justifique a variação.",
                        )
                estimate = estimated_overflow(e, cfg)
                if estimate["estimated_height"] > estimate["available_height"]:
                    emit(
                        "D010",
                        "Possível overflow de texto (estimativa aproximada).",
                        e,
                        estimate,
                        "Amplie a caixa, reduza o conteúdo ou a fonte; confira no PowerPoint.",
                    )
            if e.role not in {"background", "decoracao"}:
                clipped = [
                    intersection(box(e), box(up))
                    for up in valid
                    if up.z > e.z and up.type != "text"
                ]
                covered = union_area(r for r in clipped if r)
                fraction = covered / area(box(e))
                if fraction > cfg["occlusion_maximum"]:
                    emit(
                        "D008",
                        "Elemento relevante encoberto por objetos em camadas superiores.",
                        e,
                        {
                            "covered_area": covered,
                            "fraction": fraction,
                            "maximum": cfg["occlusion_maximum"],
                            "approximation": "caixas retangulares; texto transparente não cobre caixa inteira",
                        },
                        "Traga o objeto para frente, reduza a interseção ou anote o papel decorativo.",
                    )
        for r in s.relations:
            if r.kind in {"below", "right"}:
                continue
            a, b = object_box(r.target), object_box(r.reference)
            if a is None or b is None:
                continue
            axis = {
                "left": (a[0], b[0]),
                "align_right": (a[2], b[2]),
                "center": ((a[0] + a[2]) / 2, (b[0] + b[2]) / 2),
                "top": (a[1], b[1]),
            }[r.kind]
            delta = abs(axis[0] - axis[1])
            if delta > cfg["alignment_tolerance"]:
                emit(
                    "D004",
                    "Alinhamento declarado tem desvio acima da tolerância.",
                    by_id.get(r.target),
                    {
                        "target": r.target,
                        "reference": r.reference,
                        "axis": r.kind,
                        "delta": delta,
                        "tolerance": cfg["alignment_tolerance"],
                    },
                    "Execute novamente alinhar ou corrija as coordenadas.",
                )
                ds[-1].element = r.target
                ds[-1].line = r.source_line
                ds[-1].column = r.source_column
        for g in s.groups:
            members = [by_id[id] for id in g.members if id in by_id]
            worst = max((distance(box(a), box(b)) for a, b in combinations(members, 2)), default=0)
            if worst > cfg["proximity_maximum"]:
                emit(
                    "D005",
                    "Integrantes do grupo muito distantes.",
                    evidence={
                        "group": g.id,
                        "maximum_gap": worst,
                        "threshold": cfg["proximity_maximum"],
                    },
                    suggestion="Aproxime os membros ou reorganize os grupos.",
                )
                ds[-1].element = g.id
                ds[-1].line = g.source_line
        titles = [e for e in valid if e.type == "text" and e.role == "titulo"]
        bodies = [e for e in valid if e.type == "text" and e.role == "corpo"]
        if bodies:
            largest = max(e.font_size or 0 for e in bodies)
            for e in titles:
                if (e.font_size or 0) < largest:
                    emit(
                        "D006",
                        "Título menor que texto de corpo conhecido.",
                        e,
                        {"body_font_size": largest},
                        "Aumente o título ou reduza o corpo.",
                    )
        occupied = [
            intersection(box(e), (0, 0, 1280, 720)) for e in valid if e.role != "background"
        ]
        density = union_area(r for r in occupied if r) / (1280 * 720)
        if density > cfg["density_maximum"]:
            emit(
                "D007",
                "Densidade aproximada acima do limite; não mede beleza.",
                evidence={
                    "fraction": density,
                    "threshold": cfg["density_maximum"],
                    "approximation": "união de caixas, incluindo decoração e caixas de texto",
                },
                suggestion="Reduza a ocupação e crie mais espaço livre.",
            )
    return ds
