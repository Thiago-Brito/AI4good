import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {render,validateScene} from '../../../renderer/render.mjs';
import {renderPptx,buildAlto} from '../dist/index.js';
import {readFixture} from './compare.mjs';
import {slidesInZip} from './zip.mjs';
const fixtures=new URL('./fixtures/',import.meta.url);
const manifest=JSON.parse(await fs.readFile(new URL('manifest.json',fixtures),'utf8'));
const out=new URL(`../../../outputs/apk-core-render/${process.pid}/`,import.meta.url);
await fs.mkdir(out,{recursive:true});
const pixel='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
await fs.writeFile(new URL('image.png',out),Buffer.from(pixel.split(',')[1],'base64'));
for(const row of manifest.entries.filter(r=>r.has_ir)) {
  const fixture=await readFixture(new URL(row.id+'/',fixtures));
  const ir=buildAlto(fixture.deck,fixture.facts,fixture.images).ir;
  // O renderer existente rejeita cenas fora do canvas antes de gerar o ZIP.
  // Tais cenas continuam comparadas integralmente em parity.test.mjs.
  try{validateScene(ir);}catch{continue;}
  test(`PPTX textos/formas: ${row.id}`,async()=>{
    const deck=structuredClone(ir);
    for(const s of deck.slides)for(const e of s.elements)if(e.type==='image')e.file='image.png';
    const actual=await renderPptx(deck,{images:{'image.png':pixel}});
    assert.ok(actual instanceof ArrayBuffer);
    const target=new URL(row.id+'.pptx',out);
    await render(deck,fileURLToPath(target),fileURLToPath(out));
    const a=slidesInZip(actual),b=slidesInZip(await fs.readFile(target));
    assert.equal(a.length,deck.slides.length);assert.deepEqual(a,b);
    assert.equal(a.reduce((n,s)=>n+s.shapes+s.pictures,0),deck.slides.reduce((n,s)=>n+s.elements.length,0));
    await fs.writeFile(new URL(row.id+'-ts.pptx',out),Buffer.from(actual));
  });
}
test('PPTX preserva imagem via data URI e formas editáveis',async()=>{
  const ir={schema_version:'1.1',title:'Contrato de renderização',theme:'claro',canvas:{width:1280,height:720,unit:'px_logico'},slides:[{number:1,notes:'Notas',groups:[],relations:[],elements:[
    {id:'titulo',type:'text',x:64,y:64,width:500,height:100,z:0,text:'Ação & evidência',font_size:42,font_face:'Georgia',color:'#14233D',bold:true,align:'left'},
    ...['rectangle','ellipse','arrow','image'].map((type,i)=>({id:'forma'+i,type,x:64+i*200,y:220,width:160,height:120,z:i+1,color:type==='image'?null:'#2563EB',file:type==='image'?'image.png':null,rounded:type==='rectangle'}))]}]};
  const a=await renderPptx(ir,{images:{'image.png':pixel}}),target=new URL('formas.pptx',out);
  await render(ir,fileURLToPath(target),fileURLToPath(out));
  assert.deepEqual(slidesInZip(a),slidesInZip(await fs.readFile(target)));
  assert.equal(slidesInZip(a)[0].pictures,1);assert.equal(slidesInZip(a)[0].shapes,4);
  await assert.rejects(renderPptx(ir),/data URI/);
  await fs.writeFile(new URL('formas-ts.pptx',out),Buffer.from(a));
});
