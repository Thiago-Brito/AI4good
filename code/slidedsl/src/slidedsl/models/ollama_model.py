import os

import httpx

from .base import ModelError


class OllamaTextModel:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        timeout: float = 300,
        client: httpx.Client | None = None,
        context_length: int = 16384,
        output_tokens: int = 8192,
    ):
        self.model = model
        self.base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ).rstrip("/")
        self.timeout = timeout
        self.client = client
        self.context_length = context_length
        self.output_tokens = output_tokens
        self.thinking = False
        self.controls_detected = False
        self.last_request = None
        self.last_response = None
        self.model_show = None
        self.metadata = {
            "provider": "ollama",
            "model_requested": model,
            "seed_supported": True,
            "thinking": False,
            "thinking_requested": False,
            "num_ctx": context_length,
            "num_predict": output_tokens,
        }

    def _request(self, method: str, endpoint: str, **kwargs):
        try:
            if self.client:
                response = self.client.request(method, self.base_url + endpoint, **kwargs)
            else:
                with httpx.Client(timeout=self.timeout, trust_env=False) as client:
                    response = client.request(method, self.base_url + endpoint, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise ModelError(
                f"Ollama respondeu HTTP {exc.response.status_code}; confira modelo e serviço."
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelError("Ollama indisponível, timeout ou resposta JSON inválida.") from exc

    def _detect_controls(self):
        if self.controls_detected:
            return
        details = self._request("POST", "/api/show", json={"model": self.model})
        self.model_show = details
        controls = details.get("thinking")
        self.metadata["thinking_controls"] = controls
        if isinstance(controls, dict):
            values = controls.get("values", [])
            if False not in values and values:
                self.thinking = controls.get("default", values[0])
                self.metadata["thinking_limitation"] = (
                    "Modelo não permite think=false; usado valor suportado."
                )
        self.metadata["thinking"] = self.thinking
        self.controls_detected = True

    def available(self):
        try:
            d = self._request("GET", "/api/tags", timeout=3)
            models = {x["name"]: x for x in d.get("models", [])}
            if self.model not in models:
                return False, f"Modelo não instalado. Execute: ollama pull {self.model}"
            self.metadata.update(
                {
                    "model_digest": models[self.model].get("digest"),
                    "model_details": models[self.model].get("details"),
                }
            )
            self._detect_controls()
            return True, "Modelo instalado no serviço Ollama."
        except ModelError as exc:
            return False, str(exc) + " Instale/inicie Ollama e execute ollama pull."

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0,
        seed: int | None = None,
        response_schema: dict | None = None,
    ) -> str:
        self._detect_controls()
        options = {
            "temperature": temperature,
            "num_ctx": self.context_length,
            "num_predict": self.output_tokens,
        }
        if seed is not None:
            options["seed"] = seed
        payload = {
            "model": self.model,
            "stream": False,
            "think": self.thinking,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": options,
        }
        if response_schema is not None:
            payload["format"] = response_schema
        self.last_request = payload
        self.last_response = None
        d = self._request("POST", "/api/chat", json=payload)
        self.last_response = d
        content = d.get("message", {}).get("content")
        if not isinstance(content, str):
            raise ModelError("Ollama não retornou message.content textual.")
        self.metadata.update(
            {
                "model_returned": d.get("model"),
                "temperature": temperature,
                "seed": seed,
                "eval_count": d.get("eval_count"),
                "prompt_eval_count": d.get("prompt_eval_count"),
                "done_reason": d.get("done_reason"),
                "thinking_output_chars": len(d.get("message", {}).get("thinking") or ""),
            }
        )
        return content
