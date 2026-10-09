from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IRModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, validate_assignment=True)


class Canvas(IRModel):
    width: Literal[1280] = 1280
    height: Literal[720] = 720
    unit: Literal["px_logico"] = "px_logico"


class Element(IRModel):
    id: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    type: Literal["rectangle", "ellipse", "text", "image"]
    x: float
    y: float
    width: float
    height: float
    z: int = 0
    text: str | None = None
    file: str | None = None
    font_size: int | None = None
    font_face: str = "Arial"
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    role: Literal["titulo", "corpo", "decoracao", "background"] | None = None
    role_origin: str | None = None
    source_line: int | None = None
    source_column: int | None = None


class Group(IRModel):
    id: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    members: list[str]
    label: str | None = None
    source_line: int | None = None


class Relation(IRModel):
    kind: Literal["below", "right", "left", "align_right", "center", "top"]
    target: str
    reference: str
    margin: float = 0
    source_line: int | None = None
    source_column: int | None = None


class Slide(IRModel):
    number: int
    elements: list[Element]
    groups: list[Group] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class Presentation(IRModel):
    schema_version: Literal["1.1"] = "1.1"
    title: str
    theme: Literal["claro", "escuro"]
    canvas: Canvas = Field(default_factory=Canvas)
    slides: list[Slide]


def semantic_snapshot(deck: Presentation) -> dict:
    """Comparação canônica ignora somente proveniência textual, não a cena."""
    result = deck.model_dump()
    for s in result["slides"]:
        s["elements"].sort(key=lambda e: (e["z"], e["id"]))
        for e in s["elements"]:
            e.pop("source_line", None)
            e.pop("source_column", None)
            e.pop("role_origin", None)
        for g in s["groups"]:
            g.pop("source_line", None)
        for r in s["relations"]:
            r.pop("source_line", None)
            r.pop("source_column", None)
    return result
