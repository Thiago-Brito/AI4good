"""Pesquisa na internet para dar substância aos slides gerados por SLMs.

Fluxo: pedido → consultas → busca (Wikipedia sem chave; Brave, Tavily ou SearXNG
opcionais) → leitura das páginas → trechos relevantes → fichas de fatos.

Um SLM lembra pouco e alucina quando tenta lembrar; em compensação, extrai bem
informações de um trecho curto. Por isso cada chamada recebe um único trecho, e toda
ficha precisa trazer um `trecho` copiado literalmente da página: fichas cujo trecho
não é encontrado no texto (ou cujo número não aparece nele) são descartadas.

O compilador continua offline: a pesquisa só produz um dossiê JSON com fatos e URLs.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlencode, urlsplit

from .paths import project_root

FACT_KINDS = ["numero", "data", "exemplo", "definicao", "comparacao", "ressalva", "citacao"]
STOPWORDS = set(
    """a o e é de do da dos das em no na nos nas um uma uns umas para por com sem sobre como que
    se ao aos à às ou mais menos muito seu sua seus suas ser são foi era entre também quando
    the of and to in is for on with as by an are be or from at this that it its which""".split()
)


# ---------------------------------------------------------------------------
# Modelo de dados


@dataclass
class Source:
    id: str
    title: str
    url: str
    provider: str
    text: str = ""
    snippet: str = ""


@dataclass
class Fact:
    id: str
    claim: str
    kind: str
    quote: str
    source_id: str
    url: str
    source_title: str
    value: str = ""
    author: str = ""
    relevance: str = ""


@dataclass
class Dossier:
    topic: str
    queries: list[str] = field(default_factory=list)
    sources: list[Source] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    central_terms: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def fact_map(self) -> dict[str, dict]:
        return {f.id: asdict(f) for f in self.facts}

    def to_json(self, include_text: bool = False) -> dict:
        data = asdict(self)
        if not include_text:
            for s in data["sources"]:
                s["text_chars"] = len(s.pop("text"))
        return data

    def save(self, path: Path, include_text: bool = False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_json(include_text), ensure_ascii=False, indent=2) + "\n", "utf-8"
        )

    @classmethod
    def load(cls, path: Path) -> "Dossier":
        data = json.loads(Path(path).read_text("utf-8"))
        sources = []
        for s in data.get("sources", []):
            s.pop("text_chars", None)
            sources.append(Source(**s))
        return cls(
            topic=data["topic"],
            queries=data.get("queries", []),
            sources=sources,
            facts=[Fact(**f) for f in data.get("facts", [])],
            rejected=data.get("rejected", []),
            log=data.get("log", []),
            central_terms=data.get("central_terms", []),
            created_at=data.get("created_at", ""),
        )

    def prompt_block(self, limit: int = 40) -> str:
        """Fichas no formato compacto usado nos prompts do SLM."""
        lines = []
        for f in self.facts[:limit]:
            value = f" [valor: {f.value}]" if f.value else ""
            lines.append(f"{f.id} ({f.kind}){value}: {f.claim} — fonte: {f.source_title}")
        return "\n".join(lines) or "(nenhum fato encontrado)"


# ---------------------------------------------------------------------------
# Rede (sempre por media.fetch_public, que bloqueia IPs internos) e cache


Fetcher = Callable[..., tuple[bytes, str]]


def default_fetcher(url, **kw):
    from .media import fetch_public

    return fetch_public(url, **kw)


def cache_dir() -> Path:
    custom = os.environ.get("SLIDEDSL_RESEARCH_CACHE")
    return Path(custom) if custom else project_root() / "outputs/research/cache"


def decode_body(body: bytes) -> str:
    """UTF-8 quando válido; senão o charset declarado no HTML; senão Windows-1252."""
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        pass
    head = body[:4096].decode("ascii", errors="ignore")
    match = re.search(r"charset=[\"']?([\w-]+)", head, re.I)
    for encoding in ([match.group(1)] if match else []) + ["cp1252", "latin-1"]:
        try:
            return body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace")


def cached_fetch(fetcher: Fetcher, url: str, *, offline=False, **kw) -> tuple[bytes, str]:
    key = hashlib.sha256((url + json.dumps(kw.get("body"), sort_keys=True)).encode()).hexdigest()
    path = cache_dir() / f"{key}.json"
    if path.is_file():
        data = json.loads(path.read_text("utf-8"))
        return data["body"].encode("utf-8"), data["mime"]
    if offline:
        raise ValueError(f"Sem cache para {url} no modo offline.")
    body, mime = fetcher(url, **kw)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = decode_body(body)
    path.write_text(json.dumps({"url": url, "mime": mime, "body": text}), "utf-8")
    return text.encode("utf-8"), mime


# ---------------------------------------------------------------------------
# Texto


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[“”«»\"']", "", value)
    return re.sub(r"\s+", " ", value).strip()


def terms(value: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9]+", normalize(value)) if t not in STOPWORDS and len(t) > 2
    }


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"}
    BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "td", "th", "blockquote", "figcaption", "dd"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.parts: list[str] = []
        self.current: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.depth += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.depth:
            self.depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self._flush()

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.depth:
            self.current.append(data)

    def _flush(self):
        text = re.sub(r"\s+", " ", "".join(self.current)).strip()
        if len(text) > 40:
            self.parts.append(text)
        self.current = []


def html_to_text(html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(html)
    parser._flush()
    return parser.title.strip(), "\n\n".join(parser.parts)


def passages(text: str, size: int = 900) -> list[str]:
    """Agrupa parágrafos em trechos de ~size caracteres, sem cortar frases."""
    out, current = [], ""
    for paragraph in re.split(r"\n\s*\n|\n(?==)", text):
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if not paragraph or paragraph.startswith("=="):
            continue
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        for sentence in sentences:
            if current and len(current) + len(sentence) > size:
                out.append(current)
                current = ""
            current = f"{current} {sentence}".strip()
        if len(current) > size * 0.6:
            out.append(current)
            current = ""
    if current:
        out.append(current)
    return [p for p in out if len(p) > 80]


def rank_passages(items: list[str], query: str, limit: int) -> list[str]:
    wanted = terms(query)

    def score(p):
        found = terms(p)
        overlap = len(wanted & found) / (len(wanted) or 1)
        numbers = min(3, len(re.findall(r"\b\d[\d.,]*\b", p))) * 0.08
        return overlap + numbers

    ranked = sorted(enumerate(items), key=lambda x: (-score(x[1]), x[0]))
    return [p for _, p in ranked[:limit] if score(p) > 0]


# ---------------------------------------------------------------------------
# Buscadores


SEARXNG_DEFAULT = "http://127.0.0.1:8888"


def searxng_url() -> str | None:
    """URL configurada ou, sem configuração, a instância local do projeto (searxng/)."""
    configured = os.environ.get("SLIDEDSL_SEARXNG_URL", "").rstrip("/")
    if configured:
        return configured
    import httpx

    try:
        with httpx.Client(timeout=0.8, trust_env=False) as client:
            if client.get(SEARXNG_DEFAULT + "/healthz").status_code == 200:
                return SEARXNG_DEFAULT
    except httpx.HTTPError:
        pass
    return None


def provider_auto() -> str:
    """O projeto usa o SearXNG local como buscador padrão (decisão de 12/10/2026).

    Tavily, Brave e Wikipedia continuam implementados para experimentos comparativos,
    mas só são usados quando pedidos explicitamente."""
    return "searxng"


def searxng_status() -> dict:
    url = searxng_url()
    if not url:
        return {"ok": False, "url": SEARXNG_DEFAULT,
                "message": "SearXNG não encontrado. Rode scripts\\iniciar_searxng.cmd."}
    import httpx

    try:
        with httpx.Client(timeout=20, trust_env=False) as client:
            response = client.get(url + "/search", params={"q": "teste", "format": "json"})
        if response.status_code == 403:
            return {"ok": False, "url": url,
                    "message": "SearXNG recusou JSON (403): ative 'json' em search.formats."}
        response.raise_for_status()
        count = len(response.json().get("results", []))
        return {"ok": count > 0, "url": url, "results": count,
                "message": f"SearXNG respondeu com {count} resultados de teste."
                if count else "SearXNG respondeu sem resultados (buscadores bloqueando?)."}
    except httpx.TimeoutException:
        return {"ok": False, "url": url,
                "message": "SearXNG demorou mais de 20 s (buscadores lentos ou bloqueando)."}
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "url": url, "message": f"SearXNG com erro: {exc}"}


def _json(fetcher, url, offline, **kw):
    body, _ = cached_fetch(fetcher, url, offline=offline, allowed={"application/json"}, **kw)
    return json.loads(body)


def search_wikipedia(query, *, lang="pt", limit=3, fetcher=default_fetcher, offline=False):
    base = f"https://{lang}.wikipedia.org/w/api.php?"
    found = _json(
        fetcher,
        base
        + urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "format": "json",
                "utf8": 1,
            }
        ),
        offline,
    )
    results = []
    for hit in found.get("query", {}).get("search", [])[:limit]:
        title = hit["title"]
        page = _json(
            fetcher,
            base
            + urlencode(
                {
                    "action": "query",
                    "prop": "extracts",
                    "explaintext": 1,
                    "redirects": 1,
                    "titles": title,
                    "format": "json",
                    "utf8": 1,
                }
            ),
            offline,
        )
        pages = page.get("query", {}).get("pages", {})
        text = next(iter(pages.values()), {}).get("extract", "") if pages else ""
        results.append(
            {
                "title": f"{title} — Wikipédia ({lang})",
                "url": f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}",
                "text": text,
                "snippet": re.sub(r"<[^>]+>", "", hit.get("snippet", "")),
            }
        )
    return results


def search_brave(query, *, limit=4, fetcher=default_fetcher, offline=False):
    key = os.environ.get("BRAVE_API_KEY")
    if not key:
        raise ValueError("Defina BRAVE_API_KEY para usar a busca Brave.")
    data = _json(
        fetcher,
        "https://api.search.brave.com/res/v1/web/search?"
        + urlencode({"q": query, "count": limit, "search_lang": "pt-br"}),
        offline,
        headers={"X-Subscription-Token": key, "Accept": "application/json"},
    )
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])[:limit]
    ]


def search_tavily(query, *, limit=4, fetcher=default_fetcher, offline=False):
    key = os.environ.get("TAVILY_API_KEY")
    if not key:
        raise ValueError("Defina TAVILY_API_KEY para usar a busca Tavily.")
    data = _json(
        fetcher,
        "https://api.tavily.com/search",
        offline,
        method="POST",
        body={"api_key": key, "query": query, "max_results": limit, "include_raw_content": True},
        headers={"Content-Type": "application/json"},
    )
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
            "text": r.get("raw_content") or r.get("content", ""),
        }
        for r in data.get("results", [])[:limit]
    ]


def search_searxng(query, *, limit=4, fetcher=None, offline=False):
    """SearXNG local configurado explicitamente pelo usuário (pode ser 127.0.0.1)."""
    import httpx

    base = searxng_url()
    if not base:
        raise ValueError(
            "SearXNG não encontrado em 127.0.0.1:8888. Rode scripts\\iniciar_searxng.cmd "
            "ou defina SLIDEDSL_SEARXNG_URL."
        )
    if fetcher is not None and fetcher is not default_fetcher:
        body, _ = fetcher(f"{base}/search?" + urlencode({"q": query, "format": "json"}))
        data = json.loads(body)
    else:
        try:
            with httpx.Client(timeout=30, trust_env=False) as client:
                response = client.get(f"{base}/search", params={"q": query, "format": "json"})
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise ValueError(
                "SearXNG não respondeu em 30 s (os buscadores que ele consulta podem estar "
                "bloqueando ou lentos). Veja: docker logs slidedsl-searxng"
            ) from exc
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in data.get("results", [])[:limit]
    ]


def read_page(url, *, fetcher=default_fetcher, offline=False) -> tuple[str, str]:
    body, mime = cached_fetch(
        fetcher,
        url,
        offline=offline,
        allowed={"text/html", "application/xhtml+xml", "text/plain"},
        limit=3 * 1024 * 1024,
    )
    text = body.decode("utf-8", errors="replace")
    if mime == "text/plain":
        return "", text
    return html_to_text(text)


def search(
    query, provider="auto", *, langs=("pt", "en"), limit=3, fetcher=default_fetcher, offline=False
) -> list[dict]:
    provider = provider_auto() if provider == "auto" else provider
    if provider == "wikipedia":
        results = []
        for lang in langs:
            results += search_wikipedia(
                query, lang=lang, limit=limit, fetcher=fetcher, offline=offline
            )
        return results
    fn = {"brave": search_brave, "tavily": search_tavily, "searxng": search_searxng}[provider]
    results = fn(query, limit=limit, fetcher=fetcher, offline=offline)
    for r in results:
        if not r.get("text") and urlsplit(r.get("url", "")).scheme == "https":
            try:
                title, text = read_page(r["url"], fetcher=fetcher, offline=offline)
                r["text"] = text
                r["title"] = r.get("title") or title
            except Exception as exc:  # página inacessível não interrompe a pesquisa
                r["error"] = str(exc)
                r["text"] = r.get("snippet", "")
    return results


# ---------------------------------------------------------------------------
# Extração de fatos


QUERY_SYSTEM = """Você planeja pesquisas na web para montar uma apresentação.
Gere de 3 a 5 consultas CURTAS (2 a 6 palavras), em português ou inglês, que tragam:
definição do tema, números/dados, exemplos reais (empresas, casos, datas) e limitações.
Foque no ASSUNTO CENTRAL do pedido. Palavras de contexto (público, cenário, "para uma
startup", "para iniciantes") só entram como complemento, nunca como assunto da busca.
"assunto_central": o assunto em poucas palavras (ex.: "arquitetura monolítica vs
microsserviços"). "termos_centrais": 2 a 6 palavras que TODO fato útil deve mencionar
(inclua variações e a forma em inglês, ex.: "monolito", "monolítica", "microsserviços",
"microservices"). Não inclua palavras de contexto como "startup" ou "empresa".
Não use aspas nem operadores. Responda só JSON."""

EXTRACT_SYSTEM = """Você extrai fatos verificáveis de UM trecho de texto para slides.
Regras:
- Use SOMENTE o que está escrito no trecho. Não complete com conhecimento próprio.
- "trecho" deve ser uma cópia LITERAL de uma frase do texto (sem alterar palavras).
- "afirmacao" resume o fato em português, em até 25 palavras, com o dado concreto.
- "valor" é o número/data principal (ex.: "90%", "2014", "1.000"), ou "" se não houver.
- "afirmacao" é uma frase completa (sujeito + verbo + dado), nunca um nome solto.
- Mantenha o sujeito exato: se o texto fala de "a plataforma", não escreva "o mercado".
- "tipo": "citacao" é RARO: só quando o trecho mostra entre aspas uma frase dita por uma
  pessoa nomeada; "autor" é o nome como aparece no texto. Afirmações de um artigo ou site
  NÃO são citações (use "definicao", "exemplo", "numero"...). Fora de citações, "autor" = "".
- "relevancia": "alta" se o fato ajuda a explicar o ASSUNTO CENTRAL do tema; "baixa" se
  só tem uma palavra em comum (ex.: estatística de mercado num tema técnico).
- Prefira números, datas, exemplos nomeados e ressalvas; ignore generalidades.
- Se o trecho não tiver nada útil para o tema, devolva lista vazia.
Responda só JSON."""


def query_schema():
    return {
        "type": "object",
        "properties": {
            "assunto_central": {"type": "string", "minLength": 3, "maxLength": 120},
            "termos_centrais": {
                "type": "array",
                "minItems": 1,
                "maxItems": 6,
                "items": {"type": "string", "minLength": 3, "maxLength": 40},
            },
            "consultas": {
                "type": "array",
                "minItems": 2,
                "maxItems": 5,
                "items": {"type": "string", "minLength": 3, "maxLength": 120},
            },
        },
        "required": ["assunto_central", "termos_centrais", "consultas"],
    }


def extract_schema():
    return {
        "type": "object",
        "properties": {
            "fatos": {
                "type": "array",
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        # Limites folgados: o decoder corta a frase ao atingir maxLength.
                        "afirmacao": {"type": "string", "minLength": 10, "maxLength": 500},
                        "tipo": {"type": "string", "enum": FACT_KINDS},
                        "valor": {"type": "string", "maxLength": 40},
                        "trecho": {"type": "string", "minLength": 10, "maxLength": 900},
                        "autor": {"type": "string", "maxLength": 120},
                        "relevancia": {"type": "string", "enum": ["alta", "media", "baixa"]},
                    },
                    "required": ["afirmacao", "tipo", "valor", "trecho", "autor", "relevancia"],
                },
            }
        },
        "required": ["fatos"],
    }


def _generate_json(model, system, user, schema, seed=None):
    try:
        raw = model.generate(system, user, temperature=0, seed=seed, response_schema=schema)
    except TypeError:  # modelos sem suporte a schema
        raw = model.generate(system, user, temperature=0, seed=seed)
    match = re.search(r"\{.*\}", raw, re.S)
    return json.loads(match.group(0) if match else raw)


def plan_queries(topic: str, model=None, max_queries: int = 4) -> list[str]:
    return plan_research(topic, model, max_queries)[0]


def plan_research(topic: str, model=None, max_queries: int = 4) -> tuple[list[str], list[str]]:
    """(consultas, termos centrais). Sem modelo, consultas heurísticas e sem filtro."""
    base = re.sub(r"\s+", " ", topic).strip()[:200]
    if model is None:
        core = " ".join(
            list(
                dict.fromkeys(
                    t
                    for t in re.findall(r"\w+", base)
                    if t.casefold() not in STOPWORDS and len(t) > 3
                )
            )[:5]
        )
        queries = list(dict.fromkeys([core or base, f"{core} história", f"{core} exemplos"]))
        return queries[:max_queries], []
    data = _generate_json(model, QUERY_SYSTEM, f"Tema da apresentação: {base}", query_schema())
    queries = [q.strip() for q in data.get("consultas", []) if q.strip()]
    terms = [t.strip() for t in data.get("termos_centrais", []) if len(t.strip()) >= 3]
    # Termos centrais precisam vir do próprio pedido (ou ser variação dele) para não
    # filtrar com palavras que o modelo inventou.
    from .alto_quality import covers

    terms = [t for t in terms if covers(base, [t]) or any(covers(t, [w]) for w in base.split()
                                                           if len(w) > 4)]
    return list(dict.fromkeys(queries))[:max_queries] or [base], list(dict.fromkeys(terms))


def quote_found(quote_text: str, passage: str) -> bool:
    q, p = normalize(quote_text), normalize(passage)
    if len(q) < 10:
        return False
    if q in p:
        return True
    match = SequenceMatcher(None, p, q, autojunk=False).find_longest_match(0, len(p), 0, len(q))
    return match.size >= 0.85 * len(q)


def verify_fact(item: dict, passage: str, central_terms: list[str] | None = None) -> str | None:
    """Retorna o motivo da rejeição, ou None se a ficha estiver ancorada no trecho.

    Pode ajustar `item` (ex.: "citacao" sem autor no texto vira "definicao")."""
    from .alto import number_tokens
    from .alto_quality import covers

    quote_text = (item.get("trecho") or "").strip()
    claim = (item.get("afirmacao") or "").strip()
    if not quote_found(quote_text, passage):
        return "trecho não encontrado literalmente no texto"
    if re.search(r"(\.\.\.|…)\s*$", quote_text) or "\ufffd" in quote_text + claim:
        return "trecho incompleto ou com caracteres inválidos"
    if len(claim.split()) < 6:
        return "afirmação incompleta (menos de 6 palavras)"
    if item.get("relevancia") == "baixa":
        return "pouco relevante para o assunto central"
    if number_tokens(item.get("valor", "")) - number_tokens(quote_text):
        return "valor não aparece no trecho citado"
    if number_tokens(claim) - number_tokens(passage):
        return "número da afirmação não está no texto"
    if central_terms and not covers(claim + " " + quote_text, central_terms):
        return "fora do assunto central (não menciona " + ", ".join(central_terms[:3]) + ")"
    if item.get("tipo") == "citacao":
        author = (item.get("autor") or "").strip()
        if not author or normalize(author) not in normalize(passage):
            # Não é uma citação atribuível: continua valendo como fato comum.
            item["tipo"], item["autor"] = "definicao", ""
    return None


def heuristic_facts(passage: str) -> list[dict]:
    """Extração sem modelo: frases com números ou definições (modo offline/testes)."""
    out = []
    for sentence in re.split(r"(?<=[.!?])\s+", passage):
        sentence = sentence.strip()
        if not 40 <= len(sentence) <= 300:
            continue
        number = re.search(r"\b\d[\d.,]*\s?%?", sentence)
        definition = re.search(r"\b(é|são|consiste|refere-se|is|are)\b", sentence)
        if number or definition:
            out.append(
                {
                    "afirmacao": sentence,
                    "tipo": "numero" if number else "definicao",
                    "valor": number.group(0).strip() if number else "",
                    "trecho": sentence,
                }
            )
        if len(out) >= 3:
            break
    return out


def _add_sources(dossier, results, seen_urls, provider):
    for r in results:
        if not r.get("url") or r["url"] in seen_urls or not r.get("text"):
            continue
        seen_urls.add(r["url"])
        dossier.sources.append(
            Source(
                id=f"S{len(dossier.sources) + 1}",
                title=r.get("title", "")[:160],
                url=r["url"],
                provider=provider,
                text=r["text"][:200_000],
                snippet=r.get("snippet", "")[:300],
            )
        )


def research(
    topic: str,
    *,
    model=None,
    provider: str = "searxng",
    langs=("pt", "en"),
    max_queries: int = 4,
    results_per_query: int = 2,
    passages_per_source: int = 2,
    max_passages: int = 10,
    max_facts: int = 24,
    max_facts_per_source: int = 5,
    fetcher: Fetcher = default_fetcher,
    offline: bool = False,
    progress: Callable[[str], None] | None = None,
    contact: str | None = None,
    fallback_wikipedia: bool = False,
) -> Dossier:
    say = progress or (lambda message: None)
    if contact or os.environ.get("SLIDEDSL_CONTACT"):
        from .media import user_agent

        base_fetcher, agent = fetcher, user_agent(contact)

        def fetcher(url, **kw):  # noqa: F811 — injeta o User-Agent com contato
            kw["headers"] = {**(kw.get("headers") or {}), "User-Agent": agent}
            return base_fetcher(url, **kw)

    dossier = Dossier(topic=topic)
    provider = provider_auto() if provider == "auto" else provider
    say(f"Buscador: {provider}")
    dossier.queries, dossier.central_terms = plan_research(topic, model, max_queries)
    if dossier.central_terms:
        say(f"Termos centrais: {dossier.central_terms}")
    say(f"Consultas: {dossier.queries}")
    seen_urls = set()
    providers = [provider] + (["wikipedia"] if fallback_wikipedia and provider != "wikipedia" else [])
    for current in providers:
        failures = 0
        for query in dossier.queries:
            try:
                results = search(
                    query,
                    current,
                    langs=langs,
                    limit=results_per_query,
                    fetcher=fetcher,
                    offline=offline,
                )
            except Exception as exc:
                failures += 1
                dossier.log.append({"query": query, "provider": current, "error": str(exc)})
                say(f"Busca falhou ({current}): {str(exc)[:120]}")
                # Buscador fora do ar: não espera o timeout de todas as consultas.
                if failures >= 2 and not dossier.sources:
                    break
                continue
            dossier.log.append({"query": query, "provider": current, "results": len(results)})
            _add_sources(dossier, results, seen_urls, current)
        if dossier.sources:
            break
        if current != providers[-1]:
            say(f"{current} não trouxe fontes; tentando a Wikipedia")
    ranked = [
        [
            (source, p)
            for p in rank_passages(
                passages(source.text), topic + " " + " ".join(dossier.queries), passages_per_source
            )
        ]
        for source in dossier.sources
    ]
    # Intercala fontes (1º trecho de cada uma, depois o 2º...) para não depender de uma página.
    selected = [
        pair
        for rank in range(passages_per_source)
        for group in ranked
        if rank < len(group)
        for pair in [group[rank]]
    ][:max_passages]
    say(f"{len(dossier.sources)} fontes, {len(selected)} trechos selecionados")
    seen_claims = set()
    per_source: dict[str, int] = {}
    for source, passage in selected:
        if model is None:
            items = heuristic_facts(passage)
        else:
            try:
                items = _generate_json(
                    model,
                    EXTRACT_SYSTEM,
                    f"Tema: {topic}\nFonte: {source.title}\n\nTRECHO:\n{passage}",
                    extract_schema(),
                ).get("fatos", [])
            except Exception as exc:
                dossier.log.append({"source": source.id, "error": f"extração: {exc}"})
                continue
        for item in items:
            reason = verify_fact(item, passage, dossier.central_terms)
            key = normalize(item.get("afirmacao", ""))
            if not reason and per_source.get(source.id, 0) >= max_facts_per_source:
                reason = f"limite de {max_facts_per_source} fatos por fonte"
            if reason or key in seen_claims:
                dossier.rejected.append(
                    {**item, "source_id": source.id, "reason": reason or "duplicada"}
                )
                continue
            seen_claims.add(key)
            dossier.facts.append(
                Fact(
                    id=f"F{len(dossier.facts) + 1}",
                    claim=item["afirmacao"].strip(),
                    kind=item.get("tipo", "definicao"),
                    value=item.get("valor", "").strip(),
                    quote=item["trecho"].strip(),
                    source_id=source.id,
                    url=source.url,
                    source_title=source.title,
                    author=(item.get("autor") or "").strip() if item.get("tipo") == "citacao" else "",
                    relevance=item.get("relevancia", ""),
                )
            )
            per_source[source.id] = per_source.get(source.id, 0) + 1
            if len(dossier.facts) >= max_facts:
                break
        if len(dossier.facts) >= max_facts:
            break
    distinct = len({f.source_id for f in dossier.facts})
    say(
        f"{len(dossier.facts)} fatos verificados de {distinct} fontes, "
        f"{len(dossier.rejected)} descartados"
    )
    if dossier.facts and (len(dossier.facts) < 4 or distinct < 2):
        say("Atenção: poucos fatos ou uma única fonte; slides sem fato serão qualitativos.")
        dossier.log.append({"warning": "poucos fatos ou fonte única", "facts": len(dossier.facts),
                            "sources": distinct})
    return dossier
