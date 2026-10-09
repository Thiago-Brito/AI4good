import os

import httpx

from .base import ModelError


class OpenAITextModel:
    def __init__(self, model: str, timeout: float = 300, client: httpx.Client | None = None):
        self.model, self.timeout, self.client = model, timeout, client
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
                with httpx.Client(timeout=self.timeout) as client:
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
    ) -> str:
        payload = {
            "model": self.model,
            "temperature": temperature,
            "max_completion_tokens": 8192,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "store": False,
        }
        if seed is not None:
            payload["seed"] = seed
        d = self._request("POST", "/chat/completions", json=payload)
        try:
            content = d["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise KeyError("content")
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("OpenAI não retornou conteúdo textual.") from exc
        self.metadata.update(
            {
                "model_returned": d.get("model"),
                "system_fingerprint": d.get("system_fingerprint"),
                "usage": d.get("usage"),
                "temperature": temperature,
                "seed": seed,
                "finish_reason": d["choices"][0].get("finish_reason"),
            }
        )
        return content
