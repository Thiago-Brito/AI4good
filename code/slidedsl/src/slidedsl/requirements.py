"""Frozen, independently evaluated requirements; no model-authored success flags."""

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .geometry import area, bounds, box, distance, intersection


class Requirement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    kind: Literal[
        "slides",
        "shapes",
        "images",
        "layers",
        "groups",
        "columns",
        "footer",
        "margins",
        "text",
        "component",
        "original",
    ]
    slide: int | None = Field(default=None, ge=1, le=12)
    minimum: int = Field(default=1, ge=1, le=12)
    distinct_colors: bool = False
    value: str = ""
    description: str


def normalized(text):
    return "".join(
        c for c in unicodedata.normalize("NFD", text.casefold()) if unicodedata.category(c) != "Mn"
    )


def extract_requirements(request, count):
    """Conservative Portuguese recognizer; unknown prose stays visible for review."""
    reqs = [
        Requirement(id="slides", kind="slides", minimum=count, description=f"{count} slides"),
        Requirement(id="margins", kind="margins", description="Margens de 64 px"),
    ]
    ordinals = {
        "primeiro": 1,
        "segundo": 2,
        "terceiro": 3,
        "quarto": 4,
        "quinto": 5,
        "sexto": 6,
        "setimo": 7,
        "oitavo": 8,
        "nono": 9,
        "decimo": 10,
    }
    text = normalized(request)
    pattern = r"(?:slide\s+(\d+)|\b(" + "|".join(ordinals) + r")\s+slide)"
    marks = list(re.finditer(pattern, text))
    if not marks and count == 1:
        sections = [(1, text)]
    else:
        sections = [
            (
                int(m[1]) if m[1] else ordinals[m[2]],
                text[m.end() : marks[i + 1].start() if i + 1 < len(marks) else len(text)],
            )
            for i, m in enumerate(marks)
        ]
    for slide, clause in sections:
        if slide > count:
            continue
        clause = re.sub(
            r"\b(?:sem|nao (?:inclua|use|coloque|adicione))\s+(?:(?:um|uma|nenhum|nenhuma)\s+)?"
            r"(?:rodape|imagem|imagens|formas?|retangulos?|elipses?|grupos|colunas|cards|fluxo|camadas)\b",
            "",
            clause,
        )

        def add(kind, description, **kwargs):
            reqs.append(
                Requirement(
                    id=f"s{slide}_{kind}_{len(reqs)}",
                    kind=kind,
                    slide=slide,
                    description=description,
                    **kwargs,
                )
            )

        if re.search(r"\b(?:formas?|retangulos?|elipses?)\b", clause):
            n = re.search(
                r"(\d+|duas|dois|tres|quatro|uma|um)\s+(?:formas?|retangulos?|elipses?)", clause
            )
            number = {"duas": 2, "dois": 2, "tres": 3, "quatro": 4, "uma": 1, "um": 1}
            minimum = number.get(n[1], int(n[1]) if n and n[1].isdigit() else 1) if n else 1
            add(
                "shapes",
                "Formas solicitadas e cores",
                minimum=minimum,
                distinct_colors=bool(
                    re.search(r"coloridas|cores distintas|cores diferentes", clause)
                ),
            )
        if "imagem" in clause:
            add("images", "Imagem local presente")
        if "camadas" in clause or ("tras" in clause and "frente" in clause):
            add("layers", "Imagem atrás e depois à frente, com sobreposição parcial")
        if "grupos" in clause:
            add("groups", "Dois grupos separados por 64 px", minimum=2)
        if "colunas" in clause or "comparacao" in clause:
            add("columns", "Conteúdo em duas colunas", minimum=2)
        if "rodape" in clause:
            add("footer", "Texto na região de rodapé")
        for word, component in [("cards", "cards"), ("etapas", "sequence"), ("fluxo", "flow")]:
            if word in clause:
                add("component", f"Componente {component}", value=component)
    return [r.model_dump() for r in reqs]


