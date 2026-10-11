"""Additional AABB checks; never an aesthetic-quality certificate."""

from itertools import combinations

from .geometry import box, distance, intersection


def check_visual(deck, mapping=None):
    ds = []
    for s in deck.slides:
        texts = [e for e in s.elements if e.type == "text" and e.role in {"corpo", "titulo"}]
        for a, b in combinations(texts, 2):
            code = (
                "V001"
                if intersection(box(a), box(b))
                else "V002"
                if distance(box(a), box(b)) < 8
                else None
            )
            if code:
                ds.append(
                    {
                        "code": code,
                        "severity": "ERRO",
                        "slide": s.number,
                        "element": b.id,
                        "message": "Caixas de texto sobrepostas"
                        if code == "V001"
                        else "Espaçamento textual menor que 8 px",
                        "evidence": {
                            "elements": [a.id, b.id],
                            "path": (mapping or {}).get(b.id),
                            "approximation": "AABB",
                        },
                    }
                )
        for e in texts:
            if (e.font_size or 0) < 18 and not e.id.endswith("_rodape"):
                ds.append(
                    {
                        "code": "V003",
                        "severity": "AVISO",
                        "slide": s.number,
                        "element": e.id,
                        "message": "Fonte de título/corpo abaixo de 18 pt",
                        "evidence": {"font_size": e.font_size, "path": (mapping or {}).get(e.id)},
                    }
                )
    return ds
