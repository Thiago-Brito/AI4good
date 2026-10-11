import json

from .ast_nodes import Command, Position, PresentationNode


def number(v: float) -> str:
    return str(int(v)) if v == int(v) else repr(v)


def quote(v: str) -> str:
    return json.dumps(v, ensure_ascii=False)


def pair(v: tuple[float, float]) -> str:
    return f"({number(v[0])}, {number(v[1])})"


def print_position(p: Position) -> str:
    if p.kind == "absolute":
        return pair((p.x, p.y))
    if p.kind == "corner":
        return "canto superior direito"
    prefix = "abaixo de" if p.kind == "below" else "a direita de"
    return f"{prefix} {p.reference} com margem {number(p.margin)}"


def print_command(c: Command, indent: str = "    ") -> str:
    if c.op == "add":
        kind = {
            "rectangle": "retangulo",
            "ellipse": "elipse",
            "text": "texto",
            "image": "imagem",
            "arrow": "seta",
        }[c.element_type]
        s = f"adicionar {kind} id {c.id}"
        if c.element_type == "text":
            s += f" {quote(c.text)}"
        elif c.element_type == "image":
            s += f" arquivo {quote(c.file)}"
        s += f" em {print_position(c.position)} tamanho {pair(c.size)}"
        if c.element_type == "text":
            s += f" fonte {c.font_size} cor {c.color}"
        elif c.element_type != "image":
            s += f" cor {c.color}"
        if c.role is not None:
            s += f" papel {c.role}"
        if c.element_type == "text" and c.font_face is not None:
            s += f" familia {quote(c.font_face)}"
    elif c.op == "move":
        s = f"mover {c.id} para {print_position(c.position)}"
    elif c.op == "resize":
        s = f"redimensionar {c.id} para {pair(c.size)}"
    elif c.op == "color":
        s = f"mudar cor de {c.id} para {c.color}"
    elif c.op == "align":
        axis = {
            "left": "pela esquerda",
            "right": "pela direita",
            "center": "pelo centro horizontal",
            "top": "pelo topo",
        }[c.axis]
        s = f"alinhar {c.id} com {c.reference} {axis}"
    elif c.op == "group":
        s = f"agrupar [{', '.join(c.ids)}] como {c.id}"
        if c.text is not None:
            s += f" rotulo {quote(c.text)}"
    elif c.op == "distribute":
        s = f"distribuir horizontalmente [{', '.join(c.ids)}] com intervalo {number(c.value)}"
    elif c.op == "layer":
        s = f"definir camada de {c.id} como {number(c.value)}"
    elif c.op == "layout":
        body = "\n".join(print_command(x, indent + "  ") for x in c.children)
        return f"{indent}grupo {quote(c.text)} {{\n{body}\n{indent}}}"
    else:
        s = {
            "remove": f"remover {c.id}",
            "front": f"trazer {c.id} para frente",
            "back": f"enviar {c.id} para tras",
            "ungroup": f"desagrupar {c.id}",
        }[c.op]
    return indent + s


def print_ast(ast: PresentationNode) -> str:
    lines = [f"apresentacao {quote(ast.title)} {{", f"  tema {ast.theme}"]
    for slide in ast.slides:
        lines += [f"  slide {slide.number} {{", *[print_command(c) for c in slide.commands], "  }"]
    return "\n".join([*lines, "}", ""])
