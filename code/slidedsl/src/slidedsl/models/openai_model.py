from copy import deepcopy
import json
import os

import httpx
from jsonschema import ValidationError, validate

from .base import ModelError
from ..https import system_tls_context


def strict_schema(schema: dict) -> dict:
    """Adaptar os schemas do domínio ao contrato estrito sem alterar o original."""
    result = deepcopy(schema)

    def visit(node):
        if not isinstance(node, dict):
            return
        if node.get("type") == "object":
            node["additionalProperties"] = False
            node["required"] = list(node.get("properties", {}))
        if node.get("type") == "array":
            node.setdefault("items", {"type": "string"})
        # Comprimentos continuam sendo validados localmente; não são portáveis
        # entre todos os modelos com Structured Outputs.
        node.pop("minLength", None)
        node.pop("maxLength", None)
        for value in node.values():
            if isinstance(value, dict):
                visit(value)
            elif isinstance(value, list):
                for item in value:
                    visit(item)

    visit(result)
    return result


def fit_to_schema(value, schema: dict):
    """Cortar textos e listas acima do máximo, como o decoder restrito do Ollama faz.

    O schema estrito enviado à OpenAI não leva maxLength; sem este corte, um campo
    um pouco longo (ex.: um trecho literal de documento) derrubava a geração inteira.
    Mínimos e enums continuam sendo exigidos pela validação local.
    """
    if not isinstance(schema, dict):
        return value
    if isinstance(value, str) and isinstance(schema.get("maxLength"), int):
        return value[: schema["maxLength"]]
    if isinstance(value, list):
        items = [fit_to_schema(item, schema.get("items", {})) for item in value]
        limit = schema.get("maxItems")
        return items[:limit] if isinstance(limit, int) else items
    if isinstance(value, dict):
        props = schema.get("properties", {})
        return {k: fit_to_schema(v, props.get(k, {})) for k, v in value.items()}
    return value


class OpenAITextModel:
    supports_response_schema = True
    supports_grammar = False

    def __init__(
        self,
        model: str,
        timeout: float = 300,
        client: httpx.Client | None = None,
        output_tokens: int = 2048,
    ):
        self.model, self.timeout, self.client = model, timeout, client
        self.output_tokens = output_tokens
        self.metadata = {
            "provider": "openai",
            "model_requested": model,
            "seed_supported": "parâmetro opcional; não garante determinismo",
            "seed_default": None,
        }

    def _request(self, method, endpoint, **kwargs):
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ModelError("OPENAI_API_KEY ausente; configure no ambiente para ativar OpenAI.")
        try:
            headers = {"Authorization": "Bearer " + key}
            if self.client:
                response = self.client.request(
                    method, "https://api.openai.com/v1" + endpoint, headers=headers, **kwargs
                )
            else:
                # Repositório do sistema: antivírus/proxies corporativos que inspecionam TLS
                # instalam a raiz ali, não no certifi. A verificação continua ativa.
                with httpx.Client(timeout=self.timeout, verify=system_tls_context()) as client:
                    response = client.request(
                        method, "https://api.openai.com/v1" + endpoint, headers=headers, **kwargs
                    )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            # Nunca registrar corpo/headers HTTP que possam incluir dados da conta.
            raise ModelError(
                f"OpenAI respondeu HTTP {exc.response.status_code}; verifique acesso/cota do modelo."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelError("OpenAI indisponível, timeout ou resposta JSON inválida.") from exc

    def available(self):
        if not os.environ.get("OPENAI_API_KEY"):
            return False, "OPENAI_API_KEY ausente; não houve chamada remota."
        try:
            d = self._request("GET", "/models/" + self.model, timeout=10)
            self.metadata["model_catalog_id"] = d.get("id")
            return True, "Modelo acessível no catálogo; geração ainda pode depender de cota."
        except ModelError as exc:
            return False, str(exc)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0,
        seed: int | None = None,
        response_schema: dict | None = None,
    ) -> str:
        # Nunca reutilizar uso da resposta anterior em erro de transporte/recusa.
        self.metadata.update(
            usage=None, model_returned=None, finish_reason=None, schema_truncated=False
        )
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_completion_tokens": self.output_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "store": False,
        }
        if seed is not None:
            payload["seed"] = seed
        if response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "slidedsl",
                    "strict": True,
                    "schema": strict_schema(response_schema),
                },
            }
        d = self._request("POST", "/chat/completions", json=payload)
        self.metadata.update(
            model_returned=d.get("model"),
            usage=d.get("usage"),
            system_fingerprint=d.get("system_fingerprint"),
            temperature=temperature,
            seed=seed,
        )
        try:
            choice = d["choices"][0]
            self.metadata["finish_reason"] = choice.get("finish_reason")
            if choice["message"].get("refusal"):
                raise ModelError("O modelo recusou o pedido; revise o conteúdo solicitado.")
            if choice.get("finish_reason") != "stop":
                raise ModelError("Resposta OpenAI interrompida; verifique o limite de saída.")
            content = choice["message"]["content"]
            if not isinstance(content, str):
                raise KeyError("content")
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("OpenAI não retornou conteúdo textual.") from exc
        if response_schema is not None:
            try:
                data = json.loads(content)
                fitted = fit_to_schema(data, response_schema)
                validate(fitted, response_schema)
                if fitted != data:
                    self.metadata["schema_truncated"] = True
                    content = json.dumps(fitted, ensure_ascii=False)
            except (ValueError, ValidationError) as exc:
                raise ModelError("A resposta OpenAI não atende ao schema do domínio.") from exc
        return content
