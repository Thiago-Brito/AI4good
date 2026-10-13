"""Geração de apresentações por SLM sobre a SlideDSL Alto.

Etapas (cada chamada do modelo é pequena, o que favorece modelos de 1–8B):

1. Pesquisa opcional (`research.py`) → dossiê com fatos F1..Fn e trechos literais.
2. Roteiro: uma chamada escolhe, para cada slide, o tipo, a mensagem (tese) e os fatos
   que a sustentam. O schema só oferece IDs de fatos reais e esconde tipos que exigem
   dados (`numeros`, `grafico`, `citacao`) quando não há fatos.
3. Conteúdo: uma chamada por slide, com contrato editorial (mensagem → evidência →
   exemplo → ressalva nas notas). Três modos:
   - `json`: JSON Schema por tipo de slide (Ollama, llama.cpp, OpenAI);
   - `gramatica`: o SLM escreve SlideDSL Alto restrito pela GLC convertida em GBNF
     (llama.cpp) — a saída é sintaticamente válida por construção;
   - `direto`: SlideDSL Alto livre, validada pelo parser e reparada com diagnósticos.
4. Validação A0xx + verificação de layout (A010) e reparo localizado (até N vezes).
5. Best-of-N: gera N candidatos por slide e escolhe pela pontuação de qualidade.
6. Compilação: SlideDSL Alto → SlideDSL 1.1 → regras de design → PPTX editável.
"""

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Callable

from .alto import (
    DESCRIPTIONS,
    LIMITS,
    SLIDE_KINDS,
    AltoDeck,
    AltoSlide,
    Bar,
    Item,
    Milestone,
    Side,
    Value,
    parse_alto,
    print_alto,
    print_slide,
    validate_alto,
)
from .alto_layout import alto_to_ast
from .diagnostics import Diagnostic, DSLException

DATA_KINDS = {"numeros", "grafico", "citacao", "linha_do_tempo"}
PATH_WORDS = {
    "items": "itens",
    "label": "rotulo",
    "detail": "detalhe",
    "values": "valores",
    "value": "valor",
    "sides": "lados",
    "name": "nome",
    "milestones": "marcos",
    "date": "data",
    "bars": "barras",
    "title": "titulo",
    "subtitle": "subtitulo",
    "text": "texto",
    "author": "autor",
    "caption": "legenda",
    "unit": "unidade",
    "sources": "fontes",
    "notes": "notas",
    "image_query": "busca_imagem",
    "image": "busca_imagem",
}
# Caminhos de truncamento já vêm com as chaves do JSON em português.
PATH_WORDS.update({v: v for v in list(PATH_WORDS.values())})

# ---------------------------------------------------------------------------
# Prompts

OUTLINE_SYSTEM = """Você é um roteirista de apresentações. Planeje o deck slide a slide.
Para cada slide escolha o TIPO que melhor comunica a mensagem:
{kinds}
Regras:
- O primeiro slide é capa e o último é conclusao.
- "mensagem" é uma AFIRMAÇÃO específica que o slide prova (não um tema).
  Ruim: "Vantagens dos microsserviços". Bom: "Microsserviços escalam só o que está sob carga".
- "objetivo" diz que evidência, exemplo ou comparação sustenta a mensagem.
- "fatos" lista os IDs de fatos da pesquisa que sustentam o slide; não repita o mesmo
  fato em muitos slides. Prefira slides com números, datas e exemplos reais.
- Varie os tipos; não use o mesmo tipo em dois slides seguidos (exceto se inevitável).
- "mensagem" com até 60 caracteres: ela vira o título do slide.
- Se houver TÓPICOS OBRIGATÓRIOS, cada um deve aparecer em "topicos" de pelo menos um
  slide do meio (nem capa, nem só na conclusão).
- Os fatos só sustentam o que dizem: não use uma estatística de mercado para justificar
  uma decisão técnica, nem um caso de uma empresa como regra geral.
- TODO slide responde à pergunta do pedido. Fato que não trata do assunto central fica
  de fora; nunca crie um slide só porque há um fato sobre outro tema.
Responda só JSON, em português do Brasil."""

CONTENT_SYSTEM = """Você escreve o conteúdo de UM slide de uma apresentação profissional.
Contrato editorial:
- O título é a mensagem do slide: uma afirmação completa, com até 60 caracteres.
- Cada item tem "rotulo" (2 a 5 palavras, sem repetir o título) e "detalhe": UMA frase
  completa, com sujeito e verbo, de 8 a 22 palavras, que explica o rótulo com algo
  concreto (número, nome, data, exemplo ou condição). Não escreva cenário solto como
  "uma casa com telhado inclinado"; escreva o que acontece nele e por quê.
- Ao usar um fato, mantenha o mesmo sujeito, número e período do fato: "a plataforma
  cresceu 30%" não vira "o mercado cresceu 30%"; "nos anos 1970" não vira "em 1970".
- Proibido detalhe genérico como "facilita a manutenção" ou "melhora o desempenho"
  sem dizer quanto, onde, para quem ou em que condição.
- Use SOMENTE números e datas presentes nos fatos fornecidos e cite seus IDs em
  "fontes". Sem fato numérico, use exemplos qualitativos nomeados — nunca invente dados.
- "notas" são 2 a 4 frases para o apresentador: o raciocínio, o exemplo e a ressalva.
- Nunca invente empresas, pessoas, produtos, datas ou estatísticas. Nomes próprios e
  números só podem vir dos fatos. Sem fatos, use exemplos descritos de forma genérica
  ("uma loja online", "um aplicativo de entregas") e condições ("quando a equipe cresce").
- Não escreva IDs de fatos (F1, F2...) no texto visível; eles vão só em "fontes".
- Escreva em português do Brasil, com acentos corretos."""

