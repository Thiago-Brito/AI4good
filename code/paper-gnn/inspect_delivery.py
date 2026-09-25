"""Optional visual inspection with local Edge and PyMuPDF."""
import json
from pathlib import Path
import fitz
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from data import ROOT, OUTPUTS


def main():
    destination=ROOT.parents[1]/'academy/papers/artigo-overleaf/outputs/ordered-gnn'
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1365,'height':1000},device_scale_factor=1)
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto('http://127.0.0.1:8765',wait_until='networkidle')
        page.locator('#status').filter(has_text='Inferência concluída').wait_for()
        page.locator('#node').fill('1713'); page.locator('#run').click()
        page.wait_for_function("JSON.parse(document.querySelector('#raw').textContent).node_id === 1713")
        assert page.locator('#original .answer').inner_text() == 'Aprendizado baseado em casos'
        assert page.locator('#modified .answer').inner_text() == 'Teoria'
        # Exercita os exemplos de acerto E erro, além da consulta manual.
        expected = {1709: (2, 2, 2), 1713: (0, 5, 0), 1797: (1, 1, 4), 1708: (3, 0, 0)}
        for node, (truth, base, modified) in expected.items():
            page.locator(f'[data-node="{node}"]').click()
            page.wait_for_function(f"JSON.parse(document.querySelector('#raw').textContent).node_id === {node}")
            response = json.loads(page.locator('#raw').text_content())
            assert (response['target'], response['models']['original']['predicted_class'], response['models']['modified']['predicted_class']) == (truth, base, modified)
        assert 'Redes neurais' in page.locator('#expected').inner_text()
        assert 'Errou este documento' in page.locator('#original').inner_text()
        assert page.locator('#original .answer').inner_text() == 'Teoria'
        page.screenshot(path=str(destination/'demonstracao.png'),full_page=True)
        for link in ['/paper.pdf','/report.pdf']:
            response=page.request.get('http://127.0.0.1:8765'+link)
            assert response.status==200 and response.body().startswith(b'%PDF')
        assert not errors,errors
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        browser.close()
    document=fitz.open(destination/'samplepaper.pdf')
    thumbnails=[]
    for index,page in enumerate(document):
        pix=page.get_pixmap(matrix=fitz.Matrix(.8,.8))
        pix.save(destination/f'pagina-{index+1}.png')
        im=Image.open(destination/f'pagina-{index+1}.png').convert('RGB')
        im.thumbnail((330,470)); thumbnails.append(im.copy())
    sheet=Image.new('RGB',(3*350,((len(thumbnails)+2)//3)*500),'#dbe2eb')
    draw=ImageDraw.Draw(sheet)
    for i,im in enumerate(thumbnails):
        x=(i%3)*350+10; y=(i//3)*500+22
        draw.text((x,y-17),f'Pagina {i+1}',fill='black'); sheet.paste(im,(x,y))
    sheet.save(destination/'revisao-paginas.png')
    text='\n'.join(page.get_text() for page in document)
    (destination/'pdf-text.txt').write_text(text,encoding='utf-8')
    assert '87.23' in text and '87.10' in text
    result={'browser_errors':errors,'http_inference_node1713_verified':True,
            'four_guided_examples_verified':True, 'semantic_category_labels_verified':True,
            'pdf_links_verified':True,'mobile_no_horizontal_overflow':True,'pdf_pages':len(document)}
    (OUTPUTS/'delivery-inspection.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__': main()
