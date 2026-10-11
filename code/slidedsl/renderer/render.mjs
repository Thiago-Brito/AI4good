import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import pptxgen from 'pptxgenjs';

export function validateScene(deck) {
  if (deck.schema_version !== '1.1' || !['claro', 'escuro'].includes(deck.theme)) throw new Error('Versão/tema IR inválido.');
  if (deck.canvas?.width !== 1280 || deck.canvas?.height !== 720 || !deck.slides?.length) throw new Error('Canvas/slides inválidos.');
  for (const [index, slide] of deck.slides.entries()) {
    if (slide.number !== index + 1) throw new Error('Slides fora de ordem.');
    const ids = new Set();
    for (const e of slide.elements) {
      if (ids.has(e.id) || !/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(e.id)) throw new Error('ID inválido/duplicado.');
      ids.add(e.id);
      if (!['text', 'rectangle', 'ellipse', 'image', 'arrow'].includes(e.type)) throw new Error('Tipo não suportado.');
      if (![e.x,e.y,e.width,e.height,e.z].every(Number.isFinite) || e.width<=0 || e.height<=0 || !Number.isInteger(e.z)) throw new Error('Geometria inválida.');
      if (e.x<0 || e.y<0 || e.x+e.width>1280 || e.y+e.height>720) throw new Error('Objeto fora do canvas.');
      if (e.type!=='image' && !/^#[0-9A-Fa-f]{6}$/.test(e.color)) throw new Error('Cor inválida.');
      if (e.type==='text' && (typeof e.text!=='string' || !Number.isInteger(e.font_size) || e.font_size<10 || e.font_size>96)) throw new Error('Texto/fonte inválidos.');
    }
  }
}

export async function render(deck, output, root) {
  validateScene(deck);
  const pres = new pptxgen();
  pres.defineLayout({name:'SLIDEDSL',width:1280/96,height:720/96});
  pres.layout='SLIDEDSL';
  pres.author='SlideDSL'; pres.subject='Programa SlideDSL compilado'; pres.title=deck.title; pres.lang='pt-BR';
  const realRoot = await fs.realpath(root);
  for (const scene of deck.slides) {
    const slide = pres.addSlide();
    const credits = [];
    slide.background={color:deck.theme==='claro'?'F6F8FC':'14233D'};
    for (const e of [...scene.elements].sort((a,b)=>a.z-b.z)) {
      const rect={x:e.x/96,y:e.y/96,w:e.width/96,h:e.height/96};
      if (e.type==='text') {
        slide.addText(e.text,{...rect,objectName:e.id,fontFace:e.font_face,fontSize:e.font_size,
          color:e.color.slice(1),margin:6,breakLine:false,valign:'top',wrap:true,lang:'pt-BR',
          lineSpacingMultiple:1.2,align:'left',isTextBox:true});
      } else if (e.type==='image') {
        if (typeof e.file!=='string' || e.file.includes(':') || path.isAbsolute(e.file)) throw new Error('Imagem deve ser local e relativa.');
        const asset=await fs.realpath(path.resolve(realRoot,e.file));
        const relative=path.relative(realRoot,asset);
        if (relative.startsWith('..') || path.isAbsolute(relative) || !/\.(png|jpe?g)$/i.test(asset)) throw new Error('Asset fora da raiz ou formato inválido.');
        slide.addImage({...rect,sizing:{type:'contain',w:rect.w,h:rect.h},path:asset,altText:e.id,objectName:e.id});
        const mediaId = /^assets\/media\/([a-f0-9]{64})\.png$/.exec(e.file)?.[1];
        if (mediaId) {
          const metadata = JSON.parse(await fs.readFile(path.join(realRoot,'outputs/media/assets',mediaId+'.json'),'utf8'));
          credits.push(`${metadata.attribution}\nOrigem: ${metadata.page}\nLicença: ${metadata.license_url}\nArquivo convertido para PNG; exibição sem corte.`);
        }
      } else {
        slide.addShape(e.type==='arrow'?pres.ShapeType.downArrow:e.type==='rectangle'?pres.ShapeType.rect:pres.ShapeType.ellipse,
          {...rect,objectName:e.id,fill:{color:e.color.slice(1)},line:{color:e.color.slice(1),transparency:100}});
      }
    }
    slide.addNotes(`Slide ${scene.number}; objetos: ${scene.elements.map(e=>e.id).join(', ')}. Cena gerada pela SlideDSL.\n${credits.join('\n\n')}`);
  }
  await pres.writeFile({fileName:output,compression:true});
}

if (process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  try {
    const [input,output,root]=process.argv.slice(2);
    if (!input || !output || !root) throw new Error('Uso: node render.mjs IR.json saída.pptx raiz');
    const deck=JSON.parse(await fs.readFile(input,'utf8'));
    await render(deck,path.resolve(output),path.resolve(root));
    console.log(`PPTX gerado: ${deck.slides.length} slides.`);
  } catch (e) { console.error(e.message); process.exitCode=1; }
}
