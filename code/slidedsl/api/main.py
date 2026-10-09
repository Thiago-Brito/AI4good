"""Compatibilidade: uvicorn api.main:app a partir da raiz."""

from slidedsl.server import app

__all__ = ["app"]
