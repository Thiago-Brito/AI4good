"""SlideDSL Alto: GLC de alto nível, AST tipada, validação (A0xx) e impressão canônica.

A linguagem alto nível descreve a intenção de cada slide (tópicos, números, comparação,
linha do tempo...). `alto_layout` traduz a AST para a SlideDSL 1.1 de baixo nível, que
continua passando pelo parser, semântica e regras de design originais.
"""

from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Literal

from lark import Lark, Token, Tree, UnexpectedInput
from pydantic import BaseModel, ConfigDict, Field

from .diagnostics import Diagnostic, DSLException

SlideKind = Literal[
    "capa",
    "secao",
    "topicos",
    "numeros",
    "comparacao",
    "etapas",
    "linha_do_tempo",
    "citacao",
    "grafico",
    "imagem",
    "conclusao",
]
SLIDE_KINDS: tuple[str, ...] = SlideKind.__args__

# Limites por tipo: (mínimo, máximo) de itens/valores/marcos/barras.
LIMITS = {
    "topicos": ("items", 2, 5),
    "etapas": ("items", 2, 5),
    "conclusao": ("items", 2, 4),
    "numeros": ("values", 1, 3),
    "linha_do_tempo": ("milestones", 2, 6),
    "grafico": ("bars", 2, 7),
    "imagem": ("items", 0, 3),
}
TEXT_LIMITS = {
    "title": 80,
    "subtitle": 140,
    "author": 80,
    "text": 260,
    "caption": 140,
    "unit": 40,
    "notes": 1500,
    "label": 48,
    "detail": 170,
    "value": 14,
    "date": 16,
    "side": 40,
}

DESCRIPTIONS = {
    "capa": "abertura: título do deck, subtítulo com a promessa da apresentação",
    "secao": "divisória entre partes; título curto e subtítulo opcional",
    "topicos": "2–5 ideias paralelas, cada uma com rótulo e explicação concreta",
    "numeros": "1–3 números grandes que sustentam a mensagem (dados reais, com fonte)",
    "comparacao": "duas alternativas lado a lado, 2–4 itens em cada lado",
    "etapas": "processo em 2–5 passos ordenados",
    "linha_do_tempo": "2–6 marcos com data, rótulo e detalhe",
    "citacao": "frase literal de uma pessoa ou documento, com autor",
    "grafico": "gráfico de barras com 2–7 categorias numéricas (dados reais, com fonte)",
    "imagem": "imagem explicativa com legenda e até 3 itens",
    "conclusao": "2–4 conclusões ou próximos passos acionáveis",
}


class AltoModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Item(AltoModel):
    label: str
    detail: str | None = None


class Value(AltoModel):
    value: str
    label: str


class Side(AltoModel):
    name: str
    items: list[Item]


class Milestone(AltoModel):
    date: str
    label: str
    detail: str | None = None


class Bar(AltoModel):
    label: str
    value: float


class AltoSlide(AltoModel):
    kind: SlideKind
    title: str | None = None
    subtitle: str | None = None
    author: str | None = None
    text: str | None = None
    caption: str | None = None
    unit: str | None = None
    image_file: str | None = None
    image_query: str | None = None
    items: list[Item] = Field(default_factory=list)
    values: list[Value] = Field(default_factory=list)
    sides: list[Side] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    bars: list[Bar] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    notes: str | None = None
    line: int | None = None
    column: int | None = None


class AltoDeck(AltoModel):
    title: str
    theme: Literal["claro", "escuro"] = "claro"
    slides: list[AltoSlide]


@lru_cache
def grammar_text() -> str:
    return Path(__file__).with_name("grammar").joinpath("slidedsl_alto.lark").read_text("utf-8")


@lru_cache
def alto_parser() -> Lark:
    return Lark(grammar_text(), parser="lalr", propagate_positions=True, maybe_placeholders=False)


def _s(token) -> str:
    return json.loads(str(token))


def _field(tree: Tree, name: str):
    for child in tree.children:
        if isinstance(child, Tree) and child.data == name:
            return child
    return None


