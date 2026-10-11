"""Purposeful native-object compositions; no generated content or arbitrary geometry."""

from .layouts import text_height


def compose_slide(slide, base, add, issue, title_font=36):
    layout = slide.layout
    two = layout == "comparison_visual"
    if len(slide.columns) != (2 if two else 1):
        issue("L001", "Quantidade de colunas incompatível com a composição.", base + ".columns")
    if slide.decorations or slide.relations or slide.media:
        issue(
            "L007", "Composição usa seus próprios objetos; campos adicionais incompatíveis.", base
        )
    bottom = 612 if slide.footer else 656

    def text(key, path, label, x, y, w, h, font=22, role="corpo", color="texto"):
        if not label.strip():
            issue("L003", "Texto vazio.", path)
        if role == "corpo":
            while font > 18 and text_height(label, w, font) > h:
                font -= 1
        if text_height(label, w, font) > h or y + h > bottom:
            issue("L004", "Texto completo excede a composição; reduza ou reorganize o plano.", path)
        return add(key, path, "text", x, y, w, h, text=label, font=font, role=role, color=color)

    def panel(key, path, x, y, w, h):
        add(key, path, "rectangle", x, y, w, h, color="secundaria", role="background")
        add(key + "_signal", path, "rectangle", x, y, 5, h, color="primaria", role="background")

    if layout == "visual_cover":
        add(
            "signal",
            base + ".layout",
            "rectangle",
            64,
            144,
            8,
            272,
            color="primaria",
            role="decoracao",
        )
        text("titulo", base + ".title", slide.title, 88, 144, 704, 272, title_font, "titulo")
        for ci, col in enumerate(slide.columns):
            path = f"{base}.columns.{ci}"
            if col.heading:
                text("c1_heading", path + ".heading", col.heading, 88, 452, 704, 144, 24)
            if len(col.items) > 3:
                issue("L006", "Capa suporta até três conceitos.", path + ".items")
            for i, item in enumerate(col.items):
                y = 160 + i * 168
                panel(f"panel{i + 1}", path + f".items.{i}", 864, y, 352, 160)
                text(f"c1_i{i + 1}", path + f".items.{i}", item, 880, y + 12, 320, 136, 20)
    else:
        text("titulo", base + ".title", slide.title, 64, 64, 1152, 144, title_font, "titulo")
        add(
            "signal",
            base + ".layout",
            "rectangle",
            64,
            208,
            96,
            5,
            color="primaria",
            role="decoracao",
        )
        for ci, col in enumerate(slide.columns):
            path = f"{base}.columns.{ci}"
            x = 64 + ci * 608 if two else 64
            if col.group:
                issue("L007", "Grupos explícitos exigem um layout compatível.", path + ".group")
            if layout == "comparison_visual":
                panel(f"comparison{ci + 1}", path + ".heading", x, 224, 544, 112)
                text(f"c{ci + 1}_heading", path + ".heading", col.heading, x + 24, 232, 496, 96, 24)
                if not 2 <= len(col.items) <= 3:
                    issue(
                        "L006",
                        "Comparação suporta dois ou três nós por alternativa.",
                        path + ".items",
                    )
                for i, item in enumerate(col.items):
                    if col.representation == "services" and i < 2:
                        nx, ny, nw, nh, font = x + i * 280, 352, 264, 152, 18
                    elif col.representation == "services":
                        nx, ny, nw, nh, font = x, 528, 544, 120, 20
                    else:
                        nx, ny, nw, nh, font = x, 344 + i * 104, 544, 92, 20
                    panel(f"c{ci + 1}_panel{i + 1}", path + f".items.{i}", nx, ny, nw, nh)
                    text(
                        f"c{ci + 1}_i{i + 1}",
                        path + f".items.{i}",
                        item,
                        nx + 16,
                        ny + 4,
                        nw - 32,
                        nh - 8,
                        font,
                    )
                    if i < len(col.items) - 1 and col.representation == "stack":
                        add(
                            f"c{ci + 1}_link{i + 1}",
                            path + ".representation",
                            "arrow",
                            x + 256,
                            ny + nh,
                            32,
                            12,
                            color="primaria",
                            role="decoracao",
                        )
            elif layout in {"architecture_diagram", "visual_flow", "visual_sequence"}:
                if not 2 <= len(col.items) <= 3:
                    issue(
                        "L006", "Diagrama suporta dois ou três nós sem paginação.", path + ".items"
                    )
                if col.heading:
                    text("c1_heading", path + ".heading", col.heading, 64, 224, 1152, 36, 20)
                for i, item in enumerate(col.items):
                    y = 264 + i * 128
                    panel(f"panel{i + 1}", path + f".items.{i}", 64, y, 1152, 108)
                    text(f"c1_i{i + 1}", path + f".items.{i}", item, 112, y + 8, 1056, 92, 22)
                    if i < len(col.items) - 1 and (
                        layout != "architecture_diagram" or col.representation == "stack"
                    ):
                        add(
                            f"link{i + 1}",
                            path + ".representation",
                            "arrow",
                            624,
                            y + 108,
                            32,
                            20,
                            color="primaria",
                            role="decoracao",
                        )
                    if layout == "visual_sequence":
                        text(
                            f"step{i + 1}",
                            path + ".representation",
                            str(i + 1),
                            72,
                            y + 12,
                            36,
                            64,
                            22,
                            "decoracao",
                        )
            elif layout == "takeaway":
                if col.heading:
                    text("c1_heading", path + ".heading", col.heading, 64, 224, 1152, 48, 22)
                for i, item in enumerate(col.items):
                    if i == 0:
                        panel("panel1", path + ".items.0", 64, 288, 1152, 192)
                        text("c1_i1", path + ".items.0", item, 96, 304, 1088, 160, 30)
                    else:
                        text(
                            f"c1_i{i + 1}",
                            path + f".items.{i}",
                            item,
                            64,
                            504 + (i - 1) * 76,
                            1152,
                            68,
                            22,
                        )
            else:
                if len(col.items) > 4:
                    issue("L006", "Cards suportam até quatro itens.", path + ".items")
                if col.heading:
                    text("c1_heading", path + ".heading", col.heading, 64, 224, 1152, 64, 20)
                for i, item in enumerate(col.items):
                    cx, cy = 64 + (i % 2) * 608, (304 if col.heading else 272) + (i // 2) * 184
                    panel(f"panel{i + 1}", path + f".items.{i}", cx, cy, 544, 160)
                    text(f"c1_i{i + 1}", path + f".items.{i}", item, cx + 24, cy + 12, 496, 136, 22)
    if slide.footer:
        add(
            "rodape",
            base + ".footer",
            "text",
            64,
            628,
            1152,
            28,
            text=slide.footer,
            font=12,
            role="decoracao",
        )
