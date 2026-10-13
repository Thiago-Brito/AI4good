"""Compila SlideDSL Alto para SlideDSL 1.1 (baixo nível) com layouts determinísticos.

Cada tipo de slide tem uma composição própria (cards, números grandes, linha do tempo,
gráfico de barras em formas editáveis...). Tamanhos de fonte são escolhidos medindo o
texto com a mesma estimativa das regras de design e com a medição Arial local; o texto
nunca é cortado: quando não cabe nem na fonte mínima, emite A010 com o caminho do campo.
"""

from dataclasses import dataclass, field
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

from .alto import AltoDeck, AltoSlide
from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .design_rules import load_rules
from .diagnostics import Diagnostic
from .printer import print_ast

W, H, M = 1280, 720, 64
CONTENT_BOTTOM = 636

PALETTES = {
    "claro": {
        "bg": "#F6F8FC",
        "text": "#14233D",
        "muted": "#475569",
        "primary": "#2563EB",
        "on_primary": "#FFFFFF",
        "soft": "#DDE8F9",
        "card": "#FFFFFF",
        "accent": "#B45309",
        "on_accent": "#FFFFFF",
        "line": "#CBD5E1",
    },
    "escuro": {
        "bg": "#14233D",
        "text": "#F1F5F9",
        "muted": "#CBD5E1",
        "primary": "#60A5FA",
        "on_primary": "#14233D",
        "soft": "#334765",
        "card": "#1E3252",
        "accent": "#FBBF24",
        "on_accent": "#14233D",
        "line": "#334765",
    },
}


def needed_height(text: str, width: float, size: int, bold: bool = False) -> int:
    """Maior altura entre a estimativa de D010 e a medição Arial com quebra de palavras."""
    cfg = load_rules()
    px = size * 96 / 72
    capacity = max(
        1,
        math.floor((width - 2 * cfg["text_padding"]) / (cfg["character_width_factor"] * px)),
    )
    lines = sum(max(1, math.ceil(len(line) / capacity)) for line in text.split("\n"))
    estimate = math.ceil(lines * px * cfg["line_height_factor"] + 2 * cfg["text_padding"] + 2)
    from .text_metrics import text_height

    # Negrito ocupa ~10% a mais; a margem evita quebras extras no PowerPoint.
    return max(estimate, text_height(text, width * (0.95 if bold else 0.98), size, bold))


@dataclass
class Builder:
    number: int
    palette: dict
    commands: list[Command] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)
    counter: int = 0

    def _id(self, name: str) -> str:
        self.counter += 1
        return f"s{self.number}_{name}_{self.counter}"

    def rect(self, name, x, y, w, h, color, role="decoracao", rounded=False):
        id = self._id(name)
        self.commands.append(
            Command(
                op="add",
                id=id,
                element_type="rectangle",
                position=Position(kind="absolute", x=round(x), y=round(y)),
                size=(max(1, round(w)), max(1, round(h))),
                color=color,
                role=role,
                rounded=rounded,
            )
        )
        return id

    def ellipse(self, name, x, y, w, h, color, role="decoracao"):
        id = self._id(name)
        self.commands.append(
            Command(
                op="add",
                id=id,
                element_type="ellipse",
                position=Position(kind="absolute", x=round(x), y=round(y)),
                size=(round(w), round(h)),
                color=color,
                role=role,
            )
        )
        return id

    def image(self, name, file, x, y, w, h):
        id = self._id(name)
        self.commands.append(
            Command(
                op="add",
                id=id,
                element_type="image",
                file=file,
                position=Position(kind="absolute", x=round(x), y=round(y)),
                size=(round(w), round(h)),
                role="nenhum",
            )
        )
        return id

    def fit(self, text, w, max_h, sizes, bold=False, path=None):
        for size in sizes:
            h = needed_height(text, w, size, bold)
            if h <= max_h:
                return size, h
        size = sizes[-1]
        h = needed_height(text, w, size, bold)
        self.diagnostics.append(
            Diagnostic(
                code="A010",
                severity="ERRO",
                message=f"Texto não cabe no espaço do layout nem com {size} pt.",
                slide=self.number,
                evidence={"path": path, "needed": h, "available": max_h},
                suggestion="Encurte este campo ou divida o conteúdo em dois slides.",
            )
        )
        return size, h

    def text(
        self,
        name,
        value,
        x,
        y,
        w,
        h,
        size,
        color,
        bold=False,
        align="left",
        role="nenhum",
        path=None,
    ):
        id = self._id(name)
        self.commands.append(
            Command(
                op="add",
                id=id,
                element_type="text",
                text=value,
                position=Position(kind="absolute", x=round(x), y=round(y)),
                size=(round(w), max(1, round(h))),
                font_size=size,
                color=color,
                role=role,
                font_face="Arial",
                bold=bold,
                align=align,
            )
        )
        if path:
            self.mapping[id] = path
        return id

    def fitted(self, name, value, x, y, w, max_h, sizes, color, *, path, **kw):
        size, h = self.fit(value, w, max_h, sizes, kw.get("bold", False), path)
        self.text(name, value, x, y, w, h, size, color, path=path, **kw)
        return h

    def notes(self, value):
        if value:
            self.commands.append(Command(op="notes", text=value))


