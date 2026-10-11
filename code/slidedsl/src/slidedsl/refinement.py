"""Post-composition refinement with hard validation, content conservation and rollback.

Scores are engineering objectives, not measurements of aesthetic quality.
The output is ordinary AST/DSL; explicit spatial constraints are left untouched.
"""

from copy import deepcopy
import math
import re

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .layouts import text_height
from .pipeline import validate_source
from .printer import print_ast
from .visual_planning import COMPOSED_LAYOUTS
from .visual_validation import check_visual


def normalized(text):
    # Keep meaningful symbols (C++, operators, questions); ignore case/spacing/full stops.
    return re.sub(r"\s+", " ", text.casefold().strip()).rstrip(".")


def candidate(slide, number, mode, style, verbatim=False):
    commands, paths, duplicates = [], {}, []
    base = f"slides.{number - 1}"
    end = 604 if slide.footer else 656
    title_y, title_w = 64, 1152
    title_h = text_height(slide.title, title_w, 42)
    top = max(232, title_y + title_h + 20)
    panels = []

    def add(key, path, kind, x, y, w, h, text=None, font=22, color="texto", role="corpo"):
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
                color=color,
                role=role,
            )
        )
        paths[id] = path
        return id

    def panel(key, path, rect, accent="primaria"):
        x, y, w, h = rect
        id = add(key, path, "rectangle", x, y, w, h, color="secundaria", role="background")
        if "minimal" not in style.casefold():
            add(key + "_signal", path, "rectangle", x, y, 4, h, color=accent, role="background")
        panels.append(rect)
        return id

    def text(key, path, value, rect, font=22, color="texto", role="corpo"):
        return add(key, path, "text", *rect, text=value, font=font, color=color, role=role)

    def node(key, path, value, rect, horizontal=False):
        x, y, w, h = rect
        label, sep, detail = value.partition(": ") if not verbatim else (value, "", "")
        if sep and detail.casefold().startswith(label.casefold() + " "):
            detail = detail[len(label) :].lstrip()
            retained = label + ": " + detail
            duplicates.append(
                {
                    "path": path,
                    "text": label,
                    "represented_by": f"s{number}_{key}_ref_inline"
                    if slide.layout == "comparison_visual"
                    else f"s{number}_{key}_ref_label",
                    "retained_text": retained,
                    "kind": "component_label_prefix",
                }
            )
            value = retained
        if slide.layout == "comparison_visual" and not verbatim:
            # Inline runs use the full column width, avoiding clipped long labels.
            text(key + "_ref_inline", path, value, (x + 16, y + 8, w - 32, h - 16), 22)
            return
        if not sep:
            text(key, path, value, (x + 16, y + 12, w - 32, h - 24), 24)
            return
        label += ":"
        if (
            not verbatim
            and len(normalized(detail)) >= 24
            and normalized(detail) in normalized(slide.title)
        ):
            duplicates.append({"path": path, "text": detail, "represented_by": f"s{number}_titulo"})
            detail = ""
        if horizontal:
            lw = min(192, w * 0.26)
            text(key + "_ref_label", path, label, (x + 16, y + 8, lw, h - 16), 22)
            if detail:
                text(key, path, detail, (x + lw + 28, y + 8, w - lw - 44, h - 16), 22)
        else:
            lh = text_height(label, w - 32, 24)
            text(key + "_ref_label", path, label, (x + 16, y + 12, w - 32, lh), 24)
            if detail:
                text(key, path, detail, (x + 16, y + lh + 24, w - 32, h - lh - 36), 22)

    def connect(key, path, source, target):
        by_id = {c.id: c for c in commands if c.op == "add"}
        a, b = by_id[source], by_id[target]
        gap = b.position.y - a.position.y - a.size[1]
        arrow = add(
            key,
            path,
            "arrow",
            a.position.x + a.size[0] / 2 - 8,
            a.position.y + a.size[1],
            16,
            gap,
            color="primaria",
            role="decoracao",
        )
        # Explicit spatial declarations survive DSL export and IR round trips.
        commands.extend(
            [
                Command(
                    op="move", id=arrow, position=Position(kind="below", reference=source, margin=0)
                ),
                Command(
                    op="move", id=target, position=Position(kind="below", reference=arrow, margin=0)
                ),
                Command(
                    op="move",
                    id=arrow,
                    position=Position(
                        kind="absolute",
                        x=a.position.x + a.size[0] / 2 - 8,
                        y=a.position.y + a.size[1],
                    ),
                ),
                Command(op="move", id=target, position=deepcopy(b.position)),
            ]
        )

    if slide.layout == "visual_cover":
        col = slide.columns[0]
        centered = (
            not verbatim
            and len(col.items) == 1
            and ": " in col.items[0]
            and normalized(col.items[0].partition(": ")[2]) in normalized(slide.title)
        )
        title_y, title_w = (232 if centered else 152), 1088
        title_h = text_height(slide.title, title_w, 42)
        panel(
            "cover",
            base + ".layout",
            (64, 208 if centered else 128, 1152, 304 if centered else 288),
        )
        text(
            "titulo",
            base + ".title",
            slide.title,
            (96, title_y, title_w, title_h),
            42,
            role="titulo",
        )
        if col.heading:
            text(
                "c1_heading",
                base + ".columns.0.heading",
                col.heading,
                (96, title_y + title_h + 16, 1088, 72),
                24,
            )
        n = len(col.items)
        gap = 24
        width = (1152 - gap * (n - 1)) / n
        for i, value in enumerate(col.items):
            path = f"{base}.columns.0.items.{i}"
            label, sep, detail = value.partition(": ")
            if (
                not verbatim
                and sep
                and len(normalized(detail)) >= 24
                and normalized(detail) in normalized(slide.title)
            ):
                text(
                    f"c1_i{i + 1}_ref_label",
                    path,
                    label + ":",
                    (96, (144 if centered else 64) + i * 60, 1088, 54),
                    22,
                )
                duplicates.append(
                    {"path": path, "text": detail, "represented_by": f"s{number}_titulo"}
                )
                continue
            rect = (64 + i * (width + gap), 456, width, 176)
            panel(f"panel{i + 1}", path, rect)
            node(f"c1_i{i + 1}", path, value, rect)
    elif slide.layout == "takeaway":
        col = slide.columns[0]
        repeated = [
            i
            for i, v in enumerate(col.items)
            if not verbatim and normalized(v) == normalized(slide.title)
        ]
        if repeated:
            panel("takeaway", base + ".title", (64, 184, 1152, 224))
            text(
                "titulo",
                base + ".title",
                slide.title,
                (96, 216, 1088, text_height(slide.title, 1088, 42)),
                42,
                role="titulo",
            )
            for i in repeated:
                duplicates.append(
                    {
                        "path": f"{base}.columns.0.items.{i}",
                        "text": col.items[i],
                        "represented_by": f"s{number}_titulo",
                    }
                )
            top = 448
        else:
            text("titulo", base + ".title", slide.title, (64, 64, 1152, title_h), 42, role="titulo")
        remaining = [(i, v) for i, v in enumerate(col.items) if i not in repeated]
        for j, (i, value) in enumerate(remaining):
            path = f"{base}.columns.0.items.{i}"
            if repeated and len(remaining) <= 3:
                width = (1152 - 24 * (len(remaining) - 1)) / len(remaining)
                rect = (64 + j * (width + 24), top, width, end - top)
            else:
                height = (end - top - 16 * (len(remaining) - 1)) / max(1, len(remaining))
                rect = (64, top + j * (height + 16), 1152, height)
            panel(f"panel{i + 1}", path, rect)
            text(
                f"c1_i{i + 1}",
                path,
                value,
                (rect[0] + 16, rect[1] + 12, rect[2] - 32, rect[3] - 24),
                22,
            )
        if col.heading:
            text("c1_heading", base + ".columns.0.heading", col.heading, (64, 120, 1152, 56), 24)
    else:
        text("titulo", base + ".title", slide.title, (64, 64, 1152, title_h), 42, role="titulo")
        for ci, col in enumerate(slide.columns):
            path = f"{base}.columns.{ci}"
            x, w = (64 + ci * 608, 544) if slide.layout == "comparison_visual" else (64, 1152)
            y = top
            if col.heading:
                hh = text_height(col.heading, w, 24)
                text(
                    f"c{ci + 1}_heading",
                    path + ".heading",
                    col.heading,
                    (x, y, w, hh),
                    24,
                    "primaria",
                )
                y += hh + 12
            n = len(col.items)
            diagram = slide.layout in {
                "architecture_diagram",
                "visual_flow",
                "visual_sequence",
                "comparison_visual",
            }
            if diagram:
                gap = 12 if slide.layout == "comparison_visual" else 24
                height = (end - y - gap * (n - 1)) / n
                previous = None
                for i, value in enumerate(col.items):
                    rect = (x, y + i * (height + gap), w, height)
                    nodepath = path + f".items.{i}"
                    p = panel(
                        f"c{ci + 1}_panel{i + 1}",
                        nodepath,
                        rect,
                        accent="destaque" if col.representation == "services" else "primaria",
                    )
                    text_rect = rect
                    if slide.layout == "visual_sequence":
                        text(
                            f"c{ci + 1}_step{i + 1}",
                            nodepath,
                            str(i + 1),
                            (x + 16, rect[1] + 8, 40, height - 16),
                            22,
                        )
                        text_rect = (x + 56, rect[1], w - 56, height)
                    node(f"c{ci + 1}_i{i + 1}", nodepath, value, text_rect, horizontal=True)
                    connected = col.representation == "stack" or slide.layout in {
                        "visual_flow",
                        "visual_sequence",
                    }
                    if previous and connected:
                        connect(f"c{ci + 1}_link{i}", path + ".representation", previous, p)
                    previous = p
            else:
                cols = 3 if n == 3 and mode == "row" else 2 if n > 1 else 1
                rows = math.ceil(n / cols)
                gap = 24
                cw = (1152 - gap * (cols - 1)) / cols
                ch = min(256, (end - y - gap * (rows - 1)) / rows)
                sy = y + max(0, (end - y - (ch * rows + gap * (rows - 1))) / 2)
                for i, value in enumerate(col.items):
                    row, colindex = divmod(i, cols)
                    rowcount = min(cols, n - row * cols)
                    offset = (1152 - (rowcount * cw + gap * (rowcount - 1))) / 2
                    rect = (64 + offset + colindex * (cw + gap), sy + row * (ch + gap), cw, ch)
                    nodepath = path + f".items.{i}"
                    panel(f"panel{i + 1}", nodepath, rect)
                    node(f"c{ci + 1}_i{i + 1}", nodepath, value, rect)
    if slide.footer:
        text("rodape", base + ".footer", slide.footer, (64, 628, 1152, 28), 12, role="decoracao")
    return SlideNode(number=number, commands=commands), paths, duplicates, panels


