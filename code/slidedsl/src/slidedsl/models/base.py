from typing import Protocol


class TextModel(Protocol):
    metadata: dict

    def generate(
        self, system_prompt: str, user_prompt: str, *, temperature: float, seed: int | None
    ) -> str: ...

    def available(self) -> tuple[bool, str]: ...


class ModelError(RuntimeError):
    pass