def source_label(ref: str, facts: dict) -> str:
    fact = facts.get(ref)
    if fact:
        title = fact.get("source_title") or ""
        host = urlsplit(fact.get("url") or "").hostname or ""
        host = re.sub(r"^www\.", "", host)
        return f"{title} ({host})" if title and host else title or host or ref
    return ref


def header(b: Builder, s: AltoSlide, base: str) -> float:
    p = b.palette
    b.rect("marca", M, 52, 56, 6, p["primary"], rounded=False)
    # Até duas linhas a 42 pt (tamanho do tema). Título mais longo reduz a fonte
    # (D003 vira aviso, não erro) antes de acusar A010.
    size, h = b.fit(s.title, W - 2 * M, 160, [42, 38, 34, 32], True, f"{base}.title")
    b.text(
        "titulo",
        s.title,
        M,
        66,
        W - 2 * M,
        h,
        size,
        p["text"],
        bold=True,
        role="titulo",
        path=f"{base}.title",
    )
    return 66 + h + 16


def footer(b: Builder, s: AltoSlide, facts: dict, total: int):
    """Rodapé curto (domínios das fontes, uma linha); títulos e URLs completos vão nas notas."""
    p = b.palette
    labels = []
    for ref in s.sources:
        fact = facts.get(ref)
        if fact:
            label = re.sub(r"^www\.", "", urlsplit(fact.get("url") or "").hostname or "") or ref
        else:
            label = ref
        if label not in labels:
            labels.append(label)
    if labels:
        shown = list(labels)
        while True:
            extra = len(labels) - len(shown)
            value = "Fonte: " + "; ".join(shown) + (f" e mais {extra}" if extra else "")
            if needed_height(value, 1000, 12) <= 40 or len(shown) == 1:
                break
            shown.pop()
        if needed_height(value, 1000, 12) > 40:
            value = value[:100].rsplit(" ", 1)[0] + "…"
        b.text("fonte", value, M, 664, 1000, 40, 12, p["muted"], path=f"slides.{b.number - 1}.sources")
    b.text(
        "pagina", f"{b.number}/{total}", W - M - 120, 664, 120, 40, 12, p["muted"], align="right"
    )


# ---------------------------------------------------------------------------
# Composições por tipo de slide. Textos do mesmo papel compartilham um único
# tamanho de fonte (o maior que cabe para todos), mantendo o slide uniforme.


def uniform(b, entries, w, max_h, sizes, bold=False):
    """entries: [(texto, caminho)]. Retorna (fonte, maior altura) comum ao grupo."""
    entries = [(t, path) for t, path in entries if t]
    if not entries:
        return sizes[0], 0
    for size in sizes:
        heights = [needed_height(t, w, size, bold) for t, _ in entries]
        if max(heights) <= max_h:
            return size, max(heights)
    size = sizes[-1]
    for t, path in entries:
        b.fit(t, w, max_h, [size], bold, path)
    return size, max(needed_height(t, w, size, bold) for t, _ in entries)


