"""Ordered, deterministic theme selection. No inference or network."""

from .research import normalize


def choose_theme(request, outline=None):
    text = normalize(request + " " + str(outline or ""))
    # Audience precedes topic; academic intent precedes technology in a TCC.
    rules = [
        ("vibrante", ("infantil", "crianca", "escolar", "ensino", "7o ano", "7º ano")),
        ("claro", ("academico", "tcc", "pesquisa", "banca", "dissertacao")),
        ("escuro", ("tecnologia", "programacao", "software", "git", "computacao")),
        ("natural", ("natureza", "ambiente", "alimentacao", "horta", "planta", "reciclagem")),
        ("editorial", ("historia", "humanidades", "leitura", "literatura")),
    ]
    import re

    return next((theme for theme, words in rules if any(
        re.search(r"\b" + re.escape(word) + r"\b", text) for word in words)), "claro")
