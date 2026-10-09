from dataclasses import dataclass, field
from pathlib import Path

from .ast_nodes import PresentationNode
from .design_rules import check_design, load_rules
from .diagnostics import Diagnostic, DSLException, failed
from .ir import Presentation
from .parser import parse
from .semantic import analyze


@dataclass
class ValidationResult:
    ast: PresentationNode | None = None
    ir: Presentation | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    parse_success: bool = False
    semantic_success: bool = False

    def success(self, strict=False):
        return self.semantic_success and not failed(
            self.diagnostics, set(load_rules()["strict_codes"]) if strict else None
        )

    def report(self, strict=False):
        return {
            "parse_success": self.parse_success,
            "semantic_success": self.semantic_success,
            "valid": self.success(strict),
            "strict": strict,
            "diagnostics": [d.model_dump() for d in self.diagnostics],
        }


def validate_source(source: str, root: Path | None = None, *, design=True) -> ValidationResult:
    result = ValidationResult()
    try:
        result.ast = parse(source)
        result.parse_success = True
        result.ir = analyze(result.ast, root)
        result.semantic_success = True
        if design:
            result.diagnostics = check_design(result.ir)
    except DSLException as exc:
        result.diagnostics = exc.diagnostics
    return result
