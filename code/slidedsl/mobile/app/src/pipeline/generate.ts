import {buildAlto, renderPptx, type AltoDeck, type AltoSlide, type Diagnostic, type Facts, type SlideKind, type Presentation} from '@slidedsl/core';
import {prompts, schemaErrors, schemaWithFacts} from './contracts.js';
import type {ExtractMode} from './sentences.js';
import {collectFacts, type SourceChoice, type FetchText, type ReadDocument, type DocumentUsage} from './sources.js';
import {genericDocumentRequest, MAX_EXTRACT_CALLS} from './documents.js';
import {Recorder} from './usage.js';
import {cleanVisible} from './editorial.js';
import {resolveImages, type DeckImages, type ImageSource} from './images.js';
import {altoFormatHint, altoToJson, slideGrammar, truncatedPaths, withCompilerLimits} from './altoText.js';
/** Como o modelo escreve cada slide: JSON Schema; SlideDSL Alto sob gramática com os mesmos campos e limites
 * folgados do JSON; ou a mesma gramática com os limites de texto do compilador (gramatica_limites). */
export type SlideMode = 'json' | 'gramatica' | 'gramatica_limites';
import {checkCancelled, type CallRecord, type JsonSchema, type TextModel} from './types.js';
export interface Progress {stage: string; slide?: number; total: number}
export interface GenerationResult {
  deck: AltoDeck; ir: Presentation; pptx: ArrayBuffer; diagnostics: Diagnostic[];
  calls: CallRecord[]; facts: Facts; source: Awaited<ReturnType<typeof collectFacts>>;
  wall_ms: number; max_calls: number;
  /** Para editar depois (refazer um slide com o mesmo prompt): pedido, roteiro e modo de escrita. */
  request: string; outline: Outline; slideMode: SlideMode;
  /** Fotos dos slides "imagem" (com Fotos da internet ligado): dimensões/crédito e data URIs. */
  images: DeckImages;
}
export class GenerationError extends Error {
  constructor(message: string, readonly diagnostics: Diagnostic[]) { super(message); }
}
// Conversion of the Python json_to_slide field mapping; data is schema-validated first.
export function jsonToSlide(kind: SlideKind, data: Record<string, any>): AltoSlide {
  const text = (key: string) => (data[key] as string | undefined)?.trim() || null;
  const items = (values: any[] = []) => values.map(v => ({label: v.rotulo.trim(), detail: v.detalhe?.trim() || null}));
  return {kind, title: text('titulo'), subtitle: text('subtitulo'), author: text('autor'),
    text: text('texto'), caption: text('legenda'), unit: text('unidade'), notes: text('notas'), image_query: text('busca_imagem'),
    items: items(data.itens), values: (data.valores ?? []).map((v: any) => ({value: v.valor.trim(), label: v.legenda.trim()})),
    sides: (data.lados ?? []).map((v: any) => ({name: v.nome.trim(), items: items(v.itens)})),
    milestones: (data.marcos ?? []).map((v: any) => ({date: v.data.trim(), label: v.rotulo.trim(), detail: v.detalhe?.trim() || null})),
    bars: (data.barras ?? []).map((v: any) => ({label: v.rotulo.trim(), value: v.valor})),
    sources: [...new Set<string>(data.fontes ?? [])]};
}
export interface PlanSlide {tipo: SlideKind; mensagem: string; objetivo: string; fatos?: string[]}
const TRAILING = new Set(['a', 'o', 'as', 'os', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
  'para', 'por', 'pelo', 'pela', 'com', 'sem', 'e', 'ou', 'que', 'se', 'ao', 'aos', 'à', 'às', 'é']);
export function shortTitle(text: string, max: number): string {
  let out = '';
  for (const word of text.trim().split(/\s+/)) {
    const next = out ? `${out} ${word}` : word;
    if (next.length > max) break;
    out = next;
  }
  // Não terminar em artigo/preposição/conjunção ("... alternativa para a"), visto no emulador em 23/11.
  const words = out.split(' ');
  while (words.length > 2 && TRAILING.has(words[words.length - 1].toLowerCase().replace(/[,.;:]$/, ''))) words.pop();
  out = words.join(' ').replace(/[,;:]$/, '');
  return out || text.trim().slice(0, max);
}
/** Slide montado pelo compilador quando a IA falha após o reparo (teste no emulador, 23/11/2026:
 * a capa do Qwen3 0.6B continuou inválida e a geração inteira era abortada). Capa: título do roteiro;
 * demais tipos: divisória com a mensagem planejada. Sem nova chamada ao modelo. */
