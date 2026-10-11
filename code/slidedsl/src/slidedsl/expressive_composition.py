"""Finite, measured composition alternatives; no free geometry or text truncation."""

import math

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .layouts import contain
from .text_metrics import text_height, text_width, manifest
from .planning import ContentBlock
from .printer import print_ast
from .pipeline import validate_source
from .visual_validation import check_visual


CONTENT_SYSTEM = """Planeje conteúdo em português conforme pedido e visual_outline.
Retorne somente JSON com title, theme e slide_1, slide_2 etc. conforme schema.
Cada título é a mensagem da primeira etapa e deve ser sustentado pelo conteúdo.
Sem IDs ou coordenadas. decorations=[], relations=[], group=false.
Contrato expressivo: cada item tem label, detail e explanation, todos strings.
label nomeia a entidade; detail é uma descrição curta de sua função; explanation
explica um conceito, exemplo, condição ou trade-off pertinente. Pode ser vazia
quando o diagrama já explica o conteúdo. Não repita label, detail ou título.
Não há regra de oito palavras para explanation. Prefira uma frase concreta.
Escolha a quantidade necessária ao pedido, não preencha a capacidade máxima.
Até seis conceitos curtos ou cinco camadas curtas; explicações longas precisam
de menos elementos. Com imagem use até três elementos. Comparação: até três
por alternativa. Em quatro a seis cards, explanation deve ser vazia e detail breve.
Em diagramas/comparações com três ou mais nós, deixe explanation
vazia, salvo necessidade explícita; detail deve explicar a função em uma frase curta.
Para aprofundar conceitos, use dois ou três elementos com explanation específica.
O compilador rejeita texto que não cabe a 22 pt, sem cortar.
composition escolhe auto, grid, row ou vertical conforme as opções do schema.
auto compara composições medidas; stack/flow/sequence preservam ordem vertical.
Não invente relações entre serviços. Não acrescente decoração nem relação livre.
Mídia é opcional em capa, conceito, benefícios, comparação e conclusão. Use-a
somente para explicar a mensagem; assets exclusivamente da lista images.
Uma comparação com mídia usa uma imagem pertinente por alternativa.
Sem ativo selecionado e pesquisa desativada use media=[]; não prometa imagem.
Em comparison com stack use CAMADAS REAIS (Interface, Negócio, Dados), não vantagens.
Em services use SERVIÇOS REAIS (Pedidos, Pagamentos, Estoque), sem conectá-los.
Exemplos: adapte ao assunto; não force esses nomes fora de arquitetura de software.
Não escreva sobre o próprio slide, sua estética ou suas intenções de apresentação.
Conclua todas as frases com ponto; não esgote o limite de caracteres.
Não repita a mensagem principal na conclusão; explique uma decisão contextual.
Preserve condições das vantagens e conclusão contextual, sem superioridade universal.
"""


DIAGRAM_LAYOUTS = {"architecture_diagram", "comparison_visual", "visual_flow", "visual_sequence"}


def connected(slide, column):
    if slide.semantic:
        from .semantic_planning import DRAWN_TYPES

        ci = next(i for i, c in enumerate(slide.columns) if c is column) + 1
        if any(
            r.type in DRAWN_TYPES and r.source.startswith(f"c{ci}_") for r in slide.relationships
        ):
            return True
    return slide.layout in {"visual_flow", "visual_sequence"} or (
        slide.layout in DIAGRAM_LAYOUTS and column.representation == "stack"
    )


def modes_for(slide):
    return (
        ["vertical"]
        if any(connected(slide, c) for c in slide.columns)
        or (
            slide.semantic
            and slide.layout == "comparison_visual"
            and any(c.representation == "cards" for c in slide.columns)
        )
        else ["grid", "row", "vertical"]
    )


def block_schema(layout):
    node = ContentBlock.model_json_schema()
    for key in ("role", "sources"):
        node["properties"].pop(key)
    node["required"] = list(node["properties"])
    node["properties"]["label"]["maxLength"] = 40
    node["properties"]["detail"]["maxLength"] = 80
    node["properties"]["explanation"]["maxLength"] = 160
    for field in ["detail", "explanation"]:
        node["properties"][field]["pattern"] = r"^$|[.!?]$"
    if layout in {"architecture_diagram", "visual_flow", "visual_sequence", "comparison_visual"}:
        node["properties"]["explanation"] = {"type": "string", "const": ""}
    if layout == "comparison_visual":
        node["properties"]["detail"]["maxLength"] = 80
        node["properties"]["label"]["maxLength"] = 30
    return node


