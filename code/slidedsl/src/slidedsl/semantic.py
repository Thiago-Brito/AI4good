import math
from pathlib import Path

import yaml

from .ast_nodes import Command, PresentationNode
from .diagnostics import Diagnostic, DSLException
from .geometry import aligned_position, bounds, resize_group, resolve_position, translate
from .ir import Element, Group, Presentation, Relation, Slide
from .paths import asset_path, project_root


def infer_role(id: str, type: str, x: float, y: float, w: float, h: float):
    if type == "rectangle" and (x, y, w, h) == (0, 0, 1280, 720):
        return "background", "heurística: retângulo do canvas completo"
    if id.startswith(("fundo", "decoracao")):
        return "decoracao", "heurística: prefixo de ID"
    if type == "text" and id.startswith("titulo"):
        return "titulo", "heurística: prefixo titulo"
    if type == "text" and id.startswith(
        ("corpo", "subtitulo", "vantagem", "limitacao", "rodape", "explicacao")
    ):
        return "corpo", "heurística: prefixo de ID"
    return None, None


def analyze(ast: PresentationNode, root: Path | None = None) -> Presentation:
    root = (root or project_root()).resolve()
    theme = yaml.safe_load((project_root() / "config/themes.yaml").read_text(encoding="utf-8"))[
        ast.theme
    ]
    diagnostics = []
    slides = []
    for expected, sn in enumerate(ast.slides, 1):
        if sn.number != expected:
            diagnostics.append(
                Diagnostic(
                    code="S001",
                    severity="ERRO",
                    message=f"Slides devem seguir 1..N: esperado {expected}, recebido {sn.number}.",
                    slide=sn.number,
                    line=sn.line,
                    column=sn.column,
                )
            )
        scene: dict[str, Element] = {}
        groups: dict[str, Group] = {}
        relations: list[Relation] = []

        def objects(id: str) -> list[Element]:
            if id in scene:
                return [scene[id]]
            if id in groups:
                return [scene[m] for m in groups[id].members]
            raise KeyError(id)

        def normalize():
            ordered = sorted(scene.values(), key=lambda e: e.z)
            for z, e in enumerate(ordered):
                e.z = z

        def relation(c: Command, kind: str, ref: str, margin: float = 0):
            # Última declaração do mesmo eixo/relação permanece para inspeção.
            family = "position" if kind in ("below", "right") else "alignment"
            relations[:] = [
                r
                for r in relations
                if not (
                    r.target == c.id
                    and ("position" if r.kind in ("below", "right") else "alignment") == family
                )
            ]
            relations.append(
                Relation(
                    kind=kind,
                    target=c.id,
                    reference=ref,
                    margin=margin,
                    source_line=c.line,
                    source_column=c.column,
                )
            )

        def pos(c: Command, size):
            p = c.position
            if p.reference is not None:
                refs = objects(p.reference)
                r = bounds(refs)
                proxy = Element(
                    id="reference",
                    type="rectangle",
                    x=r[0],
                    y=r[1],
                    width=r[2] - r[0],
                    height=r[3] - r[1],
                )
                relation(c, p.kind, p.reference, p.margin)
                return resolve_position(p, size, {p.reference: proxy})
            return resolve_position(p, size, scene)

        def color(value: str) -> str:
            if value.startswith("#"):
                return value.upper()
            if value not in theme["colors"]:
                raise ValueError(f"Token de cor inexistente: {value}")
            return theme["colors"][value]

        def execute(c: Command):
            if c.op in {"add", "resize"} and any(v <= 0 or not math.isfinite(v) for v in c.size):
                raise ValueError("S004|Largura e altura devem ser finitas e maiores que zero.")
            if c.op == "layout":
                before = set(scene)
                for child in c.children:
                    safe_execute(child)
                members = [id for id in scene if id not in before]
                if len(members) < 2:
                    raise ValueError("Bloco de layout deve criar ao menos dois elementos.")
                id = "layout_" + str(len(groups) + 1)
                while id in scene or id in groups:
                    id += "_"
                if any(set(members) & set(g.members) for g in groups.values()):
                    raise ValueError("Grupos aninhados ou sobrepostos não são suportados.")
                groups[id] = Group(id=id, members=members, label=c.text, source_line=c.line)
                return
            if c.op == "add":
                if c.id in scene or c.id in groups:
                    raise ValueError(f"S002|ID duplicado no slide: {c.id}")
                font = (
                    theme["fonts"].get(c.font_size) if isinstance(c.font_size, str) else c.font_size
                )
                if c.element_type == "text" and (font is None or not 10 <= font <= 96):
                    raise ValueError(
                        "S005|Fonte deve estar entre 10 e 96 pontos ou usar token de tema válido."
                    )
                if c.element_type == "image":
                    asset_path(c.file, root)
                x, y = pos(c, c.size)
                role, origin = infer_role(c.id, c.element_type, x, y, *c.size)
                if c.role is not None:
                    role = None if c.role == "nenhum" else c.role
                    origin = "anotação explícita" if role else None
                scene[c.id] = Element(
                    id=c.id,
                    type=c.element_type,
                    text=c.text,
                    file=c.file.replace("\\", "/") if c.file else None,
                    x=x,
                    y=y,
                    width=c.size[0],
                    height=c.size[1],
                    color=color(c.color) if c.color else None,
                    font_size=font,
                    font_face=c.font_face or theme["font_face"],
                    z=len(scene),
                    role=role,
                    role_origin=origin,
                    source_line=c.line,
                    source_column=c.column,
                )
                return
            if c.op == "group":
                if c.id in scene or c.id in groups:
                    raise ValueError(f"S002|ID duplicado no slide: {c.id}")
                if len(set(c.ids)) != len(c.ids) or len(c.ids) < 2:
                    raise ValueError("Grupo exige pelo menos dois IDs distintos.")
                for id in c.ids:
                    if id not in scene:
                        raise KeyError(id)
                if any(set(c.ids) & set(g.members) for g in groups.values()):
                    raise ValueError("Elemento já pertence a outro grupo; desagrupe primeiro.")
                groups[c.id] = Group(id=c.id, members=c.ids, label=c.text, source_line=c.line)
                return
            if c.op == "distribute":
                if len(c.ids) < 3 or len(set(c.ids)) != len(c.ids):
                    raise ValueError("Distribuição exige ao menos três IDs distintos.")
                lists = [objects(id) for id in c.ids]
                if len({e.id for ls in lists for e in ls}) != sum(len(ls) for ls in lists):
                    raise ValueError("Distribuição não permite conjuntos sobrepostos.")
                x = bounds(lists[0])[0]
                for ls in lists:
                    r = bounds(ls)
                    translate(ls, x, r[1])
                    x += r[2] - r[0] + c.value
                return
            elems = objects(c.id)
            if c.op == "remove":
                removed = {e.id for e in elems}
                for id in removed:
                    del scene[id]
                for id in list(groups):
                    groups[id].members = [m for m in groups[id].members if m not in removed]
                    if len(groups[id].members) < 2:
                        del groups[id]
                active = set(scene) | set(groups)
                relations[:] = [
                    r
                    for r in relations
                    if r.target not in removed | {c.id}
                    and r.reference not in removed | {c.id}
                    and r.target in active
                    and r.reference in active
                ]
            elif c.op == "move":
                r = bounds(elems)
                x, y = pos(c, (r[2] - r[0], r[3] - r[1]))
                translate(elems, x, y)
            elif c.op == "resize":
                resize_group(elems, *c.size)
            elif c.op == "color":
                if any(e.type == "image" for e in elems):
                    raise ValueError("S006|Mudar cor não é aplicável a imagens.")
                for e in elems:
                    e.color = color(c.color)
            elif c.op in {"front", "back", "layer"}:
                low, high = min(e.z for e in scene.values()), max(e.z for e in scene.values())
                value = (
                    high + 1 if c.op == "front" else low - len(elems) if c.op == "back" else c.value
                )
                for offset, e in enumerate(sorted(elems, key=lambda e: e.z)):
                    e.z = int(value) + offset
            elif c.op == "align":
                if c.reference == c.id:
                    raise ValueError("Alinhamento exige IDs diferentes.")
                ref = objects(c.reference)
                if {e.id for e in elems} & {e.id for e in ref}:
                    raise ValueError("Alinhamento não permite conjuntos sobrepostos.")
                x, y = aligned_position(bounds(elems), bounds(ref), c.axis)
                translate(elems, x, y)
                relation(c, "align_right" if c.axis == "right" else c.axis, c.reference)
            elif c.op == "ungroup":
                if c.id not in groups:
                    raise ValueError("ID não é grupo.")
                del groups[c.id]
                relations[:] = [r for r in relations if r.target != c.id and r.reference != c.id]
            normalize()

        def safe_execute(c: Command):
            try:
                execute(c)
            except (KeyError, ValueError) as exc:
                msg = (
                    f"ID não existe no slide: {exc.args[0]}"
                    if isinstance(exc, KeyError)
                    else str(exc)
                )
                code = (
                    "S003"
                    if isinstance(exc, KeyError)
                    else "S007"
                    if c.element_type == "image"
                    else "S008"
                )
                if "|" in msg:
                    code, msg = msg.split("|", 1)
                diagnostics.append(
                    Diagnostic(
                        code=code,
                        severity="ERRO",
                        message=msg,
                        slide=sn.number,
                        element=c.id or None,
                        line=c.line,
                        column=c.column,
                        evidence={"command": c.op, "file": c.file},
                    )
                )

        for c in sn.commands:
            safe_execute(c)
        slides.append(
            Slide(
                number=sn.number,
                elements=sorted(scene.values(), key=lambda e: e.z),
                groups=list(groups.values()),
                relations=relations,
            )
        )
    if diagnostics:
        raise DSLException(diagnostics)
    return Presentation(title=ast.title, theme=ast.theme, slides=slides)


