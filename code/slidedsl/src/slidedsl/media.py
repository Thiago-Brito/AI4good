"""Optional public API search and bounded, IP-pinned downloads; no compiler networking."""

from datetime import datetime, timezone
import hashlib
import html
from io import BytesIO
import ipaddress
import json
import re
import socket
import time
from urllib.parse import urlencode, urljoin, urlsplit

import httpx
from PIL import Image

from .paths import project_root

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 20_000_000
AGENT = "SlideDSL/1.1 (local educational presentation tool; limited interactive search)"
NASA_TERMS = "https://www.nasa.gov/nasa-brand-center/images-and-media/"


def public_target(url, resolver=socket.getaddrinfo):
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
        or parsed.fragment
    ):
        raise ValueError(
            "Use uma URL pública HTTPS sem credenciais, fragmento ou porta alternativa."
        )
    addresses = {r[4][0] for r in resolver(parsed.hostname, 443, type=socket.SOCK_STREAM)}
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ValueError("Endereço interno, reservado ou não público bloqueado.")
    return parsed, sorted(addresses)[0]


def fetch_public(url, *, limit=MAX_BYTES, json_only=False):
    """Validate every redirect and connect to the checked IP (including TLS SNI)."""
    started = time.monotonic()
    for _ in range(4):
        parsed, address = public_target(url)
        host = parsed.hostname
        pinned = httpx.URL(url).copy_with(host=address)
        with httpx.Client(timeout=10, trust_env=False, follow_redirects=False) as client:
            with client.stream(
                "GET",
                pinned,
                headers={"Host": host, "User-Agent": AGENT, "Accept-Encoding": "identity"},
                extensions={"sni_hostname": host},
            ) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    url = urljoin(url, response.headers.get("location", ""))
                    continue
                response.raise_for_status()
                mime = response.headers.get("content-type", "").split(";")[0].lower()
                allowed = {"application/json"} if json_only else {"image/png", "image/jpeg"}
                if mime not in allowed:
                    raise ValueError(f"MIME não permitido: {mime}")
                length = response.headers.get("content-length")
                if length and int(length) > limit:
                    raise ValueError("Download excede o limite.")
                data = bytearray()
                for block in response.iter_bytes():
                    if len(data) + len(block) > limit or time.monotonic() - started > 25:
                        raise ValueError("Download excede tamanho ou tempo permitido.")
                    data.extend(block)
                return bytes(data), mime
    raise ValueError("Redirecionamentos demais.")


def clean(value):
    return html.unescape(re.sub(r"<[^>]*>", "", str(value or "")))[:2000]


def api_json(url):
    data, _ = fetch_public(url, limit=2 * 1024 * 1024, json_only=True)
    return json.loads(data)


def _candidate(provider, title, url, page, author, license, license_url, **extra):
    if urlsplit(page).scheme not in {"http", "https"} or urlsplit(license_url).scheme not in {
        "http",
        "https",
    }:
        raise ValueError("Metadados de origem/licença devem conter links web válidos.")
    return {
        "id": hashlib.sha256((provider + url).encode()).hexdigest(),
        "provider": provider,
        "title": clean(title),
        "url": url,
        "page": page,
        "author": clean(author),
        "license": license,
        "license_url": license_url,
        "attribution": f"{clean(title)} — {clean(author)} — {license}",
        **extra,
    }


