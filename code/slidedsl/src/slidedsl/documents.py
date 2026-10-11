"""Local bounded text extraction and lexical retrieval, without embeddings or uploads."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
from uuid import uuid4

from .paths import project_root

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_TEXT = 200_000


def document_root():
    return project_root() / "outputs/references"


def document_path(id):
    if not re.fullmatch(r"[a-f0-9]{32}", id):
        raise ValueError("Identificador de documento inválido.")
    path = (document_root() / id).resolve()
    if not path.is_relative_to(document_root().resolve()):
        raise ValueError("Documento fora da pasta local.")
    return path


def _pdf_text(path):
    from pypdf import PdfReader

    reader = PdfReader(path, strict=True)
    if reader.is_encrypted or len(reader.pages) > 50:
        raise ValueError("PDF criptografado ou com mais de 50 páginas.")
    pages, size = [], 0
    for number, page in enumerate(reader.pages, 1):
        contents = page.get_contents()
        if contents and len(contents.get_data()) > 16 * 1024 * 1024:
            raise ValueError("Página PDF excede o limite de processamento.")
        text = page.extract_text() or ""
        size += len(text)
        if size > MAX_TEXT:
            raise ValueError("Texto extraído excede 200 mil caracteres.")
        pages.append({"page": number, "text": text})
    return pages


def extract_pdf(path):
    import psutil

    process = subprocess.Popen(
        [sys.executable, "-m", "slidedsl.documents", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    # communicate drains pipes while checking time; subprocess bounds parser damage.
    started = time.monotonic()
    try:
        while True:
            try:
                output, error = process.communicate(timeout=0.2)
                break
            except subprocess.TimeoutExpired:
                if (
                    time.monotonic() - started > 15
                    or psutil.Process(process.pid).memory_info().rss > 512 * 1024 * 1024
                ):
                    process.kill()
                    process.communicate()
                    raise ValueError("PDF excede tempo ou memória de processamento.")
        if process.returncode:
            raise ValueError(
                "PDF inválido ou não processável: " + error.decode("utf-8", errors="replace")[-300:]
            )
        return json.loads(output)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def add_document(name, data):
    if not 0 < len(data) <= MAX_DOCUMENT_BYTES:
        raise ValueError("Documento vazio ou maior que 2 MiB.")
    suffix = Path(name).suffix.casefold()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise ValueError("Formatos suportados: TXT, Markdown e PDF textual.")
    folder = document_path(uuid4().hex)
    folder.mkdir(parents=True)
    path = folder / ("document" + suffix)
    path.write_bytes(data)
    try:
        if suffix == ".pdf":
            if not data.startswith(b"%PDF-"):
                raise ValueError("Assinatura PDF inválida.")
            pages = extract_pdf(path)
        else:
            text = data.decode("utf-8-sig")
            if "\x00" in text or len(text) > MAX_TEXT:
                raise ValueError("Texto binário ou longo demais.")
            pages = [{"page": None, "text": text}]
        chunks = []
        for page in pages:
            # Paragraphs first, then bounded pieces; no hidden content execution.
            for paragraph in re.split(r"\n\s*\n", page["text"]):
                for offset in range(0, len(paragraph), 900):
                    text = paragraph[offset : offset + 900].strip()
                    if text:
                        chunks.append(
                            {
                                "id": f"{folder.name}_c{len(chunks) + 1}",
                                "page": page["page"],
                                "text": text,
                            }
                        )
        if not chunks:
            raise ValueError("Documento sem texto extraível; OCR não está disponível.")
        record = {
            "id": folder.name,
            "name": Path(name.replace("\\", "/")).name[:180],
            "sha256": hashlib.sha256(data).hexdigest(),
            "format": suffix,
            "processed_utc": datetime.now(timezone.utc).isoformat(),
            "origin": "local upload",
            "chunks": chunks,
        }
        (folder / "index.json").write_text(json.dumps(record, ensure_ascii=False), "utf-8")
        return {k: v for k, v in record.items() if k != "chunks"} | {"chunk_count": len(chunks)}
    except Exception:
        for file in folder.iterdir():
            file.unlink()
        folder.rmdir()
        raise


def tokens(text):
    return re.findall(r"\w{3,}", text.casefold())


def retrieve(ids, query, *, max_chars=6000):
    if len(ids) > 8 or len(ids) != len(set(ids)):
        raise ValueError("Selecione até oito documentos diferentes.")
    chunks = []
    for id in ids:
        doc = json.loads((document_path(id) / "index.json").read_text("utf-8"))
        chunks.extend(
            {
                **c,
                "document_id": id,
                "document_name": doc["name"],
                "origin": doc["origin"],
                "processed_utc": doc["processed_utc"],
            }
            for c in doc["chunks"]
        )
    words = set(tokens(query))
    frequency = Counter(word for c in chunks for word in set(tokens(c["text"])))
    for chunk in chunks:
        counts = Counter(tokens(chunk["text"]))
        chunk["score"] = sum(
            math.log(1 + len(chunks) / (1 + frequency[w])) * min(3, counts[w]) for w in words
        )
    chunks.sort(key=lambda c: (-c["score"], c["id"]))
    selected, length = [], 0
    for chunk in chunks[:8]:
        if chunk["score"] > 0 and length + len(chunk["text"]) <= max_chars:
            selected.append(chunk)
            length += len(chunk["text"])
    return selected


def delete_document(id):
    folder = document_path(id)
    if folder.exists():
        for path in folder.iterdir():
            if path.is_file():
                path.unlink()
        folder.rmdir()


if __name__ == "__main__":
    try:
        print(json.dumps(_pdf_text(sys.argv[1]), ensure_ascii=True))
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