KIND_RULES = {
    "capa": "titulo do deck (até 60 caracteres), subtitulo com a promessa da apresentação "
    "(até 110), autor opcional.",
    "secao": "titulo curto da parte e subtitulo opcional.",
    "topicos": "2 a 5 itens paralelos (3 é o ideal).",
    "etapas": "2 a 5 passos em ordem; rotulo começa com verbo no infinitivo.",
    "conclusao": "2 a 4 conclusões acionáveis; rotulo é a recomendação, detalhe é o porquê.",
    "numeros": '1 a 3 valores; valor é o número curto exatamente como no fato (ex.: "90%", '
    '"7 anos"), legenda explica o que ele mede (até 110 caracteres).',
    "comparacao": "exatamente 2 lados, cada um com 2 a 4 itens; detalhe até 70 caracteres; "
    "itens na mesma ordem comparam o mesmo aspecto.",
    "linha_do_tempo": '2 a 6 marcos em ordem cronológica; data curta ("2014"), rotulo até 30 '
    "caracteres, detalhe até 80.",
    "citacao": "texto é uma frase LITERAL de um fato do tipo citacao; autor é quem disse.",
    "grafico": "2 a 7 barras com valores numéricos dos fatos (mesma unidade); unidade "
    "descreve a medida; rotulo da barra até 18 caracteres.",
    "imagem": "busca_imagem com 2 a 5 palavras em inglês para encontrar uma foto ilustrativa, "
    "legenda e até 3 itens.",
}

EXAMPLES = {
    "topicos": 'topicos {\n  titulo "Microsserviços escalam só o que está sob carga"\n'
    '  item "Escala seletiva" "Na Black Friday, só o serviço de pagamentos ganha réplicas."\n'
    '  item "Falhas isoladas" "Um erro no catálogo não derruba o carrinho de compras."\n'
    "  fontes F2\n"
    '  notas "Explique que a vantagem depende de fronteiras bem definidas."\n}',
}


def kinds_text(kinds) -> str:
    return "\n".join(f"- {k}: {DESCRIPTIONS[k]}" for k in kinds)


# ---------------------------------------------------------------------------
# Schemas JSON


def _str(max_length, min_length=1):
    return {"type": "string", "minLength": min_length, "maxLength": max_length}


# Limites do schema são FOLGADOS de propósito: o decoder restrito corta o texto ao atingir
# maxLength (era a causa dos títulos terminando em "mais esf"). O tamanho certo é pedido no
# prompt e cobrado pela validação A005, que devolve o campo ao modelo para encurtar.


def outline_schema(
    n_slides: int, kinds: list[str], fact_ids: list[str], topics: list[str] | None = None
) -> dict:
    slide = {
        "type": "object",
        "properties": {
            "tipo": {"type": "string", "enum": kinds},
            "mensagem": _str(160, 8),
            "objetivo": _str(300, 8),
        },
        "required": ["tipo", "mensagem", "objetivo"],
    }
    if fact_ids:
        slide["properties"]["fatos"] = {
            "type": "array",
            "maxItems": 4,
            "items": {"type": "string", "enum": fact_ids},
        }
        slide["required"].append("fatos")
    if topics:
        slide["properties"]["topicos"] = {
            "type": "array",
            "maxItems": 4,
            "items": {"type": "string", "enum": topics},
        }
        slide["required"].append("topicos")
    return {
        "type": "object",
        "properties": {
            "titulo": _str(140, 4),  # título do deck
            "slides": {"type": "array", "minItems": n_slides, "maxItems": n_slides, "items": slide},
        },
        "required": ["titulo", "slides"],
    }


def _items_schema(low, high, detail=360):
    return {
        "type": "array",
        "minItems": low,
        "maxItems": high,
        "items": {
            "type": "object",
            "properties": {"rotulo": _str(120, 2), "detalhe": _str(detail, 8)},
            "required": ["rotulo", "detalhe"],
        },
    }