def search_provider(provider, query):
    if not query.strip() or len(query) > 200:
        raise ValueError("Consulta deve conter de 1 a 200 caracteres.")
    if provider == "openverse":
        data = api_json(
            "https://api.openverse.org/v1/images/?"
            + urlencode(
                {
                    "q": query,
                    "page_size": 8,
                    "license": "by,by-sa,cc0,pdm",
                    "extension": "jpg,png",
                    "mature": "false",
                }
            )
        )
        return [
            _candidate(
                provider,
                i["title"],
                i["url"],
                i["foreign_landing_url"],
                i.get("creator"),
                i["license"],
                i.get("license_url", ""),
                width=i.get("width"),
                height=i.get("height"),
            )
            for i in data.get("results", [])
            if i.get("license") in {"by", "by-sa", "cc0", "pdm"}
        ]
    if provider == "commons":
        data = api_json(
            "https://commons.wikimedia.org/w/api.php?"
            + urlencode(
                {
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": query,
                    "gsrnamespace": 6,
                    "gsrlimit": 8,
                    "prop": "imageinfo",
                    "iiprop": "url|size|mime|extmetadata",
                    "iiurlwidth": 1200,
                }
            )
        )
        result = []
        for page in data.get("query", {}).get("pages", {}).values():
            i = page.get("imageinfo", [{}])[0]
            meta = {k: clean(v.get("value")) for k, v in i.get("extmetadata", {}).items()}
            license_url = meta.get("LicenseUrl", "")
            if i.get("mime") not in {"image/png", "image/jpeg"} or not reusable(license_url):
                continue
            result.append(
                _candidate(
                    provider,
                    page["title"],
                    i.get("thumburl", i["url"]),
                    i["descriptionurl"],
                    meta.get("Artist"),
                    meta.get("LicenseShortName", ""),
                    license_url,
                    width=i.get("thumbwidth", i.get("width")),
                    height=i.get("thumbheight", i.get("height")),
                )
            )
        return result
    if provider == "nasa":
        data = api_json(
            "https://images-api.nasa.gov/search?"
            + urlencode(
                {
                    "q": query,
                    "media_type": "image",
                    "page_size": 8,
                }
            )
        )
        result = []
        for entry in data.get("collection", {}).get("items", [])[:8]:
            i = entry["data"][0]
            links = [
                link["href"] for link in entry.get("links", []) if link.get("render") == "image"
            ]
            if links:
                result.append(
                    _candidate(
                        provider,
                        i["title"],
                        links[0],
                        "https://images.nasa.gov/details/" + i["nasa_id"],
                        i.get("photographer", i.get("center", "NASA")),
                        "NASA media guidelines — revisão individual",
                        NASA_TERMS,
                        review_required=True,
                        description=clean(i.get("description")),
                    )
                )
        return result
    raise ValueError("Provedor desconhecido.")


def reusable(url):
    parsed = urlsplit(url)
    return parsed.hostname in {"creativecommons.org", "www.creativecommons.org"} and (
        parsed.path.startswith(
            ("/licenses/by/", "/licenses/by-sa/", "/publicdomain/zero/", "/publicdomain/mark/")
        )
    )


def store_root():
    return project_root() / "outputs/media"


def safe_id(value):
    if not re.fullmatch(r"[a-f0-9]{64}", value):
        raise ValueError("Identificador inválido.")
    return value


def search_images(provider, query, *, offline=False):
    folder = store_root() / "searches"
    folder.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256((provider + query).encode()).hexdigest()
    cache = folder / f"{key}.json"
    if offline:
        return {
            "results": json.loads(cache.read_text("utf-8")) if cache.exists() else [],
            "offline": True,
        }
    # At most one interactive search per provider every two seconds, plus a cache.
    if cache.exists() and time.time() - cache.stat().st_mtime < 3600:
        return {"results": json.loads(cache.read_text("utf-8")), "cached": True}
    recent = store_root() / f"{provider}.stamp"
    if recent.exists() and time.time() - recent.stat().st_mtime < 2:
        raise ValueError("Aguarde dois segundos entre buscas neste provedor.")
    recent.touch()
    results = search_provider(provider, query)
    words = set(re.findall(r"\w+", query.casefold()))
    for result in results:
        terms = set(re.findall(r"\w+", result["title"].casefold()))
        result["lexical_score"] = len(words & terms) / max(1, len(words))
        candidates = store_root() / "candidates"
        candidates.mkdir(exist_ok=True)
        (candidates / f"{result['id']}.json").write_text(
            json.dumps(result, ensure_ascii=False), "utf-8"
        )
    results.sort(key=lambda i: i["lexical_score"], reverse=True)
    cache.write_text(json.dumps(results, ensure_ascii=False), "utf-8")
    return {"results": results, "offline": False, "ranking": "lexical; relevance requires review"}


def cache_image(id, *, reviewed=False):
    id = safe_id(id)
    target = store_root() / "assets" / f"{id}.json"
    if target.exists():
        return json.loads(target.read_text("utf-8"))
    candidate = json.loads((store_root() / "candidates" / f"{id}.json").read_text("utf-8"))
    if candidate["provider"] == "nasa":
        if not reviewed:
            raise ValueError(
                "NASA exige revisar os direitos individuais e os termos antes de selecionar."
            )
    elif not reusable(candidate["license_url"]):
        raise ValueError("Licença de reutilização ausente ou não autorizada.")
    data, mime = fetch_public(candidate["url"])
    return _store_image(candidate, data, mime, reviewed=reviewed)


