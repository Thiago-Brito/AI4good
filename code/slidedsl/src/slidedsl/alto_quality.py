"""Verificações de qualidade do conteúdo gerado (além da validade estrutural).

* Sustentação: cada frase com número ou nome próprio é julgada contra os fatos citados
  (sustentada / parcial / não sustentada). É uma tarefa curta de comparação, adequada a
  SLMs; a verificação é do mesmo modelo, portanto reduz erros mas não os elimina.
* Cobertura: tópicos que o pedido exige explicitamente são extraídos, atribuídos a slides
  no roteiro e conferidos no texto visível de cada slide.
* Truncamento: campo que atingiu exatamente o limite do schema foi cortado pelo decoder.
* Citação: o slide de citação é montado a partir do trecho literal e do autor do fato.
"""

from copy import deepcopy
import json
import re
import unicodedata
from typing import Callable

from .alto import AltoSlide, number_tokens
from .diagnostics import Diagnostic

Call = Callable[..., str]  # call(stage, slide, system, user, schema) -> resposta crua

# ---------------------------------------------------------------------------
# Texto


def normalize(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", (value or "").casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[\W_]+", " ", value).strip()


PROPER = re.compile(r"(?<=[\s(])[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç]{2,}")


def has_specifics(text: str | None) -> bool:
    """Número ou nome próprio no meio da frase: afirmação específica que precisa de fonte."""
    return bool(text) and (bool(number_tokens(text)) or bool(PROPER.search(" " + text[1:])))


def factual_units(slide: AltoSlide) -> list[tuple[str, str, str]]:
    """(caminho relativo, contexto, texto) das frases específicas do slide."""
    units = []
    if slide.kind not in ("capa", "secao") and has_specifics(slide.title):
        units.append(("title", "título", slide.title))
    if slide.kind == "capa" and has_specifics(slide.subtitle):
        units.append(("subtitle", "subtítulo", slide.subtitle))
    for k, i in enumerate(slide.items):
        if has_specifics(f"{i.label} {i.detail or ''}"):
            units.append((f"items.{k}.detail", f"item '{i.label}'", i.detail or i.label))
    for k, v in enumerate(slide.values):
        units.append((f"values.{k}.label", f"número '{v.value}'", f"{v.value}: {v.label}"))
    for k, side in enumerate(slide.sides):
        for j, i in enumerate(side.items):
            if has_specifics(f"{i.label} {i.detail or ''}"):
                units.append(
                    (f"sides.{k}.items.{j}.detail", f"{side.name} / '{i.label}'", i.detail or "")
                )
    for k, m in enumerate(slide.milestones):
        units.append(
            (f"milestones.{k}.detail", f"marco {m.date} '{m.label}'",
             f"{m.date}: {m.label}. {m.detail or ''}".strip())
        )
    for k, b in enumerate(slide.bars):
        units.append((f"bars.{k}.label", "barra", f"{b.label}: {b.value}"))
    return [u for u in units if u[2]][:8]


def get_path(slide: AltoSlide, path: str):
    obj = slide
    for part in path.split("."):
        obj = obj[int(part)] if part.isdigit() else getattr(obj, part)
    return obj


def set_path(slide: AltoSlide, path: str, value: str):
    parts = path.split(".")
    obj = slide
    for part in parts[:-1]:
        obj = obj[int(part)] if part.isdigit() else getattr(obj, part)
    setattr(obj, parts[-1], value)


# ---------------------------------------------------------------------------
# Sustentação

SUPPORT_SYSTEM = """Você confere se frases de um slide dizem exatamente o que os fatos dizem.
Para cada frase numerada responda:
- "sustentada": os fatos afirmam isso com o mesmo sujeito, o mesmo número/data e a mesma relação;
- "parcial": mistura fatos, generaliza (ex.: "a plataforma" virou "o mercado"), muda a data
  ("anos 1970" virou "1970") ou tira uma conclusão que os fatos não tiram;
- "nao_sustentada": os fatos não dizem isso.
Em "correcao", reescreva a frase usando SOMENTE os fatos, com tamanho parecido; deixe ""
se a frase estiver sustentada. Responda só JSON, em português do Brasil."""


