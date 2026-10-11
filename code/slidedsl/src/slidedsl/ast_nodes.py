from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TypedNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line: int = 1
    column: int = 1


class Position(BaseModel):
    kind: Literal["absolute", "corner", "below", "right"]
    x: float = 0
    y: float = 0
    reference: str | None = None
    margin: float = 0


class Command(TypedNode):
    op: Literal[
        "add",
        "remove",
        "move",
        "resize",
        "color",
        "front",
        "back",
        "align",
        "group",
        "ungroup",
        "distribute",
        "layer",
        "layout",
    ]
    id: str = ""
    element_type: Literal["rectangle", "ellipse", "text", "image", "arrow"] | None = None
    position: Position | None = None
    size: tuple[float, float] | None = None
    color: str | None = None
    text: str | None = None
    file: str | None = None
    font_size: int | str | None = None
    font_face: str | None = None
    role: Literal["titulo", "corpo", "decoracao", "background", "nenhum"] | None = None
    reference: str | None = None
    axis: Literal["left", "right", "center", "top"] | None = None
    ids: list[str] = Field(default_factory=list)
    value: float | None = None
    children: list["Command"] = Field(default_factory=list)


class SlideNode(TypedNode):
    number: int
    commands: list[Command]


class PresentationNode(TypedNode):
    title: str
    theme: Literal["claro", "escuro"]
    slides: list[SlideNode]
