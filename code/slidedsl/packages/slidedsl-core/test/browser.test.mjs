import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import vm from 'node:vm';
import {slidesInZip} from './zip.mjs';
test('renderPptx gera ZIP em ambiente sem process/Buffer/require/fs',async()=>{
  const bundle=await fs.readFile(new URL('pptxgen.bundle.js',import.meta.resolve('pptxgenjs')),'utf8');
  const code=(await fs.readFile(new URL('../dist/render.js',import.meta.url),'utf8'))
    .replace("import pptxgen from 'pptxgenjs';",'')
    .replace('export async function renderPptx','async function renderPptx');
  // PptxGenJS browser + a mesma função compilada do pacote. Só agendadores
  // Web são fornecidos ao JSZip; não há objetos de Node no contexto isolado.
  const context=vm.createContext({setTimeout,clearTimeout,console});
  vm.runInContext(bundle,context);
  context.pptxgen=context.PptxGenJS;
  vm.runInContext(code+'\nglobalThis.renderPptx=renderPptx;',context);
  for(const name of ['process','Buffer','require','fs'])assert.equal(vm.runInContext('typeof '+name,context),'undefined');
  const ir={schema_version:'1.1',title:'Sem Node',theme:'claro',canvas:{width:1280,height:720},slides:[{number:1,elements:[
    {id:'titulo',type:'text',x:64,y:64,width:800,height:100,z:0,text:'Ambiente sem Node',font_size:42,font_face:'Calibri',color:'#14233D'},
    {id:'foto',type:'image',x:64,y:220,width:100,height:100,z:1,file:'image.png'},
  ]}]};
  const bytes=await context.renderPptx(ir,{images:{'image.png':'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='}});
  const slides=slidesInZip(new Uint8Array(bytes));
  assert.equal(slides.length,1);assert.deepEqual(slides[0].texts,['Ambiente sem Node']);
  assert.equal(slides[0].shapes,1);assert.equal(slides[0].pictures,1);
});
