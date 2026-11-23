"""Envio de PPTX para o Google Slides (Drive API v3), com login OAuth do usuário.

Fluxo de app para computador recomendado pelo Google: PKCE (S256) e retorno em
http://127.0.0.1:<porta aleatória>/. O escopo é ``drive.file``: o SlideDSL só enxerga
os arquivos que ele mesmo criou. O Drive converte o PPTX em apresentação do Google
quando o metadado pede ``application/vnd.google-apps.presentation``.

Arquivos locais (fora do Git): ``config/google_client_secret.json`` (baixado do
Google Cloud) e ``config/google_token.json`` (gravado após o login).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx

from .https import system_tls_context
from .paths import project_root

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
SCOPE = "https://www.googleapis.com/auth/drive.file"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
SLIDES_MIME = "application/vnd.google-apps.presentation"


class GoogleError(RuntimeError):
    pass


def secret_path() -> Path:
    custom = os.environ.get("SLIDEDSL_GOOGLE_CLIENT_SECRET")
    return Path(custom) if custom else project_root() / "config" / "google_client_secret.json"


def token_path() -> Path:
    return project_root() / "config" / "google_token.json"


def client_config(path: Path | None = None) -> dict:
    target = path or secret_path()
    if not target.is_file():
        raise GoogleError(
            f"Credencial do Google não encontrada em {target}. Veja docs/GOOGLE_SLIDES.md."
        )
    data = json.loads(target.read_text("utf-8"))
    conf = data.get("installed") or data.get("web") or data
    if not conf.get("client_id") or not conf.get("client_secret"):
        raise GoogleError("Arquivo de credencial sem client_id/client_secret.")
    return conf


def _client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    if transport is not None:
        return httpx.Client(transport=transport, timeout=60)
    return httpx.Client(timeout=60, trust_env=False, verify=system_tls_context())


def _pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge.rstrip(b"=").decode()


def _save_token(data: dict, path: Path | None = None) -> None:
    target = path or token_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data), "utf-8")


def load_token(path: Path | None = None) -> dict | None:
    target = path or token_path()
    if not target.is_file():
        return None
    try:
        return json.loads(target.read_text("utf-8"))
    except (OSError, ValueError):
        return None


def _token_record(payload: dict, previous: dict | None = None) -> dict:
    record = dict(previous or {})
    record["access_token"] = payload["access_token"]
    record["expires_at"] = time.time() + int(payload.get("expires_in", 3600)) - 60
    if payload.get("refresh_token"):
        record["refresh_token"] = payload["refresh_token"]
    return record


class LoginFlow:
    """Um login por vez: abre o retorno local e troca o código pelo token."""

    def __init__(self, transport: httpx.BaseTransport | None = None):
        self.transport = transport
        self.state = "idle"  # idle | pending | authorized | error
        self.error = ""
        self._server: HTTPServer | None = None
        self._lock = threading.Lock()

    def start(self) -> str:
        with self._lock:
            self._shutdown()
            conf = client_config()
            verifier, challenge = _pkce()
            expected = secrets.token_urlsafe(24)
            flow = self

            class Handler(BaseHTTPRequestHandler):
                def do_GET(self):  # noqa: N802 (nome exigido pelo http.server)
                    query = parse_qs(urlsplit(self.path).query)
                    if "code" not in query and "error" not in query:
                        self.send_response(404)
                        self.end_headers()
                        return
                    ok, message = flow._finish(query, expected, verifier, redirect, conf)
                    body = (
                        "<!doctype html><meta charset='utf-8'><title>SlideDSL</title>"
                        f"<p style='font:16px sans-serif;margin:40px'>{message}</p>"
                    ).encode("utf-8")
                    self.send_response(200 if ok else 400)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(body)
                    threading.Thread(target=flow._shutdown, daemon=True).start()

                def log_message(self, *args):
                    pass

            self._server = HTTPServer(("127.0.0.1", 0), Handler)
            redirect = f"http://127.0.0.1:{self._server.server_address[1]}/"
            threading.Thread(target=self._server.serve_forever, daemon=True).start()
            self.state, self.error = "pending", ""
            return AUTH_URL + "?" + urlencode({
                "client_id": conf["client_id"],
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": SCOPE,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "access_type": "offline",
                "prompt": "consent",
                "state": expected,
            })

    def _finish(self, query, expected, verifier, redirect, conf) -> tuple[bool, str]:
        if query.get("state", [""])[0] != expected:
            self.state, self.error = "error", "Resposta do Google com state inválido."
        elif "error" in query:
            self.state, self.error = "error", f"Login recusado: {query['error'][0]}."
        else:
            try:
                with _client(self.transport) as client:
                    r = client.post(TOKEN_URL, data={
                        "code": query["code"][0],
                        "client_id": conf["client_id"],
                        "client_secret": conf["client_secret"],
                        "redirect_uri": redirect,
                        "grant_type": "authorization_code",
                        "code_verifier": verifier,
                    })
                if r.status_code != 200:
                    raise GoogleError(f"Troca do código falhou (HTTP {r.status_code}).")
                _save_token(_token_record(r.json()))
                self.state, self.error = "authorized", ""
                return True, "Pronto! O SlideDSL está conectado ao seu Google. Pode fechar esta aba."
            except (httpx.HTTPError, GoogleError, KeyError, ValueError) as exc:
                self.state, self.error = "error", str(exc)
        return False, f"Não foi possível conectar: {self.error}"

    def _shutdown(self) -> None:
        server, self._server = self._server, None
        if server is not None:
            server.shutdown()
            server.server_close()


def access_token(transport: httpx.BaseTransport | None = None) -> str:
    token = load_token()
    if not token:
        raise GoogleError("Faça login no Google primeiro.")
    if token.get("expires_at", 0) > time.time():
        return token["access_token"]
    if not token.get("refresh_token"):
        raise GoogleError("Sessão do Google expirada; faça login de novo.")
    conf = client_config()
    with _client(transport) as client:
        r = client.post(TOKEN_URL, data={
            "client_id": conf["client_id"],
            "client_secret": conf["client_secret"],
            "refresh_token": token["refresh_token"],
            "grant_type": "refresh_token",
        })
    if r.status_code != 200:
        token_path().unlink(missing_ok=True)
        raise GoogleError("Sessão do Google expirada ou revogada; faça login de novo.")
    record = _token_record(r.json(), token)
    _save_token(record)
    return record["access_token"]


def upload_pptx(pptx: Path, title: str, transport: httpx.BaseTransport | None = None) -> dict:
    """Envia o PPTX convertendo em Google Slides; devolve id, nome e link de edição."""
    token = access_token(transport)
    boundary = "slidedsl-" + uuid.uuid4().hex
    meta = json.dumps({"name": (title or "Apresentação SlideDSL")[:200], "mimeType": SLIDES_MIME})
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
        f"--{boundary}\r\nContent-Type: {PPTX_MIME}\r\n\r\n"
    ).encode("utf-8") + pptx.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    with _client(transport) as client:
        r = client.post(
            UPLOAD_URL,
            params={"uploadType": "multipart", "fields": "id,name,webViewLink"},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/related; boundary={boundary}",
            },
            content=body,
        )
    if r.status_code == 401:
        token_path().unlink(missing_ok=True)
        raise GoogleError("O Google recusou a sessão; faça login de novo.")
    if r.status_code >= 400:
        try:
            message = r.json().get("error", {}).get("message", "")
        except ValueError:
            message = ""
        raise GoogleError(f"Envio ao Google Drive falhou (HTTP {r.status_code}). {message}".strip())
    data = r.json()
    url = data.get("webViewLink") or f"https://docs.google.com/presentation/d/{data['id']}/edit"
    return {"id": data["id"], "name": data.get("name", title), "url": url}


def status(flow: LoginFlow | None = None) -> dict:
    try:
        client_config()
        configured = True
    except (GoogleError, OSError, ValueError):
        configured = False
    return {
        "configured": configured,
        "authorized": bool(load_token()),
        "login": flow.state if flow else "idle",
        "error": flow.error if flow else "",
    }