def label_detail_sizes(b, labels, details, w, label_max, block_h, label_sizes, detail_sizes):
    """Escolhe o par (rótulo, detalhe) que dá ao detalhe a maior fonte possível.

    Rótulos menores liberam espaço para o detalhe; só emite A010 se nenhum par couber.
    """
    probe = Builder(b.number, b.palette)
    best = None
    for ls in label_sizes:
        ls_, lh = uniform(probe, labels, w, label_max, [ls], True)
        if probe.diagnostics:
            probe.diagnostics.clear()
            continue
        for ds in detail_sizes:
            ds_, dh = uniform(probe, details, w, block_h - lh, [ds])
            if not probe.diagnostics:
                if best is None or ds > best[2] or (ds == best[2] and ls > best[0]):
                    best = (ls, lh, ds, dh)
                break
            probe.diagnostics.clear()
    if best:
        return best
    ls, lh = uniform(b, labels, w, label_max, label_sizes[-1:], True)
    ds, dh = uniform(b, details, w, block_h - lh, detail_sizes[-1:])
    return ls, lh, ds, dh


def layout_capa(b, s, base, deck):
    p = b.palette
    import zlib

    variant = zlib.crc32((deck.title or "").encode("utf-8")) % 3
    if variant == 0:
        b.rect("painel", 800, 0, 480, H, p["soft"])
        b.ellipse("circulo", 860, 170, 360, 360, p["primary"])
        b.ellipse("ponto", 1120, 90, 96, 96, p["accent"])
    elif variant == 1:
        b.rect("painel", 840, 72, 376, 576, p["primary"], rounded=True)
        b.rect("bloco", 800, 380, 220, 220, p["soft"], rounded=True)
        b.ellipse("ponto", 1100, 120, 72, 72, p["accent"])
    else:
        for k, (height, color) in enumerate(
            [(220, p["soft"]), (360, p["primary"]), (280, p["soft"]), (480, p["accent"])]
        ):
            b.rect("barra", 840 + k * 96, 600 - height, 72, height, color, rounded=True)
        b.rect("base", 816, 612, 400, 6, p["line"])
    w = 680
    th = needed_height(s.title, w, 42, True)
    if th > 320:
        b.fit(s.title, w, 320, [42], True, f"{base}.title")
    ss, sh = uniform(b, [(s.subtitle, f"{base}.subtitle")], w, 150, [26, 24, 22, 20])
    ah = needed_height(s.author, w, 18) if s.author else 0
    total = th + (sh + 12 if s.subtitle else 0) + (ah + 20 if s.author else 0)
    y = max(120, (H - total) / 2)
    b.rect("marca", M, y - 28, 72, 8, p["primary"])
    b.text(
        "titulo",
        s.title,
        M,
        y,
        w,
        th,
        42,
        p["text"],
        bold=True,
        role="titulo",
        path=f"{base}.title",
    )
    y += th + 12
    if s.subtitle:
        b.text("subtitulo", s.subtitle, M, y, w, sh, ss, p["muted"], path=f"{base}.subtitle")
        y += sh + 20
    if s.author:
        b.text("autor", s.author, M, y, w, ah, 18, p["primary"], bold=True, path=f"{base}.author")


def layout_secao(b, s, base, deck):
    p = b.palette
    b.rect("painel", 0, 0, 420, H, p["primary"])
    index = sum(1 for x in deck.slides[: b.number] if x.kind == "secao")
    b.text(
        "numero",
        f"{index:02d}",
        64,
        270,
        300,
        needed_height("00", 300, 96, True),
        96,
        p["on_primary"],
        bold=True,
    )
    th = needed_height(s.title, 732, 42, True)
    ss, sh = uniform(b, [(s.subtitle, f"{base}.subtitle")], 732, 180, [26, 24, 22, 20])
    y = (H - th - (sh + 12 if s.subtitle else 0)) / 2
    b.text(
        "titulo",
        s.title,
        484,
        y,
        732,
        th,
        42,
        p["text"],
        bold=True,
        role="titulo",
        path=f"{base}.title",
    )
    if s.subtitle:
        b.text(
            "subtitulo",
            s.subtitle,
            484,
            y + th + 12,
            732,
            sh,
            ss,
            p["muted"],
            path=f"{base}.subtitle",
        )


