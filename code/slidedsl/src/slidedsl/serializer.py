import json
from pathlib import Path

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .ir import Presentation
from .printer import print_ast


def save_ir(deck: Presentation, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(deck.model_dump_json(indent=2) + "\n", encoding="utf-8")


def load_ir(path: str | Path) -> Presentation:
    return Presentation.model_validate_json(Path(path).read_text(encoding="utf-8-sig"))


def ir_to_ast(deck: Presentation) -> PresentationNode:
    slides = []
    for s in deck.slides:
        commands = []
        for e in sorted(s.elements, key=lambda e: e.z):
            commands.append(
                Command(
                    op="add",
                    id=e.id,
                    element_type=e.type,
                    text=e.text,
                    file=e.file,
                    font_size=e.font_size,
                    color=e.color,
                    role=e.role or "nenhum",
                    font_face=e.font_face if e.type == "text" else None,
                    position=Position(kind="absolute", x=e.x, y=e.y),
                    size=(e.width, e.height),
                )
            )
        for g in s.groups:
            commands.append(Command(op="group", id=g.id, ids=g.members, text=g.label))
        for r in s.relations:
            if r.kind in ("below", "right"):
                commands.append(
                    Command(
                        op="move",
                        id=r.target,
                        position=Position(kind=r.kind, reference=r.reference, margin=r.margin),
                    )
                )
            else:
                commands.append(
                    Command(
                        op="align",
                        id=r.target,
                        reference=r.reference,
                        axis="right" if r.kind == "align_right" else r.kind,
                    )
                )
        # Restaurar a geometria materializada, mantendo a declaração para o checker.
        # Isso conserva inclusive desvios intencionais ou erros editados visualmente.
        if s.relations:
            for e in s.elements:
                commands.append(
                    Command(op="move", id=e.id, position=Position(kind="absolute", x=e.x, y=e.y))
                )
        slides.append(SlideNode(number=s.number, commands=commands))
    return PresentationNode(title=deck.title, theme=deck.theme, slides=slides)


def to_dsl(deck: Presentation) -> str:
    return print_ast(ir_to_ast(deck))


def write_schema():
    path = Path(__file__).with_name("schemas") / "ir.schema.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(Presentation.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