def evaluate(node, theme, title, panels):
    test = deepcopy(node)
    test.number = 1
    validation = validate_source(
        print_ast(PresentationNode(title=title, theme=theme, slides=[test]))
    )
    ds = [d.model_dump() for d in validation.diagnostics]
    visual = check_visual(validation.ir) if validation.ir else []
    valid = validation.success(strict=True) and not any(d["severity"] == "ERRO" for d in visual)
    if not valid:
        return None, {"valid": False, "diagnostics": ds + visual}
    # Penalize unequal panel sizes and off-centre occupied groups, not shape counts.
    areas = [w * h for _, _, w, h in panels]
    area = sum(areas)
    cx = sum((x + w / 2) * w * h for x, y, w, h in panels) / area if area else 640
    cy = sum((y + h / 2) * w * h for x, y, w, h in panels) / area if area else 440
    variance = (
        sum((a - sum(areas) / len(areas)) ** 2 for a in areas) / max(1, len(areas)) if areas else 0
    )
    score = (
        abs(cx - 640) / 640
        + abs(cy - 440) / 440
        + math.sqrt(variance) / max(1, sum(areas) / max(1, len(areas)))
    )
    return score, {
        "valid": True,
        "score": score,
        "panel_centroid": [cx, cy],
        "panel_area_fraction": area / (1280 * 720),
        "diagnostics": ds + visual,
    }


