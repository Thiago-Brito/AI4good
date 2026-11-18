"""Diagramas SVG desenhados pelo compilador a partir dos blocos da SlideDSL Alto.

O modelo só escreve o conteúdo (itens de ``etapas``, barras de ``grafico``); este módulo
calcula posições, quebras de linha, tamanhos de fonte, setas e alturas das barras de forma
determinística. O texto é medido com ``text_metrics`` (Arial local); se não couber nem na
fonte mínima, o diagrama sai mesmo assim e a função devolve um aviso com o campo afetado.

Cada elemento leva atributos ``data-*`` (papel, índice, valor) para a conferência
automática contra o gabarito do experimento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from xml.sax.saxutils import escape

from .alto import AltoDeck, AltoSlide, Bar, Item
from .text_metrics import text_width

FONT = "Arial, Helvetica, sans-serif"
PX = 96 / 72  # pt -> px
LINE = 1.2

PALETTE = {
    "bg": "#FFFFFF",
    "text": "#14233D",
    "muted": "#475569",
    "primary": "#2563EB",
    "on_primary": "#FFFFFF",
    "soft": "#DDE8F9",
    "accent": "#B45309",
    "line": "#94A3B8",
}


@dataclass
class SvgResult:
    svg: str
    kind: str
    warnings: list[str] = field(default_factory=list)


def wrap(text: str, width: float, size_pt: float, bold: bool = False) -> list[str] | None:
    """Quebra gulosa por palavras; ``None`` se uma palavra sozinha não cabe."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            if text_width(word, size_pt, bold) > width:
                return None
            proposed = f"{current} {word}" if current else word
            if current and text_width(proposed, size_pt, bold) > width:
                lines.append(current)
                current = word
            else:
                current = proposed
        lines.append(current)
    return lines


def block_height(lines: list[str], size_pt: float) -> float:
    return len(lines) * size_pt * PX * LINE


def fit(text: str, width: float, max_h: float, sizes: list[float], bold=False):
    """Maior fonte da lista em que o texto cabe na largura e na altura."""
    for size in sizes:
        lines = wrap(text, width, size, bold)
        if lines is not None and block_height(lines, size) <= max_h:
            return size, lines, True
    size = sizes[-1]
    lines = wrap(text, width, size, bold) or [text]
    return size, lines, False


def text_el(lines, cx, top, size_pt, color, bold=False, anchor="middle", attrs="") -> str:
    """Bloco de texto com ``tspan`` por linha; ``top`` é o topo da primeira linha."""
    lh = size_pt * PX * LINE
    weight = ' font-weight="700"' if bold else ""
    spans = "".join(
        f'<tspan x="{cx:.1f}" y="{top + lh * k + size_pt * PX * 0.95:.1f}">{escape(line)}</tspan>'
        for k, line in enumerate(lines)
    )
    return (f'<text font-family="{FONT}" font-size="{size_pt * PX:.1f}" fill="{color}"'
            f' text-anchor="{anchor}"{weight}{attrs}>{spans}</text>')


def svg_doc(width: int, height: int, body: list[str], title: str, palette) -> str:
    marker = (
        '<defs><marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"'
        f' markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"'
        f' fill="{palette["line"]}"/></marker></defs>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"'
        f' viewBox="0 0 {width} {height}" role="img"><title>{escape(title)}</title>{marker}'
        f'<rect width="{width}" height="{height}" fill="{palette["bg"]}"/>'
        + "".join(body)
        + "</svg>"
    )


def _item_block(item: Item, k: int, x, y, w, h, palette, warnings, pad=16):
    """Caixa de uma etapa: número, rótulo em negrito e detalhe opcional."""
    body = [
        f'<rect data-role="etapa" data-index="{k + 1}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}"'
        f' height="{h:.1f}" rx="14" fill="{palette["soft"]}" stroke="{palette["primary"]}"'
        ' stroke-width="2"/>'
    ]
    r = 18
    body.append(f'<circle cx="{x + w / 2:.1f}" cy="{y + pad + r:.1f}" r="{r}"'
                f' fill="{palette["primary"]}"/>')
    body.append(text_el([str(k + 1)], x + w / 2, y + pad + r - 13 * PX * 0.6, 13,
                        palette["on_primary"], bold=True))
    inner_w = w - 2 * pad
    top = y + pad + 2 * r + 10
    avail = y + h - pad - top
    label_share = avail if not item.detail else avail * 0.6
    ls, llines, ok1 = fit(item.label, inner_w, label_share, [20, 18, 16, 14, 12], bold=True)
    if not ok1:
        warnings.append(f"etapa {k + 1}: rótulo não coube")
    body.append(text_el(llines, x + w / 2, top, ls, palette["text"], bold=True,
                        attrs=f' data-role="rotulo" data-index="{k + 1}"'))
    if item.detail:
        dtop = top + block_height(llines, ls) + 8
        ds, dlines, ok2 = fit(item.detail, inner_w, y + h - pad - dtop, [16, 14, 13, 12, 11])
        if not ok2:
            warnings.append(f"etapa {k + 1}: detalhe não coube")
        body.append(text_el(dlines, x + w / 2, dtop, ds, palette["muted"],
                            attrs=f' data-role="detalhe" data-index="{k + 1}"'))
    return body


