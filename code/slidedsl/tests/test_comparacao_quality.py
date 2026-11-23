"""Contratos de qualidade e rede: sem API paga nem acesso à internet."""

from contextlib import contextmanager
import json
import re
import ssl

import httpx
import pytest

from slidedsl import media, research
from slidedsl.alto_generation import generate_alto
from slidedsl.repetition import repetition_pairs


class EditorialModel:
    supports_response_schema = True

    def __init__(self, author="", repeated=False, repair=True):
        self.author, self.repeated, self.repair = author, repeated, repair
        self.calls = []

    def generate(self, system, user, **kwargs):
        self.calls.append((system, user, kwargs))
        if "roteirista" in system:
            return json.dumps({"titulo": "Aprender com exemplos", "slides": [
                {"tipo": kind, "mensagem": title, "objetivo": "Explicar com exemplo concreto",
                 "busca_imagem": "green leaf"}
                for kind, title in zip(
                    ["capa", "topicos", "etapas", "conclusao"],
                    ["Aprender com exemplos", "Observe uma folha", "Prepare o ambiente", "Pratique com cuidado"],
                )
            ]})
        index = int(re.search(r"Escreva o slide (\d+)", user)[1])
        if index == 1:
            data = {"titulo": "Aprender com exemplos", "subtitulo": "Uma introdução prática",
                    "autor": self.author, "notas": ""}
        else:
            details = {
                2: [("Observar a folha", "A folha recebe luz e transforma energia durante o dia."),
                    ("Comparar ambientes", "Uma planta na sombra recebe menos luz pela janela.")],
                3: [("Preparar o ambiente", "Escolha uma mesa livre para organizar materiais antes da atividade."),
                    ("Registrar resultados", "Anote as mudanças observadas para comparar os resultados depois.")],
                4: [("Revisar suas anotações", "Confira suas observações antes de explicar o processo para outra pessoa."),
                    ("Compartilhar uma dúvida", "Apresente uma pergunta específica para orientar a próxima atividade prática.")],
            }
            source = 2 if index == 3 and self.repeated and (
                not self.repair or "Problemas encontrados" not in user
            ) else index
            data = {"titulo": ["", "", "Observe uma folha", "Prepare o ambiente", "Pratique com cuidado"][index],
                    "itens": [{"rotulo": a, "detalhe": b} for a, b in details[source]],
                    "fontes": [], "notas": ""}
            if "(tipo imagem)" in user:
                data.update(busca_imagem="green leaf", legenda="Luz sobre uma folha")
        return json.dumps(data, ensure_ascii=False)


def run(model, **kwargs):
    return generate_alto(
        kwargs.pop("request", "Uma introdução prática"), model, n_slides=4,
        coverage=False, verify_support=False, repair_max=1, **kwargs,
    )


@pytest.mark.parametrize("author,brief,expected", [
    ("Equipe Inventada", "Uma introdução prática", None),
    ("Ana Silva", "Uma introdução prática. Autora: Ana Silva", "Ana Silva"),
    ("Ana", "Uma introdução para Mariana", None),
])
def test_cover_author_only_when_present_without_extra_calls(author, brief, expected):
    model = EditorialModel(author=author)
    result = run(model, request=brief)
    assert result.deck.slides[0].author == expected
    assert len(model.calls) == 5
    assert "organização ou data" in model.calls[1][0]


def test_happy_path_context_short_layout_and_no_extra_calls():
    model = EditorialModel()
    run(model)
    assert len(model.calls) == 5
    prompt = model.calls[3][1]
    assert "Roteiro:" in prompt and "Slides já escritos" in prompt
    assert "A folha recebe luz" in prompt
    assert "detalhes até 110" in model.calls[3][0]


@pytest.mark.parametrize("repair", [True, False])
def test_duplicate_items_trigger_only_one_targeted_repair(repair):
    model = EditorialModel(repeated=True, repair=repair)
    result = run(model)
    assert len(model.calls) == 6
    repairs = [u for _, u, _ in model.calls if "Problemas encontrados" in u]
    assert len(repairs) == 1 and "A017" in repairs[0]
    assert "repete o slide 2" in repairs[0]
    assert any(d.code == "A017" for d in result.diagnostics) is (not repair)


