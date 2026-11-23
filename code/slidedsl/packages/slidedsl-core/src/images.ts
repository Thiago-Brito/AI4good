// @ts-nocheck
import {bind} from './pythonCompat.js';
export function variants_for(...args) {
  const [s,images={}]=bind(args,['s','root'],[undefined,{}]);
  if(s.kind==='topicos')return s.items.length===4?['cards','rows','grid']:['cards','rows'];
  if(s.kind==='conclusao')return ['actions_columns','actions_rows'];
  if(s.kind==='numeros')return ['number_columns','number_rows'];
  if(s.kind==='comparacao')return ['comparison_columns','comparison_pairs','comparison_text'];
  if(s.kind==='imagem'&&s.image_file){const image=images[s.image_file];return [image&&!image.missing&&Math.max(image.width,image.height)<600?'photo_text':'photo50'];}
  return [s.kind==='imagem'?'cards':s.kind];
}
export function photo(...args) {
  const [b,s,base]=bind(args,['b','s','base','top'],[undefined,undefined,undefined,null]);
  const image=b.root?.[s.image_file];
  if(image&&!image.missing&&Math.max(image.width,image.height)<1000) {
    b.diagnostics.push({code:'A031',severity:'AVISO',message:'Imagem local com lado maior abaixo de 1000 px.',slide:b.number,evidence:{path:base+'.image_file',file:s.image_file,width:image.width,height:image.height,minimum:1000}});
    if(Math.max(image.width,image.height)<600)return false;
  }
  b.image('imagem',s.image_file,664,0,616,600);
  let credit='Imagem local · direitos não informados';const asset=image?.metadata;
  if(asset) {
    let author=String(asset.author??'').split(/\r?\n/).map(s=>s.trim().replace(/\s+/g,' ')).find(Boolean)||'Wikimedia Commons';
    if(author.length>54)author=author.slice(0,51).split(' ').slice(0,-1).join(' ')+'…';
    credit=author+' · '+(asset.license||'ver notas');
    b.notes('Imagem: '+(asset.attribution??'')+'\n'+(asset.page??'')+'\n'+(asset.license_url??''));
  }
  const h=b.fit(credit,584,48,[12],false,base+'.image_file')[1];
  b.text('credito',credit,680,604,584,h,12,b.palette.muted);
  return true;
}