def _content_height(item: Item, w: float, pad=16, r=18) -> float:
    """Altura mínima da caixa com rótulo e detalhe nas maiores fontes que cabem na largura."""
    inner = w - 2 * pad
    for ls in (20, 18, 16, 14, 12):
        lines = wrap(item.label, inner, ls, True)
        if lines is not None:
            break
    label_h = block_height(lines or [item.label], ls)
    content = label_h
    if item.detail:
        for ds in (16, 14, 13, 12, 11):
            dlines = wrap(item.detail, inner, ds)
            if dlines is not None:
                break
        content = max(label_h / 0.6, label_h + 8 + block_height(dlines or [item.detail], ds))
    return max(160, pad + 2 * r + 10 + content + pad + 4)


def etapas_svg(items: list[Item], title: str = "Etapas", palette=PALETTE,
               width: int = 1200, height: int = 420) -> SvgResult:
    """Fluxo horizontal: caixas iguais, ligadas por setas na ordem dos itens."""
    if not 2 <= len(items) <= 6:
        raise ValueError("etapas em SVG aceita de 2 a 6 itens")
    n, margin, gap = len(items), 24, 48
    w = (width - 2 * margin - (n - 1) * gap) / n
    h = min(height - 2 * margin, max(_content_height(i, w) for i in items))
    height = int(math.ceil(h + 2 * margin))
    warnings: list[str] = []
    body: list[str] = []
    for k, item in enumerate(items):
        x = margin + k * (w + gap)
        body += _item_block(item, k, x, margin, w, h, palette, warnings)
        if k < n - 1:
            ax, ay = x + w + 6, margin + h / 2
            body.append(f'<line data-role="seta" data-from="{k + 1}" data-to="{k + 2}"'
                        f' x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax + gap - 12:.1f}" y2="{ay:.1f}"'
                        f' stroke="{palette["line"]}" stroke-width="3" marker-end="url(#seta)"/>')
    return SvgResult(svg_doc(width, height, body, title, palette), "etapas", warnings)


def _clip_to_box(cx, cy, tx, ty, hw, hh):
    """Ponto onde o segmento centro→alvo sai do retângulo (meia largura/altura)."""
    dx, dy = tx - cx, ty - cy
    scale = min(hw / abs(dx) if dx else math.inf, hh / abs(dy) if dy else math.inf)
    return cx + dx * scale, cy + dy * scale


def ciclo_svg(items: list[Item], title: str = "Ciclo", palette=PALETTE,
              width: int = 1200, height: int = 700) -> SvgResult:
    """Itens numa elipse, no sentido horário a partir do topo; a última seta volta ao 1."""
    if not 3 <= len(items) <= 6:
        raise ValueError("ciclo em SVG aceita de 3 a 6 itens")
    n = len(items)
    bw, bh = 250, 170 if any(i.detail for i in items) else 120
    rx, ry = (width - bw) / 2 - 30, (height - bh) / 2 - 24
    cx0, cy0 = width / 2, height / 2
    centers = [
        (cx0 + rx * math.sin(2 * math.pi * k / n), cy0 - ry * math.cos(2 * math.pi * k / n))
        for k in range(n)
    ]
    warnings: list[str] = []
    body: list[str] = []
    for k in range(n):
        (ax, ay), (bx, by) = centers[k], centers[(k + 1) % n]
        x1, y1 = _clip_to_box(ax, ay, bx, by, bw / 2 + 8, bh / 2 + 8)
        x2, y2 = _clip_to_box(bx, by, ax, ay, bw / 2 + 10, bh / 2 + 10)
        body.append(f'<line data-role="seta" data-from="{k + 1}" data-to="{(k + 1) % n + 1}"'
                    f' x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"'
                    f' stroke="{palette["line"]}" stroke-width="3" marker-end="url(#seta)"/>')
    for k, (item, (cx, cy)) in enumerate(zip(items, centers)):
        body += _item_block(item, k, cx - bw / 2, cy - bh / 2, bw, bh, palette, warnings, pad=10)
    return SvgResult(svg_doc(width, height, body, title, palette), "ciclo", warnings)


