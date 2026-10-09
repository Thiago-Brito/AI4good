import test from 'node:test';
import assert from 'node:assert/strict';
import { validateScene, render } from './render.mjs';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const scene=()=>({schema_version:'1.1',theme:'claro',title:'Teste',canvas:{width:1280,height:720},slides:[{number:1,elements:[{id:'a',type:'text',text:'Texto editável',x:80,y:80,width:600,height:100,z:0,font_size:24,font_face:'Arial',color:'#14233D'}]}]});
test('rejeita geometria inválida antes de renderizar',()=>{
  const d=scene(); d.slides[0].elements[0].width=-20;
  assert.throws(()=>validateScene(d),/Geometria/);
});
test('gera um ZIP PowerPoint real com caminho contendo espaços',async()=>{
  const temp=await fs.mkdtemp(path.join(os.tmpdir(),'slidedsl node '));
  try {
    const output=path.join(temp,'apresentação teste.pptx');
    await render(scene(),output,temp);
    const bytes=await fs.readFile(output);
    assert.equal(bytes.subarray(0,2).toString(),'PK');
    assert.ok(bytes.length>1000);
  } finally {await fs.rm(temp,{recursive:true,force:true});}
});