def layout_topicos(b, s, base, deck, top):
    p = b.palette
    n = len(s.items)
    labels = [(i.label, f"{base}.items.{k}.label") for k, i in enumerate(s.items)]
    details = [(i.detail, f"{base}.items.{k}.detail") for k, i in enumerate(s.items)]
    if n <= 3 and b.number % 2 == 0:  # alterna cards e lista para não repetir o visual
        gap = 24
        w = (W - 2 * M - gap * (n - 1)) / n
        h = CONTENT_BOTTOM - top
        inner = w - 48
        ls, lh = uniform(b, labels, inner, 110, [28, 26, 24, 22], True)
        ds, dh = uniform(b, details, inner, h - 32 - 64 - lh - 24, [24, 22, 20, 18, 16])
        for k, item in enumerate(s.items):
            x = M + k * (w + gap)
            b.rect("card", x, top, w, h, p["card"], rounded=True)
            b.rect("faixa", x, top, w, 8, p["primary"])
            b.ellipse("num", x + 24, top + 32, 48, 48, p["primary"])
            b.text(
                "num_txt",
                str(k + 1),
                x + 24,
                top + 32,
                48,
                48,
                18,
                p["on_primary"],
                bold=True,
                align="center",
            )
            b.text(
                "rotulo",
                item.label,
                x + 24,
                top + 96,
                inner,
                lh,
                ls,
                p["text"],
                bold=True,
                path=f"{base}.items.{k}.label",
            )
            if item.detail:
                b.text(
                    "detalhe",
                    item.detail,
                    x + 24,
                    top + 96 + lh + 4,
                    inner,
                    dh,
                    ds,
                    p["muted"],
                    path=f"{base}.items.{k}.detail",
                )
        return
    row = (CONTENT_BOTTOM - top) / n
    label_w = 340
    detail_w = W - M - (M + 64 + label_w + 16)
    ls, _ = uniform(b, labels, label_w, row - 8, [24, 22, 20, 18], True)
    ds, _ = uniform(b, details, detail_w, row - 8, [22, 20, 18, 16])
    for k, item in enumerate(s.items):
        y = top + k * row
        b.ellipse("num", M, y + 6, 44, 44, p["primary"])
        b.text(
            "num_txt", str(k + 1), M, y + 6, 44, 44, 16, p["on_primary"], bold=True, align="center"
        )
        b.text(
            "rotulo",
            item.label,
            M + 64,
            y,
            label_w,
            needed_height(item.label, label_w, ls, True),
            ls,
            p["text"],
            bold=True,
            path=f"{base}.items.{k}.label",
        )
        if item.detail:
            b.text(
                "detalhe",
                item.detail,
                M + 64 + label_w + 16,
                y,
                detail_w,
                needed_height(item.detail, detail_w, ds),
                ds,
                p["muted"],
                path=f"{base}.items.{k}.detail",
            )
        if k < n - 1:
            b.rect("divisor", M + 64, y + row - 6, W - 2 * M - 64, 2, p["line"])