def br_number(value: float) -> str:
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def barras_svg(bars: list[Bar], unit: str | None = None, title: str = "Gráfico",
               palette=PALETTE, width: int = 1200, height: int = 600) -> SvgResult:
    """Barras verticais com altura exatamente proporcional ao valor (base comum em zero)."""
    if not 2 <= len(bars) <= 8:
        raise ValueError("grafico em SVG aceita de 2 a 8 barras")
    if any(b.value < 0 for b in bars):
        raise ValueError("grafico em SVG não aceita valores negativos")
    margin, n = 32, len(bars)
    warnings: list[str] = []
    body: list[str] = []
    top = margin
    if unit:
        us, ulines, _ = fit(unit, width - 2 * margin, 40, [14, 12])
        body.append(text_el(ulines, margin, top, us, palette["muted"], anchor="start",
                            attrs=' data-role="unidade"'))
        top += block_height(ulines, us) + 8
    slot = (width - 2 * margin) / n
    label_sizes = [16, 14, 13, 12]
    for size in label_sizes:
        wrapped = [wrap(b.label, slot - 12, size) for b in bars]
        if all(w is not None and len(w) <= 3 for w in wrapped):
            break
    else:
        warnings.append("rótulos das barras não couberam em 3 linhas")
        wrapped = [wrap(b.label, slot - 12, size) or [b.label] for b in bars]
    label_h = max(block_height(w, size) for w in wrapped)
    value_size = 16
    value_h = value_size * PX * LINE
    base_y = height - margin - label_h - 8
    chart_h = base_y - top - value_h - 4
    peak = max(b.value for b in bars) or 1.0
    bar_w = min(120, slot * 0.6)
    body.append(f'<line data-role="base" x1="{margin}" y1="{base_y:.2f}"'
                f' x2="{width - margin}" y2="{base_y:.2f}" stroke="{palette["line"]}"'
                ' stroke-width="2"/>')
    best = max(range(n), key=lambda k: bars[k].value)
    for k, bar in enumerate(bars):
        cx = margin + k * slot + slot / 2
        h = chart_h * bar.value / peak
        color = palette["accent"] if k == best else palette["primary"]
        body.append(f'<rect data-role="barra" data-index="{k + 1}" data-valor="{bar.value:g}"'
                    f' x="{cx - bar_w / 2:.2f}" y="{base_y - h:.2f}" width="{bar_w:.2f}"'
                    f' height="{h:.2f}" fill="{color}"/>')
        body.append(text_el([br_number(bar.value)], cx, base_y - h - value_h - 2, value_size,
                            palette["text"], bold=True,
                            attrs=f' data-role="valor" data-index="{k + 1}"'))
        body.append(text_el(wrapped[k], cx, base_y + 8, size, palette["muted"],
                            attrs=f' data-role="rotulo" data-index="{k + 1}"'))
    return SvgResult(svg_doc(width, height, body, title, palette), "grafico", warnings)


def slide_svg(slide: AltoSlide, palette=PALETTE) -> SvgResult | None:
    """SVG de um slide ``etapas`` (fluxo), ``ciclo`` (etapas com volta) ou ``grafico``."""
    title = slide.title or slide.kind
    if slide.kind == "etapas":
        if slide.cycle:
            return ciclo_svg(slide.items, title, palette)
        return etapas_svg(slide.items, title, palette)
    if slide.kind == "grafico":
        return barras_svg(slide.bars, slide.unit, title, palette)
    return None


def deck_svgs(deck: AltoDeck, palette=PALETTE) -> list[tuple[int, SvgResult]]:
    """Todos os diagramas do deck, com o número (1-based) do slide de origem."""
    out = []
    for number, slide in enumerate(deck.slides, start=1):
        result = slide_svg(slide, palette)
        if result is not None:
            out.append((number, result))
    return out