def content_array(layout, minimum, maximum):
    from copy import deepcopy

    node = block_schema(layout)
    normal = {"type": "array", "minItems": minimum, "maxItems": min(3, maximum), "items": node}
    if maximum <= 3 or layout in {"architecture_diagram", "visual_flow", "visual_sequence"}:
        normal["maxItems"] = maximum
        return normal
    concise = deepcopy(node)
    concise["properties"]["explanation"] = {"type": "string", "const": ""}
    concise["properties"]["detail"]["maxLength"] = 40
    concise["properties"]["label"]["maxLength"] = 30
    return {
        "anyOf": [normal, {"type": "array", "minItems": 4, "maxItems": maximum, "items": concise}]
    }


def expressive_schema(schema, outline, explicit=None):
    from .visual_planning import constrain_visual_schema, COMPOSED_LAYOUTS

    result = constrain_visual_schema(schema, outline, explicit)
    for variant in result["properties"]["slides"]["prefixItems"]:
        props = variant["properties"]
        layout = props["layout"]["const"]
        if layout not in COMPOSED_LAYOUTS:
            continue  # Explicit historical image layouts keep their existing contract.
        columns = [props["columns"]["items"], *props["columns"].get("prefixItems", [])]
        ordered = layout in {"visual_flow", "visual_sequence"} or (
            layout in DIAGRAM_LAYOUTS
            and any(c["properties"]["representation"]["const"] == "stack" for c in columns)
        )
        props["expressive"] = {"type": "boolean", "const": True}
        props["composition"] = {
            "type": "string",
            "enum": ["auto", "vertical"] if ordered else ["auto", "grid", "row", "vertical"],
        }
        variant["required"] += ["expressive", "composition"]
        maximum = 3 if layout in {"comparison_visual", "visual_cover"} else 5 if ordered else 6
        if layout == "takeaway":
            maximum = 4
        for col in columns:
            if layout in {"concept_map", "benefit_cards", "comparison_visual"}:
                col["properties"]["items"]["minItems"] = 1
            col["properties"]["items"]["maxItems"] = maximum
            col["properties"]["items"]["items"]["maxLength"] = 624
            col["properties"]["content"] = content_array(
                layout, col["properties"]["items"]["minItems"], maximum
            )
            col["required"].append("content")
        if layout in {"visual_cover", "concept_map", "benefit_cards", "takeaway"}:
            props["media"].update(minItems=0, maxItems=1)
            variant["allOf"] = [
                {
                    "if": {"properties": {"media": {"minItems": 1}}},
                    "then": {
                        "properties": {
                            "columns": {
                                "items": {
                                    "properties": {
                                        "items": {"maxItems": 3},
                                        "content": {"maxItems": 3},
                                    }
                                }
                            }
                        }
                    },
                }
            ]
        elif layout == "comparison_visual" and not ordered:
            props["media"] = {
                "anyOf": [
                    {"type": "array", "maxItems": 0},
                    {
                        "type": "array",
                        "items": {"$ref": "#/$defs/MediaPlan"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                ]
            }
    return result


def build_candidate(slide, number, mode, style=""):
    """Measure first; fixed typographic roles never shrink to manufacture capacity."""
    commands, paths, failures, panels = [], {}, [], []
    base = f"slides.{number - 1}"
    if slide.semantic or slide.relationships:
        from .semantic_planning import relation_issues

        failures.extend(
            (code, message, base + "." + path) for code, message, path in relation_issues(slide)
        )

    def add(key, path, kind, rect, text=None, font=22, role="corpo", color="texto", file=None):
        x, y, w, h = rect
        id = f"s{number}_{key}"
        commands.append(
            Command(
                op="add",
                id=id,
                element_type=kind,
                position=Position(kind="absolute", x=x, y=y),
                size=(w, h),
                text=text,
                font_size=font if kind == "text" else None,
                role=role,
                color=None if kind == "image" else color,
                file=file,
            )
        )
        paths[id] = path
        return id

    def text(key, path, value, x, y, width, font=22, role="corpo"):
        bold = key.endswith("_ref_label")
        height = text_height(value, width, font, bold)
        if any(text_width(word, font, bold) > width - 16 for word in value.split()):
            failures.append(("L004", "Palavra inteira excede a largura da caixa.", path))
        add(key, path, "text", (x, y, width, height), value, font, role)
        return height

    title_height = text("titulo", base + ".title", slide.title, 64, 64, 1152, 42, "titulo")
    top = max(208, 64 + title_height + 12)
    bottom = 604 if slide.footer else 656
    expected = 2 if slide.layout == "comparison_visual" else 1
    if len(slide.columns) != expected:
        failures.append(("L001", "Número de colunas incompatível.", base + ".columns"))
    if slide.decorations or slide.relations or any(c.group for c in slide.columns):
        failures.append(
            ("L007", "Composição expressiva não reorganiza restrições explícitas.", base)
        )
    if slide.media and (
        len(slide.media) != expected
        or slide.layout in {"architecture_diagram", "visual_flow", "visual_sequence"}
        or any(connected(slide, c) for c in slide.columns)
    ):
        failures.append(
            ("L008", "Mídia incompatível com a estrutura ou cardinalidade.", base + ".media")
        )

    for ci, col in enumerate(slide.columns):
        x, width = 64 + ci * 608, 544 if expected == 2 else 1152
        y = top
        if col.heading:
            header_h = text(
                f"c{ci + 1}_heading",
                f"{base}.columns.{ci}.heading",
                col.heading,
                x,
                y,
                width,
                26,
            )
            if slide.semantic and expected == 2:
                header_h = max(text_height(c.heading, width, 26) for c in slide.columns)
            y += header_h + 12
        if slide.media:
            from .media import resolve_asset

            media = slide.media[min(ci, len(slide.media) - 1)]
            path = f"{base}.media.{ci}"
            if expected == 1:
                image_box = (672, y, 544, min(300, bottom - y - 64))
                width = 544
            else:
                image_box = (x, y, width, 100)
                y += 100 + 16
            if not media.asset:
                failures.append(("M001", "Imagem não selecionada.", path + ".asset"))
            else:
                try:
                    asset = resolve_asset(media.asset)
                    add(
                        f"media{ci + 1}",
                        path + ".asset",
                        "image",
                        contain(asset["width"], asset["height"], image_box),
                        role="decoracao",
                        file=media.asset,
                    )
                except ValueError as exc:
                    failures.append(("M002", str(exc), path + ".asset"))
            if media.caption:
                cx, cy, cw, ch = image_box
                caption_h = text(
                    f"caption{ci + 1}",
                    path + ".caption",
                    media.caption,
                    cx,
                    cy + ch + 8,
                    cw,
                    18,
                    "decoracao",
                )
                if expected == 2:
                    y += caption_h + 8
                elif cy + ch + 8 + caption_h > bottom:
                    failures.append(("L004", "Legenda excede o espaço.", path + ".caption"))
        blocks = col.content or [ContentBlock(label=t) for t in col.items]
        count = len(blocks)
        # At most six short concepts, five ordered nodes, three alongside media.
        limit = (
            3
            if slide.media or expected == 2
            else 5
            if mode == "vertical" and connected(slide, col)
            else 6
        )
        if count > limit:
            failures.append(
                (
                    "L006",
                    "Quantidade excede a capacidade desta composição.",
                    f"{base}.columns.{ci}.{'content' if col.content else 'items'}",
                )
            )
        nc = (
            1
            if mode == "vertical"
            else count
            if mode == "row"
            else min(3 if width > 1000 and count >= 5 else 2, count)
        )
        rows = math.ceil(count / nc)
        gap = 16 if mode == "vertical" else 24
        if slide.semantic and any(
            r.source.startswith(f"c{ci + 1}_")
            and r.type in {"calls", "accesses", "depends_on", "precedes"}
            for r in slide.relationships
        ):
            gap = 48
        cw = (width - (nc - 1) * gap) / nc
        inline = mode == "vertical" and width >= 500 and (not slide.media or expected == 2)

        def dimensions(block, i, side):
            lw, bw = (cw * 0.36 - 32, cw * 0.64 - 48) if side else (cw - 40, cw - 40)
            label = block.label if slide.layout != "visual_sequence" else f"{i + 1}. {block.label}"
            lh = text_height(label, lw, 24, True)
            bh = sum(text_height(t, bw, 22) for t in [block.detail, block.explanation] if t)
            if block.detail and block.explanation:
                bh += 8
            return (
                max(lh, bh) + 12
                if side
                else lh + (8 + bh if bh else 0) + (12 if mode == "vertical" else 32)
            )

        if inline and (
            any(
                text_width(word, 24, True) > cw * 0.36 - 48
                for b in blocks
                for word in b.label.split()
            )
            or sum(dimensions(b, i, False) for i, b in enumerate(blocks))
            < sum(dimensions(b, i, True) for i, b in enumerate(blocks))
        ):
            inline = False
        heights = [dimensions(block, i, inline) for i, block in enumerate(blocks)]
        if (
            slide.semantic
            and expected == 2
            and all(c.representation == "cards" for c in slide.columns)
            and len(slide.columns[0].content) == len(slide.columns[1].content)
        ):
            peers = [b for c in slide.columns for b in c.content]
            inline = all(
                text_width(word, 24, True) <= cw * 0.36 - 48
                for b in peers
                for word in b.label.split()
            ) and sum(dimensions(b, 0, True) for b in peers) <= sum(
                dimensions(b, 0, False) for b in peers
            )
            heights = [
                max(dimensions(c.content[i], i, inline) for c in slide.columns)
                for i in range(count)
            ]
        row_heights = [max(heights[r * nc : (r + 1) * nc]) for r in range(rows)]
        used = sum(row_heights) + (rows - 1) * gap
        if used > bottom - y:
            failures.append(
                (
                    "L004",
                    "Texto completo não cabe a 22 pt; escolha menos elementos ou outra composição.",
                    f"{base}.columns.{ci}.{'content' if col.content else 'items'}",
                )
            )
        y += max(0, (bottom - y - used) / 2)
        previous = None
        for i, block in enumerate(blocks):
            row, column = divmod(i, nc)
            rh = row_heights[row]
            row_count = min(nc, count - row * nc)
            nx = x + (width - row_count * cw - (row_count - 1) * gap) / 2 + column * (cw + gap)
            ny = y + sum(row_heights[:row]) + row * gap
            path = (
                f"{base}.columns.{ci}.content.{i}"
                if col.content
                else f"{base}.columns.{ci}.items.{i}"
            )
            key = f"c{ci + 1}_i{i + 1}"
            panel = add(
                key + "_panel",
                path,
                "rectangle",
                (nx, ny, cw, rh),
                role="background",
                color="secundaria",
            )
            panels.append((nx, ny, cw, rh))
            label = block.label if slide.layout != "visual_sequence" else f"{i + 1}. {block.label}"
            lw, bw = (cw * 0.36 - 32, cw * 0.64 - 48) if inline else (cw - 40, cw - 40)
            lh = text(
                key + "_ref_label",
                path + ".label" if col.content else path,
                label,
                nx + 20,
                ny + (6 if mode == "vertical" else 16),
                lw,
                24,
            )
            bx, by = (
                (nx + cw * 0.36 + 8, ny + 6)
                if inline
                else (nx + 20, ny + (6 if mode == "vertical" else 16) + lh + 8)
            )
            for field in ["detail", "explanation"]:
                value = getattr(block, field)
                if value:
                    by += text(key + "_" + field, path + "." + field, value, bx, by, bw) + 8
            edge = next(
                (
                    r
                    for r in slide.relationships
                    if r.source == f"c{ci + 1}_i{i}"
                    and r.target == key
                    and r.type in {"calls", "accesses", "depends_on", "precedes"}
                ),
                None,
            )
            if previous and connected(slide, col) and (not slide.semantic or edge is not None):
                source = next(c for c in commands if c.id == previous)
                arrow = add(
                    key + "_link",
                    path,
                    "arrow",
                    (nx + cw / 2 - 8, ny - gap, 16, gap),
                    role="decoracao",
                    color="primaria",
                )
                commands.extend(
                    [
                        Command(
                            op="move",
                            id=arrow,
                            position=Position(kind="below", reference=previous, margin=0),
                        ),
                        Command(
                            op="move",
                            id=panel,
                            position=Position(kind="below", reference=arrow, margin=0),
                        ),
                        Command(
                            op="move",
                            id=arrow,
                            position=Position(
                                kind="absolute",
                                x=source.position.x + source.size[0] / 2 - 8,
                                y=source.position.y + source.size[1],
                            ),
                        ),
                        Command(
                            op="move", id=panel, position=Position(kind="absolute", x=nx, y=ny)
                        ),
                    ]
                )
                if edge is not None:
                    from .semantic_planning import EDGE_LABELS

                    edge_index = slide.relationships.index(edge)
                    text(
                        key + "_edge_label",
                        f"{base}.relationships.{edge_index}.type",
                        EDGE_LABELS[edge.type],
                        nx + cw / 2 + 24,
                        ny - gap,
                        min(180, cw / 2 - 40),
                        18,
                        "decoracao",
                    )
            previous = panel
    if slide.footer:
        fh = text("rodape", base + ".footer", slide.footer, 64, 612, 1152, 12)
        if 612 + fh > 656:
            failures.append(("L004", "Rodapé excede o espaço reservado.", base + ".footer"))
    return SlideNode(number=number, commands=commands), paths, failures, panels


def select_candidate(slide, number, theme, style="", requirements=None):
    choices, reports = [], []
    modes = modes_for(slide)
    if slide.composition != "auto":
        modes = [slide.composition] if slide.composition in modes else []
    if not modes:
        modes = ["vertical"]  # Retain source for inspection, with an explicit failure.
    for mode in modes:
        node, paths, failures, panels = build_candidate(slide, number, mode, style)
        if slide.composition not in {"auto", *modes_for(slide)}:
            failures.append(
                (
                    "L007",
                    "Variante incompatível com a ordem espacial obrigatória.",
                    f"slides.{number - 1}.composition",
                )
            )
        validation = validate_source(
            print_ast(
                PresentationNode(
                    title="Composição", theme=theme, slides=[node.model_copy(update={"number": 1})]
                )
            )
        )
        if validation.ir:
            validation.ir.slides[0].number = number
        for diagnostic in validation.diagnostics:
            if diagnostic.slide is not None:
                diagnostic.slide = number
        visual = check_visual(validation.ir, paths) if validation.ir else []
        valid = (
            not failures
            and validation.success(strict=True)
            and not any(d["severity"] == "ERRO" for d in visual)
        )
        from .requirements import evaluate_requirements

        local_requirements = [r for r in requirements or [] if r.get("slide") == number]
        checks = evaluate_requirements(validation, local_requirements)["items"]
        # Prefer fewer wrapped lines and balanced rectangles. This is not an aesthetic score.
        text_area = sum(c.size[0] * c.size[1] for c in node.commands if c.element_type == "text")
        score = (
            text_area / (1152 * 592)
            + sum(abs(w / h - 2.8) for _, _, w, h in panels) / max(1, len(panels)) * 0.05
        )
        if "compact" in style.casefold() and mode == "vertical":
            score += 0.1
        reports.append(
            {
                "mode": mode,
                "valid": valid,
                "score": score,
                "failures": failures,
                "requirements": checks,
                "diagnostics": [d.model_dump() for d in validation.diagnostics] + visual,
            }
        )
        if valid:
            choices.append((-sum(checks.values()), score, mode, node, paths))
    if choices:
        _, _, mode, node, paths = min(choices, key=lambda c: (c[0], c[1], c[2]))
        return node, paths, [], {"slide": number, "chosen": mode, "candidates": reports}
    node, paths, failures, _ = build_candidate(slide, number, modes[0], style)
    if slide.composition not in {"auto", *modes_for(slide)}:
        failures.append(
            (
                "L007",
                "Variante incompatível com a ordem espacial obrigatória.",
                f"slides.{number - 1}.composition",
            )
        )
    failures = failures or [
        (
            "L004",
            "Nenhuma composição passou pela validação estrita/visual.",
            f"slides.{number - 1}.columns",
        )
    ]
    return node, paths, failures, {"slide": number, "chosen": None, "candidates": reports}


def composition_report(plan):
    return {
        "protocol": "expressive-planning-v1",
        "text_measurement": manifest(),
        "aesthetic_assessment": None,
        "slides": [
            select_candidate(
                s,
                i,
                plan.theme,
                (plan.refinement or {}).get("style", ""),
                (plan.refinement or {}).get("requirements", []),
            )[3]
            for i, s in enumerate(plan.slides, 1)
            if s.expressive
        ],
    }