def layout_numeros(b, s, base, deck, top):
    p = b.palette
    n = len(s.values)
    if n == 1:  # um número só: destaque à esquerda, explicação à direita
        v = s.values[0]
        h = CONTENT_BOTTOM - top
        b.rect("card", M, top, 520, h, p["card"], rounded=True)
        b.rect("faixa", M, top + h - 10, 520, 10, p["primary"])
        vs, vh = uniform(
            b,
            [(v.value, f"{base}.values.0.value")],
            472,
            h - 40,
            [96, 88, 80, 72, 64, 56, 48],
            True,
        )
        b.text(
            "valor",
            v.value,
            M + 24,
            top + (h - vh) / 2,
            472,
            vh,
            vs,
            p["primary"],
            bold=True,
            align="center",
            path=f"{base}.values.0.value",
        )
        cs, ch = uniform(
            b, [(v.label, f"{base}.values.0.label")], W - 2 * M - 584, h, [32, 30, 28, 26, 24, 22]
        )
        b.rect("marca", M + 584, top + (h - ch) / 2 - 20, 56, 6, p["accent"])
        b.text(
            "legenda",
            v.label,
            M + 584,
            top + (h - ch) / 2,
            W - 2 * M - 584,
            ch,
            cs,
            p["text"],
            path=f"{base}.values.0.label",
        )
        return
    gap = 32
    w = (W - 2 * M - gap * (n - 1)) / n
    h = min(CONTENT_BOTTOM - top, 380)
    y = top + (CONTENT_BOTTOM - top - h) / 2
    vs, vh = uniform(
        b,
        [(v.value, f"{base}.values.{k}.value") for k, v in enumerate(s.values)],
        w - 32,
        150,
        [88, 80, 72, 64, 56, 48],
        True,
    )
    cs, ch = uniform(
        b,
        [(v.label, f"{base}.values.{k}.label") for k, v in enumerate(s.values)],
        w - 48,
        h - vh - 72,
        [24, 22, 20, 18],
    )
    for k, v in enumerate(s.values):
        x = M + k * (w + gap)
        b.rect("card", x, y, w, h, p["card"], rounded=True)
        b.rect("faixa", x, y + h - 10, w, 10, p["accent"] if k % 2 else p["primary"])
        b.text(
            "valor",
            v.value,
            x + 16,
            y + 32,
            w - 32,
            vh,
            vs,
            p["primary"],
            bold=True,
            align="center",
            path=f"{base}.values.{k}.value",
        )
        b.text(
            "legenda",
            v.label,
            x + 24,
            y + 40 + vh,
            w - 48,
            ch,
            cs,
            p["text"],
            align="center",
            path=f"{base}.values.{k}.label",
        )


def layout_comparacao(b, s, base, deck, top):
    p = b.palette
    gap = 40
    bottom = CONTENT_BOTTOM + 12
    w = (W - 2 * M - gap) / 2
    sides = s.sides[:2]
    ns, nh = uniform(
        b,
        [(x.name, f"{base}.sides.{k}.name") for k, x in enumerate(sides)],
        w - 32,
        64,
        [26, 24, 22],
        True,
    )
    body_top = top + nh + 20
    rows = max(len(x.items) for x in sides)
    row = (bottom - body_top - 8) / rows
    labels = [
        (i.label, f"{base}.sides.{k}.items.{j}.label")
        for k, x in enumerate(sides)
        for j, i in enumerate(x.items)
    ]
    details = [
        (i.detail, f"{base}.sides.{k}.items.{j}.detail")
        for k, x in enumerate(sides)
        for j, i in enumerate(x.items)
    ]
    ls, lh, ds, dh = label_detail_sizes(
        b, labels, details, w - 64, 60, row + 14, [24, 22, 20, 18], [22, 20, 18, 16]
    )
    for k, side in enumerate(sides):
        x = M + k * (w + gap)
        color, on = (p["primary"], p["on_primary"]) if k == 0 else (p["accent"], p["on_accent"])
        b.rect("cabecalho", x, top, w, nh + 8, color, rounded=True)
        b.text(
            "lado",
            side.name,
            x + 16,
            top + 4,
            w - 32,
            nh,
            ns,
            on,
            bold=True,
            align="center",
            path=f"{base}.sides.{k}.name",
        )
        b.rect("corpo", x, body_top - 8, w, bottom - body_top + 8, p["card"], rounded=True)
        for j, item in enumerate(side.items):
            y = body_top + j * row
            b.rect("marcador", x + 24, y + 16, 12, 12, color)
            b.text(
                "rotulo",
                item.label,
                x + 44,
                y,
                w - 64,
                lh,
                ls,
                p["text"],
                bold=True,
                path=f"{base}.sides.{k}.items.{j}.label",
            )
            if item.detail:
                b.text(
                    "detalhe",
                    item.detail,
                    x + 44,
                    y + lh - 16,
                    w - 64,
                    dh,
                    ds,
                    p["muted"],
                    path=f"{base}.sides.{k}.items.{j}.detail",
                )