def slide_schema(kind: str, fact_ids: list[str]) -> dict:
    props: dict = {}
    if kind == "citacao":
        props.update(texto=_str(500, 10), autor=_str(160, 2))
    else:
        props["titulo"] = _str(160, 4)
    if kind in ("capa", "secao"):
        props["subtitulo"] = _str(300, 0)
    if kind == "capa":
        props["autor"] = _str(160, 0)
    if kind in ("topicos", "etapas", "conclusao"):
        _, low, high = LIMITS[kind]
        props["itens"] = _items_schema(low, high)
    if kind == "imagem":
        props.update(busca_imagem=_str(120, 3), legenda=_str(300, 0), itens=_items_schema(0, 3))
    if kind == "numeros":
        props["valores"] = {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {"valor": _str(40), "legenda": _str(300, 6)},
                "required": ["valor", "legenda"],
            },
        }
    if kind == "comparacao":
        props["lados"] = {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {"nome": _str(80), "itens": _items_schema(2, 4, 240)},
                "required": ["nome", "itens"],
            },
        }
    if kind == "linha_do_tempo":
        props["marcos"] = {
            "type": "array",
            "minItems": 2,
            "maxItems": 6,
            "items": {
                "type": "object",
                "properties": {"data": _str(40), "rotulo": _str(100), "detalhe": _str(240, 0)},
                "required": ["data", "rotulo", "detalhe"],
            },
        }
    if kind == "grafico":
        props["unidade"] = _str(100, 0)
        props["barras"] = {
            "type": "array",
            "minItems": 2,
            "maxItems": 7,
            "items": {
                "type": "object",
                "properties": {"rotulo": _str(60), "valor": {"type": "number", "minimum": 0}},
                "required": ["rotulo", "valor"],
            },
        }
    if kind not in ("capa", "secao"):
        props["fontes"] = (
            {"type": "array", "maxItems": 4, "items": {"type": "string", "enum": fact_ids}}
            if fact_ids
            else {"type": "array", "maxItems": 0}
        )
    props["notas"] = _str(2000, 0)
    return {"type": "object", "properties": props, "required": list(props)}


def _items(values) -> list[Item]:
    return [
        Item(label=v["rotulo"].strip(), detail=(v.get("detalhe") or "").strip() or None)
        for v in values or []
    ]


def json_to_slide(kind: str, data: dict) -> AltoSlide:
    s = AltoSlide(kind=kind)
    s.title = (data.get("titulo") or "").strip() or None
    s.subtitle = (data.get("subtitulo") or "").strip() or None
    s.author = (data.get("autor") or "").strip() or None
    s.text = (data.get("texto") or "").strip() or None
    s.caption = (data.get("legenda") or "").strip() or None
    s.unit = (data.get("unidade") or "").strip() or None
    s.image_query = (data.get("busca_imagem") or "").strip() or None
    s.notes = (data.get("notas") or "").strip() or None
    s.items = _items(data.get("itens"))
    s.values = [
        Value(value=v["valor"].strip(), label=v["legenda"].strip())
        for v in data.get("valores") or []
    ]
    s.sides = [
        Side(name=v["nome"].strip(), items=_items(v.get("itens"))) for v in data.get("lados") or []
    ]
    s.milestones = [
        Milestone(
            date=v["data"].strip(),
            label=v["rotulo"].strip(),
            detail=(v.get("detalhe") or "").strip() or None,
        )
        for v in data.get("marcos") or []
    ]
    s.bars = [
        Bar(label=v["rotulo"].strip(), value=float(v["valor"])) for v in data.get("barras") or []
    ]
    s.sources = list(dict.fromkeys(data.get("fontes") or []))
    return s


# ---------------------------------------------------------------------------
# Validação, reparo e pontuação


def translate_path(path: str | None) -> str:
    if not path:
        return "slide"
    parts = path.split(".")[2:]  # remove "slides.N"
    out = []
    for part in parts:
        out.append(f"[{part}]" if part.isdigit() else "." + PATH_WORDS.get(part, part))
    return "".join(out).lstrip(".") or "slide"


def check_slide(
    slide: AltoSlide, facts: dict, theme="claro", topics: list[dict] | None = None,
    truncated: list[str] | None = None,
) -> list[Diagnostic]:
    from .alto_quality import coverage_diagnostics

    deck = AltoDeck(title="candidato", theme=theme, slides=[slide])
    ds = [
        Diagnostic(
            code="A013",
            severity="ERRO",
            message="Texto cortado no limite de tamanho (frase incompleta).",
            evidence={"path": "slides.0." + re.sub(r"\[(\d+)\]", r".\1", path)},
            suggestion="Reescreva a frase completa e mais curta.",
        )
        for path in truncated or []
    ]
    ds += validate_alto(deck, facts)
    if topics and slide.kind not in ("capa", "secao"):
        ds += coverage_diagnostics(slide, topics, 1)
    if not any(d.severity == "ERRO" for d in ds):
        try:
            _, _, layout = alto_to_ast(deck, facts)
            ds += layout
        except Exception as exc:  # layout inesperado vira diagnóstico, não exceção
            ds.append(Diagnostic(code="A010", severity="ERRO", message=f"Layout falhou: {exc}"))
    return ds


def diagnostics_feedback(ds: list[Diagnostic]) -> str:
    lines = []
    for d in ds:
        if d.severity == "INFORMAÇÃO":
            continue
        path = translate_path((d.evidence or {}).get("path"))
        lines.append(f"- {d.code} {d.severity} em {path}: {d.message} {d.suggestion or ''}".strip())
    return "\n".join(lines)


