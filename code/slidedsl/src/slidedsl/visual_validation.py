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
        images = [e for e in s.elements if e.type == "image"]
        for image in images:
            from .paths import asset_path, project_root
            from PIL import Image

            try:
                with Image.open(asset_path(image.file, project_root())) as source:
                    if image.width > source.width * 1.5 or image.height > source.height * 1.5:
                        ds.append(
                            {
                                "code": "V006",
                                "severity": "AVISO",
                                "slide": s.number,
                                "element": image.id,
                                "message": "Imagem ampliada acima de 150% da resolução original",
                                "evidence": {
                                    "source_pixels": list(source.size),
                                    "display_box": [image.width, image.height],
                                    "path": (mapping or {}).get(image.id),
                                },
                                "suggestion": "Escolha uma versão com mais pixels ou reduza a caixa.",
                            }
                        )
            except (ValueError, OSError):
                pass  # The semantic asset validator reports unreadable or missing files.
            for text in texts:
                if intersection(box(image), box(text)):
                    ds.append(
                        {
                            "code": "V004",
                            "severity": "ERRO",
                            "slide": s.number,
                            "element": text.id,
                            "message": "Imagem sobrepõe caixa de título/corpo",
                            "evidence": {
                                "image": image.id,
                                "path": (mapping or {}).get(text.id),
                                "approximation": "AABB",
                            },
                            "suggestion": "Reposicione a imagem ou escolha outro layout.",
                        }
                    )
    titles = [e for s in deck.slides for e in s.elements if e.role == "titulo"]
    if len({(e.font_size, e.font_face, e.color) for e in titles}) > 1:
        ds.append(
            {
                "code": "V005",
                "severity": "AVISO",
                "slide": None,
                "element": None,
                "message": "Tipografia/cor de títulos varia entre slides",
                "evidence": {"elements": [e.id for e in titles]},
                "suggestion": "Revise se a variação é intencional.",
            }
        )
    return ds
