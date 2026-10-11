"""Content plans without model-authored identifiers or coordinates."""

from typing import Literal

from pydantic import Field

from .structured_slide import OutputModel


class ColumnPlan(OutputModel):
    heading: str = Field(max_length=120)
    items: list[str] = Field(min_length=1, max_length=6)
    group: bool


class DecorationPlan(OutputModel):
    kind: Literal["rectangle", "ellipse", "image"]
    slot: Literal["left", "right", "overlay"]
    color: Literal["primaria", "secundaria", "destaque"]


class RelationPlan(OutputModel):
    kind: Literal["left", "right", "center", "top", "front", "back"]
    target: str
    reference: str


class SlidePlan(OutputModel):
    title: str = Field(min_length=1, max_length=120)
    layout: Literal["title_content", "two_columns", "comparison"]
    columns: list[ColumnPlan] = Field(min_length=1, max_length=2)
    decorations: list[DecorationPlan] = Field(max_length=4)
    relations: list[RelationPlan] = Field(max_length=12)
    footer: str = Field(max_length=240)


class DeckPlan(OutputModel):
    title: str = Field(min_length=1, max_length=160)
    theme: Literal["claro", "escuro"]
    slides: list[SlidePlan] = Field(min_length=1, max_length=12)


def plan_schema(slide_count: int) -> dict:
    if not 1 <= slide_count <= 12:
        raise ValueError("Use de 1 a 12 slides.")
    schema = DeckPlan.model_json_schema()
    schema["properties"]["slides"].update(minItems=slide_count, maxItems=slide_count)
    return schema


def plan_system() -> str:
    return """Planeje uma apresentação em português conforme o pedido integral.
Retorne somente JSON no schema. Você escreve o conteúdo; o compilador calcula IDs,
coordenadas, margens e tamanhos. Não inclua coordenadas ou IDs.
Escolha title_content para uma coluna, two_columns para dois assuntos e comparison
para comparar duas alternativas. Uma coluna para title_content; duas para os demais.
Cada coluna tem heading (pode ser vazio), items (frases completas, idealmente até
90 caracteres, sem cortar palavras), group (true só quando o pedido exige proximidade).
Títulos curtos; não repita títulos. Preserve a ordem e TODOS os requisitos do pedido.
Use decorations=[] quando não forem necessárias. Imagem usa exclusivamente o asset
local assets/imagem_demo.png. Para camadas: rectangle slot left e image slot overlay;
relations back e front para d2, nessa ordem. Cores primaria/secundaria/destaque.
Referências lógicas existentes: titulo, c1_heading, c1_i1, c1_i2, c2_i1, d1, d2 etc.
Não use referência a heading vazio ou a item/decoração que não foi criado.
Relações left/right/center/top exigem target e reference existentes e diferentes.
Para front/back, reference deve ser vazio. O sistema resolverá todas essas referências.
Use footer se o pedido exigir rodapé. Não invente imagens externas.
"""