def score_slide(slide: AltoSlide, ds: list[Diagnostic], facts: dict) -> float:
    weights = {"A007": 15, "A012": 8, "A008": 5, "A009": 4, "A011": 3}
    score = 0.0
    for d in ds:
        if d.severity == "ERRO":
            score -= 100
        elif d.severity == "AVISO":
            score -= weights.get(d.code, 2)
    cited = [r for r in slide.sources if r in facts]
    score += 5 * min(3, len(cited))
    details = [i.detail for i in slide.items if i.detail]
    details += [i.detail for side in slide.sides for i in side.items if i.detail]
    details += [m.detail for m in slide.milestones if m.detail]
    for detail in details:
        words = len(detail.split())
        score += 1 if 8 <= words <= 24 else -1
        if re.search(r"\d", detail):
            score += 2
        cited_text = " ".join(
            facts[r].get("claim", "") + " " + facts[r].get("quote", "") for r in cited
        ).casefold()
        for name in re.findall(r"(?<=\s)[A-ZÁÉÍÓÚÂÊÔÃÕ][\wáéíóúâêôãõç]{2,}", detail):
            # Nome próprio sustentado por fato = exemplo concreto; sem fato, pode ser inventado.
            score += 1 if name.casefold() in cited_text else -2
    if slide.notes and len(slide.notes.split()) >= 15:
        score += 2
    if slide.title and len(slide.title) <= 60:
        score += 1
    return score


# ---------------------------------------------------------------------------
# Execução


@dataclass
class Call:
    stage: str
    slide: int | None
    candidate: int | None
    attempt: int
    system: str
    user: str
    constraint: str
    raw: str | None = None
    error: str | None = None


@dataclass
class GenerationResult:
    request: str
    outline: dict | None = None
    deck: AltoDeck | None = None
    calls: list[Call] = field(default_factory=list)
    candidates: list[dict] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    topics: list[dict] = field(default_factory=list)
    coverage: list[dict] = field(default_factory=list)
    support: list[dict] = field(default_factory=list)

    @property
    def source(self) -> str | None:
        return print_alto(self.deck) if self.deck else None


def _call(
    model,
    result,
    *,
    stage,
    slide,
    candidate,
    attempt,
    system,
    user,
    schema=None,
    grammar=None,
    temperature=0.2,
    seed=None,
):
    constraint = "grammar" if grammar else "json_schema" if schema else "none"
    call = Call(stage, slide, candidate, attempt, system, user, constraint)
    result.calls.append(call)
    kwargs = {"temperature": temperature, "seed": seed}
    if grammar is not None:
        kwargs["grammar"] = grammar
    elif schema is not None:
        kwargs["response_schema"] = schema
    try:
        call.raw = model.generate(system, user, **kwargs)
    except TypeError:
        kwargs.pop("grammar", None)
        kwargs.pop("response_schema", None)
        call.raw = model.generate(system, user, **kwargs)
    except Exception as exc:
        call.error = str(exc)
        raise
    return call.raw


def _load_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw or "", re.S)
    return json.loads(match.group(0) if match else raw)


def _parse_slide_text(raw: str, kind: str, theme: str) -> AltoSlide:
    text = re.sub(r"^```\w*|```$", "", (raw or "").strip(), flags=re.M).strip()
    start = text.find(kind)
    if start < 0:
        raise DSLException(
            [
                Diagnostic(
                    code="P001",
                    severity="ERRO",
                    message=f"Bloco {kind} não encontrado na resposta.",
                )
            ]
        )
    depth, end = 0, None
    in_string, escape = False, False
    for k in range(start, len(text)):
        c = text[k]
        if in_string:
            escape = c == "\\" and not escape
            if c == '"' and not escape:
                in_string = False
            continue
        if c == '"':
            in_string = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = k + 1
                break
    block = text[start:end] if end else text[start:]
    deck = parse_alto(f'deck "x" {{\n  tema {theme}\n{block}\n}}\n')
    if len(deck.slides) != 1 or deck.slides[0].kind != kind:
        raise DSLException(
            [Diagnostic(code="A003", severity="ERRO", message=f"Esperado um único slide {kind}.")]
        )
    return deck.slides[0]


def fix_outline(outline: dict, kinds: list[str]) -> dict:
    slides = outline.get("slides", [])
    if slides and slides[0].get("tipo") != "capa" and "capa" in kinds:
        slides[0]["tipo"] = "capa"
    if len(slides) > 1 and slides[-1].get("tipo") != "conclusao":
        slides[-1]["tipo"] = "conclusao"
    for s in slides[1:-1]:
        if s.get("tipo") == "capa":
            s["tipo"] = "topicos"
    return outline


def data_kind_supported(kind: str, facts: dict) -> bool:
    """Slides de dados só existem quando há fatos com o tipo de dado que eles exibem."""
    from .alto import number_tokens

    texts = [f.get("claim", "") + " " + f.get("quote", "") for f in facts.values()]
    numeric = sum(1 for t in texts if number_tokens(t))
    dated = sum(1 for t in texts if re.search(r"\b(1[5-9]\d\d|20\d\d)\b", t))
    return {
        "numeros": numeric >= 1,
        "grafico": numeric >= 2,
        "linha_do_tempo": dated >= 2,
    }.get(kind, True)


