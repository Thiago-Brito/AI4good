from ..paths import project_root


class MockTextModel:
    """Somente fixture de infraestrutura; jamais resultado de SLM/LLM real."""

    def __init__(self, outputs: list[str] | None = None):
        self.outputs = outputs or [
            (project_root() / "examples/cinco_slides.sld").read_text(encoding="utf-8")
        ]
        self.calls = 0
        self.metadata = {
            "provider": "mock",
            "model_returned": "fixture-offline",
            "is_mock": True,
            "seed_supported": False,
        }

    def available(self):
        return True, "Fixture para teste offline; não é modelo real."

    def generate(self, system_prompt, user_prompt, *, temperature=0, seed=None):
        value = self.outputs[min(self.calls, len(self.outputs) - 1)]
        self.calls += 1
        return value
