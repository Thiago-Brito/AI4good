from typing import Literal

from pydantic import BaseModel, Field


class Diagnostic(BaseModel):
    code: str
    severity: Literal["ERRO", "AVISO", "INFORMAÇÃO"]
    message: str
    slide: int | None = None
    element: str | None = None
    line: int | None = None
    column: int | None = None
    evidence: dict = Field(default_factory=dict)
    suggestion: str = "Revise o comando indicado."


class DSLException(Exception):
    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__("; ".join(d.message for d in diagnostics))


def failed(diagnostics: list[Diagnostic], strict_codes: set[str] | None = None) -> bool:
    return any(
        d.severity == "ERRO" or (d.severity == "AVISO" and d.code in (strict_codes or set()))
        for d in diagnostics
    )