def _fact_ref_pattern(ids) -> re.Pattern | None:
    ids = sorted({i for i in ids if re.fullmatch(r"F\d+", i)}, key=len, reverse=True)
    if not ids:
        return None
    ref = "(?:" + "|".join(ids) + ")"
    return re.compile(
        r"\s*[,;(]?\s*(?:\b(?:conforme|segundo|de acordo com|como (?:mostra|previsto|"
        r"mostrado|destacado|indicado|visto) em|ver|vide|fonte:?)\s+)?(?:destacado em\s+)?"
        rf"\b{ref}\b(?:\s*(?:e|,)\s*{ref}\b)*\)?",
        re.IGNORECASE,
    )


def strip_fact_ids(text: str | None, ids=()) -> str | None:
    """Remove menções a IDs de fatos do dossiê ("conforme F3") do texto visível.

    Só remove IDs que existem no dossiê, para não apagar nomes como "F1" (Fórmula 1)."""
    pattern = _fact_ref_pattern(ids)
    if not text or pattern is None:
        return text
    cleaned = pattern.sub("", text)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned or text


def clean_visible(slide: AltoSlide, ids) -> AltoSlide:
    for name in ("title", "subtitle", "caption", "unit"):
        setattr(slide, name, strip_fact_ids(getattr(slide, name), ids))
    for item in slide.items + [i for side in slide.sides for i in side.items]:
        item.label = strip_fact_ids(item.label, ids)
        item.detail = strip_fact_ids(item.detail, ids)
    for v in slide.values:
        v.label = strip_fact_ids(v.label, ids)
    for m in slide.milestones:
        m.label, m.detail = strip_fact_ids(m.label, ids), strip_fact_ids(m.detail, ids)
    return slide


def facts_block(ids: list[str], facts: dict, all_facts: bool = False) -> str:
    chosen = list(facts) if all_facts else [i for i in ids if i in facts]
    lines = []
    for fid in chosen[:8]:
        f = facts[fid]
        value = f" [valor: {f['value']}]" if f.get("value") else ""
        lines.append(f"{fid} ({f['kind']}){value}: {f['claim']}\n   trecho: \"{f['quote'][:300]}\"")
    return "\n".join(lines) or "(nenhum fato: não use números; use exemplos qualitativos)"