def layout_etapas(b, s, base, deck, top):
    p = b.palette
    n = len(s.items)
    col = (W - 2 * M) / n
    circle = 72
    cy = top + 16
    y = cy + circle + 20
    ls, lh = uniform(
        b,
        [(i.label, f"{base}.items.{k}.label") for k, i in enumerate(s.items)],
        col - 16,
        100,
        [24, 22, 20, 18],
        True,
    )
    ds, dh = uniform(
        b,
        [(i.detail, f"{base}.items.{k}.detail") for k, i in enumerate(s.items)],
        col - 16,
        CONTENT_BOTTOM - (y + lh + 4),
        [22, 20, 18, 16],
    )
    b.rect("trilho", M + col / 2, cy + circle / 2 - 3, col * (n - 1), 6, p["soft"])
    for k, item in enumerate(s.items):
        cx = M + k * col + col / 2
        b.ellipse("circulo", cx - circle / 2, cy, circle, circle, p["primary"])
        b.text(
            "num_txt",
            str(k + 1),
            cx - circle / 2,
            cy,
            circle,
            circle,
            26,
            p["on_primary"],
            bold=True,
            align="center",
        )
        b.text(
            "rotulo",
            item.label,
            M + k * col + 8,
            y,
            col - 16,
            lh,
            ls,
            p["text"],
            bold=True,
            align="center",
            path=f"{base}.items.{k}.label",
        )
        if item.detail:
            b.text(
                "detalhe",
                item.detail,
                M + k * col + 8,
                y + lh + 4,
                col - 16,
                dh,
                ds,
                p["muted"],
                align="center",
                path=f"{base}.items.{k}.detail",
            )


def layout_linha(b, s, base, deck, top):
    p = b.palette
    n = len(s.milestones)
    col = (W - 2 * M) / n
    ms = s.milestones
    dsz, dth = uniform(
        b,
        [(m.date, f"{base}.milestones.{k}.date") for k, m in enumerate(ms)],
        col - 8,
        80,
        [32, 28, 24, 20],
        True,
    )
    line_y = top + dth + 24
    y = line_y + 30
    ls, lh = uniform(
        b,
        [(m.label, f"{base}.milestones.{k}.label") for k, m in enumerate(ms)],
        col - 8,
        110,
        [22, 20, 18, 16],
        True,
    )
    ds, dh = uniform(
        b,
        [(m.detail, f"{base}.milestones.{k}.detail") for k, m in enumerate(ms)],
        col - 8,
        CONTENT_BOTTOM - (y + lh + 2),
        [20, 18, 16, 14],
    )
    b.rect("eixo", M, line_y - 2, W - 2 * M, 4, p["line"])
    for k, m in enumerate(ms):
        x = M + k * col
        cx = x + col / 2
        path = f"{base}.milestones.{k}"
        b.text(
            "data",
            m.date,
            x + 4,
            top,
            col - 8,
            dth,
            dsz,
            p["primary"],
            bold=True,
            align="center",
            path=f"{path}.date",
        )
        b.ellipse(
            "ponto", cx - 14, line_y - 14, 28, 28, p["accent"] if k == n - 1 else p["primary"]
        )
        b.text(
            "rotulo",
            m.label,
            x + 4,
            y,
            col - 8,
            lh,
            ls,
            p["text"],
            bold=True,
            align="center",
            path=f"{path}.label",
        )
        if m.detail:
            b.text(
                "detalhe",
                m.detail,
                x + 4,
                y + lh + 2,
                col - 8,
                dh,
                ds,
                p["muted"],
                align="center",
                path=f"{path}.detail",
            )


def layout_citacao(b, s, base, deck):
    p = b.palette
    b.rect("painel", M, 120, W - 2 * M, 440, p["card"], rounded=True)
    b.rect("barra", M, 120, 12, 440, p["primary"])
    b.text(
        "aspas",
        "“",
        M + 48,
        128,
        120,
        needed_height("“", 120, 96, True),
        96,
        p["primary"],
        bold=True,
    )
    th = b.fitted(
        "citacao",
        s.text,
        M + 64,
        236,
        W - 2 * M - 128,
        230,
        [34, 32, 30, 28, 26, 24],
        p["text"],
        path=f"{base}.text",
    )
    b.fitted(
        "autor",
        "— " + s.author,
        M + 64,
        min(236 + th + 16, 480),
        W - 2 * M - 128,
        60,
        [22, 20],
        p["muted"],
        align="right",
        path=f"{base}.author",
    )


