// @ts-nocheck
import pptxgen from 'pptxgenjs';
import type { Presentation } from './ir.js';
export interface RenderOptions { images?: Record<string,string> }
/** IR → PPTX editável. Entradas de imagem são data URIs, saída sem filesystem. */
export async function renderPptx(deck: Presentation, {images={}}: RenderOptions = {}): Promise<ArrayBuffer> {
  if(deck.schema_version!=='1.1'||!['claro','escuro'].includes(deck.theme)||deck.canvas.width!==1280||deck.canvas.height!==720||!deck.slides.length)throw Error('IR inválida.');
  const pres=new pptxgen();
  pres.defineLayout({name:'SLIDEDSL',width:1280/96,height:720/96});pres.layout='SLIDEDSL';
  pres.author='SlideDSL';pres.subject='Programa SlideDSL compilado';pres.title=deck.title;pres.lang='pt-BR';
  for(const scene of deck.slides) {
    const slide=pres.addSlide();slide.background={color:deck.theme==='claro'?'F6F8FC':'14233D'};
    for(const e of [...scene.elements].sort((a,b)=>a.z-b.z)) {
      const rect={x:e.x/96,y:e.y/96,w:e.width/96,h:e.height/96};
      if(e.type==='text') {
        const split=e.id.endsWith('_ref_inline')?e.text.indexOf(': '):-1;
        const content=split<0?e.text:[{text:e.text.slice(0,split+2),options:{bold:true}},{text:e.text.slice(split+2),options:{bold:false}}];
        slide.addText(content,{...rect,objectName:e.id,fontFace:e.font_face,fontSize:e.font_size,color:e.color.slice(1),bold:Boolean(e.bold)||e.id.endsWith('_ref_label'),margin:6,breakLine:false,valign:e.align==='center'?'middle':'top',wrap:true,lang:'pt-BR',lineSpacingMultiple:1.2,align:e.align||'left',isTextBox:true});
      } else if(e.type==='image') {
        const data=images[e.file];if(typeof data!=='string'||!/^data:image\/(png|jpeg);base64,/.test(data))throw Error('Imagem exige data URI PNG/JPEG: '+e.file);
        const bleed=/^s\d+_imagem_\d+$/.test(e.id)&&e.x===664&&e.y===0;
        slide.addImage({...rect,sizing:{type:bleed?'crop':'contain',w:rect.w,h:rect.h},data,altText:e.id,objectName:e.id});
      } else {
        const shape=e.type==='arrow'?pres.ShapeType.downArrow:e.type==='rectangle'?(e.rounded?pres.ShapeType.roundRect:pres.ShapeType.rect):pres.ShapeType.ellipse;
        slide.addShape(shape,{...rect,objectName:e.id,fill:{color:e.color.slice(1)},line:{color:e.color.slice(1),transparency:100},...(e.rounded?{rectRadius:.12}:{})});
      }
    }
    slide.addNotes(`${scene.notes?scene.notes+'\n\n':''}Slide ${scene.number}; objetos: ${scene.elements.map(e=>e.id).join(', ')}. Cena gerada pela SlideDSL.\n`);
  }
  return await pres.write({outputType:'arraybuffer',compression:true}) as ArrayBuffer;
}