def validate_ir(deck: Presentation, root: Path | None = None) -> list[Diagnostic]:
    """Revalidação do estado recebido do editor antes de exportar/compilar."""
    root = root or project_root()
    ds = []
    for n, slide in enumerate(deck.slides, 1):

        def error(code, message, id=None):
            ds.append(
                Diagnostic(
                    code=code, severity="ERRO", message=message, slide=slide.number, element=id
                )
            )

        if slide.number != n:
            error("S001", "Slides devem seguir 1..N.")
        ids = [e.id for e in slide.elements] + [g.id for g in slide.groups]
        if len(set(ids)) != len(ids):
            error("S002", "IDs duplicados no mesmo slide.")
        if not slide.elements:
            error("S009", "Slide vazio não é exportável pela gramática v1.1.")
        elems = {e.id: e for e in slide.elements}
        seen_members = set()
        for g in slide.groups:
            if (
                len(set(g.members)) != len(g.members)
                or len(g.members) < 2
                or not set(g.members) <= elems.keys()
                or seen_members & set(g.members)
            ):
                error("S008", "Grupo inválido, aninhado ou sobreposto.", g.id)
            seen_members.update(g.members)
        for r in slide.relations:
            if r.target not in ids or r.reference not in ids or r.target == r.reference:
                error("S003", "Referência espacial inválida.", r.target)
        for e in slide.elements:
            incompatible = (
                (e.type != "text" and (e.text is not None or e.font_size is not None))
                or (e.type != "image" and e.file is not None)
                or (e.type == "image" and e.color is not None)
                or (e.type != "text" and e.font_face != "Arial")
            )
            if incompatible:
                error("S006", "Propriedades incompatíveis com o tipo de elemento.", e.id)
            if e.type == "text" and (
                e.text is None
                or e.font_size is None
                or not 10 <= e.font_size <= 96
                or e.color is None
            ):
                error("S005", "Texto exige conteúdo, cor e fonte de 10 a 96.", e.id)
            elif e.type in {"rectangle", "ellipse", "arrow"} and e.color is None:
                error("S006", "Forma exige cor.", e.id)
            elif e.type == "image":
                try:
                    asset_path(e.file or "", root)
                except ValueError as exc:
                    error("S007", str(exc), e.id)
    if not deck.slides:
        ds.append(
            Diagnostic(
                code="S009", severity="ERRO", message="Apresentação exige ao menos um slide."
            )
        )
    return ds
