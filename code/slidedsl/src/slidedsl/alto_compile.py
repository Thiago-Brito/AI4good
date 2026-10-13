"""Cadeia completa da SlideDSL Alto: parse → validação A → layout → SlideDSL 1.1 → PPTX."""

from dataclasses import dataclass, field
from pathlib import Path

from .alto import AltoDeck, parse_alto, validate_alto
from .alto_layout import alto_to_dsl
from .diagnostics import Diagnostic, DSLException
from .pipeline import ValidationResult, validate_source


@dataclass
class AltoResult:
    deck: AltoDeck | None = None
    dsl: str | None = None
    mapping: dict[str, str] = field(default_factory=dict)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    validation: ValidationResult | None = None

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.all_diagnostics if d.severity == "ERRO"]

    @property
    def all_diagnostics(self) -> list[Diagnostic]:
        return self.diagnostics + (self.validation.diagnostics if self.validation else [])

    def success(self, strict=False) -> bool:
        return (
            self.validation is not None
            and not any(d.severity == "ERRO" for d in self.diagnostics)
            and self.validation.success(strict)
        )

    def report(self, strict=False) -> dict:
        return {
            "valid": self.success(strict),
            "alto_diagnostics": [d.model_dump() for d in self.diagnostics],
            "dsl_validation": self.validation.report(strict) if self.validation else None,
        }


def build_alto(
    source: str | AltoDeck, facts: dict | None = None, root: Path | None = None
) -> AltoResult:
    result = AltoResult()
    try:
        result.deck = parse_alto(source) if isinstance(source, str) else source
    except DSLException as exc:
        result.diagnostics = exc.diagnostics
        return result
    result.diagnostics = validate_alto(result.deck, facts)
    if any(d.severity == "ERRO" for d in result.diagnostics):
        return result
    result.dsl, result.mapping, layout = alto_to_dsl(result.deck, facts, root)
    result.diagnostics += layout
    result.validation = validate_source(result.dsl, root)
    return result


def compile_alto(
    source: str | AltoDeck,
    out: Path,
    facts: dict | None = None,
    root: Path | None = None,
    *,
    strict: bool = False,
) -> tuple[AltoResult, dict]:
    from .compiler import compile_ir

    result = build_alto(source, facts, root)
    if not result.success(strict):
        raise DSLException(result.all_diagnostics)
    return result, compile_ir(result.validation.ir, out, root, strict=strict)