def generate_alto(
    request: str,
    model,
    *,
    facts: dict | None = None,
    n_slides: int = 6,
    theme: str = "claro",
    mode: str = "json",
    candidates: int = 1,
    repair_max: int = 2,
    images: bool = False,
    seed: int = 42,
    temperature: float = 0.2,
    progress: Callable[[str], None] | None = None,
    result: GenerationResult | None = None,
    verify_support: bool = True,
    coverage: bool = True,
) -> GenerationResult:
    from .alto_quality import (
        apply_corrections,
        check_support,
        coverage_report,
        extract_topics,
        quote_candidates,
        quote_slide,
        support_diagnostics,
        truncated_paths,
    )

    say = progress or (lambda message: None)
    facts = facts or {}
    if mode not in ("json", "gramatica", "direto"):
        raise ValueError("Modo deve ser json, gramatica ou direto.")
    if mode == "gramatica" and not getattr(model, "supports_grammar", False):
        raise ValueError("Modo gramatica exige provedor com GBNF (use --provider llamacpp).")
    result = result or GenerationResult(request=request)
    kinds = [
        k
        for k in SLIDE_KINDS
        if (facts or k not in DATA_KINDS)
        and (images or k != "imagem")
        and data_kind_supported(k, facts)
        and (k != "citacao" or quote_candidates(facts))
    ]
    fact_ids = list(facts)

    def call(stage, slide, system, user, schema, attempt=0, candidate=None, temp=0.0, s=None):
        return _call(model, result, stage=stage, slide=slide, candidate=candidate,
                     attempt=attempt, system=system, user=user, schema=schema,
                     temperature=temp, seed=seed if s is None else s)

    # 0. Tópicos obrigatórios do pedido (só para pedidos detalhados)
    topics = []
    if coverage:
        try:
            topics = extract_topics(call, request)
        except (ValueError, KeyError, TypeError) as exc:
            say(f"Não foi possível extrair os tópicos do pedido: {exc}")
        if topics:
            say("Tópicos pedidos: " + ", ".join(t["nome"] for t in topics))
    result.topics = topics
    topic_names = [t["nome"] for t in topics]

    # 1. Roteiro (com uma correção se faltar tópico obrigatório)
    say("Planejando o roteiro")
    user = (
        f"Pedido: {request}\nNúmero de slides: {n_slides}\n\n"
        f"Fatos da pesquisa:\n{facts_block(fact_ids, facts, all_facts=True)}"
    )
    if topics:
        user += "\n\nTÓPICOS OBRIGATÓRIOS (cada um em algum slide):\n" + "\n".join(
            f"- {t}" for t in topic_names
        )
    schema = outline_schema(n_slides, kinds, fact_ids, topic_names)
    outline = None
    for attempt in range(2):
        raw = call("roteiro", None, OUTLINE_SYSTEM.format(kinds=kinds_text(kinds)), user, schema,
                   attempt=attempt, temp=temperature)
        outline = fix_outline(_load_json(raw), kinds)
        assigned = {t for sl in outline["slides"][1:] for t in sl.get("topicos", [])}
        missing = [t for t in topic_names if t not in assigned]
        if not missing:
            break
        user += (
            f"\n\nSua resposta anterior:\n{json.dumps(outline, ensure_ascii=False)}\n"
            f"Faltaram os tópicos obrigatórios: {', '.join(missing)}. Refaça o roteiro "
            "cobrindo todos, juntando tópicos afins no mesmo slide se precisar."
        )
    result.outline = outline
    summary = "\n".join(
        f"{k + 1}. {sl['tipo']}: {sl['mensagem']}" for k, sl in enumerate(outline["slides"])
    )

    def produce(kind, base_user, k, c, slide_topics, extra=None):
        """Gera (com reparos) um candidato. Retorna (slide, diagnósticos, tentativas)."""
        user, attempt, slide, ds, raw = base_user + (extra or ""), 0, None, [], ""
        while True:
            temp = temperature if c == 0 else min(1.0, temperature + 0.5)
            s_seed = seed + 100 * (k + 1) + 10 * c + attempt
            truncated = []
            try:
                if mode == "json":
                    schema = slide_schema(kind, fact_ids)
                    raw = call("slide", k + 1, CONTENT_SYSTEM, user, schema, attempt, c, temp,
                               s_seed)
                    data = _load_json(raw)
                    truncated = truncated_paths(data, schema)
                    slide = json_to_slide(kind, data)
                else:
                    grammar = None
                    if mode == "gramatica":
                        from .gbnf import alto_gbnf

                        grammar = alto_gbnf(kind)
                    raw = _call(model, result, stage="slide", slide=k + 1, candidate=c,
                                attempt=attempt, system=CONTENT_SYSTEM, user=user,
                                grammar=grammar, temperature=temp, seed=s_seed)
                    slide = _parse_slide_text(raw, kind, theme)
                clean_visible(slide, facts)  # "conforme F2" não aparece para a plateia
                # IDs de fatos inexistentes são descartados (o modelo não cria fontes).
                slide.sources = [
                    r for r in slide.sources if r in facts or not re.fullmatch(r"F\d+", r)
                ]
                ds = check_slide(slide, facts, theme, slide_topics, truncated)
            except DSLException as exc:
                slide, ds = None, exc.diagnostics
            except (ValueError, KeyError, TypeError) as exc:
                slide = None
                ds = [Diagnostic(code="P002", severity="ERRO",
                                 message=f"Resposta fora do formato: {exc}")]
            errors = [d for d in ds if d.severity == "ERRO"]
            warnings = [d for d in ds if d.severity == "AVISO"]
            if (not errors and not warnings) or attempt >= repair_max:
                return slide, ds, attempt + 1, raw
            if not errors and slide is not None and all(d.code == "A009" for d in warnings):
                return slide, ds, attempt + 1, raw  # avisos leves não justificam nova chamada
            attempt += 1
            previous = (
                json.dumps(_load_json(raw), ensure_ascii=False)
                if mode == "json" and slide is not None
                else (raw or "")[:3000]
            )
            user = (
                f"{base_user}\n\nSua resposta anterior:\n{previous}\n\n"
                f"Problemas encontrados:\n{diagnostics_feedback(ds)}\n"
                "Corrija SOMENTE os campos indicados e mantenha o restante."
            )

    # 2. Conteúdo por slide: candidatos, reparo, verificação de sustentação
    slides = []
    for k, plan in enumerate(outline["slides"]):
        kind = plan["tipo"] if plan["tipo"] in kinds else "topicos"
        ids = [i for i in plan.get("fatos", []) if i in facts]
        slide_topics = [t for t in topics if t["nome"] in plan.get("topicos", [])]
        say(f"Slide {k + 1}/{len(outline['slides'])}: {kind}")
        if kind == "citacao":
            quoted = quote_slide(facts, ids, notes=plan.get("objetivo"))
            if quoted is not None:  # citação literal montada do fato, sem o modelo reescrever
                slides.append(quoted)
                result.candidates.append({"slide": k + 1, "candidate": 0, "attempts": 0,
                                          "score": 0, "diagnostics": [],
                                          "alto": print_slide(quoted), "deterministic": True})
                continue
            kind = "topicos"
        base_user = (
            f"Pedido original: {request}\nApresentação: {outline['titulo']}\n"
            f"Roteiro:\n{summary}\n\n"
            f"Escreva o slide {k + 1} (tipo {kind}).\nMensagem: {plan['mensagem']}\n"
            f"Objetivo: {plan['objetivo']}\nRegras do tipo: {KIND_RULES[kind]}\n\n"
            f"Fatos para este slide:\n{facts_block(ids, facts)}"
        )
        if slide_topics:
            base_user += "\n\nEste slide DEVE tratar, no texto visível, de: " + "; ".join(
                f"{t['nome']} (palavras: {', '.join(t['termos'][:3])})" for t in slide_topics
            )
        if ids and len(ids) < 3:
            others = [i for i in fact_ids if i not in ids][:4]
            if others:
                base_user += f"\n\nOutros fatos que podem ajudar:\n{facts_block(others, facts)}"
        if mode != "json":
            from .alto import grammar_text

            rules = "\n".join(
                line
                for line in grammar_text().splitlines()
                if line.strip() and not line.lstrip().startswith(("//", "%"))
            )
            base_user += (
                "\n\nResponda SOMENTE com o bloco SlideDSL Alto deste slide (começando por "
                f"'{kind} {{'), sem comentários nem Markdown.\nGramática:\n{rules}\n"
                f"Exemplo de formato:\n{EXAMPLES['topicos']}"
            )
        best = None
        for c in range(max(1, candidates)):
            slide, ds, attempts, raw = produce(kind, base_user, k, c, slide_topics)
            score = score_slide(slide, ds, facts) if slide else -1000
            result.candidates.append({
                "slide": k + 1, "candidate": c, "attempts": attempts, "score": score,
                "diagnostics": [d.model_dump() for d in ds],
                "alto": print_slide(slide) if slide else None,
            })
            if slide is not None and (best is None or score > best[0]):
                best = (score, slide, ds, raw)
        if best is None:
            raise DSLException(ds or [Diagnostic(code="P001", severity="ERRO",
                                                 message=f"Slide {k + 1} sem candidato válido.")])
        _, slide, ds, raw = best

        # Sustentação: o melhor candidato é conferido contra os fatos que cita.
        if verify_support and facts:
            try:
                problems = check_support(call, slide, facts, k + 1)
                rounds = 0
                while problems and rounds < repair_max:
                    rounds += 1
                    say(f"Slide {k + 1}: {len(problems)} frase(s) sem sustentação; corrigindo")
                    feedback = diagnostics_feedback(support_diagnostics(problems, k + 1))
                    previous = (json.dumps(_load_json(raw), ensure_ascii=False)
                                if mode == "json" else (raw or "")[:3000])
                    fixed, fixed_ds, _, fixed_raw = produce(
                        kind, base_user, k, 0, slide_topics,
                        extra=(f"\n\nSua resposta anterior:\n{previous}\n\n"
                               f"Frases que os fatos NÃO sustentam:\n{feedback}\n"
                               "Reescreva SOMENTE essas frases usando apenas o que os fatos "
                               "dizem e mantenha o restante."),
                    )
                    if fixed is None or any(d.severity == "ERRO" for d in fixed_ds):
                        break
                    new_problems = check_support(call, fixed, facts, k + 1)
                    if len(new_problems) <= len(problems):
                        slide, ds, raw, problems = fixed, fixed_ds, fixed_raw, new_problems
                    else:
                        break
                if problems:
                    corrected = apply_corrections(slide, problems)
                    corrected_ds = check_slide(corrected, facts, theme, slide_topics)
                    if not any(d.severity == "ERRO" for d in corrected_ds):
                        remaining = check_support(call, corrected, facts, k + 1)
                        if len(remaining) < len(problems):
                            slide, ds, problems = corrected, corrected_ds, remaining
                            say(f"Slide {k + 1}: correções do verificador aplicadas")
                result.support.append({"slide": k + 1, "problems": problems})
                ds = ds + support_diagnostics(problems, k + 1, severity="AVISO")
            except (ValueError, KeyError, TypeError) as exc:
                say(f"Slide {k + 1}: verificação de sustentação falhou ({exc})")
        slides.append(slide)
        result.diagnostics += ds

    deck = AltoDeck(title=outline["titulo"], theme=theme, slides=slides)
    if images:
        resolve_images(deck, say)
    result.coverage = coverage_report(slides, topics)
    missing = [c["topico"] for c in result.coverage if not c["coberto"]]
    if missing:
        say("Tópicos pedidos sem slide: " + ", ".join(missing))
    result.deck = deck
    return result