function fallbackSlide(kind: SlideKind, plan: PlanSlide, deckTitle: string, deck: AltoDeck, facts: Facts): AltoSlide | null {
  const fbKind: SlideKind = kind === 'capa' ? 'capa' : 'secao';
  const source = kind === 'capa' ? deckTitle : plan.mensagem;
  for (const max of [60, 40, 28]) {
    const slide = jsonToSlide(fbKind, {titulo: shortTitle(source, max)});
    slide.notes = `Slide montado pelo compilador após falha da IA. Mensagem planejada: ${plan.mensagem}`;
    const built = buildAlto({...deck, slides: [...deck.slides, slide]}, facts);
    const own = built.diagnostics.filter(d => d.slide == null || d.slide === deck.slides.length + 1);
    if (!own.some(d => d.severity === 'ERRO')) return slide;
  }
  return null;
}
export interface Outline {titulo: string; slides: PlanSlide[]}
/** Porte de fix_outline (alto_generation.py): o primeiro slide vira capa, o último conclusão e capas no meio
 * viram tópicos. Na bancada de 24/11 (Qwen3 1.7B), um roteiro sem capa/conclusão abortava o deck inteiro. */
export function fixOutline(outline: Outline, images = false): Outline {
  const slides = outline.slides.map(s => ({...s}));
  if (slides.length) slides[0].tipo = 'capa';
  if (slides.length > 1) slides[slides.length - 1].tipo = 'conclusao';
  for (const s of slides.slice(1, -1)) if (s.tipo === 'capa') s.tipo = 'topicos';
  // Com fotos ligadas, ao menos um slide imagem (como o PC: o 0.6B e o 1.7B quase nunca o escolhem sozinhos).
  if (images && slides.length >= 4 && !slides.some(s => s.tipo === 'imagem')) slides[1].tipo = 'imagem';
  return {...outline, slides};
}
export interface GenerateOptions {
  request: string; slides: number; source: SourceChoice; model: TextModel;
  fetchJson?: FetchText; signal?: AbortSignal; onProgress?: (p: Progress) => void;
  onCalls?: (c: CallRecord[]) => void;
  readDocument?: ReadDocument; onDocument?: (doc: DocumentUsage) => void;
  slideMode?: SlideMode;
  /** Só em gramatica_limites: campo que chegou ao limite (cortado) vira aviso e pede 1 reparo. Padrão: não —
   * na bancada de 24/11 o reparo não reduziu os cortes (28/673 × 31/677) e custou +22% de reparos. */
  repairTruncated?: boolean;
  /** Leitura do documento: `json` (o modelo copia o trecho) ou `frases` (escolhe frases numeradas). Padrão: json. */
  extractMode?: ExtractMode;
  /** Fotos da internet: o roteiro pode usar slides "imagem" e a foto é buscada no Openverse/NASA. */
  images?: ImageSource;
}
/** O que writeSlide precisa da geração em curso (ou de uma apresentação pronta, ao refazer um slide). */
export interface SlideContext {
  request: string; deck: AltoDeck; facts: Facts; ids: string[]; mode: 'with_facts' | 'without_facts'; summary: string;
  slideMode: SlideMode; recorder: Recorder; repairTruncated: boolean; progress: (stage: string, slide?: number) => void;
  /** Slides antes e depois do slide i (na geração, `after` é vazio). */
  before: AltoSlide[]; after: AltoSlide[]; n: number; signal?: AbortSignal;
}
/** Escreve o slide i (1 chamada + 1 reparo) com o prompt, a gramática e as conferências da geração.
 * `extra` vai ao fim do pedido (ex.: instrução do usuário ao refazer). Retorna null se continuar inválido. */
