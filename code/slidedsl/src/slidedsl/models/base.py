import inspect
from typing import Protocol


class TextModel(Protocol):
    metadata: dict

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float,
        seed: int | None,
        response_schema: dict | None = None,
    ) -> str: ...

    def available(self) -> tuple[bool, str]: ...


class ModelError(RuntimeError):
    pass


class GenerationLimitError(ModelError):
    """Limite local atingido antes de iniciar outra chamada de geração."""


def supports_parameter(model, name: str) -> bool:
    declared = getattr(model, "supports_" + name, None)
    if declared is not None:
        return bool(declared)
    parameters = inspect.signature(model.generate).parameters
    return name in parameters or any(p.kind == p.VAR_KEYWORD for p in parameters.values())


def generate_text(
    model,
    system,
    user,
    *,
    temperature=0,
    seed=None,
    response_schema=None,
    grammar=None,
    context=None,
):
    """Não retirar restrições nem repetir inferência após erro de implementação."""
    kwargs = {"temperature": temperature, "seed": seed}
    for name, value in (("response_schema", response_schema), ("grammar", grammar)):
        if value is not None:
            if not supports_parameter(model, name):
                raise ModelError(f"O adaptador não suporta {name}; escolha um modo compatível.")
            kwargs[name] = value
    recorded = getattr(model, "generate_recorded", None)
    if recorded:
        return recorded(system, user, context=context, **kwargs)
    return model.generate(system, user, **kwargs)
