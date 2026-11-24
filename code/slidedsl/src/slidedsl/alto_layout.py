"""Compila SlideDSL Alto para SlideDSL 1.1 (baixo nível) com layouts determinísticos.

Cada tipo de slide tem uma composição própria (cards, números grandes, linha do tempo,
gráfico de barras em formas editáveis...). Tamanhos de fonte são escolhidos medindo o
texto com a mesma estimativa das regras de design e com a medição Arial local; o texto
nunca é cortado: quando não cabe nem na fonte mínima, emite A010 com o caminho do campo.
"""

from dataclasses import dataclass, field
import math
from functools import lru_cache
from pathlib import Path
import re
from urllib.parse import urlsplit

from .alto import AltoDeck, AltoSlide
from .ast_nodes import Command, Position, PresentationNode, SlideNode
from .design_rules import load_rules
from .diagnostics import Diagnostic
from .printer import print_ast
from .editorial import (BODY_PT, LABEL_PT, MIN_TITLE_PT, MIN_LABEL_PT, MIN_BODY_PT,
                        MIN_SUBTITLE_PT, balanced_title, sentence_case,
                        visible_labels)
from .text_metrics import optical_size, text_width

from .design_system import (
    Estilo, col, distribute, WIDTH as W, HEIGHT as H, MARGIN as M,
    CONTENT_BOTTOM, TITLE_Y, CARD_PADDING, OPTICAL_LABEL_PT, LABEL_GAP, RULE,
    card_position,
    XS, SM, MD, LG, XL, XXL,
)
from .layout_score import BLOCKERS, choose, content_preference, score_slide


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


def _palette(bg, text, muted, primary, soft, card, accent, line, on_primary="#FFFFFF",
             on_accent="#FFFFFF"):
    return {"bg": bg, "text": text, "muted": muted, "primary": primary, "on_primary": on_primary,
            "soft": soft, "card": card, "accent": accent, "on_accent": on_accent, "line": line}


# Estilos visuais: paleta dos slides comuns, paleta de abertura/fechamento e tema-base
# da IR (o renderizador só conhece claro/escuro; cores próprias entram como fundo explícito).
# Inspirados em tendências recorrentes (tipografia forte, editorial, paleta contida,
# blocos de cor), sem copiar modelos de terceiros.
_PALETTE_STYLES = {
    "claro": (PALETTES["claro"], PALETTES["escuro"], "claro"),
    "escuro": (PALETTES["escuro"], PALETTES["claro"], "escuro"),
    "editorial": (
        _palette("#FAF7F2", "#1C1917", "#57534E", "#B4532A", "#EFE6DA", "#FFFFFF", "#1D4E89", "#D6CFC4"),
        _palette("#1C1917", "#FAF7F2", "#D6D3D1", "#F0A27A", "#3A3330", "#2A2522", "#9CC3F0", "#3A3330",
                 on_primary="#1C1917", on_accent="#1C1917"),
        "claro"),
    "vibrante": (
        _palette("#FFFFFF", "#111827", "#4B5563", "#6D28D9", "#EDE9FE", "#F5F3FF", "#B45309", "#DDD6FE"),
        _palette("#4C1D95", "#FFFFFF", "#E9D5FF", "#FCD34D", "#5B21B6", "#5B21B6", "#FCD34D", "#6D28D9",
                 on_primary="#4C1D95", on_accent="#4C1D95"),
        "claro"),
    "natural": (
        _palette("#F4F7F2", "#1F2A1F", "#4A5A4A", "#2F7A4F", "#DCEBDF", "#FFFFFF", "#B45309", "#C8D8CB"),
        _palette("#1F3D2B", "#F4F7F2", "#CFE3D4", "#9AE6B4", "#2C5440", "#2C5440", "#FBD38D", "#2C5440",
                 on_primary="#1F3D2B", on_accent="#1F3D2B"),
        "claro"),
    "noturno": (
        _palette("#0F172A", "#E2E8F0", "#CBD5E1", "#38BDF8", "#1E293B", "#1E293B", "#F472B6", "#334155",
                 on_primary="#0F172A", on_accent="#0F172A"),
        _palette("#020617", "#F8FAFC", "#CBD5E1", "#38BDF8", "#0F172A", "#0F172A", "#F472B6", "#1E293B",
                 on_primary="#020617", on_accent="#020617"),
        "escuro"),
}
# Cada par difere em ao menos três atributos não cromáticos.
STYLE_ATTRIBUTES = {
    "claro": ("Calibri", "Calibri", 0, "preenchido", "barra", "left", "lateral"),
    "escuro": ("Calibri", "Calibri", 12, "preenchido", "ponto", "center", "base"),
    "editorial": ("Georgia", "Calibri", 0, "fio", "numero", "left", "duplo"),
    "vibrante": ("Trebuchet MS", "Calibri", 12, "preenchido", "numero", "center", "degraus"),
    "natural": ("Cambria", "Calibri", 0, "bloco", "ponto", "left", "ramo"),
    "noturno": ("Calibri", "Calibri", 0, "fio", "barra", "left", "canto", True),
}
STYLES = {name: Estilo(*palettes, *STYLE_ATTRIBUTES[name])
          for name, palettes in _PALETTE_STYLES.items()}
RENDER_BG = {"claro": PALETTES["claro"]["bg"], "escuro": PALETTES["escuro"]["bg"]}

FEATURE_KINDS = {"capa", "conclusao"}


@lru_cache(maxsize=32768)
def needed_height(text: str, width: float, size: int, bold: bool = False, family="Arial") -> int:
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
    measured = text_height(text, width * (0.95 if bold else 0.98), size, bold, family)
    return max(estimate, measured) if family == "Arial" else measured


