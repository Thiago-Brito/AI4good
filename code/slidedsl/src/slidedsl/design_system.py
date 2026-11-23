"""Grade e tokens do compilador Alto. Coordenadas nunca vêm do modelo."""

from dataclasses import dataclass

WIDTH, HEIGHT, MARGIN, RIGHT = 1280, 720, 64, 1216
GUTTER = 24
SPACES = (8, 16, 24, 32, 48, 64)
XS, SM, MD, LG, XL, XXL = SPACES
TITLE_Y = MARGIN
CONTENT_BOTTOM = 636
CARD_PADDING = LG
LABEL_GAP = 12  # exceção tipográfica explícita, não token de espaço geral
RULE = 4
OPTICAL_CENTER = .44
MIN_BLOCK_FRACTION = .60
OPTICAL_LABEL_PT = 23.5  # referência óptica: arredonda para 24 Arial / 26 Calibri
COL_WIDTH = (RIGHT - MARGIN - 11 * GUTTER) / 12


def card_position(top, natural_height, bottom=CONTENT_BOTTOM):
    """Centro do bloco 5% acima do centro útil; excesso continua diagnosticável."""
    available = bottom - top
    return top + max(0, (available - natural_height) / 2 - .05 * available)


def col(i, span=1):
    """Colunas 0..11; devolve (x, largura), incluindo gutters internos."""
    if i < 0 or span < 1 or i + span > 12:
        raise ValueError("Coluna/span fora da grade de 12 colunas.")
    return MARGIN + i * (COL_WIDTH + GUTTER), span * COL_WIDTH + (span - 1) * GUTTER


def distribute(top, natural_height, count=1, bottom=CONTENT_BOTTOM):
    available = max(1, bottom - top)
    target = max(natural_height, available * MIN_BLOCK_FRACTION if count >= 2 else natural_height)
    height = min(available, target)
    return top + max(0, available - height) * OPTICAL_CENTER, height


@dataclass(frozen=True)
class Estilo:
    comum: dict
    destaque: dict
    tema: str
    fonte_titulo: str = "Calibri"
    fonte_corpo: str = "Calibri"
    raio: int = 0
    cartao: str = "preenchido"
    marcador: str = "barra"
    alinhamento_titulo: str = "left"
    motivo_capa: str = "lateral"
    margem_vertical: bool = False


def title_style(element, background):
    """Reconhece o sistema declarado na DSL compilada, sem alterar o contrato IR."""
    import re
    from .alto_layout import STYLES
    if not re.fullmatch(r"s\d+_(titulo|transicao)_\d+", element.id):
        return None
    for style in STYLES.values():
        for palette in (style.comum, style.destaque):
            if (element.font_face == style.fonte_titulo and background and
                    background.upper() == palette["bg"].upper()):
                from .text_metrics import optical_size
                size = (min(54, optical_size(48, style.fonte_titulo, 32))
                        if "_transicao_" in element.id else optical_size(42, style.fonte_titulo, 32))
                return (size, palette["text"], style.fonte_titulo)
    return None
