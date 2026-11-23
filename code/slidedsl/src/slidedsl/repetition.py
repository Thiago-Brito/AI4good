"""Sobreposição lexical de blocos de conteúdo entre slides, sem inferência."""

import re
import unicodedata

THRESHOLD = 0.72
STOPWORDS = set("a o as os de da do das dos e em no na nos nas um uma para por com que se ao".split())


def tokens(text: str) -> set[str]:
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return set(re.findall(r"[a-z0-9]+", text)) - STOPWORDS


def repetition_pairs(slides: list[list[str]], threshold=THRESHOLD) -> list[dict]:
    """Jaccard >= limiar; ignora blocos com menos de quatro tokens úteis."""
    pairs = []
    for index, blocks in enumerate(slides):
        for previous in range(index):
            for text in blocks:
                current = tokens(text)
                if len(current) < 4:
                    continue
                for old in slides[previous]:
                    before = tokens(old)
                    if len(before) < 4:
                        continue
                    score = len(current & before) / len(current | before)
                    if score >= threshold:
                        pairs.append({
                            "slide": index + 1, "previous_slide": previous + 1,
                            "text": text, "previous_text": old, "jaccard": round(score, 4),
                        })
    return pairs


def alto_blocks(slide) -> list[str]:
    items = slide.items + [i for side in slide.sides for i in side.items]
    return [text for i in items for text in (i.label, i.detail) if text]


def sibling_repetitions(items):
    """Prefixo de quatro palavras ou Jaccard alto entre descrições irmãs."""
    found = []
    for k, item in enumerate(items):
        current = re.findall(r"\w+", (item.detail or "").casefold())
        label = re.findall(r"\w+", item.label.casefold())
        if len(label) >= 2 and current[:len(label)] == label:
            found.append({"item": k, "reason": "descrição repete o rótulo"})
        for j, other in enumerate(items[:k]):
            old = re.findall(r"\w+", (other.detail or "").casefold())
            a, b = tokens(item.detail or ""), tokens(other.detail or "")
            overlap = len(a & b) / len(a | b) if a | b else 0
            if (len(current) >= 4 and current[:4] == old[:4]) or (min(len(a), len(b)) >= 4 and overlap >= THRESHOLD):
                found.append({"item": k, "sibling": j, "reason": "descrições repetem início ou conteúdo"})
    return found