@dataclass
class Builder:
    number: int
    palette: dict
    commands: list[Command] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)
    counter: int = 0
    label_pt: int = LABEL_PT
    body_pt: int = BODY_PT
    style: Estilo | None = None
    variant: str = ""
    root: Path | None = None

    @property
    def title_pt(self):
        return optical_size(42, self.style.fonte_titulo if self.style else "Arial", MIN_TITLE_PT)

    def family(self, size, bold=False):
        if not self.style:
            return "Arial"
        return self.style.fonte_titulo if bold and size >= MIN_TITLE_PT else self.style.fonte_corpo

    def height(self, text, width, size, bold=False):
        return needed_height(text, width, size, bold, self.family(size, bold))

    def card(self, x, y, w, h, accent=False):
        p = self.palette
        style = self.style or STYLES["claro"]
        if style.cartao == "fio":
            self.rect("card", x, y, w, RULE, p["primary"])
        else:
            self.rect("card", x, y, w, h,
                      p["soft"] if style.fonte_titulo == "Trebuchet MS" else p["card"],
                      rounded=bool(style.raio))
            if style.cartao == "bloco" or accent:
                self.rect("faixa", x, y, XS, h, p["primary"])

    def marker(self, k, x, y):
        style = self.style or STYLES["claro"]
        if style.marcador == "numero":
            h = self.height("00", XXL, self.label_pt, True)
            self.text("marcador", f"{k + 1:02d}", x, y, XXL, h,
                      self.label_pt, self.palette["primary"], bold=True)
        elif style.marcador == "ponto":
            self.ellipse("marcador", x, y + SM, XS, XS, self.palette["primary"])
        else:
            self.rect("marcador", x, y + SM, XS, MD, self.palette["primary"])

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
            h = self.height(text, w, size, bold)
            if h <= round(max_h):
                return size, h
        size = sizes[-1]
        h = self.height(text, w, size, bold)
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
        minimum = (MIN_TITLE_PT if role == "titulo" else
                   MIN_SUBTITLE_PT if path and path.endswith(".subtitle") else
                   MIN_LABEL_PT if path and path.endswith((".label", ".name", ".date")) else
                   MIN_BODY_PT if path and path.endswith((".detail", ".text", ".unit")) else 0)
        if size < minimum:
            self.diagnostics.append(Diagnostic(code="A019", severity="ERRO", slide=self.number,
                message="Fonte abaixo do mínimo do papel.",
                evidence={"path": path, "actual": size, "minimum": minimum},
                suggestion="Mude a composição ou encurte o texto; não reduza a fonte."))
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
                font_face=self.family(size, bold),
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
    width = col(0, 6)[1] if s.kind == "imagem" and b.variant == "photo50" else col(0, 12)[1]
    title = balanced_title(s.title, width, b.title_pt, family=b.family(b.title_pt, True))
    b.rect("marca", M, TITLE_Y - SM, XL, RULE, p["primary"])
    if b.style.margem_vertical:
        b.rect("margem", MD, TITLE_Y, RULE, CONTENT_BOTTOM - TITLE_Y, p["primary"])
    size, h = b.fit(title, width, XXL * 4, [b.title_pt], True, f"{base}.title")
    b.text("titulo", title, M, TITLE_Y, width, h, size, p["text"], bold=True,
           align="left", role="titulo", path=f"{base}.title")
    return TITLE_Y + h + SM


LABELED_REF = re.compile(r"^[A-ZÀ-Ý][\wÀ-ÿ ]{1,24}:\s")


def footer(b: Builder, s: AltoSlide, facts: dict, total: int):
    """Rodapé curto (domínios das fontes, uma linha); títulos e URLs completos vão nas notas."""
    p = b.palette
    labels = []
    for ref in s.sources:
        fact = facts.get(ref)
        if fact and (fact.get("url") or "").startswith("documento:"):
            # Fato de arquivo do usuário não tem domínio: mostrar o nome do documento.
            label = fact.get("source_title") or ref
        elif fact:
            label = re.sub(r"^www\.", "", urlsplit(fact.get("url") or "").hostname or "") or ref
        else:
            label = ref
        if label not in labels:
            labels.append(label)
    if labels:
        shown = list(labels)
        while True:
            extra = len(labels) - len(shown)
            # Referência com rótulo próprio ("Execução: commit abc") dispensa "Fonte:".
            prefix = "" if all(LABELED_REF.match(x) for x in shown) else "Fonte: "
            value = prefix + "; ".join(shown) + (f" e mais {extra}" if extra else "")
            if b.height(value, 1000, 12) <= 40 or len(shown) == 1:
                break
            shown.pop()
        if b.height(value, 1000, 12) > 40:
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
    if entries and all(path.endswith((".label", ".detail", ".subtitle")) for _, path in entries):
        sizes = [b.label_pt if bold else b.body_pt]
    if not entries:
        return sizes[0], 0
    for size in sizes:
        heights = [b.height(t, w, size, bold) for t, _ in entries]
        if max(heights) <= max_h:
            return size, max(heights)
    size = sizes[-1]
    for t, path in entries:
        b.fit(t, w, max_h, [size], bold, path)
    return size, max(b.height(t, w, size, bold) for t, _ in entries)