def evaluate_requirements(validation, requirements, plan=None):
    from .benchmarking import instruction_coverage

    requirements = [Requirement.model_validate(r) for r in requirements]
    if len({r.id for r in requirements}) != len(requirements):
        raise ValueError("Requisitos devem ter IDs únicos")
    deck = validation.ir if validation else None
    original = instruction_coverage(validation)["items"] if validation else {}
    rows, diagnostics = [], []
    for r in requirements:
        slides = [s for s in deck.slides if r.slide is None or s.number == r.slide] if deck else []
        elements = [e for s in slides for e in s.elements]
        witnesses, ok, detail = [], False, {}
        if r.kind == "original":
            ok = original.get(r.value, False)
            witnesses = [e.id for e in elements]
        elif r.kind == "slides":
            ok = bool(deck and len(deck.slides) == r.minimum)
        elif r.kind == "shapes":
            selected = [
                e for e in elements if e.type in {"rectangle", "ellipse"} and e.role != "background"
            ]
            witnesses = [e.id for e in selected]
            colors = {e.color for e in selected if e.color}
            ok = len(selected) >= r.minimum and (not r.distinct_colors or len(colors) >= r.minimum)
            detail = {"count": len(selected), "colors": sorted(colors)}
        elif r.kind == "images":
            witnesses = [
                e.id for e in elements if e.type == "image" and (not r.value or e.file == r.value)
            ]
            ok = len(witnesses) >= r.minimum
        elif r.kind == "layers":
            for s in slides:
                ast_slide = (
                    next((a for a in validation.ast.slides if a.number == s.number), None)
                    if validation.ast
                    else None
                )

                def flatten(commands):
                    return [
                        x
                        for c in commands
                        for x in (flatten(c.children) if c.op == "layout" else [c])
                    ]

                commands = flatten(ast_slide.commands) if ast_slide else []
                for image in (e for e in s.elements if e.type == "image"):
                    ops = [c.op for c in commands if c.id == image.id and c.op in {"back", "front"}]
                    actions = "back" in ops and "front" in ops[ops.index("back") + 1 :]
                    for shape in (
                        e for e in s.elements if e.type == "rectangle" and e.role != "background"
                    ):
                        overlap = intersection(box(image), box(shape))
                        if (
                            actions
                            and image.z > shape.z
                            and overlap
                            and 0 < area(overlap) < min(area(box(image)), area(box(shape)))
                        ):
                            ok, witnesses = True, [shape.id, image.id]
        elif r.kind == "groups":
            for s in slides:
                lookup = {e.id: e for e in s.elements}
                groups = [
                    g
                    for g in s.groups
                    if len(g.members) >= 2 and all(i in lookup for i in g.members)
                ]
                boxes = [bounds([lookup[i] for i in g.members]) for g in groups]
                if len(groups) >= r.minimum and all(
                    distance(a, b) >= 64 for i, a in enumerate(boxes) for b in boxes[i + 1 :]
                ):
                    ok, witnesses = True, [g.id for g in groups]
        elif r.kind == "columns":
            texts = [e for e in elements if e.type == "text" and e.role == "corpo"]
            ok = any(e.x < 640 for e in texts) and any(e.x >= 640 for e in texts)
            witnesses = [e.id for e in texts]
        elif r.kind == "footer":
            witnesses = [e.id for e in elements if e.type == "text" and e.text and e.y >= 580]
            ok = bool(witnesses)
        elif r.kind == "margins":
            selected = [e for e in elements if e.role != "background"]
            ok = bool(deck) and all(
                e.x >= 64 and e.y >= 64 and e.x + e.width <= 1216 and e.y + e.height <= 656
                for e in selected
            )
            witnesses = [e.id for e in selected]
        elif r.kind == "text":
            witnesses = [
                e.id for e in elements if e.text and normalized(r.value) in normalized(e.text)
            ]
            ok = bool(witnesses)
        elif r.kind == "component":
            # Component evidence is emitted geometry, never solely a plan declaration.
            panels = [
                e for e in elements if re.search(r"_panel\d+$", e.id) and e.type == "rectangle"
            ]
            bodies = [e for e in elements if re.search(r"_c1_i\d+$", e.id) and e.type == "text"]
            ok = bool(panels and len(panels) == len(bodies))
            if r.value == "cards":
                ok = ok and all(e.width == 544 for e in panels)
            elif r.value == "sequence":
                ok = ok and all(
                    (e.text or "").startswith(f"{i}. ") for i, e in enumerate(bodies, 1)
                )
            if r.value == "flow":
                arrows = [e for e in elements if e.text == "↓" or e.type == "arrow"]
                nodes = sorted(bodies, key=lambda e: e.y)
                ok = ok and {e.y for e in arrows} == {e.y + e.height for e in nodes[:-1]}
            witnesses = [e.id for e in panels + bodies]
        path = repair_path(r)
        row = {
            **r.model_dump(),
            "met": bool(ok),
            "elements": witnesses,
            "evidence": detail,
            "path": path,
        }
        rows.append(row)
        if not ok:
            diagnostics.append(
                {
                    "code": "R001",
                    "severity": "ERRO",
                    "message": r.description,
                    "slide": r.slide,
                    "element": None,
                    "evidence": {"requirement": r.id, "path": path, **detail},
                }
            )
    return {
        "items": {r["id"]: r["met"] for r in rows},
        "details": rows,
        "numerator": sum(r["met"] for r in rows),
        "denominator": len(rows),
        "all_met": all(r["met"] for r in rows),
        "diagnostics": diagnostics,
        "limitation": "Reconhecedor português limitado; verificações estruturais não avaliam verdade factual ou beleza. Requisitos não reconhecidos exigem revisão humana.",
    }


def repair_path(r):
    if r.kind == "original":
        paths = {
            "title": "title",
            "theme": "theme",
            "contrast_examples": "slides.1.decorations",
            "layer_actions": "slides.3.relations",
            "local_image": "slides.3.decorations",
            "final_layer": "slides.3.decorations",
            "proximity_groups": "slides.2.columns",
            "comparison_columns": "slides.4.columns",
            "footer": "slides.4.footer",
        }
        return paths.get(r.value)
    if r.slide:
        field = {
            "shapes": "decorations",
            "images": "decorations",
            "layers": "relations",
            "groups": "columns",
            "columns": "columns",
            "footer": "footer",
            "text": "columns",
            "component": "layout",
        }.get(r.kind)
        return f"slides.{r.slide - 1}.{field}" if field else None
    return None
