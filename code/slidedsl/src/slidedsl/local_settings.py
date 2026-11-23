"""Carregamento explícito de configuração local, sem executar conteúdo do .env."""

import os
from pathlib import Path

from .paths import project_root

KEYS = {
    "OPENAI_API_KEY",
    "SLIDEDSL_OPENAI_MODEL",
    "SLIDEDSL_OPENAI_PRICING",
    "OLLAMA_BASE_URL",
    "SLIDEDSL_NODE",
    "SLIDEDSL_CONTACT",
    "SLIDEDSL_GOOGLE_CLIENT_SECRET",
}


def load_local_settings(path: Path | None = None) -> None:
    target = path or project_root() / ".env"
    if not target.is_file():
        return
    for line in target.read_text("utf-8-sig").splitlines():
        name, separator, value = line.strip().partition("=")
        if not separator or name not in KEYS or name in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if value:
            os.environ[name] = value