def automatic_search(query, *, offline=False):
    """Choose providers by topic/availability; retain failures and license constraints."""
    original_query = query
    # Remove generic photographic qualifiers, never a standalone proper-name "Real".
    query = re.sub(r"\b(?:real photos?|fotografias? rea(?:l|is))\b", " ", query, flags=re.I)
    query = " ".join(query.split()) or original_query
    space = bool(
        re.search(
            r"\b(nasa|space|moon|lunar|apollo|solar|planet\w*|astronom\w*)\b", query.casefold()
        )
    )
    providers = ["nasa", "openverse", "commons"] if space else ["openverse", "commons"]
    results, attempts = [], []
    for provider in providers:
        try:
            response = search_images(provider, query, offline=offline)
            results.extend(response["results"])
            attempts.append(
                {
                    "provider": provider,
                    "count": len(response["results"]),
                    "cached": response.get("cached", False),
                }
            )
            if any(automatic_candidate(i) for i in results):
                break
        except Exception as exc:
            attempts.append({"provider": provider, "error": str(exc)})
    results.sort(
        key=lambda i: (
            automatic_candidate(i),
            i.get("lexical_score", 0),
            min(i.get("width") or 0, i.get("height") or 0),
        ),
        reverse=True,
    )
    return {
        "original_query": original_query,
        "query": query,
        "results": results,
        "providers": attempts,
        "offline": offline,
        "ranking": "lexical + resolution + reuse eligibility; not semantic proof",
    }


def automatic_candidate(item):
    return bool(
        item.get("lexical_score") == 1
        and (item.get("width") or 0) >= 600
        and (item.get("height") or 0) >= 300
        and not item.get("review_required")
        and reusable(item.get("license_url", ""))
    )


def local_image(name, data, *, author="", license_note="", rights_confirmed=False):
    """Import an authorized local file without contacting an external service."""
    if not rights_confirmed or not license_note.strip():
        raise ValueError("Declare a permissão ou licença e confirme os direitos de uso.")
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("Imagem local deve ter até 2 MiB.")
    name = name.replace("\\", "/").split("/")[-1]
    suffix = name.rsplit(".", 1)[-1].lower()
    if suffix not in {"png", "jpg", "jpeg"}:
        raise ValueError("Imagem local deve ser PNG ou JPEG.")
    metadata = {"title": clean(name), "author": clean(author), "license": clean(license_note)}
    id = hashlib.sha256(data + json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    candidate = {
        **metadata,
        "id": id,
        "provider": "local",
        "page": "arquivo local: " + clean(name),
        "url": "",
        "license_url": "",
        "attribution": f"{metadata['title']} — {metadata['author']} — {metadata['license']}",
        "rights_basis": "declaração do usuário; não verificada independentemente",
    }
    mime = "image/png" if suffix == "png" else "image/jpeg"
    return _store_image(candidate, data, mime, reviewed=True)


def _store_image(candidate, data, mime, *, reviewed):
    id = safe_id(candidate["id"])
    target = store_root() / "assets" / f"{id}.json"
    if len(data) > MAX_BYTES:
        raise ValueError("Imagem excede o limite de bytes.")
    if not (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        if mime == "image/png"
        else data.startswith(b"\xff\xd8\xff")
    ):
        raise ValueError("Assinatura da imagem incompatível com MIME.")
    with Image.open(BytesIO(data)) as image:
        if image.width < 64 or image.height < 64 or image.width * image.height > MAX_PIXELS:
            raise ValueError("Dimensões fora dos limites (mínimo 64 px, máximo 20 MP).")
        if image.format not in {"PNG", "JPEG"} or getattr(image, "n_frames", 1) != 1:
            raise ValueError("Imagem deve ser PNG/JPEG estática.")
        image.verify()
    with Image.open(BytesIO(data)) as image:
        image.load()
        image = image.convert("RGB")
        width, height = image.size
        # Re-encode: no executable attachments, EXIF or private embedded metadata.
        folder = project_root() / "assets/media"
        folder.mkdir(parents=True, exist_ok=True)
        image.save(folder / f"{id}.png", "PNG")
    candidate.update(
        asset=f"assets/media/{id}.png",
        width=width,
        height=height,
        downloaded_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=hashlib.sha256(data).hexdigest(),
        reviewed=reviewed,
        asset_sha256=hashlib.sha256((folder / f"{id}.png").read_bytes()).hexdigest(),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), "utf-8")
    return candidate


def cached_assets():
    folder = store_root() / "assets"
    return [json.loads(p.read_text("utf-8")) for p in folder.glob("*.json") if p.is_file()]


def resolve_asset(file):
    if file == "assets/imagem_demo.png":
        with Image.open(project_root() / file) as im:
            return {
                "asset": file,
                "width": im.width,
                "height": im.height,
                "attribution": "Asset demonstrativo local",
            }
    for asset in cached_assets():
        if asset["asset"] == file:
            from .paths import asset_path

            asset_path(file, project_root())
            if (
                asset.get("asset_sha256")
                and hashlib.sha256((project_root() / file).read_bytes()).hexdigest()
                != asset["asset_sha256"]
            ):
                raise ValueError("Imagem armazenada foi alterada; selecione novamente.")
            return asset
    raise ValueError("Imagem não selecionada no catálogo local.")
