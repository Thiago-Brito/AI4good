import json
from functools import lru_cache
from pathlib import Path

from lark import Lark, Tree, UnexpectedInput

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .diagnostics import Diagnostic, DSLException


@lru_cache
def grammar_parser() -> Lark:
    return Lark(
        Path(__file__).with_name("grammar").joinpath("slidedsl.lark").read_text(encoding="utf-8"),
        parser="lalr",
        propagate_positions=True,
        maybe_placeholders=False,
    )


def position(tree: Tree) -> Position:
    c = tree.children
    if tree.data == "ponto":
        return Position(kind="absolute", x=float(c[0]), y=float(c[1]))
    if tree.data == "canto_superior_direito":
        return Position(kind="corner")
    return Position(
        kind="below" if tree.data == "abaixo_de" else "right",
        reference=str(c[0]),
        margin=float(c[1]),
    )


def parse_command(tree: Tree) -> Command:
    name, c = str(tree.data), tree.children
    kw = {"line": tree.meta.line, "column": tree.meta.column}
    if name.startswith("adicionar_"):
        kind = {"retangulo": "rectangle", "elipse": "ellipse", "texto": "text", "imagem": "image"}[
            name[10:]
        ]
        offset = 2 if kind in ("text", "image") else 1
        args = dict(
            op="add",
            id=str(c[0]),
            element_type=kind,
            position=position(c[offset]),
            size=tuple(float(n) for n in c[offset + 1].children),
        )
        if kind == "text":
            args.update(
                text=json.loads(str(c[1])),
                font_size=int(c[4]) if str(c[4]).isdigit() else str(c[4]),
                color=str(c[5]),
            )
        elif kind == "image":
            args.update(file=json.loads(str(c[1])))
        else:
            args.update(color=str(c[3]))
        for item in c:
            if isinstance(item, Tree) and item.data == "papel":
                args["role"] = str(item.children[0])
            if isinstance(item, Tree) and item.data == "familia":
                args["font_face"] = json.loads(str(item.children[0]))
        return Command(**kw, **args)
    if name == "layout":
        return Command(
            **kw,
            op="layout",
            text=json.loads(str(c[0])),
            children=[parse_command(t) for t in c[1:]],
        )
    if name == "agrupar":
        return Command(
            **kw,
            op="group",
            ids=[str(v) for v in c[0].children],
            id=str(c[1]),
            text=json.loads(str(c[2].children[0])) if len(c) > 2 else None,
        )
    if name == "distribuir":
        return Command(
            **kw, op="distribute", ids=[str(v) for v in c[0].children], value=float(c[1])
        )
    if name == "definir_camada":
        return Command(**kw, op="layer", id=str(c[0]), value=float(c[1]))
    if name.startswith("alinhar_"):
        axis = {"esquerda": "left", "direita": "right", "centro": "center", "topo": "top"}[name[8:]]
        return Command(**kw, op="align", id=str(c[0]), reference=str(c[1]), axis=axis)
    op = {
        "remover": "remove",
        "mover": "move",
        "redimensionar": "resize",
        "mudar_cor": "color",
        "trazer_frente": "front",
        "enviar_tras": "back",
        "desagrupar": "ungroup",
    }[name]
    args = dict(op=op, id=str(c[0]))
    if op == "move":
        args["position"] = position(c[1])
    elif op == "resize":
        args["size"] = tuple(float(v) for v in c[1].children)
    elif op == "color":
        args["color"] = str(c[1])
    return Command(**kw, **args)


def parse(source: str) -> PresentationNode:
    try:
        root = grammar_parser().parse(source).children[0]
        title, theme, *slides = root.children
        return PresentationNode(
            title=json.loads(str(title)),
            theme=str(theme.children[0]),
            line=root.meta.line,
            column=root.meta.column,
            slides=[
                SlideNode(
                    number=int(s.children[0]),
                    line=s.meta.line,
                    column=s.meta.column,
                    commands=[parse_command(c) for c in s.children[1:]],
                )
                for s in slides
            ],
        )
    except UnexpectedInput as exc:
        raise DSLException(
            [
                Diagnostic(
                    code="P001",
                    severity="ERRO",
                    message="Sintaxe inválida no português controlado.",
                    line=exc.line,
                    column=exc.column,
                    evidence={
                        "context": exc.get_context(source),
                        "expected": sorted(getattr(exc, "expected", [])),
                    },
                    suggestion="Use um comando do catálogo e confira aspas, parênteses e chaves.",
                )
            ]
        ) from exc
    except (ValueError, TypeError) as exc:
        raise DSLException(
            [Diagnostic(code="P002", severity="ERRO", message=f"Valor inválido: {exc}")]
        ) from exc