def br_number(value: float) -> str:
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def layout_grafico(b, s, base, deck, top):
    p = b.palette
    n = len(s.bars)
    if s.unit:
        uh = needed_height(s.unit, 900, 16)
        b.text("unidade", s.unit, M, top - 8, 900, uh, 16, p["muted"], path=f"{base}.unit")
        top += uh - 8
    slot = (W - 2 * M) / n
    ls, label_h = uniform(
        b,
        [(x.label, f"{base}.bars.{k}.label") for k, x in enumerate(s.bars)],
        slot - 8,
        64,
        [18, 16, 14, 12],
    )
    value_h = needed_height("0", 100, 20, True)
    base_y = CONTENT_BOTTOM - label_h - 6
    chart_h = base_y - top - value_h
    peak = max(x.value for x in s.bars) or 1
    bar_w = min(140, slot * 0.6)
    best = max(range(n), key=lambda k: s.bars[k].value)
    b.rect("base", M, base_y, W - 2 * M, 3, p["line"])
    for k, bar in enumerate(s.bars):
        x = M + k * slot + (slot - bar_w) / 2
        h = max(4, chart_h * bar.value / peak)
        b.rect("barra", x, base_y - h, bar_w, h, p["accent"] if k == best else p["primary"])
        b.text(
            "valor",
            br_number(bar.value),
            M + k * slot,
            base_y - h - value_h,
            slot,
            value_h,
            20,
            p["text"],
            bold=True,
            align="center",
            path=f"{base}.bars.{k}.value",
        )
        b.text(
            "rotulo",
            bar.label,
            M + k * slot + 4,
            base_y + 6,
            slot - 8,
            label_h,
            ls,
            p["muted"],
            align="center",
            path=f"{base}.bars.{k}.label",
        )


def layout_imagem(b, s, base, deck, top, root: Path | None):
    p = b.palette
    img_x, img_w = 664, W - M - 664
    if s.image_file:
        b.rect("moldura", img_x, top, img_w, CONTENT_BOTTOM - top - 40, p["soft"], rounded=True)
        b.image("imagem", s.image_file, img_x + 8, top + 8, img_w - 16, CONTENT_BOTTOM - top - 56)
        if s.caption:
            b.fitted(
                "legenda",
                s.caption,
                img_x,
                CONTENT_BOTTOM - 36,
                img_w,
                48,
                [14, 12],
                p["muted"],
                path=f"{base}.caption",
            )
    else:
        b.diagnostics.append(
            Diagnostic(
                code="A011",
                severity="AVISO",
                message="Imagem não resolvida; slide compilado sem a imagem.",
                slide=b.number,
                evidence={"path": f"{base}.image_query", "query": s.image_query},
                suggestion="Gere com imagens habilitadas ou informe arquivo local.",
            )
        )
        b.rect("moldura", img_x, top, img_w, CONTENT_BOTTOM - top, p["soft"], rounded=True)
        if s.caption:
            b.fitted(
                "legenda",
                s.caption,
                img_x + 32,
                top + 32,
                img_w - 64,
                CONTENT_BOTTOM - top - 64,
                [26, 24, 22, 20],
                p["text"],
                path=f"{base}.caption",
            )
    text_w = img_x - M - 56
    per = (CONTENT_BOTTOM - top) / max(1, len(s.items))
    ls, lh = uniform(
        b,
        [(i.label, f"{base}.items.{k}.label") for k, i in enumerate(s.items)],
        text_w,
        70,
        [24, 22, 20],
        True,
    )
    ds, dh = uniform(
        b,
        [(i.detail, f"{base}.items.{k}.detail") for k, i in enumerate(s.items)],
        text_w,
        per - lh - 8,
        [20, 18, 16],
    )
    for k, item in enumerate(s.items):
        y = top + k * per
        b.rect("marcador", M, y + 16, 12, 12, p["primary"])
        b.text(
            "rotulo",
            item.label,
            M + 24,
            y,
            text_w,
            lh,
            ls,
            p["text"],
            bold=True,
            path=f"{base}.items.{k}.label",
        )
        if item.detail:
            b.text(
                "detalhe",
                item.detail,
                M + 24,
                y + lh - 8,
                text_w,
                dh,
                ds,
                p["muted"],
                path=f"{base}.items.{k}.detail",
            )