def test_metric_is_normalized_and_ignores_short_common_labels():
    assert repetition_pairs([["A folha RECEBE luz, durante o dia!"],
                             ["A folha recebe luz durante o dia."]])[0]["jaccard"] == 1
    assert repetition_pairs([["Próximos passos"], ["Proximos passos"]]) == []
    assert repetition_pairs([["Cada planta absorve luz natural"],
                             ["Organize os arquivos antes de salvar"]]) == []


@pytest.mark.parametrize("available", [True, False])
def test_images_planned_commons_only_and_fallback_without_model_calls(monkeypatch, available):
    seen = []

    def search(query, **kwargs):
        seen.append((query, kwargs))
        return {"results": [{"id": "fixture", "title": "green leaf"}] if available else []}

    monkeypatch.setattr(media, "automatic_search", search)
    monkeypatch.setattr(media, "automatic_candidate", lambda item: True)
    monkeypatch.setattr(media, "cache_image", lambda ident: {"asset": "assets/imagem_demo.png"})
    model = EditorialModel()
    result = run(model, images=True)
    assert len(model.calls) == 5
    assert result.outline["slides"][1]["tipo"] == "imagem"
    assert result.outline["slides"][1]["busca_imagem"] == "green leaf"
    # Sem resultado, consultas mais simples são tentadas, sempre só no Commons e sem IA.
    expected = ["green leaf"] if available else ["green leaf", "green"]
    assert [q for q, _ in seen] == expected
    assert all(kw == {"providers": ("commons",), "wait_for_provider": True} for _, kw in seen)
    # R7 keeps imagem so that the compiler uses its dedicated textual cards fallback.
    assert result.deck.slides[1].kind == "imagem"
    assert bool(result.deck.slides[1].image_file) is available


@pytest.mark.parametrize("target", ["media", "research"])
def test_https_clients_receive_required_system_tls_context(monkeypatch, target):
    seen = []

    class Client:
        def __init__(self, **kwargs):
            seen.append(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @contextmanager
        def stream(self, method, url, **kwargs):
            yield httpx.Response(200, content=b"{}", headers={"content-type": "application/json"})

        def get(self, url, **kwargs):
            return httpx.Response(200, json={"results": [{}]}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "Client", Client)
    if target == "media":
        monkeypatch.setattr(media, "public_target", lambda url: (
            __import__("urllib.parse", fromlist=["urlsplit"]).urlsplit(url), "1.1.1.1"
        ))
        assert media.api_json("https://example.org/test") == {}
    else:
        monkeypatch.setenv("SLIDEDSL_SEARXNG_URL", "https://example.org")
        assert research.searxng_status()["ok"]
        research.search_searxng("folha")
    for kwargs in seen:
        assert isinstance(kwargs["verify"], ssl.SSLContext)
        assert kwargs["verify"].verify_mode == ssl.CERT_REQUIRED
        assert kwargs["verify"].check_hostname


class BatchModel(EditorialModel):
    """Responde à chamada em lote com o mesmo conteúdo que daria slide a slide."""

    def generate(self, system, user, **kwargs):
        if "TODOS os slides" not in system:
            return super().generate(system, user, **kwargs)
        self.calls.append((system, user, kwargs))
        slides = {}
        for n in range(1, 5):
            one = json.loads(super().generate("", f"Escreva o slide {n}", **kwargs))
            self.calls.pop()
            slides[f"slide_{n}"] = one
        return json.dumps(slides, ensure_ascii=False)


def test_batch_writes_all_slides_in_one_call_with_same_validation():
    model = BatchModel()
    result = run(model, batch=True)
    stages = [c.stage for c in result.calls]
    assert stages == ["roteiro", "lote"]
    assert len(result.deck.slides) == 4
    assert result.deck.slides[1].items[0].label == "Observar a folha"
    # Instruções e roteiro vão uma vez, não uma vez por slide.
    assert model.calls[1][1].count("Roteiro:") == 1 and "slide_4" in model.calls[1][1]


def test_batch_falls_back_per_slide_when_one_slide_is_missing():
    class Partial(BatchModel):
        def generate(self, system, user, **kwargs):
            raw = super().generate(system, user, **kwargs)
            if "TODOS os slides" in system:
                data = json.loads(raw)
                data.pop("slide_3")
                return json.dumps(data, ensure_ascii=False)
            return raw
    model = Partial()
    result = run(model, batch=True)
    assert [c.stage for c in result.calls] == ["roteiro", "lote", "slide"]
    assert result.deck.slides[2].items[0].label == "Preparar o ambiente"