def support_schema(n: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "avaliacoes": {
                "type": "array",
                "minItems": n,
                "maxItems": n,
                "items": {
                    "type": "object",
                    "properties": {
                        "frase": {"type": "integer", "minimum": 1, "maximum": n},
                        "veredito": {
                            "type": "string",
                            "enum": ["sustentada", "parcial", "nao_sustentada"],
                        },
                        "motivo": {"type": "string", "maxLength": 300},
                        "correcao": {"type": "string", "maxLength": 400},
                    },
                    "required": ["frase", "veredito", "motivo", "correcao"],
                },
            }
        },
        "required": ["avaliacoes"],
    }


def check_support(call: Call, slide: AltoSlide, facts: dict, slide_number: int) -> list[dict]:
    """Retorna as frases problemáticas: [{path, veredito, motivo, correcao, texto}]."""
    units = factual_units(slide)
    cited = [r for r in slide.sources if r in facts]
    if not units or not cited:
        return []
    facts_text = "\n".join(
        f"{r}: {facts[r]['claim']}\n   trecho: \"{facts[r].get('quote', '')[:400]}\"" for r in cited
    )
    sentences = "\n".join(f"{k + 1}. ({ctx}) {text}" for k, (_, ctx, text) in enumerate(units))
    raw = call(
        stage="sustentacao",
        slide=slide_number,
        system=SUPPORT_SYSTEM,
        user=f"FATOS:\n{facts_text}\n\nFRASES DO SLIDE:\n{sentences}",
        schema=support_schema(len(units)),
    )
    match = re.search(r"\{.*\}", raw or "", re.S)
    data = json.loads(match.group(0) if match else raw)
    problems = []
    for item in data.get("avaliacoes", []):
        k = int(item.get("frase", 0)) - 1
        if 0 <= k < len(units) and item.get("veredito") != "sustentada":
            path, _, text = units[k]
            problems.append(
                {
                    "path": path,
                    "veredito": item.get("veredito"),
                    "motivo": (item.get("motivo") or "").strip(),
                    "correcao": (item.get("correcao") or "").strip(),
                    "texto": text,
                }
            )
    return problems


def support_diagnostics(problems: list[dict], slide_number: int, severity="ERRO"):
    return [
        Diagnostic(
            code="A014",
            severity=severity,
            message=(
                f"Frase {p['veredito'].replace('_', ' ')} pelos fatos citados: {p['motivo']}"
            )[:300],
            slide=slide_number,
            evidence={"path": f"slides.0.{p['path']}", "texto": p["texto"][:200]},
            suggestion=(
                f"Reescreva usando só os fatos, por exemplo: {p['correcao']}"
                if p["correcao"]
                else "Reescreva usando só o que os fatos citados dizem."
            )[:300],
        )
        for p in problems
    ]


def apply_corrections(slide: AltoSlide, problems: list[dict]) -> AltoSlide:
    """Aplica as reescritas sugeridas pelo verificador (só em campos de texto)."""
    fixed = deepcopy(slide)
    for p in problems:
        correction = p.get("correcao")
        if not correction:
            continue
        path = p["path"]
        if path.startswith(("values.", "bars.")):
            # "valor: legenda" → mantém o número; troca só a legenda.
            correction = correction.split(":", 1)[-1].strip() if ":" in correction else correction
        if path.startswith("milestones."):
            correction = re.sub(r"^[^:]{1,20}:\s*", "", correction)
        try:
            if isinstance(get_path(fixed, path), str) or get_path(fixed, path) is None:
                set_path(fixed, path, correction)
        except (AttributeError, IndexError, ValueError):
            continue
    return fixed


# ---------------------------------------------------------------------------
# Cobertura do pedido

TOPICS_SYSTEM = """Liste os tópicos que o PEDIDO exige explicitamente que a apresentação trate.
- Só o que está escrito no pedido (comparações pedidas, aspectos a discutir, exemplos e
  recomendações pedidas). Não acrescente tópicos.
- "nome": 1 a 4 palavras. "termos": 1 a 4 palavras ou radicais que, aparecendo no slide,
  mostram que o tópico foi tratado (inclua sinônimos e a forma em inglês, se comum).
- Pedido curto e genérico: devolva lista vazia.
Responda só JSON."""


def topics_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "topicos": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string", "minLength": 2, "maxLength": 60},
                        "termos": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string", "minLength": 2, "maxLength": 40},
                        },
                    },
                    "required": ["nome", "termos"],
                },
            }
        },
        "required": ["topicos"],
    }