def refine_slides(plan, slides, mapping):
    slides = deepcopy(slides)
    mapping = deepcopy(mapping)
    accepted = set()
    reports = []
    options = plan.refinement or {}
    criteria = options.get("requirements", [])
    from .requirements import evaluate_requirements

    def measured(nodes):
        validation = validate_source(
            print_ast(PresentationNode(title=plan.title, theme=plan.theme, slides=nodes))
        )
        return evaluate_requirements(validation, criteria, plan.model_dump())["items"]

    protected = {key for key, met in measured(slides).items() if met} if criteria else set()
    for index, (spec, old) in enumerate(zip(plan.slides, slides, strict=True)):
        report = {"slide": index + 1, "candidates": [], "accepted": False}
        if (
            spec.layout not in COMPOSED_LAYOUTS
            or spec.relations
            or spec.decorations
            or spec.media
            or any(c.group for c in spec.columns)
            or any(
                c.op in {"align", "group", "distribute"}
                or (c.position and c.position.kind in {"below", "right"})
                for c in old.commands
            )
        ):
            report["reason"] = "existing_spatial_constraints_or_unsupported_layout"
            reports.append(report)
            continue
        choices = []
        for mode in (
            ["row", "grid"]
            if len(spec.columns[0].items) == 3 and spec.layout in {"benefit_cards", "concept_map"}
            else ["balanced"]
        ):
            node, paths, duplicates, panels = candidate(
                spec, index + 1, mode, options.get("style", ""), options.get("verbatim", False)
            )
            score, metrics = evaluate(node, plan.theme, plan.title, panels)
            # Conservation is independently checked before any candidate is accepted.
            emitted = normalized(" ".join(c.text or "" for c in node.commands))
            values = [spec.title, spec.footer] + [c.heading for c in spec.columns]
            values += [v for c in spec.columns for v in c.items]
            missing = [v for v in values if normalized(v) and normalized(v) not in emitted]
            # A removed duplicate remains in the retained title, with its label preserved.
            for duplicate in duplicates:
                original = spec.columns[int(duplicate["path"].split(".")[3])].items[
                    int(duplicate["path"].split(".")[-1])
                ]
                if (
                    original in missing
                    and duplicate.get("kind") == "component_label_prefix"
                    and normalized(duplicate["retained_text"]) in emitted
                ):
                    missing.remove(original)
                elif original in missing and normalized(duplicate["text"]) in normalized(
                    spec.title
                ):
                    label = original.partition(": ")[0] if ": " in original else ""
                    if not label or normalized(label) in emitted:
                        missing.remove(original)
            if missing:
                score = None
                metrics.update(valid=False, missing_content=missing)
            if score is not None and criteria:
                trial = deepcopy(slides)
                trial[index] = node
                status = measured(trial)
                lost = sorted(key for key in protected if not status.get(key))
                if lost:
                    score = None
                    metrics.update(valid=False, lost_requirements=lost)
            report["candidates"].append({"mode": mode, **metrics})
            if score is not None:
                if "compact" in options.get("style", "").casefold() and mode == "row":
                    score += 1
                metrics["selection_cost"] = score
                choices.append((score, node, paths, duplicates, mode))
        if choices:
            score, node, paths, duplicates, mode = min(choices, key=lambda c: c[0])
            slides[index] = node
            mapping = {k: v for k, v in mapping.items() if not k.startswith(f"s{index + 1}_")}
            mapping.update(paths)
            accepted.add(index + 1)
            if criteria:
                protected.update(key for key, met in measured(slides).items() if met)
            report.update(
                accepted=True,
                mode=mode,
                duplicates=duplicates,
                reason="validated_composition_content_preserved",
            )
        else:
            report["reason"] = "no_safe_candidate_preserved_original"
        reports.append(report)
    return (
        slides,
        mapping,
        accepted,
        {"protocol": "refinement-v1", "slides": reports, "aesthetic_assessment": None},
    )


def refinement_report(data):
    from .planning import DeckPlan
    from .layouts import plan_to_dsl
    from .parser import parse

    plan = DeckPlan.model_validate(data)
    source, mapping, _ = plan_to_dsl(plan.model_copy(update={"refinement": None}))
    return refine_slides(plan, parse(source).slides, mapping)[3]