def label_detail_sizes(b, labels, details, w, label_max, block_h, label_sizes, detail_sizes):
    """Escolhe o par (rótulo, detalhe) que dá ao detalhe a maior fonte possível.

    Rótulos menores liberam espaço para o detalhe; só emite A010 se nenhum par couber.
    """
    probe = Builder(b.number, b.palette, style=b.style)
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
    has_photo = photo(b, s, base) if s.image_file else False
    if not has_photo:
        # Sem foto, capa tipográfica: barra lateral na cor principal, sem forma decorativa solta.
        motif = b.style.motivo_capa
        if motif == "lateral":
            b.rect("faixa", 0, 0, SM, H, p["primary"])
        elif motif == "base":
            b.rect("faixa", 0, H - LG, W, LG, p["primary"])
        elif motif == "duplo":
            b.rect("faixa", M, XXL, col(0, 12)[1], RULE, p["primary"])
            b.rect("faixa", M, H - XXL, col(0, 12)[1], RULE, p["primary"])
        elif motif == "degraus":
            for k in range(3):
                b.rect("faixa", W - XXL * (k + 1), H - LG * (k + 1), XXL, LG, p["primary"])
        elif motif == "ramo":
            b.rect("faixa", M, H - XXL, col(0, 4)[1], XS, p["primary"])
        else:
            b.rect("faixa", W - LG, 0, LG, XXL * 3, p["primary"])
    w = col(0, 6)[1] if has_photo else col(0, 10)[1]
    align = b.style.alinhamento_titulo
    title = balanced_title(sentence_case(s.title), w, b.title_pt, family=b.family(b.title_pt, True))
    th = b.height(title, w, b.title_pt, True)
    if th > 320:
        b.fit(s.title, w, 320, [b.title_pt], True, f"{base}.title")
    ss, sh = uniform(b, [(s.subtitle, f"{base}.subtitle")], w, 180, [24])
    ah = b.height(s.author, w, 18) if s.author else 0
    total = th + (sh + 12 if s.subtitle else 0) + (ah + 20 if s.author else 0)
    y = max(120, (H - total) / 2)
    b.rect("marca", M + (w - 72) / 2 if align == "center" else M,
           y - 28, 72, 8, p["primary"])
    b.text(
        "titulo",
        title,
        M,
        y,
        w,
        th,
        b.title_pt,
        p["text"],
        bold=True,
        role="titulo",
        path=f"{base}.title",
        align=b.style.alinhamento_titulo,
    )
    y += th + 12
    if s.subtitle:
        b.text("subtitulo", s.subtitle, M, y, w, sh, ss, p["muted"],
               align=align, path=f"{base}.subtitle")
        y += sh + 20
    if s.author:
        b.text("autor", s.author, M, y, w, ah, 18, p["primary"], bold=True,
               align=align, path=f"{base}.author")


def layout_secao(b, s, base, deck):
    if len(deck.slides) < 8:
        # O motivo da família ganha massa; a frase continua sendo o foco.
        p, motif = b.palette, b.style.motivo_capa
        if motif in {"base", "ramo"}:
            b.rect("transicao_bloco", 0, H * 2 / 3, W, H / 3, p["soft"])
            b.rect("faixa", M, H * 2 / 3, col(0, 4)[1], XS, p["primary"])
        else:
            b.rect("transicao_bloco", W * 2 / 3, 0, W / 3, H, p["soft"])
            if motif == "degraus":
                for k in range(3):
                    b.rect("faixa", W * 2 / 3 + k * XXL, H - LG * (k + 1), XXL, LG, p["primary"])
            elif motif == "duplo":
                for y in (XXL, H - XXL):
                    b.rect("faixa", W * 2 / 3, y, W / 3, RULE, p["primary"])
            else:
                b.rect("faixa", W * 2 / 3, 0, XS, H, p["primary"])
        w = col(0, 8)[1]
        size = min(54, optical_size(48, b.style.fonte_titulo, MIN_TITLE_PT))
        title = balanced_title(s.title, w, size, family=b.family(size, True))
        th = b.height(title, w, size, True)
        sh = b.height(s.subtitle, w, b.body_pt) if s.subtitle else 0
        y = (H * (2 / 3 if motif in {"base", "ramo"} else 1) - th - sh - LABEL_GAP) / 2
        align = b.style.alinhamento_titulo
        b.rect("marca", M + (w - XL) / 2 if align == "center" else M,
               y - LG, XL, RULE, p["primary"])
        b.text("transicao", title, M, y, w, th, size, p["text"], bold=True,
               align=align, role="titulo", path=base + ".title")
        if s.subtitle:
            b.text("subtitulo", s.subtitle, M, y + th + LABEL_GAP, w, sh, b.body_pt,
                   p["muted"], align=align, path=base + ".subtitle")
        return
    p = b.palette
    b.rect("painel", 0, 0, 420, H, p["primary"])
    index = sum(1 for x in deck.slides[: b.number] if x.kind == "secao")
    b.text(
        "numero",
        f"{index:02d}",
        64,
        270,
        300,
        b.height("00", 300, 96, True),
        96,
        p["on_primary"],
        bold=True,
    )
    th = b.height(s.title, 732, b.title_pt, True)
    ss, sh = uniform(b, [(s.subtitle, f"{base}.subtitle")], 732, 180, [26, 24, 22, 20])
    y = (H - th - (sh + 12 if s.subtitle else 0)) / 2
    b.text(
        "titulo",
        s.title,
        484,
        y,
        732,
        th,
        b.title_pt,
        p["text"],
        bold=True,
        role="titulo",
        path=f"{base}.title",
        align=b.style.alinhamento_titulo,
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
            align=b.style.alinhamento_titulo,
            path=f"{base}.subtitle",
        )