def _items(trees) -> list[Item]:
    return [
        Item(label=_s(t.children[0]), detail=_s(t.children[1]) if len(t.children) > 1 else None)
        for t in trees
    ]


def _slide(tree: Tree) -> AltoSlide:
    kind = str(tree.data)
    data = {"kind": kind, "line": tree.meta.line, "column": tree.meta.column}
    simple = {
        "titulo": "title",
        "subtitulo": "subtitle",
        "autor": "author",
        "texto": "text",
        "legenda": "caption",
        "unidade": "unit",
        "notas": "notes",
        "arquivo": "image_file",
        "buscar": "image_query",
    }
    children = [c for c in tree.children if isinstance(c, Tree)]
    for child in children:
        name = str(child.data)
        if name in simple:
            data[simple[name]] = _s(child.children[0])
        elif name == "fontes":
            data["sources"] = [
                str(c) if c.type == "FATO" else _s(c)
                for c in child.children
                if isinstance(c, Token)
            ]
    data["items"] = _items([c for c in children if c.data == "item"])
    data["values"] = [
        Value(value=_s(c.children[0]), label=_s(c.children[1]))
        for c in children
        if c.data == "valor"
    ]
    data["sides"] = [
        Side(
            name=_s(c.children[0]),
            items=_items([i for i in c.children[1:] if isinstance(i, Tree)]),
        )
        for c in children
        if c.data == "lado"
    ]
    data["milestones"] = [
        Milestone(
            date=_s(c.children[0]),
            label=_s(c.children[1]),
            detail=_s(c.children[2]) if len(c.children) > 2 else None,
        )
        for c in children
        if c.data == "marco"
    ]
    data["bars"] = [
        Bar(label=_s(c.children[0]), value=float(c.children[1]))
        for c in children
        if c.data == "barra"
    ]
    return AltoSlide(**data)


def parse_alto(source: str) -> AltoDeck:
    try:
        root = alto_parser().parse(source).children[0]
    except UnexpectedInput as exc:
        raise DSLException(
            [
                Diagnostic(
                    code="P001",
                    severity="ERRO",
                    message="Sintaxe inválida na SlideDSL Alto.",
                    line=exc.line,
                    column=exc.column,
                    evidence={
                        "context": exc.get_context(source),
                        "expected": sorted(getattr(exc, "expected", [])),
                    },
                    suggestion="Use apenas os blocos e campos da gramática alto nível.",
                )
            ]
        ) from exc
    title, *rest = root.children
    theme = "claro"
    if rest and isinstance(rest[0], Tree) and rest[0].data == "tema":
        theme = str(rest.pop(0).children[0])
    return AltoDeck(title=_s(title), theme=theme, slides=[_slide(t) for t in rest])


# ---------------------------------------------------------------------------
# Impressão canônica (AST → texto). Permite converter JSON restrito em GLC.


