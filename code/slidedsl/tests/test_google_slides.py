"""Envio ao Google Slides com o Google simulado (httpx.MockTransport), sem rede."""

import json
import time
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest

from slidedsl import google_slides as g


@pytest.fixture
def google_files(tmp_path, monkeypatch):
    secret = tmp_path / "secret.json"
    secret.write_text(json.dumps({"installed": {"client_id": "cid", "client_secret": "csec"}}))
    token = tmp_path / "token.json"
    monkeypatch.setenv("SLIDEDSL_GOOGLE_CLIENT_SECRET", str(secret))
    monkeypatch.setattr(g, "token_path", lambda: token)
    return token


def fake_google(calls):
    def handler(request: httpx.Request):
        calls.append(request)
        if str(request.url).startswith(g.TOKEN_URL):
            form = parse_qs(request.content.decode())
            if form["grant_type"] == ["authorization_code"]:
                assert form["code"] == ["abc"] and form["code_verifier"][0]
                return httpx.Response(200, json={"access_token": "t1", "expires_in": 3600,
                                                 "refresh_token": "r1"})
            return httpx.Response(200, json={"access_token": "t2", "expires_in": 3600})
        if str(request.url).startswith(g.UPLOAD_URL):
            assert request.headers["Authorization"].startswith("Bearer ")
            assert b"application/vnd.google-apps.presentation" in request.content
            assert b"PPTXBYTES" in request.content
            return httpx.Response(200, json={"id": "abc123", "name": "Sem2",
                                             "webViewLink": "https://docs.google.com/p/abc123"})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_login_com_pkce_troca_codigo_e_grava_token(google_files):
    calls = []
    flow = g.LoginFlow(transport=fake_google(calls))
    url = flow.start()
    query = parse_qs(urlsplit(url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == [g.SCOPE]
    redirect = query["redirect_uri"][0]
    assert redirect.startswith("http://127.0.0.1:")
    # O navegador volta ao retorno local com o código e o state.
    r = httpx.get(redirect, params={"code": "abc", "state": query["state"][0]}, timeout=5)
    assert r.status_code == 200 and "conectado" in r.text
    assert flow.state == "authorized"
    assert json.loads(google_files.read_text())["refresh_token"] == "r1"


def test_state_invalido_e_recusado(google_files):
    flow = g.LoginFlow(transport=fake_google([]))
    redirect = parse_qs(urlsplit(flow.start()).query)["redirect_uri"][0]
    r = httpx.get(redirect, params={"code": "abc", "state": "outro"}, timeout=5)
    assert r.status_code == 400
    assert flow.state == "error" and not google_files.exists()


def test_upload_converte_em_slides_e_renova_token_expirado(google_files, tmp_path):
    google_files.write_text(json.dumps({"access_token": "velho", "refresh_token": "r1",
                                        "expires_at": time.time() - 10}))
    pptx = tmp_path / "deck.pptx"
    pptx.write_bytes(b"PPTXBYTES")
    calls = []
    result = g.upload_pptx(pptx, "Sem2", transport=fake_google(calls))
    assert result == {"id": "abc123", "name": "Sem2", "url": "https://docs.google.com/p/abc123"}
    assert calls[0].url.path.endswith("/token")  # renovou antes de enviar
    assert calls[1].headers["Authorization"] == "Bearer t2"


def test_sem_credencial_status_informa(monkeypatch, tmp_path):
    monkeypatch.setenv("SLIDEDSL_GOOGLE_CLIENT_SECRET", str(tmp_path / "nao_existe.json"))
    monkeypatch.setattr(g, "token_path", lambda: tmp_path / "token.json")
    assert g.status() == {"configured": False, "authorized": False, "login": "idle", "error": ""}
    with pytest.raises(g.GoogleError):
        g.LoginFlow().start()


def test_api_exige_login_antes_de_enviar(google_files):
    from fastapi.testclient import TestClient

    from slidedsl.server import app

    client = TestClient(app)
    assert client.get("/api/google/status").json()["configured"] is True
    deck = {"schema_version": "1.1", "title": "x", "theme": "claro",
            "canvas": {"width": 1280, "height": 720, "unit": "px_logico"}, "slides": []}
    r = client.post("/api/google/slides", json={"ir": deck})
    assert r.status_code == 401
