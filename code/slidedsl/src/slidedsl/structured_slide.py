"""Restricted model output; serialization only. Parser/semantics remain authoritative."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .printer import print_ast


class OutputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class Geometry(OutputModel):
    id: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    x: float = Field(ge=0, le=1280)
    y: float = Field(ge=0, le=720)
    width: float = Field(gt=0, le=1280)
    height: float = Field(gt=0, le=720)


class TextOutput(Geometry):
    type: Literal["text"]
    text: str = Field(min_length=1, max_length=500)
    font_size: Literal["titulo", "corpo", "rodape"]
    color: Literal["texto", "primaria", "secundaria", "destaque", "fundo"]
    role: Literal["titulo", "corpo"]


class ShapeOutput(Geometry):
    type: Literal["rectangle", "ellipse"]
    color: Literal["texto", "primaria", "secundaria", "destaque", "fundo"]
    role: Literal["decoracao", "background", "nenhum"]


class TitleOutput(TextOutput):
    role: Literal["titulo"]
    font_size: Literal["titulo"]
    width: float = Field(ge=1000, le=1152)
    height: float = Field(ge=100, le=180)
    text: str = Field(min_length=1, max_length=36)


class BodyOutput(TextOutput):
    role: Literal["corpo"]
    font_size: Literal["corpo", "rodape"]
    width: float = Field(ge=480, le=1152)
    height: float = Field(ge=40, le=300)
    text: str = Field(min_length=1, max_length=54)


class ImageOutput(Geometry):
    type: Literal["image"]
    file: Literal["assets/imagem_demo.png"]
    role: Literal["decoracao", "nenhum"]


class LayerOutput(OutputModel):
    op: Literal["front", "back"]
    id: str


class GroupOutput(OutputModel):
    op: Literal["group"]
    id: str
    ids: list[str] = Field(min_length=2, max_length=12)


class AlignOutput(OutputModel):
    op: Literal["align"]
    id: str
    reference: str
    axis: Literal["left", "right", "center", "top"]


class SlideOutput(OutputModel):
    title: TitleOutput
    texts: list[BodyOutput] = Field(min_length=1, max_length=12)
    shapes: list[ShapeOutput] = Field(max_length=6)
    images: list[ImageOutput] = Field(max_length=2)
    operations: list[LayerOutput | GroupOutput | AlignOutput] = Field(max_length=12)


def json_to_dsl(raw: str) -> str:
    slide = SlideOutput.model_validate_json(raw)
    commands = []
    # Contract: decorations first, then model-authored text; explicit operations follow.
    for e in [*slide.shapes, *slide.images, slide.title, *slide.texts]:
        data = e.model_dump()
        commands.append(
            Command(
                op="add",
                id=e.id,
                element_type=e.type,
                position=Position(kind="absolute", x=e.x, y=e.y),
                size=(e.width, e.height),
                role=e.role,
                **{k: data[k] for k in ("text", "color", "font_size", "file") if k in data},
            )
        )
    for op in slide.operations:
        commands.append(Command(**op.model_dump()))
    return print_ast(
        PresentationNode(
            title=slide.title.text,
            theme="claro",
            slides=[SlideNode(number=1, commands=commands)],
        )
    )
