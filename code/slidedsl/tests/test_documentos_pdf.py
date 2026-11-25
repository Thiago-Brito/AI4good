"""Limpeza e estrutura de PDF no fluxo do PC, igual à do app (teste com o PDF do TCC, 25/11/2026).

Usa as mesmas 15 páginas reais do app (mobile/app/test/fixtures/tcc_paginas.json) no lugar da extração do pypdf.
"""

import json
from pathlib import Path

import pytest

from slidedsl import documents

FIXTURE = Path(__file__).resolve().parents[1] / "mobile/app/test/fixtures/tcc_paginas.json"


@pytest.fixture
def tcc(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "document_root", lambda: tmp_path / "documents")
    pages = [{"page": p["page"], "text": p["text"]} for p in json.loads(FIXTURE.read_text("utf-8"))["paginas"]]
    monkeypatch.setattr(documents, "extract_pdf", lambda path: pages)
    info = documents.add_document("tcc.pdf", b"%PDF-1.7 fixture")
    return json.loads((documents.document_path(info["id"]) / "index.json").read_text("utf-8"))["chunks"]


def test_pdf_junta_hifenizacao_tira_cabecalhos_e_para_nas_referencias(tcc):
    text = "\n".join(c["text"] for c in tcc)
    assert "￾" not in text and "depender de serviços pagos" in text
    assert "T. Barbosa" not in text
    assert "arxiv.org" not in text and "doi.org" not in text
    assert all(c["page"] < 22 for c in tcc)


def test_pdf_secoes_de_nivel_1_como_titulo(tcc):
    headings = list(dict.fromkeys(c["heading"] for c in tcc if c["heading"]))
    assert headings[0] == "Resumo"
    assert {"1 Introdução", "6 Resultados", "7 Discussão e limitações", "8 Conclusão"} <= set(headings)
    assert not any(h.startswith("6.") for h in headings)  # subseções agrupadas na seção 6


def test_pdf_documento_usa_resumo_resultados_e_limitacoes(tcc, monkeypatch):
    # A recuperação narrativa do PC (resumo/resultado/limitações) passa a funcionar em PDF.
    ids = [tcc[0]["id"].rsplit("_c", 1)[0]]
    chosen = documents.retrieve(ids, "Apresente os resultados e as limitações do trabalho", max_chunks=6)
    heads = {c["heading"] for c in chosen}
    assert "6 Resultados" in heads or "7 Discussão e limitações" in heads


def test_texto_e_markdown_seguem_como_antes(tmp_path, monkeypatch):
    monkeypatch.setattr(documents, "document_root", lambda: tmp_path / "documents")
    info = documents.add_document("a.txt", "1 Evaporação\n\nO sol aquece a água.\n\nReferências\n\nAutor, 2020.".encode())
    chunks = json.loads((documents.document_path(info["id"]) / "index.json").read_text("utf-8"))["chunks"]
    assert "Autor, 2020." in "\n".join(c["text"] for c in chunks)
    assert all(c["heading"] == "" for c in chunks)
