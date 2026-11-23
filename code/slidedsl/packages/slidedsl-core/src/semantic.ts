// @ts-nocheck
import { bind, unkw } from './pythonCompat.js';
import themes from './data/themes.json' with { type: 'json' };
import { infer_role } from './semanticRole.js';
function model(args, defaults) { return {...defaults,...unkw(args[0]??{})}; }
// Construtores puros usados pelo Builder traduzido, equivalentes aos defaults Pydantic.
export const Diagnostic = (...args) => model(args,{slide:null,element:null,line:null,column:null,evidence:{},suggestion:'Revise o comando indicado.'});
export const Command = (...args) => model(args,{line:1,column:1,id:'',element_type:null,position:null,size:null,color:null,text:null,file:null,font_size:null,font_face:null,role:null,reference:null,axis:null,ids:[],value:null,bold:false,align:'left',rounded:false,children:[]});
export const Position = (...args) => model(args,{x:0,y:0,reference:null,margin:0});
export const SlideNode = (...args) => model(args,{line:1,column:1});
export const PresentationNode = SlideNode;
export const Element = (...args) => model(args,{z:0,text:null,file:null,font_size:null,font_face:'Arial',color:null,role:null,role_origin:null,source_line:null,source_column:null,bold:false,align:'left',rounded:false});
export class DSLException extends Error {
  constructor(public diagnostics) {super(diagnostics.map(d=>d.message).join('; '));}
}
export function analyze(...args) {
  const [ast,images={}]=bind(args,['ast','root'],[undefined,{}]);
  const theme=themes[ast.theme],slides=[],diagnostics=[];
  for(const sn of ast.slides) {
    const elements=[],notes=[];
    for(const c of sn.commands) {
      if(c.op==='notes'){if(c.text.trim())notes.push(c.text.trim());continue;}
      if(c.op!=='add')throw Error('O Builder Alto só emite add/notes.');
      if(c.element_type==='image'&&(!images[c.file]||images[c.file].missing||!/^((?!\.\.).)*\.(png|jpe?g)$/i.test(c.file)||/[:\\]/.test(c.file)||c.file.startsWith('/'))) {
        diagnostics.push(Diagnostic({code:'S007',severity:'ERRO',message:'Imagem ausente ou caminho inválido.',slide:sn.number,element:c.id,line:c.line,column:c.column,evidence:{command:c.op,file:c.file}}));continue;
      }
      const [x,y]=[c.position.x,c.position.y], [width,height]=c.size;
      let [role,origin]=infer_role(c.id,c.element_type,x,y,width,height);
      if(c.role!==null){role=c.role==='nenhum'?null:c.role;origin=role?'anotação explícita':null;}
      elements.push(Element({id:c.id,type:c.element_type,text:c.text,file:c.file?.replaceAll('\\','/')??null,x,y,width,height,color:c.color?.startsWith('#')?c.color.toUpperCase():theme.colors[c.color]??null,font_size:typeof c.font_size==='string'?theme.fonts[c.font_size]:c.font_size,font_face:c.font_face??theme.font_face,z:elements.length,role,role_origin:origin,source_line:c.line,source_column:c.column,bold:c.bold,align:c.align,rounded:c.rounded}));
    }
    slides.push({number:sn.number,elements,groups:[],relations:[],notes:notes.join('\n\n')||null});
  }
  if(diagnostics.length)throw new DSLException(diagnostics);
  return {schema_version:'1.1',title:ast.title,theme:ast.theme,canvas:{width:1280,height:720,unit:'px_logico'},slides};
}
// O Python imprime uma linha por comando e reparseia; reproduzir a proveniência
// sem serializar/parsing da DSL no telefone.
export function assignSourceLocations(ast) {
  let line=3;
  for(const slide of ast.slides){line++;for(const c of slide.commands){c.line=line++;c.column=5;}line++;}
  return ast;
}