def editorial_items(b, items, base, x, top, w, bottom, headings=(), cards=False):
    """Irmãos compartilham topo e slots; altura natural sem alongar o cartão."""
    if not items:
        return
    p = b.palette
    labels = visible_labels(items, *headings)
    if cards:
        columns = 2 if b.variant == "grid" else len(items)
        rows = math.ceil(len(items) / columns)
        cw = (w - MD * (columns - 1)) / columns
        inner = cw - 2 * CARD_PADDING
        lh = max((b.height(lab, inner, b.label_pt, True) if lab else 0 for lab in labels), default=0)
        dh = max((b.height(i.detail, inner, b.body_pt) if i.detail else 0 for i in items), default=0)
        natural = rows * (2 * CARD_PADDING + lh + LABEL_GAP + dh) + MD * (rows - 1)
        y = card_position(top, natural, bottom)
        check_block_bottom(b, y, natural, bottom, base)
        ch = 2 * CARD_PADDING + lh + LABEL_GAP + dh
        for k, (item, label) in enumerate(zip(items, labels)):
            cx = x + (k % columns) * (cw + MD)
            cy = y + (k // columns) * (ch + MD)
            b.card(cx, cy, cw, ch)
            draw_item(b, item, label, f"{base}.{k}", cx + CARD_PADDING,
                      cy + CARD_PADDING, inner, ch - 2 * CARD_PADDING, lh, dh)
        return
    # Linhas: rótulos e descrições compartilham o topo, sem cartões artificiais.
    marker_w = XXL if b.style.marcador == "numero" else MD
    label_w = w * .32
    detail_x = x + marker_w + label_w + MD
    detail_w = w - marker_w - label_w - MD
    heights = [max(b.height(lab, label_w, b.label_pt, True) if lab else 0,
                   b.height(i.detail, detail_w, b.body_pt) if i.detail else 0)
               for i, lab in zip(items, labels)]
    # Expandir espaçamento até 64 px antes de centralizar o bloco restante.
    free = bottom - top - sum(heights)
    gap = min(XXL, max(XS, free / max(1, len(items) - 1)))
    height = sum(heights) + gap * (len(items) - 1)
    y = top + min(XL, max(0, bottom - top - height) * .44)
    for k, (item, label, h) in enumerate(zip(items, labels, heights)):
        b.marker(k, x, y)
        if label:
            b.fitted("rotulo", label, x + marker_w, y, label_w, bottom - y,
                     [b.label_pt], p["text"], bold=True, path=f"{base}.{k}.label")
        if item.detail:
            b.fitted("detalhe", item.detail, detail_x, y, detail_w, bottom - y,
                     [b.body_pt], p["muted"], role="corpo", path=f"{base}.{k}.detail")
        y += h + gap


def check_block_bottom(b, y, height, bottom, path):
    """Bloco de cartões dimensionado pelo conteúdo precisa terminar acima da área do rodapé."""
    if y + height > bottom + 0.5:
        b.diagnostics.append(Diagnostic(code="A010", severity="ERRO", slide=b.number,
            message="Bloco de cartões ultrapassa o limite inferior da área de conteúdo.",
            evidence={"path": path, "bottom": y + height, "limit": bottom}))


def draw_item(b, item, label, path, x, y, w, available, lh, dh):
    gap = LABEL_GAP if label and item.detail else 0
    if lh + dh + gap > available:
        b.diagnostics.append(Diagnostic(code="A010", severity="ERRO", slide=b.number,
            message="Conteúdo excede o cartão na fonte do papel.",
            evidence={"path": path, "needed": lh + dh + gap, "available": available}))
    if label:
        b.text("rotulo", label, x, y, w, lh, b.label_pt, b.palette["text"],
               bold=True, path=path + ".label")
    if item.detail:
        b.text("detalhe", item.detail, x, y + lh + gap, w, dh,
               b.body_pt, b.palette["muted"], role="corpo", path=path + ".detail")


def layout_topicos(b, s, base, deck, top):
    x, w = col(0, 12)
    editorial_items(b, s.items, base + ".items", x, top, w, CONTENT_BOTTOM,
                    (s.title,), cards=b.variant in {"cards", "grid"})


def layout_numeros(b, s, base, deck, top):
    p, n = b.palette, len(s.values)
    x, w = col(0, 12)
    if b.variant == "number_rows":
        natural = sum(max(b.height(v.value, col(0, 4)[1], 64, True),
                          b.height(v.label, col(4, 8)[1], b.label_pt)) for v in s.values)
        y, height = distribute(top, natural + MD * (n - 1), n)
        rh = (height - MD * (n - 1)) / n
        for k, v in enumerate(s.values):
            b.card(x, y, w, rh)
            b.fitted("valor", v.value, x + LG, y + XS, col(0, 4)[1] - LG,
                     rh - SM, [64, 56, 48], p["primary"], bold=True, path=f"{base}.values.{k}.value")
            b.fitted("legenda", v.label, col(4, 8)[0], y + SM, col(4, 8)[1] - LG,
                     rh - LG, [b.label_pt], p["text"], path=f"{base}.values.{k}.label")
            y += rh + MD
        return
    cw = (w - MD * (n - 1)) / n
    inner = cw - 2 * LG
    vs, vh = uniform(b, [(v.value, f"{base}.values.{k}.value") for k, v in enumerate(s.values)],
                     inner, XXL * 3, [88, 80, 72, 64, 56, 48], True)
    ls, lh = uniform(b, [(v.label, f"{base}.values.{k}.label") for k, v in enumerate(s.values)],
                     inner, XXL * 3, [b.label_pt])
    y, height = distribute(top, 2 * LG + vh + MD + lh, max(2, n))
    for k, v in enumerate(s.values):
        cx = x + k * (cw + MD)
        b.card(cx, y, cw, height)
        b.text("valor", v.value, cx + LG, y + LG, inner, vh, vs, p["primary"], bold=True,
               path=f"{base}.values.{k}.value")
        b.fitted("legenda", v.label, cx + LG, y + LG + vh + MD, inner,
                 height - 2 * LG - vh - MD, [ls], p["text"], path=f"{base}.values.{k}.label")


def comparison_columns(b, s, base, deck, top):
    p = b.palette
    _, cw = col(0, 6)
    inner = cw - 2 * SM
    all_items = [item for side in s.sides for item in side.items]
    longest = max((text_width(word, b.label_pt, True, b.family(b.label_pt, True))
                   for item in all_items for word in item.label.split()), default=0)
    # Escolher divisão por altura medida: rótulos longos não roubam espaço
    # desnecessário dos detalhes. A palavra mais larga inclui padding e arredondamento.
    minimum_lw = max(col(0, 2)[1], longest + SM + 2)
    options = [minimum_lw + step * XS for step in range(25)
               if minimum_lw + step * XS < inner - MD - col(0, 2)[1]]
    def total_height(label_width):
        detail_width = inner - label_width - MD
        return sum(max((max(b.height(side.items[j].label, label_width, b.label_pt, True),
                            b.height(side.items[j].detail or "", detail_width, b.body_pt))
                        for side in s.sides if j < len(side.items)), default=0)
                   for j in range(max(len(side.items) for side in s.sides)))
    lw = min(options or [minimum_lw], key=total_height)
    dw = inner - lw - MD
    nh = max(b.height(side.name, inner, b.label_pt, True) for side in s.sides)
    count = max(len(side.items) for side in s.sides)
    heights = [max((max(b.height(side.items[j].label, lw, b.label_pt, True),
                       b.height(side.items[j].detail or "", dw, b.body_pt))
                    for side in s.sides if j < len(side.items)), default=0) for j in range(count)]
    body_top = top + nh + XS
    natural = sum(heights) + XS * (count - 1)
    y, height = distribute(body_top, natural, count)
    gap = max(XS, (height - sum(heights)) / max(1, count - 1))
    for k, side in enumerate(s.sides):
        x, _ = col(k * 6, 6)
        b.rect("cabecalho", x, top, cw, nh + SM, p["soft"], rounded=bool(b.style.raio))
        b.text("lado", side.name, x + SM, top + XS, inner, nh, b.label_pt,
               p["text"], bold=True, align="center", path=f"{base}.sides.{k}.name")
        cy = y
        for j, item in enumerate(side.items):
            path = f"{base}.sides.{k}.items.{j}"
            b.fitted("rotulo", item.label, x + SM, cy, lw, CONTENT_BOTTOM - cy,
                     [b.label_pt], p["text"], bold=True, path=path + ".label")
            if item.detail:
                b.fitted("detalhe", item.detail, x + SM + lw + MD, cy, dw, CONTENT_BOTTOM - cy,
                         [b.body_pt], p["muted"], role="corpo", path=path + ".detail")
            cy += heights[j] + gap


def layout_comparacao(b, s, base, deck, top):
    if b.variant == "comparison_columns":
        return comparison_columns(b, s, base, deck, top)
    if b.variant == "comparison_text":
        # Células largas com frase contínua preservam rótulo e detalhe em pares densos.
        # Só é oferecida como alternativa às duas composições hierárquicas.
        _, cw = col(0, 6)
        inner = cw - 2 * SM
        count = max(len(side.items) for side in s.sides)
        nh = max(b.height(side.name, inner, b.label_pt, True) for side in s.sides)
        texts = [[item.label + (" — " + item.detail if item.detail else "")
                  for item in side.items] for side in s.sides]
        heights = [max((b.height(values[j], inner, b.body_pt) for values in texts
                        if j < len(values)), default=0) for j in range(count)]
        for k, side in enumerate(s.sides):
            x, _ = col(k * 6, 6)
            b.text("lado", side.name, x + SM, top, inner, nh, b.label_pt,
                   b.palette["primary"], bold=True, path=f"{base}.sides.{k}.name")
            y = top + nh + RULE
            for j, text in enumerate(texts[k]):
                b.fitted("par", text, x + SM, y, inner, CONTENT_BOTTOM - y,
                         [b.body_pt], b.palette["text"], role="corpo",
                         path=f"{base}.sides.{k}.items.{j}")
                y += heights[j] + RULE
        return
    p = b.palette
    _, cw = col(0, 6)
    count = max(len(side.items) for side in s.sides)
    inner = cw - 2 * LG
    header_h = max(b.height(side.name, inner, b.label_pt, True) for side in s.sides)
    row_heights = []
    for j in range(count):
        row_heights.append(max((b.height(side.items[j].label, inner, b.label_pt, True) + LABEL_GAP +
                               (b.height(side.items[j].detail, inner, b.body_pt) if side.items[j].detail else 0)
                               for side in s.sides if j < len(side.items)), default=0))
    natural = header_h + LG + sum(row_heights) + MD * (count - 1)
    y, height = distribute(top, natural, count)
    for k, side in enumerate(s.sides):
        x, _ = col(k * 6, 6)
        b.text("lado", side.name, x + LG, y, inner, header_h, b.label_pt,
               p["primary"], bold=True, path=f"{base}.sides.{k}.name")
        cy = y + header_h + LG
        for j, item in enumerate(side.items):
            b.rect("separador", x, cy - XS, cw, RULE, p["line"])
            lh = b.height(item.label, inner, b.label_pt, True)
            dh = b.height(item.detail, inner, b.body_pt) if item.detail else 0
            draw_item(b, item, item.label, f"{base}.sides.{k}.items.{j}", x + LG, cy, inner,
                      CONTENT_BOTTOM - cy, lh, dh)
            cy += row_heights[j] + MD


def layout_etapas(b, s, base, deck, top):
    # Passos usam a grade; numeração permanece mesmo nos estilos com marcador discreto.
    from dataclasses import replace
    original = b.style
    b.style = replace(b.style, marcador="numero")
    x, w = col(0, 12)
    editorial_items(b, s.items, base + ".items", x, top, w, CONTENT_BOTTOM, (s.title,))
    b.style = original


def layout_linha(b, s, base, deck, top):
    # Cronologia com muitos marcos usa linhas horizontais, sem estreitar o corpo.
    p = b.palette
    if len(s.milestones) >= 4:
        heights = [max(b.height(m.label, 320, b.label_pt, True),
                       b.height(m.detail or "", 640, b.body_pt), 52) for m in s.milestones]
        if sum(heights) + LABEL_GAP * (len(heights) - 1) > CONTENT_BOTTOM - top:
            # Cronologia densa: data + frase contínua, preservando os dois campos.
            # A largura das onze colunas evita reduzir o corpo abaixo de 18 pt efetivos.
            x, w = col(1, 11)
            texts = [m.label + (" — " + m.detail if m.detail else "") for m in s.milestones]
            heights = [max(b.height(text, w, b.body_pt),
                           b.height(m.date, col(0)[1] + XS, b.label_pt, True))
                       for m, text in zip(s.milestones, texts)]
            gap = min(MD, max(XS, (CONTENT_BOTTOM - top - sum(heights)) / (len(heights) - 1)))
            y = top
            for k, (m, text, h) in enumerate(zip(s.milestones, texts, heights)):
                path = f"{base}.milestones.{k}"
                b.fitted("data", m.date, M, y, col(0)[1] + XS, CONTENT_BOTTOM - y,
                         [b.label_pt], p["primary"], bold=True, path=path + ".date")
                b.fitted("marco", text, x, y, w, CONTENT_BOTTOM - y,
                         [b.body_pt], p["text"], role="corpo", path=path)
                y += h + gap
            return
        y = top + max(0, (CONTENT_BOTTOM - top - sum(heights) - 12 * (len(heights) - 1)) / 2)
        for k, (m, h) in enumerate(zip(s.milestones, heights)):
            path = f"{base}.milestones.{k}"
            b.fitted("data", m.date, M, y, 140, h, [b.label_pt], p["primary"], bold=True, path=path + ".date")
            b.fitted("rotulo", m.label, 224, y, 320, h, [b.label_pt], p["text"], bold=True, path=path + ".label")
            if m.detail:
                b.fitted("detalhe", m.detail, 568, y, 648, h, [b.body_pt], p["muted"], path=path + ".detail")
            y += h + 12
        if y - 12 > CONTENT_BOTTOM:
            b.fit("\n".join(m.label for m in s.milestones), 320, CONTENT_BOTTOM - top,
                  [b.label_pt], path=base + ".milestones")
        return
    slot_width = (W - 2 * M) / len(s.milestones)
    for k, m in enumerate(s.milestones):
        x = M + k * slot_width
        path = f"{base}.milestones.{k}"
        h = b.fitted("data", m.date, x, top, slot_width - 24, 80, [b.label_pt], p["primary"], bold=True, path=path + ".date")
        b.rect("eixo", x, top + h + 12, slot_width - 24, 4, p["line"])
        lh = b.fitted("rotulo", m.label, x, top + h + 40, slot_width - 24, 120, [b.label_pt], p["text"], bold=True, path=path + ".label")
        if m.detail:
            y = top + h + 44 + lh
            b.fitted("detalhe", m.detail, x, y, slot_width - 24, CONTENT_BOTTOM - y,
                     [b.body_pt], p["muted"], path=path + ".detail")


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
        b.height("“", 120, 96, True),
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
        uh = b.height(s.unit, 900, 16)
        b.text("unidade", s.unit, M, top - 8, 900, uh, 16, p["muted"], path=f"{base}.unit")
        top += uh - 8
    slot = (W - 2 * M) / n
    ls, label_h = uniform(
        b,
        [(x.label, f"{base}.bars.{k}.label") for k, x in enumerate(s.bars)],
        slot - 8,
        64,
        [24, 22, 20],
    )
    value_h = b.height("0", 100, 20, True)
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
    if not s.image_file:
        b.diagnostics.append(Diagnostic(code="A011", severity="AVISO",
            message="Imagem não resolvida; composição textual.", slide=b.number,
            evidence={"path": f"{base}.image_query", "query": s.image_query}))
        if s.items:
            return editorial_items(b, s.items, base + ".items", M, top,
                                   W - 2 * M, CONTENT_BOTTOM, (s.title,), cards=True)
        # A photo is optional: use the caption as a large typographic statement.
        message = s.caption or s.title or ""
        b.fitted("destaque", message, M + LG, top + LG, W - 2 * M - 2 * LG,
                 CONTENT_BOTTOM - top - 2 * LG, [48, 42, 36], b.palette["primary"],
                 path=base + ".caption")
        return None
    if b.variant == "photo_text":
        photo(b, s, base, top)  # registra A031; não amplia miniatura
        return layout_topicos(b, s, base, deck, top)
    photo(b, s, base, top)
    x, w = col(0, 6 if b.variant == "photo50" else 7)
    # Na coluna estreita, empilhar texto em vez de dividir a largura novamente.
    heights = [(b.height(i.label, w - LG, b.label_pt, True),
                b.height(i.detail, w - LG, b.body_pt) if i.detail else 0) for i in s.items]
    natural = sum(lh + dh + LABEL_GAP for lh, dh in heights) + MD * max(0, len(heights) - 1)
    y, height = distribute(top, natural, len(heights))
    gap = max(XS, (height - sum(lh + dh + LABEL_GAP for lh, dh in heights)) / max(1, len(heights) - 1))
    for k, (item, (lh, dh)) in enumerate(zip(s.items, heights)):
        draw_item(b, item, item.label, f"{base}.items.{k}", x, y, w - LG,
                  CONTENT_BOTTOM - y, lh, dh)
        y += lh + dh + LABEL_GAP + gap


def photo(b, s, base, top=None):
    """Meia página e crédito compartilhados entre capa e slide de imagem."""
    from PIL import Image
    from .paths import project_root
    try:
        with Image.open((b.root or project_root()) / s.image_file) as image:
            if max(image.size) < 1000:
                b.diagnostics.append(Diagnostic(code="A031", severity="AVISO", slide=b.number,
                    message="Imagem local com lado maior abaixo de 1000 px.",
                    evidence={"path": base + ".image_file", "file": s.image_file,
                              "width": image.width, "height": image.height, "minimum": 1000}))
            if max(image.size) < 600:
                return False
    except OSError:
        pass  # semântica reporta asset ausente/inválido
    x, w = 664, 616
    b.image("imagem", s.image_file, x, 0, w, 600)
    credit = None
    try:
        from .media import resolve_asset
        asset = resolve_asset(s.image_file)
        # O campo do Commons pode trazer várias linhas e o texto da licença: só a 1ª linha útil.
        lines = [" ".join(line.split()) for line in str(asset.get('author') or '').splitlines()]
        author = next((line for line in lines if line), '') or 'Wikimedia Commons'
        if len(author) > 54:
            author = author[:51].rsplit(' ', 1)[0] + '…'
        credit = f"{author} · {asset.get('license') or 'ver notas'}"
        b.notes("Imagem: " + str(asset.get('attribution', '')) + "\n" +
                str(asset.get('page', '')) + "\n" + str(asset.get('license_url', '')))
    except ValueError:
        credit = "Imagem local · direitos não informados"
    # Crédito completo preservado nas notas; linha visível ajustada em palavras.
    b.fitted("credito", credit, x + SM, 604, w - LG, XL, [12], b.palette["muted"],
             path=base + ".image_file")
    return True


def layout_conclusao(b, s, base, deck, top):
    """Fechamento próprio: ações numeradas; nunca reutiliza a variante de tópicos."""
    p, items = b.palette, s.items
    x, w = col(0, 12)
    if b.variant == "actions_columns":
        cw = (w - MD * (len(items) - 1)) / max(1, len(items))
        inner = cw - 2 * LG
        lh = max((b.height(i.label, inner, b.label_pt, True) for i in items), default=0)
        dh = max((b.height(i.detail, inner, b.body_pt) if i.detail else 0 for i in items), default=0)
        number_size = 32
        nh = b.height("00", inner, number_size, True)
        h = 2 * LG + nh + LABEL_GAP + lh + LABEL_GAP + dh
        y = card_position(top, h)
        check_block_bottom(b, y, h, CONTENT_BOTTOM, base + ".items")
        for k, item in enumerate(items):
            cx = x + k * (cw + MD)
            b.card(cx, y, cw, h, accent=True)
            b.text("acao", f"{k + 1:02d}", cx + LG, y + LG, inner, nh,
                   number_size, p["primary"], bold=True)
            draw_item(b, item, item.label, f"{base}.items.{k}", cx + LG,
                      y + LG + nh + LABEL_GAP, inner, h - 2 * LG - nh - LABEL_GAP, lh, dh)
    else:
        from dataclasses import replace
        original = b.style
        b.style = replace(b.style, marcador="numero")
        editorial_items(b, items, base + ".items", x, top + LG, w, CONTENT_BOTTOM, (s.title,))
        b.style = original


def full_notes(s: AltoSlide, facts: dict) -> str | None:
    parts = [s.notes] if s.notes else []
    refs = []
    for ref in s.sources:
        fact = facts.get(ref)
        if fact:
            refs.append(f"[{ref}] {fact.get('claim', '')} — {fact.get('source_title', '')} — "
                        f"{fact.get('url', '')}")
        else:
            refs.append(ref)
    if refs:
        parts.append("Fontes:\n" + "\n".join(refs))
    return "\n\n".join(parts) or None


def variants_for(s, root=None):
    if s.kind == "topicos":
        return ["cards", "rows", "grid"] if len(s.items) == 4 else ["cards", "rows"]
    if s.kind == "conclusao":
        return ["actions_columns", "actions_rows"]
    if s.kind == "numeros":
        return ["number_columns", "number_rows"]
    if s.kind == "comparacao":
        return ["comparison_columns", "comparison_pairs", "comparison_text"]
    if s.kind == "imagem" and s.image_file:
        from PIL import Image
        from .paths import project_root
        try:
            with Image.open((root or project_root()) / s.image_file) as image:
                usable = max(image.size) >= 600
        except OSError:
            usable = True
        # Uma única variante geométrica por resolução, independente de estilo/nota.
        return ["photo50"] if usable else ["photo_text"]
    if s.kind == "imagem":
        return ["cards"]
    return [s.kind]


def alto_to_ast(
    deck: AltoDeck, facts: dict | None = None, root: Path | None = None
) -> tuple[PresentationNode, dict[str, str], list[Diagnostic]]:
    from .semantic import analyze
    from .design_rules import check_design
    from .diagnostics import DSLException

    facts = facts or {}
    style = STYLES[deck.theme]
    palette, feature_palette, base_theme = style.comum, style.destaque, style.tema
    slides, mapping, diagnostics = [], {}, []
    previous, previous_visual = None, None
    history = []
    total = len(deck.slides)
    for n, s in enumerate(deck.slides, 1):
        dense = ((s.kind == "comparacao")
                 or (s.kind == "linha_do_tempo" and len(s.milestones) >= 4) or len(s.items) >= 4)
        slide_palette = feature_palette if s.kind in FEATURE_KINDS else palette
        candidates = []
        for variant, compact_profile in [(v, compact) for v in variants_for(s, root)
                                         for compact in ([True] if dense else [False, True])]:
            b = Builder(n, slide_palette,
                        label_pt=optical_size(20 if compact_profile else OPTICAL_LABEL_PT,
                                              style.fonte_corpo, MIN_LABEL_PT),
                        body_pt=optical_size(18 if compact_profile else BODY_PT, style.fonte_corpo,
                                             MIN_BODY_PT, effective_minimum=18),
                        style=style, variant=variant, root=root)
            if slide_palette["bg"].upper() != RENDER_BG[base_theme].upper():
                b.rect("fundo", 0, 0, W, H, slide_palette["bg"], role="background")
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
                    "topicos": layout_topicos, "numeros": layout_numeros,
                    "comparacao": layout_comparacao, "etapas": layout_etapas,
                    "linha_do_tempo": layout_linha, "grafico": layout_grafico,
                    "conclusao": layout_conclusao,
                }.get(s.kind, lambda *a: layout_imagem(*a, root))(b, s, base, deck, top)
                footer(b, s, facts, total)
            b.notes(full_notes(s, facts))
            visual = ("cards" if variant in {"cards", "grid", "number_columns"} else
                      "rows" if variant in {"rows", "number_rows", "etapas", "actions_rows"} else variant)
            try:
                probe = analyze(PresentationNode(title=deck.title, theme=base_theme,
                    slides=[SlideNode(number=1, commands=b.commands)]), root)
                probe.slides[0].number = n
                ds = check_design(probe)
                metrics = score_slide(probe.slides[0], variant, previous, visual, previous_visual, history)
                metrics = content_preference(metrics, s.kind, s.items)
            except DSLException as exc:
                ds = exc.diagnostics
                metrics = dict(variant=variant, visual=visual, occupancy=0., scores={}, score=0.)
            blocked = [d for d in b.diagnostics + ds if d.severity != "INFORMAÇÃO" and
                       (d.code in BLOCKERS or d.severity == "ERRO")]
            candidates.append(dict(**metrics, valid=not blocked, builder=b,
                                   blockers=[d.model_dump() for d in blocked]))
        # Para cada composição conservar o maior perfil válido. O compacto é
        # fallback local: nunca reduz vizinhos nem fica abaixo de 18 pt efetivos.
        candidates = [next((c for c in candidates if c["variant"] == variant and c["valid"]),
                           next(c for c in candidates if c["variant"] == variant))
                      for variant in variants_for(s, root)]
        if any(c["valid"] and c["variant"] in {"comparison_columns", "comparison_pairs"}
               for c in candidates):
            candidates = [c for c in candidates if c["variant"] != "comparison_text"]
        # Conteúdo curto tem preferência explícita por cartões naturais. A nota
        # geométrica não deve recompensar uma lista só por ela espalhar o texto.
        short_cards = (s.kind == "topicos" and 2 <= len(s.items) <= 3 and
                       all(len(i.label) <= 36 and len(i.detail or "") <= 110 for i in s.items))
        preferred = "actions_columns" if s.kind == "conclusao" else "cards" if short_cards else None
        pool = [c for c in candidates if c["variant"] == preferred and c["valid"]
                and c["variant"] != previous]
        chosen = choose(pool or candidates, previous)
        b = chosen["builder"]
        # Nenhuma candidata válida: preservar o conteúdo/IR e emitir erro explícito.
        if not chosen["valid"] and not any(d.severity == "ERRO" for d in b.diagnostics):
            b.diagnostics.append(Diagnostic(code="A010", severity="ERRO", slide=n,
                message="Nenhuma variante comporta o conteúdo nas restrições de design.",
                evidence={"path": f"slides.{n - 1}", "blockers": chosen["blockers"]}))
        b.diagnostics.append(Diagnostic(code="A030", severity="INFORMAÇÃO", slide=n,
            message="Variante escolhida por heurística geométrica determinística.",
            evidence={**{k: chosen[k] for k in ("variant", "visual", "score", "scores", "occupancy", "valid")},
                      "diversity_bonus": chosen.get("diversity_bonus", 0.),
                      "content_bonus": chosen.get("content_bonus", 0.),
                      "label_pt": b.label_pt, "body_pt": b.body_pt,
                      "selection_policy": "content" if pool else "geometry",
                      "recent_variants": history[-3:],
                      "candidates": [{k: c[k] for k in ("variant", "visual", "score", "scores", "occupancy", "valid", "blockers")}
                                     for c in candidates]}))
        slides.append(SlideNode(number=n, commands=b.commands))
        mapping.update({f"{n}:{k}": v for k, v in b.mapping.items()})
        diagnostics += b.diagnostics
        previous, previous_visual = chosen["variant"], chosen["visual"]
        history.append(previous)
    return PresentationNode(title=deck.title, theme=base_theme, slides=slides), mapping, diagnostics


def alto_to_dsl(deck: AltoDeck, facts: dict | None = None, root: Path | None = None):
    """Retorna (fonte SlideDSL 1.1, mapa elemento→campo alto, diagnósticos de layout)."""
    ast, mapping, diagnostics = alto_to_ast(deck, facts, root)
    return print_ast(ast), mapping, diagnostics
