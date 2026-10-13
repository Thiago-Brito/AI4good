"""Servidor llama.cpp (`llama-server`) com geração restrita por gramática GBNF.

Exemplo: llama-server -m Qwen3-4B-Instruct-Q4_K_M.gguf --port 8080
Variável: LLAMACPP_BASE_URL (padrão http://127.0.0.1:8080).

Usa o endpoint compatível com OpenAI (/v1/chat/completions), que aplica o template de
chat do modelo e aceita os parâmetros nativos `grammar` (GBNF) e `json_schema`.
"""

import os

import httpx

from .base import ModelError


class LlamaCppTextModel:
    supports_grammar = True

    def __init__(
        self,
        model: str = "local",
        base_url: str | None = None,
        timeout: float = 300,
        client: httpx.Client | None = None,
        output_tokens: int = 2048,
    ):
        self.model = model
        self.base_url = (
            base_url or os.environ.get("LLAMACPP_BASE_URL", "http://127.0.0.1:8080")
        ).rstrip("/")
        self.timeout = timeout
        self.client = client
        self.output_tokens = output_tokens
        self.last_request = None
        self.last_response = None
        self.metadata = {"provider": "llamacpp", "model_requested": model, "seed_supported": True}

    def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            if self.client:
                response = self.client.post(self.base_url + endpoint, json=payload)
            else:
                with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                    response = client.post(self.base_url + endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise ModelError(
                f"llama.cpp respondeu HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelError("llama-server indisponível, timeout ou JSON inválido.") from exc

    def available(self):
        try:
            if self.client:
                response = self.client.get(self.base_url + "/health")
            else:
                with httpx.Client(timeout=3, trust_env=False) as client:
                    response = client.get(self.base_url + "/health")
            response.raise_for_status()
            return True, "llama-server disponível."
        except httpx.HTTPError:
            return False, "Inicie: llama-server -m modelo.gguf --port 8080"

    def generate(
        self,
        system_prompt,
        user_prompt,
        *,
        temperature=0,
        seed=None,
        response_schema=None,
        grammar=None,
    ):
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": self.output_tokens,
            "stream": False,
        }
        if seed is not None:
            payload["seed"] = seed
        if grammar is not None:
            payload["grammar"] = grammar
        elif response_schema is not None:
            payload["json_schema"] = response_schema
        self.last_request = payload
        data = self._post("/v1/chat/completions", payload)
        self.last_response = data
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("llama.cpp não retornou choices[0].message.content.") from exc
        self.metadata.update(
            {
                "temperature": temperature,
                "seed": seed,
                "grammar_constrained": grammar is not None,
                "usage": data.get("usage"),
                "finish_reason": data["choices"][0].get("finish_reason"),
            }
        )
        return content
