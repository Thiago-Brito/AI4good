"""Motor "igual ao celular" no PC.

Roda o MESMO pipeline do app Android (mobile/app/src/pipeline, via mobile/app/bench/motor_pc.mjs):
gramática com os limites do compilador, leitura do documento por frases numeradas e slide de reserva do
compilador. O deck que sai do Node é compilado aqui pelo compilador do PC (mesma IR, paridade conferida em
packages/slidedsl-core), e grava os mesmos arquivos do fluxo completo, para o editor (refazer, mover, foto)
funcionar igual.

Modelos: arquivos GGUF listados em config/modelos_locais.json, servidos por um llama-server que este módulo
liga e troca quando o modelo muda. Variáveis:
- SLIDEDSL_GGUF_DIR (padrão D:/android/models): pasta dos .gguf;
- SLIDEDSL_LLAMA_SERVER (padrão D:/android/llama/llama-server.exe);
- SLIDEDSL_MOBILE_APP (padrão D:/slidedsl-mobile/app): cópia do app com node_modules e `npm test` rodado;
- SLIDEDSL_LLAMA_NGL (padrão 99): camadas na GPU (0 = só CPU);
- LLAMACPP_BASE_URL (padrão http://127.0.0.1:8080): onde o llama-server escuta (o mesmo do provedor llamacpp).
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from dataclasses import fields
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import httpx

from .paths import project_root

ETAPAS = {"Extraindo fatos da fonte": "Lendo o documento por frases numeradas",
          "Planejando roteiro": "Planejando o roteiro"}


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default))


def modelos_locais() -> list[dict]:
    """Modelos do config com a indicação de quais arquivos existem nesta máquina."""
    config = json.loads((project_root() / "config/modelos_locais.json").read_text("utf-8"))
    pasta = _env_path("SLIDEDSL_GGUF_DIR", "D:/android/models")
    return [m | {"disponivel": (pasta / m["arquivo"]).is_file()} for m in config["modelos"]]


def modelo_local(id: str) -> dict:
    for m in modelos_locais():
        if m["id"] == id:
            if not m["disponivel"]:
                raise ValueError(f"Arquivo {m['arquivo']} não encontrado em SLIDEDSL_GGUF_DIR.")
            return m
    raise ValueError("Modelo local desconhecido.")


class ServidorLlama:
    """Um llama-server por vez, com o modelo pedido. Contexto 8192: o motor do celular continua limitado a 4096
    (motor_pc.mjs calcula o espaço com 4096, como o llama.rn), e o "refazer slide" do editor do PC, cujo prompt
    passa de 4096 tokens (visto em 24/11/2026), cabe."""

    def __init__(self):
        self.lock = threading.Lock()
        self.processo: subprocess.Popen | None = None
        self.arquivo: str | None = None

    @property
    def url(self) -> str:
        return os.environ.get("LLAMACPP_BASE_URL", "http://127.0.0.1:8080").rstrip("/")

    def _saudavel(self) -> bool:
        try:
            return httpx.get(self.url + "/health", timeout=2, trust_env=False).status_code == 200
        except httpx.HTTPError:
            return False

    def _modelo_servido(self) -> str | None:
        try:
            data = httpx.get(self.url + "/props", timeout=2, trust_env=False).json()
            return Path(data.get("model_path", "")).name or None
        except (httpx.HTTPError, ValueError):
            return None

    def garantir(self, arquivo: str, say: Callable[[str], None] = lambda m: None) -> str:
        with self.lock:
            if self._saudavel() and self._modelo_servido() == arquivo:
                return self.url
            if self.processo and self.processo.poll() is None:
                self.processo.terminate()
                self.processo.wait(timeout=30)
            elif self._saudavel():
                raise RuntimeError("Já há um llama-server com outro modelo nessa porta; feche-o ou mude LLAMACPP_BASE_URL.")
            exe = _env_path("SLIDEDSL_LLAMA_SERVER", "D:/android/llama/llama-server.exe")
            gguf = _env_path("SLIDEDSL_GGUF_DIR", "D:/android/models") / arquivo
            port = str(urlparse(self.url).port or 8080)
            say(f"Carregando o modelo {arquivo}")
            log = open(project_root() / "outputs/llama_server_motor.log", "ab")
            self.processo = subprocess.Popen(
                [str(exe), "-m", str(gguf), "-ngl", os.environ.get("SLIDEDSL_LLAMA_NGL", "99"), "-c", "8192", "-np", "1", "--jinja", "--port", port,
                 "--cache-ram", "0"], stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.arquivo = arquivo
            for _ in range(240):
                if self.processo.poll() is not None:
                    raise RuntimeError("llama-server encerrou ao carregar o modelo (veja outputs/llama_server_motor.log).")
                if self._saudavel():
                    return self.url
                time.sleep(0.5)
            raise RuntimeError("llama-server não ficou pronto em 2 minutos.")


servidor = ServidorLlama()


def _documento_para_node(document_id: str, out_dir: Path) -> Path:
    """Arquivo que o código do app lê (TXT/MD/DOCX). PDF vai por página (.paginas.json), como o módulo Android
    entrega, para o app aplicar a própria limpeza e escolha por seções (teste do TCC, 25/11/2026)."""
    from .documents import document_path, extract_pdf

    folder = document_path(document_id)
    record = json.loads((folder / "index.json").read_text("utf-8"))
    original = next(folder.glob("document.*"))
    nome = Path(record["name"]).stem
    if original.suffix in {".txt", ".md", ".docx"}:
        destino = out_dir / f"{nome}{original.suffix}"
        destino.write_bytes(original.read_bytes())
        return destino
    if original.suffix == ".pdf":
        paginas = [{"page": p["page"], "text": p["text"]} for p in extract_pdf(original)]
        destino = out_dir / f"{nome}.paginas.json"
        destino.write_text(json.dumps({"nome": record["name"], "paginas": paginas}, ensure_ascii=False), "utf-8")
        return destino
    partes, titulo = [], None
    for chunk in record["chunks"]:
        if chunk.get("heading") and chunk["heading"] != titulo:
            titulo = chunk["heading"]
            partes.append(f"# {titulo}")
        partes.append(chunk["text"])
    destino = out_dir / f"{nome}.txt"
    destino.write_text("\n\n".join(partes), "utf-8")
    return destino


def _dossie(request: str, facts: dict):
    from .research import Dossier, Fact

    nomes = {f.name for f in fields(Fact)}
    lista = [Fact(**({"id": fid, "source_id": "", "url": "", "source_title": ""} | {k: str(v) for k, v in f.items() if k in nomes}))
             for fid, f in facts.items()]
    return Dossier(topic=request, facts=lista)


def _registrar_fotos(deck, out_dir: Path) -> None:
    """Fotos baixadas pelo app (imagens/ + imagens.json) entram no catálogo do PC, com crédito, para o
    compilador e o editor (trocar/remover foto) funcionarem como no fluxo completo."""
    import hashlib

    from .media import _store_image

    meta_path = out_dir / "imagens.json"
    if not meta_path.is_file():
        return
    info = json.loads(meta_path.read_text("utf-8")).get("info", {})
    for slide in deck.slides:
        meta = info.get(slide.image_file or "")
        if not meta:
            continue
        data = (out_dir / "imagens" / slide.image_file).read_bytes()
        m = meta.get("metadata", {})
        provider = m.get("attribution", "").rsplit("(", 1)[-1].rstrip(")") or "openverse"
        candidate = {"id": hashlib.sha256(data).hexdigest(), "provider": provider, "title": m.get("attribution", "")[:200],
                     "author": m.get("author", ""), "license": m.get("license", ""), "license_url": m.get("license_url", ""),
                     "page": m.get("page", ""), "url": "", "attribution": m.get("attribution", "")}
        mime = "image/png" if data.startswith(bytes([0x89]) + b"PNG") else "image/jpeg"
        slide.image_file = _store_image(candidate, data, mime, reviewed=False)["asset"]


def _rodar_node(args: list[str], app: Path, out_dir: Path, say: Callable[[str], None]) -> None:
    """Roda motor_pc.mjs, repassa o progresso e levanta o erro do Node, se houver."""
    # stderr vai para arquivo: com PIPE lido só no fim, muito aviso do Node travaria os dois processos.
    errlog = open(out_dir / "motor_node.log", "w", encoding="utf-8")
    proc = subprocess.Popen(args, cwd=app, stdout=subprocess.PIPE, stderr=errlog, text=True, encoding="utf-8",
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    erro = None
    for line in proc.stdout:
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev["evento"] == "progresso":
            say(ETAPAS.get(ev["etapa"], ev["etapa"]))
        elif ev["evento"] == "erro":
            erro = ev["mensagem"]
    proc.wait()
    errlog.close()
    if proc.returncode or erro:
        detalhe = (out_dir / "motor_node.log").read_text("utf-8", errors="replace")[-400:]
        raise RuntimeError(erro or detalhe or "motor do celular falhou")


def _app_dir() -> Path:
    app = _env_path("SLIDEDSL_MOBILE_APP", "D:/slidedsl-mobile/app")
    if not (app / "outputs/tests/pipeline/generate.js").is_file() or not (app / "bench/motor_pc.mjs").is_file():
        raise RuntimeError(f"Cópia do app incompleta em {app}: copie mobile/app (src, bench) e rode `npm test` lá.")
    return app


def refazer_celular(job_dir: Path, source: str, numero: int, instrucao: str, modelo: str,
                    progress: Callable[[str], None] | None = None) -> str:
    """Refaz o slide `numero` com o código do celular (edit.ts redoSlide: mesmo prompt e gramática com limites da
    geração), para trabalhos criados pelo motor do celular. Devolve o .slda novo; os outros slides não mudam."""
    from .alto import AltoDeck, parse_alto
    from .alto_edit import replace_slide

    say = progress or (lambda m: None)
    job_dir = Path(job_dir).resolve()
    deck = parse_alto(source)
    if not 1 <= numero <= len(deck.slides):
        raise ValueError("Número de slide fora do deck.")
    files = {i: s.image_file for i, s in enumerate(deck.slides) if s.image_file}
    sent = deck.model_copy(deep=True)
    for s in sent.slides:  # fotos ficam no PC; para o app basta a busca (imagem exige arquivo ou buscar)
        s.image_file = None
        if s.kind == "imagem" and not s.image_query:
            s.image_query = "foto"
    work = job_dir / "refazer"
    work.mkdir(exist_ok=True)
    roteiro = job_dir / "roteiro.json"
    estado = {"deck": sent.model_dump(mode="json"), "instrucao": instrucao,
              "facts": json.loads((job_dir / "fatos.json").read_text("utf-8")) if (job_dir / "fatos.json").is_file() else {},
              "roteiro": json.loads(roteiro.read_text("utf-8")) if roteiro.is_file() else None}
    (work / "estado.json").write_text(json.dumps(estado, ensure_ascii=False), "utf-8")
    url = servidor.garantir(modelo_local(modelo)["arquivo"], say)
    _rodar_node(["node", str(_app_dir() / "bench/motor_pc.mjs"), "--out", str(work), "--url", url,
                 "--refazer", str(numero), "--estado", str(work / "estado.json")], _app_dir(), work, say)
    novo = json.loads((work / "refeito.json").read_text("utf-8"))["slide"]
    slide = AltoDeck.model_validate({"title": deck.title, "slides": [novo]}).slides[0]
    if numero - 1 in files and slide.kind == "imagem":
        slide.image_file = files[numero - 1]
    return replace_slide(source, numero, slide)


def create_presentation_celular(request: str, out_dir: Path, *, modelo: str, n_slides: int = 5,
                                document_ids: list[str] | None = None, seed: int = 11, imagens: bool = False,
                                progress: Callable[[str], None] | None = None, preview: bool = True) -> dict:
    from .alto import AltoDeck, print_alto
    from .alto_compile import build_alto
    from .compiler import compile_ir

    say = progress or (lambda m: None)
    if not 4 <= n_slides <= 8:
        raise ValueError("No motor do celular, escolha de 4 a 8 slides.")
    if document_ids and len(document_ids) > 1:
        raise ValueError("No motor do celular, use um documento por vez (como no app).")
    out_dir = Path(out_dir).resolve()  # o Node roda na pasta do app
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    spec = modelo_local(modelo)
    url = servidor.garantir(spec["arquivo"], say)
    app = _env_path("SLIDEDSL_MOBILE_APP", "D:/slidedsl-mobile/app")
    script = app / "bench/motor_pc.mjs"
    if not (app / "outputs/tests/pipeline/generate.js").is_file() or not script.is_file():
        raise RuntimeError(f"Cópia do app incompleta em {app}: copie mobile/app (src, bench) e rode `npm test` lá.")
    (out_dir / "pedido.txt").write_text(request + "\n", "utf-8")
    args = ["node", str(script), "--pedido", request, "--slides", str(n_slides), "--out", str(out_dir),
            "--url", url, "--semente", str(seed)]
    if document_ids:
        args += ["--documento", str(_documento_para_node(document_ids[0], out_dir))]
    if imagens:
        args.append("--imagens")
    if spec.get("detalhe_literal"):  # modelos pequenos: detalhes = frases dos fatos, como no app
        args.append("--detalhe-literal")
    _rodar_node(args, app, out_dir, say)

    deck = AltoDeck.model_validate(json.loads((out_dir / "deck.json").read_text("utf-8")))
    _registrar_fotos(deck, out_dir)
    facts = json.loads((out_dir / "fatos.json").read_text("utf-8"))
    calls = json.loads((out_dir / "chamadas.json").read_text("utf-8"))
    diagnostics = json.loads((out_dir / "diagnosticos.json").read_text("utf-8"))
    if facts:
        _dossie(request, facts).save(out_dir / "dossie.json")
    with (out_dir / "chamadas.jsonl").open("w", encoding="utf-8") as f:
        for c in calls:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    (out_dir / "apresentacao.slda").write_text(print_alto(deck), "utf-8")
    fact_map = _dossie(request, facts).fact_map() if facts else {}
    built = build_alto(deck, fact_map)
    (out_dir / "validacao.json").write_text(json.dumps(built.report(), ensure_ascii=False, indent=2), "utf-8")
    report = {"request": request, "engine": "celular", "mode": "gramatica_limites+frases",
              "model": {"provider": "llamacpp", "model_requested": spec["arquivo"], "local_id": modelo},
              "calls": len(calls), "seconds": round(time.monotonic() - started, 1), "valid": built.success(),
              "fallback_slides": [d["slide"] for d in diagnostics if d.get("code") == "F001"]}
    if built.dsl:
        (out_dir / "apresentacao.sld").write_text(built.dsl, "utf-8")
    if built.success():
        info = compile_ir(built.validation.ir, out_dir / "apresentacao.pptx")
        report["pptx"] = str(out_dir / "apresentacao.pptx")
        report["inspection"] = {k: v for k, v in info["inspection"].items() if k != "slides"}
        if preview:
            from .ir_preview import contact_sheet, render_deck

            paths = render_deck(built.validation.ir, out_dir / "previa", 0.6)
            report["preview"] = str(contact_sheet(paths, out_dir / "previa.png"))
    else:
        report["errors"] = [d.model_dump() for d in built.errors]
    (out_dir / "relatorio.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), "utf-8")
    return report
