"""Decisões editoriais locais; não reescrevem nem cortam o conteúdo do modelo."""

import re
import unicodedata

from .text_metrics import text_width

TITLE_PT, LABEL_PT, BODY_PT, CREDIT_PT = 42, 24, 20, 12
MIN_TITLE_PT, MIN_LABEL_PT, MIN_BODY_PT, MIN_SUBTITLE_PT = 32, 20, 16, 18


def proper_words(text):
    """Palavras escritas com maiúscula no meio de frase: evidência de nome próprio."""
    found = set()
    for sentence in re.split(r"[.!?:]\s+|\n+", text or ""):
        for w in re.findall(r"[\w-]+", sentence)[1:]:
            if w[:1].isupper():
                found.add(w.casefold())
    return found


def sentence_case(text, keep=()):
    """Converte Title Case em caixa de frase; títulos já em caixa de frase ficam intactos.

    Preserva siglas, grafias mistas (GitHub) e nomes próprios atestados em `keep`."""
    words = (text or "").split()
    capitalized = [w for w in words if len(w) > 3 and w[:1].isupper()]
    long_words = [w for w in words if len(w) > 3]
    if len(long_words) < 2 or len(capitalized) / len(long_words) <= 0.7:
        return text
    keep = {k.casefold() for k in keep}
    return " ".join(w if k == 0 or (w.isupper() and len(w) > 1) or w.strip('.,:;').casefold() in keep
                    or any(c.isupper() for c in w[1:]) else w.lower()
                    for k, w in enumerate(words))


def capitalize_first(text):
    """Inicial maiúscula em texto visível ("avaliar fase atual" → "Avaliar fase atual")."""
    if text and text[0].islower():
        return text[0].upper() + text[1:]
    return text


def capitalize_visible(slide):
    for name in ("title", "subtitle", "caption"):
        setattr(slide, name, capitalize_first(getattr(slide, name)))
    for side in slide.sides:
        side.name = capitalize_first(side.name)
    for item in slide.items + [i for side in slide.sides for i in side.items]:
        item.label, item.detail = capitalize_first(item.label), capitalize_first(item.detail)
    for m in slide.milestones:
        m.label, m.detail = capitalize_first(m.label), capitalize_first(m.detail)
    return slide


def normalized(text):
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKD", text or "")
                             .encode("ascii", "ignore").decode().casefold()))


def distinct_label(label, *headings):
    """Suprime apenas rótulo redundante; sua explicação permanece visível."""
    words = normalized(label)
    meaningful = set(words.split()) - {"a", "o", "as", "os", "de", "da", "do", "das", "dos", "e", "na", "no"}
    return bool(words and all(words != normalized(h) and not (
        len(meaningful) >= 2 and meaningful <= set(normalized(h).split())
    ) for h in headings))


def visible_labels(items, *headings):
    """Rótulos de um grupo são suprimidos juntos, nunca um só (evita linha sem rótulo)."""
    distinct = [distinct_label(i.label, *headings) for i in items]
    return [i.label if any(distinct) else None for i in items]


def ordered_steps(slide):
    # Sinal verificável conservador: cada ação começa por infinitivo.
    return all(re.match(r"^[\wáéíóúâêôãõç]+(?:ar|er|ir)\b", i.label, re.I)
               for i in slide.items)


def balanced_title(text, width, size=TITLE_PT, family="Arial"):
    """Quebra explícita medida, sem linha final com uma palavra ou corte de texto."""
    words = (text or "").split()
    if text_width(" ".join(words), size, True, family) <= width - 24:
        return " ".join(words)
    candidates = []
    for cut in range(2, len(words) - 1):
        lines = [" ".join(words[:cut]), " ".join(words[cut:])]
        widths = [text_width(line, size, True, family) for line in lines]
        if max(widths) <= width - 24:
            candidates.append((abs(widths[0] - widths[1]), "\n".join(lines)))
    return min(candidates)[1] if candidates else text


def composition(slide, deck, index):
    """Escolha por densidade/conteúdo com alternância só onde há escolha equivalente."""
    if slide.kind == "etapas" and not ordered_steps(slide):
        return "rows"
    if slide.kind != "topicos":
        return slide.kind
    if len(slide.items) > 3:
        return "rows"
    previous = deck.slides[index - 1] if index else None
    if previous and previous.kind == "topicos":
        return "rows" if composition(previous, deck, index - 1) == "cards" else "cards"
    if max((len(i.detail or "") for i in slide.items), default=0) > 100:
        return "rows"
    # O tamanho dos itens determina a composição, não um número fixo de slide.
    return "cards" if sum(len(i.label) for i in slide.items) < 65 else "rows"
