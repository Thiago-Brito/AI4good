import { validateAlto, normalizeDeck, type AltoDeck } from './alto.js';
import { alto_to_ast, check_design, content_occupancy } from './port.js';
import { analyze, assignSourceLocations, DSLException } from './semantic.js';
import type { Diagnostic, Facts, Images, Presentation } from './ir.js';
export * from './alto.js';
export type * from './ir.js';
export { renderPptx } from './render.js';
export interface BuildResult { ir: Presentation|null; diagnostics: Diagnostic[] }
export function buildAlto(deck: AltoDeck, facts: Facts|null = null, images: Images = {}): BuildResult {
  deck=normalizeDeck(deck);
  const diagnostics=validateAlto(deck,facts);
  if(diagnostics.some(d=>d.severity==='ERRO'))return {ir:null,diagnostics};
  const [ast,,layoutDiagnostics]=alto_to_ast(deck,facts,images);
  diagnostics.push(...layoutDiagnostics);
  try {
    const ir=analyze(assignSourceLocations(ast),images) as Presentation;
    for(let i=0;i<ir.slides.length;i++) {
      if(['capa','secao','citacao'].includes(deck.slides[i].kind))continue;
      const fraction=content_occupancy(ir.slides[i]);
      if(fraction<.30)diagnostics.push({code:'A021',severity:'AVISO',slide:i+1,message:'Baixa ocupação da área útil por caixas de conteúdo.',evidence:{fraction,minimum:.30},suggestion:'Distribua melhor a altura ou escolha outra composição.'});
    }
    diagnostics.push(...check_design(ir));
    return {ir,diagnostics};
  } catch(error) {
    if(error instanceof DSLException)return {ir:null,diagnostics:[...diagnostics,...error.diagnostics]};
    throw error;
  }
}