export async function writeSlide(ctx: SlideContext, plan: PlanSlide, i: number, extra = ''):
    Promise<{accepted: AltoSlide | null; diagnostics: Diagnostic[]}> {
  const {request, deck, facts, ids, mode, summary, slideMode, recorder, n, signal} = ctx, kind = plan.tipo;
  const factsBlock = (selected = ids) => JSON.stringify(Object.fromEntries(selected.slice(0, 3).filter(id => id in facts).map(id => [id,
    {claim: facts[id].claim, quote: String(facts[id].quote).slice(0, 300), kind: facts[id].kind, value: facts[id].value}])));
  const progress = ctx.progress;
  const schema: JsonSchema = schemaWithFacts((prompts.slide_schemas as Record<string, any>)[kind][mode], ids);
  const base = `Pedido original: ${request}\nApresentação: ${deck.title}\nRoteiro:\n${summary}\nEscreva o slide ${i + 1} (tipo ${kind}).\nMensagem: ${plan.mensagem}\nObjetivo: ${plan.objetivo}\nRegras do tipo: ${(prompts.kind_rules as Record<string, string>)[kind]}\nFatos para este slide:\n${factsBlock(plan.fatos?.length ? plan.fatos : ids)}\nTítulos já escritos (não repetir): ${[...ctx.before, ...ctx.after].map(s => s.title).join('; ')}${extra}`;
  const limited = slideMode === 'gramatica_limites' ? withCompilerLimits(schema) : null;
  const grammar = slideMode === 'json' ? '' : slideGrammar(kind, limited ?? schema);
  const slideBase = grammar ? `${base}\n${altoFormatHint(kind, schema)}` : base;
  let accepted: AltoSlide | null = null, previous = '', diagnostics: Diagnostic[] = [];
  for (let attempt = 0; attempt <= 1; attempt++) {
    progress(attempt ? `Reparando slide ${i + 1}/${n}` : `Slide ${i + 1}/${n}`, i + 1);
    try {
      const user = attempt ? `${slideBase}\nResposta anterior:\n${previous.slice(0, 2200)}\nCorrija os diagnósticos mantendo o tipo:\n${JSON.stringify(diagnostics.filter(d => d.severity !== 'INFORMAÇÃO').slice(0, 8).map(d => ({code: d.code, severity: d.severity, message: d.message, path: d.evidence?.path, suggestion: d.suggestion})))}` : slideBase;
      let data: unknown;
      if (grammar) {
        const out = await recorder.grammar('slide', prompts.content_system, user, schema, grammar,
          text => altoToJson(kind, text, schema), i + 1, attempt);
        data = out.value; previous = out.text;
      } else {
        data = await recorder.json('slide', prompts.content_system, user, schema, i + 1, attempt);
        previous = JSON.stringify(data);
      }
      const errors = schemaErrors(data, schema);
      if (errors.length) { accepted = null; diagnostics = errors.map(message => ({code: 'P002', severity: 'ERRO', slide: i + 1, message})); }
      else {
        accepted = jsonToSlide(kind, data as Record<string, any>);
        cleanVisible(accepted, ids, request);  // como o PC: sem "conforme F2", caixa de frase, inicial maiúscula
        // The cover must not invent an author, as in alto_generation.py.
        if (kind === 'capa' && accepted.author && !request.toLowerCase().includes(accepted.author.toLowerCase())) accepted.author = null;
        if (!ids.length) accepted.notes = `conteúdo sem fontes\n${accepted.notes ?? ''}`;
        const built = buildAlto({...deck, slides: [...ctx.before, accepted, ...ctx.after]}, facts);
        diagnostics = built.diagnostics.filter(d => d.slide == null || d.slide === i + 1);
        // Texto cortado no limite da gramática: aviso que pede reparo (não bloqueia; após o reparo, aceita).
        if (limited && ctx.repairTruncated) for (const t of truncatedPaths(data, limited)) diagnostics.push({
          code: 'A005', severity: 'AVISO', slide: i + 1, evidence: {path: t.path},
          message: `Texto cortado no limite de ${t.limit} caracteres.`,
          suggestion: 'Reescreva este campo mais curto, com a ideia completa.'} as Diagnostic);
      }
    } catch (e) {
      checkCancelled(signal);
      accepted = null;
      diagnostics = [{code: 'P002', severity: 'ERRO', slide: i + 1, message: e instanceof Error ? e.message : String(e)}];
    }
    const actionable = diagnostics.filter(d => d.severity === 'ERRO' || (d.severity === 'AVISO' && d.code !== 'A009'));
    if (accepted && !actionable.length) break;
    if (attempt === 1 && (!accepted || diagnostics.some(d => d.severity === 'ERRO'))) { accepted = null; break; }
  }
  return {accepted, diagnostics};
}
export async function generate(options: GenerateOptions): Promise<GenerationResult> {
  const {slides: n, source: choice, model, signal} = options, slideMode: SlideMode = options.slideMode ?? 'json';
  const request = options.request.trim() || (choice.mode === 'document' ? `Apresente os pontos principais do documento ${choice.document.name}` : '');
  if (!request.trim() || request.length > 600) throw Error('Escreva um pedido de até 600 caracteres.');
  if (!Number.isInteger(n) || n < 4 || n > 8) throw Error('Escolha de 4 a 8 slides.');
  const start = Date.now(), maxCalls = 1 + 2 * n + (choice.mode === 'none' ? 0 : choice.mode === 'document' ? MAX_EXTRACT_CALLS : 1);
  const recorder = new Recorder(model, maxCalls, signal, options.onCalls);
  const progress = (stage: string, slide?: number) => { checkCancelled(signal); options.onProgress?.({stage, slide, total: n}); };
  progress(choice.mode === 'none' ? 'Sem pesquisa' : 'Extraindo fatos da fonte');
  const source = await collectFacts(choice, request, recorder, options.fetchJson, signal, options.readDocument, progress, options.onDocument,
    options.extractMode ?? 'json');
  const facts = source.facts, ids = Object.keys(facts), mode = ids.length ? 'with_facts' : 'without_facts';
  const factsBlock = (selected = ids) => JSON.stringify(Object.fromEntries(selected.slice(0, 3).filter(id => id in facts).map(id => [id,
    {claim: facts[id].claim, quote: String(facts[id].quote).slice(0, 300), kind: facts[id].kind, value: facts[id].value}])));
  progress('Planejando roteiro');
  const withImages = !!options.images;
  const outlineSchema = schemaWithFacts(((withImages ? prompts.outline_schemas_imagens : prompts.outline_schemas) as Record<string, any>)[String(n)][mode], ids);
  const sections = genericDocumentRequest(request) ? source.document?.sections ?? [] : [];
  const sectionPrompt = sections.length ? `\nSeções do documento em ordem; cubra estes assuntos no roteiro, agrupando se necessário. A capa pode apresentar a primeira seção. Use os IDs correspondentes:\n${JSON.stringify(sections)}` : '';
  const raw = await recorder.json('roteiro', (withImages ? prompts.outline_system_imagens : prompts.outline_system)[mode],
    `Pedido: ${request}\nNúmero de slides: ${n}\nFatos da pesquisa:\n${factsBlock()}${sectionPrompt}${withImages && n >= 4 ? prompts.image_outline_hint : ''}`, outlineSchema);
  const outlineErrors = schemaErrors(raw, outlineSchema);
  if (outlineErrors.length) throw Error(`Roteiro inválido: ${outlineErrors.join('; ')}`);
  const outline = fixOutline(raw as Outline, withImages);
  const deck: AltoDeck = {title: outline.titulo, theme: 'claro', slides: []};
  const summary = outline.slides.map((s, i) => `${i + 1}. ${s.tipo}: ${s.mensagem}`).join('\n');
  const fallbackNotes: Diagnostic[] = [];
  for (let i = 0; i < n; i++) {
    const plan = outline.slides[i], kind = plan.tipo;
    const ctx: SlideContext = {request, deck, facts, ids, mode, summary, slideMode, recorder, repairTruncated: options.repairTruncated ?? false,
      progress: (stage, slide) => progress(stage, slide), before: deck.slides, after: [], n, signal};
    let {accepted, diagnostics} = await writeSlide(ctx, plan, i);
    if (!accepted) {
      const fb = fallbackSlide(kind, plan, deck.title, deck, facts);
      if (!fb) throw new GenerationError(`Slide ${i + 1} continua inválido após um reparo.`, diagnostics);
      progress(`Slide ${i + 1}/${n} montado pelo compilador`, i + 1);
      fallbackNotes.push({code: 'F001', severity: 'AVISO', slide: i + 1,
        message: `Slide ${i + 1} montado pelo compilador após a IA falhar no reparo (${diagnostics.map(d => d.code).join(', ')}).`} as Diagnostic);
      accepted = fb;
    }
    deck.slides.push(accepted);
    // Yield to native UI between CPU-bound compiler passes.
    await new Promise<void>(resolve => setTimeout(resolve, 0));
  }
  const images: DeckImages = options.images ? await resolveImages(deck, options.images, signal, stage => progress(stage)) : {info: {}, data: {}, log: []};
  progress('Validando apresentação');
  const built = buildAlto(deck, facts, images.info);
  if (!built.ir || built.diagnostics.some(d => d.severity === 'ERRO')) throw new GenerationError('Apresentação inválida após compilação.', built.diagnostics);
  progress('Gerando PowerPoint editável');
  const pptx = await renderPptx(built.ir, {images: images.data});
  checkCancelled(signal);
  progress('Concluído');
  return {deck, ir: built.ir, pptx, calls: recorder.calls, diagnostics: [...built.diagnostics, ...fallbackNotes], source, facts,
    wall_ms: Date.now() - start, max_calls: maxCalls, request, outline, slideMode, images};
}