def extract_topics(call: Call, request: str) -> list[dict]:
    if len(request.split()) < 15:
        return []
    raw = call(stage="topicos", slide=None, system=TOPICS_SYSTEM,
               user=f"PEDIDO:\n{request}", schema=topics_schema())
    match = re.search(r"\{.*\}", raw or "", re.S)
    data = json.loads(match.group(0) if match else raw)
    topics, seen = [], set()
    for t in data.get("topicos", []):
        name = (t.get("nome") or "").strip()
        terms = [x.strip() for x in t.get("termos", []) if x.strip()] or [name]
        if name and normalize(name) not in seen:
            seen.add(normalize(name))
            topics.append({"nome": name, "termos": list(dict.fromkeys([name, *terms]))[:5]})
    return topics


def covers(text: str, terms: list[str]) -> bool:
    words = normalize(text).split()
    for term in terms:
        parts = normalize(term).split()
        if not parts:
            continue
        stem = [p[: max(4, len(p) - 2)] if len(p) > 5 else p for p in parts]
        for k in range(len(words) - len(stem) + 1):
            if all(words[k + j].startswith(stem[j]) for j in range(len(stem))):
                return True
    return False


def visible_text(slide: AltoSlide) -> str:
    parts = [slide.title, slide.subtitle, slide.text, slide.caption, slide.unit]
    parts += [f"{i.label} {i.detail or ''}" for i in slide.items]
    parts += [f"{v.value} {v.label}" for v in slide.values]
    parts += [f"{s.name} " + " ".join(f"{i.label} {i.detail or ''}" for i in s.items)
              for s in slide.sides]
    parts += [f"{m.date} {m.label} {m.detail or ''}" for m in slide.milestones]
    parts += [b.label for b in slide.bars]
    return " ".join(p for p in parts if p)


def coverage_diagnostics(slide: AltoSlide, topics: list[dict], slide_number: int):
    text = visible_text(slide)
    return [
        Diagnostic(
            code="A016",
            severity="AVISO",
            message=f"O slide deveria tratar de '{t['nome']}', pedido explicitamente.",
            slide=slide_number,
            evidence={"path": "slides.0.items", "termos": t["termos"]},
            suggestion=f"Inclua no texto visível um item sobre {t['nome']} "
            f"(use uma destas palavras: {', '.join(t['termos'][:3])}).",
        )
        for t in topics
        if not covers(text, t["termos"])
    ]


def coverage_report(slides: list[AltoSlide], topics: list[dict]) -> list[dict]:
    report = []
    for t in topics:
        visible = [k + 1 for k, s in enumerate(slides) if covers(visible_text(s), t["termos"])]
        notes = [k + 1 for k, s in enumerate(slides) if covers(s.notes or "", t["termos"])]
        report.append({"topico": t["nome"], "slides_visiveis": visible, "slides_notas": notes,
                       "coberto": bool(visible)})
    return report


# ---------------------------------------------------------------------------
# Truncamento pelo decoder e citação literal


def truncated_paths(data, schema: dict, path: str = "") -> list[str]:
    """Campos cujo texto tem exatamente o maxLength do schema: o decoder cortou a frase."""
    found = []
    kind = schema.get("type")
    if kind == "string" and isinstance(data, str):
        limit = schema.get("maxLength")
        if limit and len(data) >= limit:
            found.append(path)
    elif kind == "object" and isinstance(data, dict):
        for key, sub in schema.get("properties", {}).items():
            if key in data:
                found += truncated_paths(data[key], sub, f"{path}.{key}" if path else key)
    elif kind == "array" and isinstance(data, list):
        for k, item in enumerate(data):
            found += truncated_paths(item, schema.get("items", {}), f"{path}[{k}]")
    return found


def quote_candidates(facts: dict, preferred: list[str] | None = None) -> list[str]:
    ids = [i for i in (preferred or []) if i in facts] + [i for i in facts if i not in (preferred or [])]
    return [
        i
        for i in ids
        if facts[i].get("kind") == "citacao"
        and (facts[i].get("author") or "").strip()
        and 10 <= len(facts[i].get("quote", "")) <= 260
    ]


def quote_slide(facts: dict, preferred: list[str] | None, notes: str | None = None):
    """Slide de citação montado do trecho literal; None se não houver citação atribuída."""
    ids = quote_candidates(facts, preferred)
    if not ids:
        return None
    f = facts[ids[0]]
    return AltoSlide(
        kind="citacao",
        text=f["quote"].strip().strip('"“”'),
        author=f["author"].strip(),
        sources=[ids[0]],
        notes=notes,
    )