def resolve_images(deck: AltoDeck, say=lambda m: None):
    """Troca `buscar` por arquivo local licenciado; sem imagem, vira tópicos."""
    from .media import automatic_candidate, automatic_search, cache_image

    for s in deck.slides:
        if s.kind != "imagem" or s.image_file or not s.image_query:
            continue
        try:
            found = automatic_search(s.image_query)
            item = next((i for i in found["results"] if automatic_candidate(i)), None)
            if item:
                s.image_file = cache_image(item["id"])["asset"]
                say(f"Imagem: {item['title'][:60]}")
                continue
        except Exception as exc:
            say(f"Imagem indisponível ({exc}); usando tópicos.")
        if len(s.items) >= 2:
            s.kind = "topicos"


# ---------------------------------------------------------------------------
# Orquestração com arquivos de auditoria


class NoFactsError(ValueError):
    """A pesquisa terminou sem nenhuma ficha verificada."""


def create_presentation(
    request: str,
    out_dir: Path,
    model,
    *,
    research_provider: str | None = "searxng",
    langs=("pt", "en"),
    dossier=None,
    n_slides: int = 6,
    theme: str = "claro",
    mode: str = "json",
    candidates: int = 1,
    repair_max: int = 2,
    images: bool = False,
    seed: int = 42,
    temperature: float = 0.2,
    strict: bool = False,
    preview: bool = True,
    progress: Callable[[str], None] | None = None,
    fetcher=None,
    contact: str | None = None,
    allow_without_facts: bool = False,
    verify_support: bool = True,
    coverage: bool = True,
    fallback_wikipedia: bool = False,
) -> dict:
    """Pesquisa → roteiro → slides → PPTX. Grava todos os passos em `out_dir`."""
    from dataclasses import asdict
    import time

    from .alto_compile import build_alto
    from .compiler import compile_ir

    say = progress or (lambda message: None)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    (out_dir / "pedido.txt").write_text(request + "\n", "utf-8")
    report = {
        "request": request,
        "mode": mode,
        "candidates": candidates,
        "model": getattr(model, "metadata", {}),
        "research": research_provider,
    }
    if dossier is None and research_provider:
        from .research import default_fetcher, research

        say("Pesquisando na internet")
        dossier = research(
            request,
            model=model,
            provider=research_provider,
            langs=langs,
            fetcher=fetcher or default_fetcher,
            progress=say,
            contact=contact,
            fallback_wikipedia=fallback_wikipedia,
        )
    facts = dossier.fact_map() if dossier else {}
    if dossier:
        dossier.save(out_dir / "dossie.json")
        report["facts"] = len(facts)
        report["sources"] = len(dossier.sources)
        if not facts and not allow_without_facts:
            errors = [e["error"] for e in dossier.log if e.get("error")]
            hint = ""
            if any("searxng" in e.casefold() for e in errors):
                hint = (
                    " O SearXNG não respondeu: confira o Docker Desktop e rode "
                    "scripts\\iniciar_searxng.cmd (ou reinicie o contêiner slidedsl-searxng)."
                )
            elif any("403" in e and "wikipedia" in e.casefold() for e in errors) or any(
                "HTTP 403" in e for e in errors
            ):
                hint = (
                    " A Wikipedia recusou o acesso (403): informe um contato (e-mail ou site) "
                    "no campo Contato ou em SLIDEDSL_CONTACT, conforme a política da Wikimedia."
                )
            report["errors"] = [{"code": "R001", "message": "Pesquisa sem fatos.", "log": errors}]
            (out_dir / "relatorio.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2, default=str), "utf-8"
            )
            raise NoFactsError(
                "A pesquisa não encontrou fatos verificáveis"
                + (f" ({errors[0][:160]})" if errors else "")
                + "."
                + hint
                + " Sem fatos, o modelo tende a inventar exemplos; marque 'Continuar sem"
                " pesquisa' para gerar mesmo assim."
            )
    generation = GenerationResult(request=request)
    try:
        generate_alto(
            request,
            model,
            facts=facts,
            n_slides=n_slides,
            theme=theme,
            mode=mode,
            candidates=candidates,
            repair_max=repair_max,
            images=images,
            seed=seed,
            temperature=temperature,
            progress=say,
            result=generation,
            verify_support=verify_support,
            coverage=coverage,
        )
    finally:
        with (out_dir / "chamadas.jsonl").open("w", encoding="utf-8") as f:
            for call in generation.calls:
                f.write(json.dumps(asdict(call), ensure_ascii=False) + "\n")
        (out_dir / "candidatos.json").write_text(
            json.dumps(generation.candidates, ensure_ascii=False, indent=2), "utf-8"
        )
    (out_dir / "roteiro.json").write_text(
        json.dumps(generation.outline, ensure_ascii=False, indent=2), "utf-8"
    )
    (out_dir / "apresentacao.slda").write_text(generation.source, "utf-8")
    quality = {
        "topicos_pedidos": generation.topics,
        "cobertura": generation.coverage,
        "sustentacao": generation.support,
    }
    (out_dir / "qualidade.json").write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), "utf-8"
    )
    report["coverage"] = generation.coverage
    report["unsupported"] = [
        {"slide": x["slide"], "texto": p["texto"], "motivo": p["motivo"]}
        for x in generation.support
        for p in x["problems"]
    ]
    built = build_alto(generation.deck, facts)
    (out_dir / "validacao.json").write_text(
        json.dumps(built.report(strict), ensure_ascii=False, indent=2), "utf-8"
    )
    report.update(
        calls=len(generation.calls),
        seconds=round(time.monotonic() - started, 1),
        valid=built.success(strict),
    )
    if built.dsl:
        (out_dir / "apresentacao.sld").write_text(built.dsl, "utf-8")
    if built.success(strict):
        info = compile_ir(built.validation.ir, out_dir / "apresentacao.pptx", strict=strict)
        report["pptx"] = str(out_dir / "apresentacao.pptx")
        report["inspection"] = {k: v for k, v in info["inspection"].items() if k != "slides"}
        if preview:
            from .ir_preview import contact_sheet, render_deck

            paths = render_deck(built.validation.ir, out_dir / "previa", 0.6)
            report["preview"] = str(contact_sheet(paths, out_dir / "previa.png"))
    else:
        report["errors"] = [d.model_dump() for d in built.errors]
    (out_dir / "relatorio.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), "utf-8"
    )
    return report
