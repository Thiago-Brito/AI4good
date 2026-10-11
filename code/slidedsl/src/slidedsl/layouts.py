"""Deterministic plan compiler frontend; generated DSL uses the original pipeline."""

import math
from pathlib import Path

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .compiler import compile_source
from .design_rules import load_rules
from .diagnostics import Diagnostic
from .planning import DeckPlan
from .printer import print_ast


def text_height(text: str, width: float, font: int) -> int:
    cfg = load_rules()
    px = font * 96 / 72
    capacity = max(
        1, math.floor((width - 2 * cfg["text_padding"]) / (cfg["character_width_factor"] * px))
    )
    lines = sum(max(1, math.ceil(len(line) / capacity)) for line in text.split("\n"))
    return math.ceil(lines * px * cfg["line_height_factor"] + 2 * cfg["text_padding"] + 2)


def plan_to_dsl(plan: DeckPlan) -> tuple[str, dict[str, str], list[Diagnostic]]:
    """Return DSL, element-to-plan paths, and explicit plan/reference diagnostics.

    Content is never shortened, omitted or replaced. Overflow remains observable.
    """
    slides, mapping, diagnostics = [], {}, []
    for number, slide in enumerate(plan.slides, 1):
        commands, refs = [], {}
        base = f"slides.{number - 1}"

        def issue(code, message, path, element=None):
            diagnostics.append(
                Diagnostic(
                    code=code,
                    severity="ERRO",
                    message=message,
                    slide=number,
                    element=element,
                    evidence={"path": path},
                    suggestion="Corrija apenas o campo indicado no plano.",
                )
            )

        def add(
            key,
            path,
            kind,
            x,
            y,
            width,
            height,
            *,
            text=None,
            font=None,
            color="texto",
            role="corpo",
            file=None,
        ):
            id = f"s{number}_{key}"
            refs[key] = id
            mapping[id] = path
            commands.append(
                Command(
                    op="add",
                    id=id,
                    element_type=kind,
                    position=Position(kind="absolute", x=x, y=y),
                    size=(width, height),
                    text=text,
                    font_size=font,
                    color=color if kind != "image" else None,
                    role=role,
                    file=file,
                )
            )
            return id

        # Decorations are below text; overlap is intentional only in the overlay slot.
        for i, decoration in enumerate(slide.decorations):
            x = {"left": 160, "right": 800, "overlay": 360}[decoration.slot]
            y = 450 if decoration.slot != "overlay" else 478
            add(
                f"d{i + 1}",
                f"{base}.decorations.{i}",
                decoration.kind,
                x,
                y,
                280 if decoration.slot == "overlay" else 300,
                120 if decoration.slot == "overlay" else 145,
                color=decoration.color,
                role="decoracao",
                file="assets/imagem_demo.png" if decoration.kind == "image" else None,
            )

        add(
            "titulo",
            f"{base}.title",
            "text",
            64,
            64,
            1152,
            120,
            text=slide.title,
            font="titulo",
            role="titulo",
        )
        expected = 1 if slide.layout == "title_content" else 2
        if len(slide.columns) != expected:
            issue("L001", f"Layout {slide.layout} exige {expected} coluna(s).", f"{base}.columns")
        width = 1152 if expected == 1 else 544
        bottom = 420 if slide.decorations else (600 if slide.footer else 640)
        for ci, column in enumerate(slide.columns):
            x = 64 + ci * (width + 64)
            y = 216
            if slide.layout == "comparison" and column.heading:
                add(
                    f"comparison{ci + 1}",
                    f"{base}.layout",
                    "rectangle",
                    x,
                    208,
                    width,
                    76,
                    color="secundaria",
                    role="background",
                )
            if column.heading:
                add(
                    f"c{ci + 1}_heading",
                    f"{base}.columns.{ci}.heading",
                    "text",
                    x,
                    y,
                    width,
                    64,
                    text=column.heading,
                    font="corpo",
                )
                y += 80
            font = 24
            # Fit content with readable 18..24pt fonts; never truncate model text.
            while (
                font > 18
                and sum(text_height(t, width, font) for t in column.items)
                + 16 * (len(column.items) - 1)
                > bottom - y
            ):
                font -= 1
            members = []
            for ti, text in enumerate(column.items):
                height = text_height(text, width, font)
                id = add(
                    f"c{ci + 1}_i{ti + 1}",
                    f"{base}.columns.{ci}.items.{ti}",
                    "text",
                    x,
                    y,
                    width,
                    height,
                    text=text,
                    font=font,
                )
                if not text.strip():
                    issue("L003", "Item textual vazio.", mapping[id], id)
                if y + height > bottom:
                    issue("L004", "Conteúdo excede o espaço reservado ao layout.", mapping[id], id)
                if ti:
                    commands.append(Command(op="align", id=id, reference=members[0], axis="left"))
                members.append(id)
                y += height + 16
            if column.group:
                if len(members) < 2:
                    issue(
                        "L005",
                        "Grupo de proximidade exige pelo menos dois itens.",
                        f"{base}.columns.{ci}.group",
                    )
                else:
                    commands.append(
                        Command(
                            op="group",
                            id=f"s{number}_g{ci + 1}",
                            ids=members,
                            text=column.heading or f"Coluna {ci + 1}",
                        )
                    )
                    mapping[f"s{number}_g{ci + 1}"] = f"{base}.columns.{ci}.group"
        if slide.footer:
            add(
                "rodape",
                f"{base}.footer",
                "text",
                64,
                612,
                1152,
                44,
                text=slide.footer,
                font="rodape",
            )
        for ri, relation in enumerate(slide.relations):
            path = f"{base}.relations.{ri}"
            target = refs.get(relation.target)
            reference = refs.get(relation.reference)
            if not target or (
                relation.kind not in {"front", "back"} and (not reference or target == reference)
            ):
                issue("L002", "Relação aponta para elemento inexistente ou para si mesmo.", path)
                continue
            if relation.kind in {"front", "back"}:
                commands.append(Command(op=relation.kind, id=target))
            else:
                commands.append(
                    Command(op="align", id=target, reference=reference, axis=relation.kind)
                )
                # A moved target must map back to the relation rather than its text.
                mapping[target] = path
        slides.append(SlideNode(number=number, commands=commands))
    source = print_ast(PresentationNode(title=plan.title, theme=plan.theme, slides=slides))
    return source, mapping, diagnostics


def compile_plan(plan: DeckPlan, out: Path, *, strict=False) -> dict:
    source, mapping, diagnostics = plan_to_dsl(plan)
    if diagnostics:
        from .diagnostics import DSLException

        raise DSLException(diagnostics)
    return {
        **compile_source(source, out, strict=strict),
        "source": source,
        "element_paths": mapping,
    }
