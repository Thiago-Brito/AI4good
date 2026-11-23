import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {buildAlto,validateAlto} from '../dist/index.js';
import {round} from '../dist/pythonCompat.js';
import {textWidth,textHeight} from '../dist/textMetrics.js';
import {check_design} from '../dist/port.js';
import {difference} from './compare.mjs';
test('JSON novo: compilação determinística, sem alteração das entradas',()=>{
  const deck={title:'Novo conteúdo',theme:'natural',slides:[{kind:'capa',title:'Planejar a próxima etapa',subtitle:'Uma mensagem inédita fora das referências.'},{kind:'topicos',title:'Decisões locais ajudam a equipe',items:[{label:'Escopo definido',detail:'A equipe confere as tarefas antes de iniciar o trabalho.'},{label:'Revisão frequente',detail:'Cada entrega recebe uma revisão antes da apresentação.'}]}]};
  const original=structuredClone(deck),a=buildAlto(deck),b=buildAlto(deck);
  assert.ok(a.ir);assert.deepEqual(a,b);assert.deepEqual(deck,original);
  assert.ok(a.ir.slides[1].elements.some(e=>e.text==='Escopo definido'));
  assert.equal(a.ir.schema_version,'1.1');
});
test('validação A0xx mantém severidades e impede layout após erros',()=>{
  const deck={title:'Inválido',slides:[{kind:'grafico',title:'',bars:[{label:'a',value:-1}],sources:['F999']}]};
  const codes=validateAlto(deck,{}).map(d=>[d.code,d.severity]);
  for(const code of ['A002','A003','A004','A006'])assert.ok(codes.some(([c,s])=>c===code&&s==='ERRO'));
  assert.equal(buildAlto(deck,{}).ir,null);
  assert.equal(buildAlto({title:'Vazio',slides:[]}).diagnostics[0].code,'A001');
});
test('arredondamento Python e comparador exigem ordem/strings/z exatos',()=>{
  assert.deepEqual([round(.5),round(1.5),round(2.5),round(-.5),round(-1.5)],[0,2,2,0,-2]);
  assert.equal(difference({x:1.0000001},{x:1}),null);
  assert.ok(difference({x:1.00001},{x:1}));
  assert.ok(difference(['b','a'],['a','b']));assert.ok(difference({z:2},{z:1}));
});
test('D001–D010: geometria, contraste e overflow permanecem observáveis',()=>{
  const ir=buildAlto({title:'Teste',slides:[{kind:'capa',title:'Uma apresentação'}]}).ir;
  const title=ir.slides[0].elements.find(e=>e.type==='text');
  title.x=-2;title.color='#FFFFFF';title.width=2;title.height=2;
  title.font_face='Arial';title.font_size=10;
  const codes=check_design(ir).map(d=>d.code);
  for(const code of ['D001','D002','D003','D010'])assert.ok(codes.includes(code),code);
});
test('fontes e quebra de linha concordam com medições Python independentes',async()=>{
  const cases=JSON.parse(await fs.readFile(new URL('./data/text_metrics.json',import.meta.url),'utf8'));
  for(const c of cases) {
    assert.ok(Math.abs(textWidth(c.text,c.size,c.bold,c.family)-c.width)<=1e-6,JSON.stringify(c));
    assert.equal(textHeight(c.text,c.box,c.size,c.bold,c.family),c.height,JSON.stringify(c));
  }
});
test('D004–D009: relações, grupos, hierarquia, densidade, oclusão e dimensões',()=>{
  const ir=buildAlto({title:'Design',slides:[{kind:'capa',title:'Título'}]}).ir;
  const s=ir.slides[0],template=s.elements.find(e=>e.type==='text');
  const title={...template,id:'titulo',x:64,y:64,width:200,height:100,z:0,font_size:20,role:'titulo'};
  const body={...template,id:'corpo',x:1000,y:580,width:200,height:100,z:1,font_size:24,role:'corpo'};
  const overlay={...template,id:'overlay',type:'rectangle',text:null,font_size:null,role:null,x:0,y:0,width:1280,height:720,z:2};
  s.elements=[title,body,overlay,{...overlay,id:'zero',width:0,z:3}];
  s.groups=[{id:'g',members:['titulo','corpo'],source_line:1,label:null}];
  s.relations=[{kind:'left',target:'titulo',reference:'corpo',source_line:1,source_column:1,margin:0}];
  const codes=check_design(ir).map(d=>d.code);
  for(const code of ['D004','D005','D006','D007','D008','D009'])assert.ok(codes.includes(code),code);
});
test('fontes do pacote não importam APIs de Node nem referências de paridade',async()=>{
  const root=new URL('../src/',import.meta.url);
  for(const name of await fs.readdir(root))if(name.endsWith('.ts')){
    const source=await fs.readFile(new URL(name,root),'utf8');
    assert.doesNotMatch(source,/from\s+['"](?:node:|fs['"]|path['"])/,name);
    assert.doesNotMatch(source,/fixtures|outputs\/parity|child_process/,name);
  }
});