def layout_conclusao(b, s, base, deck, top):
    p = b.palette
    n = len(s.items)
    b.rect("painel", M, top, W - 2 * M, CONTENT_BOTTOM - top, p["soft"], rounded=True)
    row = (CONTENT_BOTTOM - top - 32) / n
    w = W - 2 * M - 120
    ls, lh, ds, dh = label_detail_sizes(
        b,
        [(i.label, f"{base}.items.{k}.label") for k, i in enumerate(s.items)],
        [(i.detail, f"{base}.items.{k}.detail") for k, i in enumerate(s.items)],
        w,
        60,
        row + 4,
        [26, 24, 22],
        [22, 20, 18, 16],
    )
    for k, item in enumerate(s.items):
        y = top + 16 + k * row
        b.rect("check", M + 24, y + 6, 44, 44, p["primary"], rounded=True)
        b.text(
            "check_txt",
            str(k + 1),
            M + 24,
            y + 6,
            44,
            44,
            14,
            p["on_primary"],
            bold=True,
            align="center",
        )
        b.text(
            "rotulo",
            item.label,
            M + 88,
            y,
            w,
            lh,
            ls,
            p["text"],
            bold=True,
            path=f"{base}.items.{k}.label",
        )
        if item.detail:
            b.text(
                "detalhe",
                item.detail,
                M + 88,
                y + lh - 8,
                w,
                dh,
                ds,
                p["text"],
                path=f"{base}.items.{k}.detail",
            )


def full_notes(s: AltoSlide, facts: dict) -> str | None:
    parts = [s.notes] if s.notes else []
    refs = []
    for ref in s.sources:
        fact = facts.get(ref)
        if fact:
            refs.append(f"[{ref}] {fact.get('claim', '')} — {fact.get('url', '')}")
        else:
            refs.append(ref)
    if refs:
        parts.append("Fontes:\n" + "\n".join(refs))
    return "\n\n".join(parts) or None


def alto_to_ast(
    deck: AltoDeck, facts: dict | None = None, root: Path | None = None
) -> tuple[PresentationNode, dict[str, str], list[Diagnostic]]:
    facts = facts or {}
    palette = PALETTES[deck.theme]
    slides, mapping, diagnostics = [], {}, []
    total = len(deck.slides)
    for n, s in enumerate(deck.slides, 1):
        b = Builder(n, palette)
        base = f"slides.{n - 1}"
        if s.kind == "capa":
            layout_capa(b, s, base, deck)
        elif s.kind == "secao":
            layout_secao(b, s, base, deck)
        elif s.kind == "citacao":
            layout_citacao(b, s, base, deck)
            footer(b, s, facts, total)
        else:
            top = header(b, s, base)
            {
                "topicos": layout_topicos,
                "numeros": layout_numeros,
                "comparacao": layout_comparacao,
                "etapas": layout_etapas,
                "linha_do_tempo": layout_linha,
                "grafico": layout_grafico,
                "conclusao": layout_conclusao,
            }.get(s.kind, lambda *a: layout_imagem(*a, root))(b, s, base, deck, top)
            footer(b, s, facts, total)
        b.notes(full_notes(s, facts))
        slides.append(SlideNode(number=n, commands=b.commands))
        mapping.update({f"{n}:{k}": v for k, v in b.mapping.items()})
        diagnostics += b.diagnostics
    return PresentationNode(title=deck.title, theme=deck.theme, slides=slides), mapping, diagnostics


def alto_to_dsl(deck: AltoDeck, facts: dict | None = None, root: Path | None = None):
    """Retorna (fonte SlideDSL 1.1, mapa elemento→campo alto, diagnósticos de layout)."""
    ast, mapping, diagnostics = alto_to_ast(deck, facts, root)
    return print_ast(ast), mapping, diagnostics
