from .base import ModelError
from .mock_model import MockTextModel
from .ollama_model import OllamaTextModel
from .openai_model import OpenAITextModel


def create_model(provider, model):
    if provider == "ollama":
        return OllamaTextModel(model)
    if provider == "openai":
        return OpenAITextModel(model)
    if provider == "mock":
        return MockTextModel()
    raise ModelError(f"Provedor não suportado: {provider}")