def q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _num(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def print_slide(s: AltoSlide, indent: str = "  ") -> str:
    inner = indent + "  "
    lines = [f"{indent}{s.kind} {{"]

    def add(text):
        lines.append(inner + text)

    def items(values, prefix=inner):
        for i in values:
            lines.append(prefix + f"item {q(i.label)}" + (f" {q(i.detail)}" if i.detail else ""))

    if s.kind == "citacao":
        add(f"texto {q(s.text or '')}")
        add(f"autor {q(s.author or '')}")
    else:
        add(f"titulo {q(s.title or '')}")
    if s.kind in ("capa", "secao") and s.subtitle:
        add(f"subtitulo {q(s.subtitle)}")
    if s.kind == "capa" and s.author:
        add(f"autor {q(s.author)}")
    if s.kind == "grafico" and s.unit:
        add(f"unidade {q(s.unit)}")
    if s.kind == "imagem":
        if s.image_file:
            add(f"arquivo {q(s.image_file)}")
        else:
            add(f"buscar {q(s.image_query or s.title or '')}")
        if s.caption:
            add(f"legenda {q(s.caption)}")
    if s.kind in ("topicos", "etapas", "conclusao", "imagem"):
        items(s.items)
    for v in s.values:
        add(f"valor {q(v.value)} {q(v.label)}")
    for side in s.sides:
        add(f"lado {q(side.name)} {{")
        items(side.items, inner + "  ")
        add("}")
    for m in s.milestones:
        add(f"marco {q(m.date)} {q(m.label)}" + (f" {q(m.detail)}" if m.detail else ""))
    for b in s.bars:
        add(f"barra {q(b.label)} {_num(b.value)}")
    if s.sources and s.kind not in ("capa", "secao"):
        refs = [r if re.fullmatch(r"F[0-9]+", r) else q(r) for r in s.sources]
        add("fontes " + ", ".join(refs))
    if s.notes:
        add(f"notas {q(s.notes)}")
    lines.append(f"{indent}}}")
    return "\n".join(lines)


def print_alto(deck: AltoDeck) -> str:
    body = "\n".join(print_slide(s) for s in deck.slides)
    return f"deck {q(deck.title)} {{\n  tema {deck.theme}\n{body}\n}}\n"


# ---------------------------------------------------------------------------
# Validação semântica alto nível (A0xx). Erros impedem a compilação;
# avisos orientam o reparo e a escolha entre candidatos.

GENERIC = re.compile(
    r"^(facilita|permite|melhora|ajuda|garante|aumenta|reduz|otimiza)\b", re.IGNORECASE
)


def _digits(value: str) -> str:
    return re.sub(r"[^0-9]", "", value)


def number_tokens(text: str | None) -> set[str]:
    """Números normalizados de um texto: "1.300"/"1,300" → "1300", "6,5" → "6.5",
    "20 mil" → {"20", "20000"}. Compara o número inteiro, não dígitos soltos."""
    found = set()
    text = re.sub(r"\bF\d+\b", " ", text or "")  # IDs de fatos não são números
    for match in re.finditer(r"\d+(?:[.,]\d+)*(\s*mil\b)?", text, re.IGNORECASE):
        raw = match.group(0)
        thousand = bool(match.group(1))
        raw = re.sub(r"\s*mil$", "", raw, flags=re.IGNORECASE)
        if re.fullmatch(r"\d{1,3}([.,]\d{3})+", raw):
            value = re.sub(r"[.,]", "", raw)
        else:
            value = raw.replace(",", ".")
        value = value.rstrip(".")
        if "." in value:
            value = value.rstrip("0").rstrip(".")
        found.add(value)
        if thousand:
            try:
                found.add(str(int(float(value) * 1000)))
            except ValueError:
                pass
    return found


def _norm(value: str | None) -> str:
    return re.sub(r"[\W_]+", " ", (value or "").casefold()).strip()


def validate_alto(deck: AltoDeck, facts: dict[str, dict] | None = None) -> list[Diagnostic]:
    """`facts` mapeia ID → ficha ({claim, quote, ...}); quando presente, confere fontes."""
    ds: list[Diagnostic] = []

    def emit(code, sev, msg, n, s, path, suggestion):
        ds.append(
            Diagnostic(
                code=code,
                severity=sev,
                message=msg,
                slide=n,
                line=s.line,
                column=s.column,
                evidence={"path": path},
                suggestion=suggestion,
            )
        )

    if not deck.slides:
        ds.append(Diagnostic(code="A001", severity="ERRO", message="Deck sem slides."))
    for n, s in enumerate(deck.slides, 1):
        base = f"slides.{n - 1}"
        required = {"citacao": ("text", "author")}.get(s.kind, ("title",))
        for name in required:
            if not (getattr(s, name) or "").strip():
                emit(
                    "A002",
                    "ERRO",
                    f"Campo obrigatório vazio: {name}.",
                    n,
                    s,
                    f"{base}.{name}",
                    "Preencha o campo com conteúdo específico do assunto.",
                )
        if s.kind in LIMITS:
            attr, low, high = LIMITS[s.kind]
            count = len(getattr(s, attr))
            if not low <= count <= high:
                emit(
                    "A003",
                    "ERRO",
                    f"{s.kind} exige de {low} a {high} {attr}; recebeu {count}.",
                    n,
                    s,
                    f"{base}.{attr}",
                    f"Use entre {low} e {high} elementos.",
                )
        if s.kind == "comparacao":
            if len(s.sides) != 2:
                emit(
                    "A003",
                    "ERRO",
                    "comparacao exige exatamente dois lados.",
                    n,
                    s,
                    f"{base}.sides",
                    "Declare dois blocos lado.",
                )
            for k, side in enumerate(s.sides):
                if not 2 <= len(side.items) <= 4:
                    emit(
                        "A003",
                        "ERRO",
                        "Cada lado da comparação exige 2–4 itens.",
                        n,
                        s,
                        f"{base}.sides.{k}.items",
                        "Use de 2 a 4 itens por lado.",
                    )
        if s.kind == "imagem" and not (s.image_file or s.image_query):
            emit(
                "A002",
                "ERRO",
                "imagem exige arquivo ou buscar.",
                n,
                s,
                f"{base}.image",
                "Informe um arquivo local ou uma consulta de busca.",
            )
        if s.kind == "grafico" and any(b.value < 0 for b in s.bars):
            emit(
                "A004",
                "ERRO",
                "Barras exigem valores não negativos.",
                n,
                s,
                f"{base}.bars",
                "Use valores maiores ou iguais a zero.",
            )
        # Comprimento de textos.
        checks = [
            (f"{base}.{k}", getattr(s, k), TEXT_LIMITS[k])
            for k in ("title", "subtitle", "author", "text", "caption", "unit", "notes")
        ]
        for k, i in enumerate(s.items):
            checks += [
                (f"{base}.items.{k}.label", i.label, TEXT_LIMITS["label"]),
                (f"{base}.items.{k}.detail", i.detail, TEXT_LIMITS["detail"]),
            ]
        for k, v in enumerate(s.values):
            checks += [
                (f"{base}.values.{k}.value", v.value, TEXT_LIMITS["value"]),
                (f"{base}.values.{k}.label", v.label, TEXT_LIMITS["detail"]),
            ]
        for k, side in enumerate(s.sides):
            checks.append((f"{base}.sides.{k}.name", side.name, TEXT_LIMITS["side"]))
            for j, i in enumerate(side.items):
                checks += [
                    (f"{base}.sides.{k}.items.{j}.label", i.label, TEXT_LIMITS["label"]),
                    (f"{base}.sides.{k}.items.{j}.detail", i.detail, 80),
                ]
        for k, m in enumerate(s.milestones):
            checks += [
                (f"{base}.milestones.{k}.date", m.date, TEXT_LIMITS["date"]),
                (f"{base}.milestones.{k}.label", m.label, 36),
                (f"{base}.milestones.{k}.detail", m.detail, 90),
            ]
        for k, b in enumerate(s.bars):
            checks.append((f"{base}.bars.{k}.label", b.label, 24))
        for path, value, limit in checks:
            if value and len(value) > limit:
                emit(
                    "A005",
                    "ERRO",
                    f"Texto com {len(value)} caracteres; limite {limit}.",
                    n,
                    s,
                    path,
                    "Reescreva de forma mais concisa, mantendo o fato principal.",
                )
        # Fontes e ancoragem em fatos.
        if facts is not None:
            for ref in s.sources:
                if re.fullmatch(r"F[0-9]+", ref) and ref not in facts:
                    emit(
                        "A006",
                        "ERRO",
                        f"Fonte {ref} não existe no dossiê de pesquisa.",
                        n,
                        s,
                        f"{base}.sources",
                        "Cite somente IDs de fatos fornecidos.",
                    )
            cited = " ".join(
                (facts[r].get("quote", "") + " " + facts[r].get("claim", ""))
                for r in s.sources
                if r in facts
            )
            numbers = [v.value for v in s.values] + [_num(b.value) for b in s.bars]
            cited_numbers = number_tokens(cited)
            for value in numbers:
                if number_tokens(value) - cited_numbers:
                    emit(
                        "A007",
                        "AVISO",
                        f"Número {value!r} não aparece nos fatos citados; pode ser inventado.",
                        n,
                        s,
                        f"{base}.sources",
                        "Use números presentes nas fichas e cite o fato correspondente.",
                    )
            texts = [(f"{base}.title", s.title), (f"{base}.subtitle", s.subtitle)]
            texts += [(f"{base}.items.{k}.detail", i.detail) for k, i in enumerate(s.items)]
            texts += [(f"{base}.items.{k}.label", i.label) for k, i in enumerate(s.items)]
            texts += [
                (f"{base}.sides.{k}.items.{j}.detail", i.detail)
                for k, side in enumerate(s.sides)
                for j, i in enumerate(side.items)
            ]
            texts += [(f"{base}.milestones.{k}.date", m.date) for k, m in enumerate(s.milestones)]
            texts += [
                (f"{base}.milestones.{k}.detail", m.detail) for k, m in enumerate(s.milestones)
            ]
            texts += [
                (f"{base}.values.{k}.label", v.label) for k, v in enumerate(s.values)
            ]
            texts += [(f"{base}.notes", s.notes)]
            for path, value in texts:
                for number in sorted(number_tokens(value) - cited_numbers):
                    if number:
                        emit(
                            "A012",
                            "AVISO",
                            f"Número {number!r} sem fato citado que o sustente.",
                            n,
                            s,
                            path,
                            "Remova o número ou cite o fato (Fn) em que ele aparece.",
                        )
                        break
            if s.kind == "citacao" and s.text:
                quotes = " ".join(facts[r].get("quote", "") for r in s.sources if r in facts)
                if re.fullmatch(r"\s*F\d+\s*", s.author or "") or not s.sources:
                    emit("A015", "ERRO", "Citação sem autor real (ID de fato não é autor).",
                         n, s, f"{base}.author", "Use o nome da pessoa ou documento citado.")
                elif _norm(s.text) not in _norm(quotes):
                    emit("A015", "ERRO", "Texto da citação não é cópia literal do fato citado.",
                         n, s, f"{base}.text", "Copie a frase exatamente como no trecho.")
            if s.kind in ("numeros", "grafico", "citacao") and not s.sources:
                emit(
                    "A008",
                    "AVISO",
                    f"Slide {s.kind} sem fonte.",
                    n,
                    s,
                    f"{base}.sources",
                    "Cite o fato (F1, F2...) que sustenta os dados.",
                )
        # Conteúdo genérico: rótulo vazio de sentido ou detalhe que só diz 'facilita...'.
        details = [(f"{base}.items.{k}.detail", i.detail) for k, i in enumerate(s.items)]
        details += [
            (f"{base}.sides.{k}.items.{j}.detail", i.detail)
            for k, side in enumerate(s.sides)
            for j, i in enumerate(side.items)
        ]
        for path, detail in details:
            if detail and detail[:1].islower():
                emit(
                    "A009",
                    "AVISO",
                    "Detalhe não é uma frase completa (começa em minúscula, como um cenário solto).",
                    n,
                    s,
                    path,
                    "Escreva uma frase com sujeito e verbo que explique o rótulo.",
                )
        for k, i in enumerate(s.items):
            if i.detail and len(i.detail.split()) < 4:
                emit(
                    "A009",
                    "AVISO",
                    "Detalhe curto demais para explicar o item.",
                    n,
                    s,
                    f"{base}.items.{k}.detail",
                    "Explique com um exemplo, número ou condição.",
                )
            elif i.detail and GENERIC.match(i.detail) and not re.search(r"[0-9]", i.detail):
                emit(
                    "A009",
                    "AVISO",
                    "Detalhe genérico (começa com verbo vago, sem dado).",
                    n,
                    s,
                    f"{base}.items.{k}.detail",
                    "Troque por um fato, exemplo concreto ou número.",
                )
    return ds
