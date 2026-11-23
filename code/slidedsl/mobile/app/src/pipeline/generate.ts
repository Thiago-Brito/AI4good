import {buildAlto, renderPptx, type AltoDeck, type AltoSlide, type Diagnostic, type Facts, type SlideKind, type Presentation} from '@slidedsl/core';
import {prompts, schemaErrors, schemaWithFacts} from './contracts.js';
import {collectFacts, type SourceChoice, type FetchText, type ReadDocument, type DocumentUsage} from './sources.js';
import {genericDocumentRequest, MAX_EXTRACT_CALLS} from './documents.js';
import {Recorder} from './usage.js';
import {checkCancelled, type CallRecord, type JsonSchema, type TextModel} from './types.js';
export interface Progress {stage: string; slide?: number; total: number}
export interface GenerationResult {
  deck: AltoDeck; ir: Presentation; pptx: ArrayBuffer; diagnostics: Diagnostic[];
  calls: CallRecord[]; facts: Facts; source: Awaited<ReturnType<typeof collectFacts>>;
  wall_ms: number; max_calls: number;
}
export class GenerationError extends Error {
  constructor(message: string, readonly diagnostics: Diagnostic[]) { super(message); }
}
// Conversion of the Python json_to_slide field mapping; data is schema-validated first.
export function jsonToSlide(kind: SlideKind, data: Record<string, any>): AltoSlide {
  const text = (key: string) => (data[key] as string | undefined)?.trim() || null;
  const items = (values: any[] = []) => values.map(v => ({label: v.rotulo.trim(), detail: v.detalhe?.trim() || null}));
  return {kind, title: text('titulo'), subtitle: text('subtitulo'), author: text('autor'),
    text: text('texto'), caption: text('legenda'), unit: text('unidade'), notes: text('notas'),
    items: items(data.itens), values: (data.valores ?? []).map((v: any) => ({value: v.valor.trim(), label: v.legenda.trim()})),
    sides: (data.lados ?? []).map((v: any) => ({name: v.nome.trim(), items: items(v.itens)})),
    milestones: (data.marcos ?? []).map((v: any) => ({date: v.data.trim(), label: v.rotulo.trim(), detail: v.detalhe?.trim() || null})),
    bars: (data.barras ?? []).map((v: any) => ({label: v.rotulo.trim(), value: v.valor})),
    sources: [...new Set<string>(data.fontes ?? [])]};
}
interface PlanSlide {tipo: SlideKind; mensagem: string; objetivo: string; fatos?: string[]}
interface Outline {titulo: string; slides: PlanSlide[]}
export interface GenerateOptions {
  request: string; slides: number; source: SourceChoice; model: TextModel;
  fetchJson?: FetchText; signal?: AbortSignal; onProgress?: (p: Progress) => void;
  onCalls?: (c: CallRecord[]) => void;
  readDocument?: ReadDocument; onDocument?: (doc: DocumentUsage) => void;
}
export async function generate(options: GenerateOptions): Promise<GenerationResult> {
  const {slides: n, source: choice, model, signal} = options;
  const request = options.request.trim() || (choice.mode === 'document' ? `Apresente os pontos principais do documento ${choice.document.name}` : '');
  if (!request.trim() || request.length > 600) throw Error('Escreva um pedido de até 600 caracteres.');
  if (!Number.isInteger(n) || n < 4 || n > 8) throw Error('Escolha de 4 a 8 slides.');
  const start = Date.now(), maxCalls = 1 + 2 * n + (choice.mode === 'none' ? 0 : choice.mode === 'document' ? MAX_EXTRACT_CALLS : 1);
  const recorder = new Recorder(model, maxCalls, signal, options.onCalls);
  const progress = (stage: string, slide?: number) => { checkCancelled(signal); options.onProgress?.({stage, slide, total: n}); };
  progress(choice.mode === 'none' ? 'Sem pesquisa' : 'Extraindo fatos da fonte');
  const source = await collectFacts(choice, request, recorder, options.fetchJson, signal, options.readDocument, progress, options.onDocument);
  const facts = source.facts, ids = Object.keys(facts), mode = ids.length ? 'with_facts' : 'without_facts';
  const factsBlock = (selected = ids) => JSON.stringify(Object.fromEntries(selected.slice(0, 3).filter(id => id in facts).map(id => [id,
    {claim: facts[id].claim, quote: String(facts[id].quote).slice(0, 300), kind: facts[id].kind, value: facts[id].value}])));
  progress('Planejando roteiro');
  const outlineSchema = schemaWithFacts((prompts.outline_schemas as Record<string, any>)[String(n)][mode], ids);
  const sections = genericDocumentRequest(request) ? source.document?.sections ?? [] : [];
  const sectionPrompt = sections.length ? `\nSeções do documento em ordem; cubra estes assuntos no roteiro, agrupando se necessário. A capa pode apresentar a primeira seção. Use os IDs correspondentes:\n${JSON.stringify(sections)}` : '';
  const raw = await recorder.json('roteiro', prompts.outline_system[mode],
    `Pedido: ${request}\nNúmero de slides: ${n}\nFatos da pesquisa:\n${factsBlock()}${sectionPrompt}`, outlineSchema);
  const outlineErrors = schemaErrors(raw, outlineSchema);
  if (outlineErrors.length) throw Error(`Roteiro inválido: ${outlineErrors.join('; ')}`);
  const outline = raw as Outline;
  if (outline.slides[0].tipo !== 'capa' || outline.slides[n - 1].tipo !== 'conclusao') throw Error('O roteiro deve começar com capa e terminar com conclusão.');
  const deck: AltoDeck = {title: outline.titulo, theme: 'claro', slides: []};
  const summary = outline.slides.map((s, i) => `${i + 1}. ${s.tipo}: ${s.mensagem}`).join('\n');
  for (let i = 0; i < n; i++) {
    const plan = outline.slides[i], kind = plan.tipo;
    const schema: JsonSchema = schemaWithFacts((prompts.slide_schemas as Record<string, any>)[kind][mode], ids);
    const base = `Pedido original: ${request}\nApresentação: ${deck.title}\nRoteiro:\n${summary}\nEscreva o slide ${i + 1} (tipo ${kind}).\nMensagem: ${plan.mensagem}\nObjetivo: ${plan.objetivo}\nRegras do tipo: ${(prompts.kind_rules as Record<string, string>)[kind]}\nFatos para este slide:\n${factsBlock(plan.fatos?.length ? plan.fatos : ids)}\nTítulos já escritos (não repetir): ${deck.slides.map(s => s.title).join('; ')}`;
    let accepted: AltoSlide | null = null, previous = '', diagnostics: Diagnostic[] = [];
    for (let attempt = 0; attempt <= 1; attempt++) {
      progress(attempt ? `Reparando slide ${i + 1}/${n}` : `Slide ${i + 1}/${n}`, i + 1);
      try {
        const data = await recorder.json('slide', prompts.content_system,
          attempt ? `${base}\nResposta anterior:\n${previous.slice(0, 2200)}\nCorrija os diagnósticos mantendo o tipo:\n${JSON.stringify(diagnostics.filter(d => d.severity !== 'INFORMAÇÃO').slice(0, 8).map(d => ({code: d.code, severity: d.severity, message: d.message, path: d.evidence?.path, suggestion: d.suggestion})))}` : base,
          schema, i + 1, attempt);
        previous = JSON.stringify(data);
        const errors = schemaErrors(data, schema);
        if (errors.length) { accepted = null; diagnostics = errors.map(message => ({code: 'P002', severity: 'ERRO', slide: i + 1, message})); }
        else {
          accepted = jsonToSlide(kind, data as Record<string, any>);
          // The cover must not invent an author, as in alto_generation.py.
          if (kind === 'capa' && accepted.author && !request.toLowerCase().includes(accepted.author.toLowerCase())) accepted.author = null;
          if (!ids.length) accepted.notes = `conteúdo sem fontes\n${accepted.notes ?? ''}`;
          const built = buildAlto({...deck, slides: [...deck.slides, accepted]}, facts);
          diagnostics = built.diagnostics.filter(d => d.slide == null || d.slide === i + 1);
        }
      } catch (e) {
        checkCancelled(signal);
        accepted = null;
        diagnostics = [{code: 'P002', severity: 'ERRO', slide: i + 1, message: e instanceof Error ? e.message : String(e)}];
      }
      const actionable = diagnostics.filter(d => d.severity === 'ERRO' || (d.severity === 'AVISO' && d.code !== 'A009'));
      if (accepted && !actionable.length) break;
      if (attempt === 1 && (!accepted || diagnostics.some(d => d.severity === 'ERRO'))) throw new GenerationError(`Slide ${i + 1} continua inválido após um reparo.`, diagnostics);
    }
    if (!accepted) throw new GenerationError(`Slide ${i + 1} inválido.`, diagnostics);
    deck.slides.push(accepted);
    // Yield to native UI between CPU-bound compiler passes.
    await new Promise<void>(resolve => setTimeout(resolve, 0));
  }
  progress('Validando apresentação');
  const built = buildAlto(deck, facts);
  if (!built.ir || built.diagnostics.some(d => d.severity === 'ERRO')) throw new GenerationError('Apresentação inválida após compilação.', built.diagnostics);
  progress('Gerando PowerPoint editável');
  const pptx = await renderPptx(built.ir);
  checkCancelled(signal);
  progress('Concluído');
  return {deck, ir: built.ir, pptx, calls: recorder.calls, diagnostics: built.diagnostics, source, facts,
    wall_ms: Date.now() - start, max_calls: maxCalls};
}
