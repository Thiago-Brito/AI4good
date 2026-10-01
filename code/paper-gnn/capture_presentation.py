"""Capturas reais da aplicação para a apresentação; não simula resultados."""
import json
from pathlib import Path
import pymupdf
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'outputs/apresentacao-ordered-gnn'
DEST.mkdir(parents=True, exist_ok=True)
PAPER = ROOT / 'academy/papers/artigo-overleaf/outputs/ordered-gnn'

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:8765',wait_until='networkidle')
    page.wait_for_function("document.querySelector('#raw').textContent.length > 20")
    page.screenshot(path=str(DEST/'aplicacao-inicio.png'))
    for node in [1713,1708]:
        page.locator(f'[data-node="{node}"]').click()
        page.wait_for_function(f"JSON.parse(document.querySelector('#raw').textContent).node_id === {node}")
        page.locator('[aria-label="Respostas dos dois modelos"]').screenshot(path=str(DEST/f'aplicacao-documento-{node}.png'))
        (DEST/f'inferencia-{node}.json').write_text(page.locator('#raw').text_content(),encoding='utf-8')
    assert not errors, errors
    browser.close()
for name,file in [('artigo','artigo-original-2023.pdf'),('relatorio','samplepaper.pdf')]:
    doc=pymupdf.open(PAPER/file)
    doc[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(DEST/f'{name}-pagina1.png')
print(DEST)
