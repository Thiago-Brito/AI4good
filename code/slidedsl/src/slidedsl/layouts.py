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

        content_width = (
            1152 if slide.layout in {"title_content", "sequence", "cards", "flow"} else 544
        )
        compact = bool(slide.decorations) and any(
            216
            + (max(64, text_height(c.heading, content_width, 24)) + 16 if c.heading else 0)
            + sum(text_height(t, content_width, 18) for t in c.items)
            + 16 * (len(c.items) - 1)
            > 420
            for c in slide.columns
        )
        # Decorations are below text; overlap is intentional only in the overlay slot.
        for i, decoration in enumerate(slide.decorations):
            x = {"left": 160, "right": 800, "overlay": 360}[decoration.slot]
            y = (
                (540 if decoration.slot != "overlay" else 568)
                if compact
                else (450 if decoration.slot != "overlay" else 478)
            )
            add(
                f"d{i + 1}",
                f"{base}.decorations.{i}",
                decoration.kind,
                x,
                y,
                280 if decoration.slot == "overlay" else 300,
                (80 if decoration.slot == "overlay" else 100)
                if compact
                else (120 if decoration.slot == "overlay" else 145),
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
        component = slide.layout in {"sequence", "cards", "flow"}
        expected = 1 if slide.layout == "title_content" or component else 2
        if len(slide.columns) != expected:
            issue("L001", f"Layout {slide.layout} exige {expected} coluna(s).", f"{base}.columns")
        width = 1152 if expected == 1 else 544
        bottom = (512 if compact else 420) if slide.decorations else (600 if slide.footer else 640)
        for ci, column in enumerate(slide.columns):
            x = 64 + ci * (width + 64)
            y = 216
            if component:
                start_y = 216
                if column.heading:
                    heading_height = max(64, text_height(column.heading, 1152, 24))
                    add(
                        "c1_heading",
                        f"{base}.columns.{ci}.heading",
                        "text",
                        64,
                        216,
                        1152,
                        heading_height,
                        text=column.heading,
                        font="corpo",
                    )
                    start_y = 216 + heading_height + 16
                members = []
                if len(column.items) > 4 or len(slide.columns) != 1:
                    issue(
                        "L006",
                        "Componente suporta uma coluna e até quatro itens.",
                        f"{base}.columns",
                    )
                for ti, text in enumerate(column.items):
                    cx = 64 + (ti % 2) * 608 if slide.layout == "cards" else 64
                    cy = start_y + (ti // 2) * 176 if slide.layout == "cards" else start_y + ti * 92
                    cw = 544 if slide.layout == "cards" else 1152
                    ch = 144 if slide.layout == "cards" else 72
                    add(
                        f"panel{ti + 1}",
                        f"{base}.columns.{ci}.items.{ti}",
                        "rectangle",
                        cx,
                        cy,
                        cw,
                        ch,
                        color="secundaria",
                        role="background",
                    )
                    label = f"{ti + 1}. {text}" if slide.layout == "sequence" else text
                    id = add(
                        f"c1_i{ti + 1}",
                        f"{base}.columns.{ci}.items.{ti}",
                        "text",
                        cx + 16,
                        cy + 8,
                        cw - 32,
                        ch - 16,
                        text=label,
                        font=20,
                    )
                    members.append(id)
                    if not text.strip():
                        issue("L003", "Item textual vazio.", mapping[id], id)
                    if text_height(label, cw - 32, 20) > ch - 16 or cy + ch > bottom:
                        issue("L004", "Conteúdo excede o componente.", mapping[id], id)
                if column.group:
                    if len(members) < 2:
                        issue(
                            "L005",
                            "Grupo exige pelo menos dois itens.",
                            f"{base}.columns.{ci}.group",
                        )
                    else:
                        group_id = f"s{number}_g{ci + 1}"
                        commands.append(
                            Command(
                                op="group",
                                id=group_id,
                                ids=members,
                                text=column.heading or "Componente",
                            )
                        )
                        mapping[group_id] = f"{base}.columns.{ci}.group"
                continue
            heading_height = max(64, text_height(column.heading, width, 24))
            if slide.layout == "comparison" and column.heading:
                add(
                    f"comparison{ci + 1}",
                    f"{base}.layout",
                    "rectangle",
                    x,
                    208,
                    width,
                    heading_height + 12,
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
                    heading_height,
                    text=column.heading,
                    font="corpo",
                )
                y += heading_height + 16
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
            elif relation.kind == "next":
                nodes = {c.id: c for c in commands if c.op == "add"}
                a, b = nodes[reference], nodes[target]
                if (
                    slide.layout != "flow"
                    or b.position.y <= a.position.y
                    or not (
                        relation.target.startswith("c1_i") and relation.reference.startswith("c1_i")
                    )
                ):
                    issue("L002", "next exige nós do fluxo em ordem vertical.", path)
                else:
                    add(
                        f"link{ri + 1}",
                        path,
                        "text",
                        616,
                        a.position.y + a.size[1],
                        48,
                        36,
                        text="↓",
                        font=12,
                        role="decoracao",
                    )
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
