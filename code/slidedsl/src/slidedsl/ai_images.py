"""Imagens geradas por IA (OpenAI Images API) quando não há foto livre adequada.

Custo por imagem conferido em developers.openai.com/api/docs/guides/image-generation
em 01/11/2026 (tamanho 1536×1024). O valor efetivo vem do `usage` da resposta quando
informado; senão, usa-se a tabela abaixo, marcada como estimativa.
"""

import base64
from datetime import datetime, timezone
import hashlib
import os
import ssl
from time import monotonic

import httpx

SIZE = "1536x1024"
PRICE_DATE = "2026-11-01"
# perfil → (modelo, qualidade, US$ por imagem 1536×1024, US$/1M tokens de saída de imagem,
#           US$/1M tokens de entrada de texto)
PROFILES = {
    "economica": ("gpt-image-2", "low", 0.005, 30.0, 5.0),
    "media": ("gpt-image-1-mini", "medium", 0.015, 8.0, 2.0),
}

STYLE = (
    "Editorial photograph or clean illustration for a presentation slide, landscape 3:2. "
    "Single clear subject, natural light, uncluttered background, calm colors. "
    "No text, no letters, no numbers, no logos, no watermarks, no user interface."
)


def image_prompt(title: str, query: str | None) -> str:
    subject = (query or "").strip() or title
    return f"{STYLE}\nSubject: {subject}.\nContext (Portuguese slide title): {title}."


def estimate(profile: str) -> float:
    return PROFILES[profile][2]


def generate_image(title, query, *, profile="economica", client=None, on_record=None):
    """Gera e guarda uma imagem; devolve (asset do catálogo, registro de custo).

    `on_record` recebe o registro também em falha: uma imagem cobrada e depois rejeitada
    localmente continua contabilizada; erro de transporte fica com custo desconhecido."""
    from .media import _store_image

    model, quality, table_cost, image_out_price, text_in_price = PROFILES[profile]
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY ausente; imagem por IA indisponível.")
    prompt = image_prompt(title, query)
    record = {"stage": "imagem_ia", "model": model, "quality": quality, "size": SIZE,
              "status": "running", "cost_usd": None, "cost_basis": None}
    started = monotonic()
    payload = {"model": model, "prompt": prompt, "size": SIZE, "quality": quality,
               "n": 1, "output_format": "jpeg"}
    try:
        own = client is None
        client = client or httpx.Client(timeout=180, verify=ssl.create_default_context())
        try:
            response = client.post("https://api.openai.com/v1/images/generations",
                                   headers={"Authorization": "Bearer " + key}, json=payload)
        finally:
            if own:
                client.close()
        if response.status_code >= 400:
            # A cobrança só ocorre em geração concluída; corpo de erro não é registrado.
            record.update(status="failed", cost_usd=0.0, cost_basis="erro HTTP sem imagem")
            raise ValueError(f"Geração de imagem recusada (HTTP {response.status_code}).")
        data = response.json()
        usage = data.get("usage") or {}
        out_tokens = usage.get("output_tokens")
        in_tokens = usage.get("input_tokens")
        if out_tokens is not None and in_tokens is not None:
            record.update(input_tokens=in_tokens, output_tokens=out_tokens,
                          cost_usd=round((out_tokens * image_out_price + in_tokens * text_in_price)
                                         / 1_000_000, 6),
                          cost_basis=f"usage × tarifa {PRICE_DATE}")
        else:
            record.update(cost_usd=table_cost, cost_basis=f"tabela por imagem {PRICE_DATE}")
        raw = base64.b64decode(data["data"][0]["b64_json"])
        candidate = {
            "id": hashlib.sha256(raw).hexdigest(),
            "provider": "openai-image",
            "title": title[:200],
            "author": "Imagem gerada por IA",
            "license": model,
            "page": "gerada por IA a partir do tema do slide",
            "url": "",
            "license_url": "",
            "attribution": f"Imagem gerada por IA ({model}) — {title[:120]}",
            "rights_basis": "gerada por IA; revisar antes de publicar",
            "prompt": prompt,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }
        mime = "image/jpeg" if raw.startswith(b"\xff\xd8\xff") else "image/png"
        asset = _store_image(candidate, raw, mime, reviewed=False)
        record["status"] = "completed"
        return asset, record
    except Exception:
        if record["status"] == "running":
            record["status"] = "failed"
        raise
    finally:
        record["seconds"] = round(monotonic() - started, 3)
        if on_record:
            on_record(record)
