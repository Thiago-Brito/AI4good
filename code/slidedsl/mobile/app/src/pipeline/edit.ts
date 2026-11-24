// Edição slide a slide da apresentação pronta, no celular (como o editor do PC: refazer com instrução, editar
// texto, mover, excluir, desfazer). Toda edição recompila o deck com o compilador e gera um PowerPoint novo; se o
// resultado for inválido, a edição é recusada e a versão anterior continua.
import {buildAlto, renderPptx, type AltoSlide, type Diagnostic} from '@slidedsl/core';
import {writeSlide, type GenerationResult, type SlideContext} from './generate.js';
import {Recorder} from './usage.js';
import type {TextModel} from './types.js';

export class EditError extends Error {
  constructor(message: string, readonly diagnostics: Diagnostic[] = []) { super(message); }
}

const clone = <T>(value: T): T => JSON.parse(JSON.stringify(value)) as T;

/** Recompila deck + roteiro novos; devolve um resultado novo (o anterior fica intacto para o desfazer). */
export async function rebuild(result: GenerationResult, slides: AltoSlide[], plans = result.outline.slides): Promise<GenerationResult> {
  const deck = {...result.deck, slides};
  const built = buildAlto(deck, result.facts, result.images.info);
  const errors = built.diagnostics.filter(d => d.severity === 'ERRO');
  if (!built.ir || errors.length) {
    throw new EditError(`Edição recusada: ${errors.slice(0, 3).map(d => `${d.code} ${d.message}`).join('; ') || 'apresentação inválida'}.`, errors);
  }
  // Avisos de slide montado pelo compilador acompanham o slide (mesmo objeto) para a nova posição.
  const fallback = result.diagnostics.filter(d => d.code === 'F001')
    .map(d => ({...d, slide: slides.indexOf(result.deck.slides[(d.slide ?? 0) - 1]) + 1})).filter(d => d.slide > 0);
  return {...result, deck, ir: built.ir, pptx: await renderPptx(built.ir, {images: result.images.data}), outline: {...result.outline, slides: plans},
    diagnostics: [...built.diagnostics, ...fallback]};
}

export function moveSlide(result: GenerationResult, from: number, to: number): Promise<GenerationResult> {
  const n = result.deck.slides.length;
  if (from < 0 || from >= n || to < 0 || to >= n) throw new EditError('Posição fora da apresentação.');
  const slides = [...result.deck.slides], plans = [...result.outline.slides];
  slides.splice(to, 0, ...slides.splice(from, 1));
  plans.splice(to, 0, ...plans.splice(from, 1));
  return rebuild(result, slides, plans);
}

export function deleteSlide(result: GenerationResult, index: number): Promise<GenerationResult> {
  if (result.deck.slides.length <= 2) throw new EditError('A apresentação precisa de pelo menos 2 slides.');
  return rebuild(result, result.deck.slides.filter((_, i) => i !== index), result.outline.slides.filter((_, i) => i !== index));
}

/** Campos de texto editáveis à mão, com caminho ("title", "items.0.detail", "sides.1.items.0.label"...). */
export function editableFields(slide: AltoSlide): {path: string; label: string; value: string; multiline: boolean}[] {
  const out: {path: string; label: string; value: string; multiline: boolean}[] = [];
  const add = (path: string, label: string, value: unknown, multiline = false) => {
    if (typeof value === 'string') out.push({path, label, value, multiline});
  };
  add('title', 'Título', slide.title); add('subtitle', 'Subtítulo', slide.subtitle); add('text', 'Texto', slide.text, true);
  add('caption', 'Legenda', slide.caption);
  (slide.items ?? []).forEach((it, k) => { add(`items.${k}.label`, `Item ${k + 1}`, it.label); add(`items.${k}.detail`, `Detalhe ${k + 1}`, it.detail, true); });
  (slide.sides ?? []).forEach((side, s) => {
    add(`sides.${s}.name`, `Lado ${s + 1}`, side.name);
    side.items.forEach((it, k) => { add(`sides.${s}.items.${k}.label`, `Lado ${s + 1} · item ${k + 1}`, it.label); add(`sides.${s}.items.${k}.detail`, `Lado ${s + 1} · detalhe ${k + 1}`, it.detail, true); });
  });
  (slide.values ?? []).forEach((v, k) => { add(`values.${k}.value`, `Valor ${k + 1}`, v.value); add(`values.${k}.label`, `Legenda do valor ${k + 1}`, v.label); });
  (slide.milestones ?? []).forEach((m, k) => { add(`milestones.${k}.date`, `Data ${k + 1}`, m.date); add(`milestones.${k}.label`, `Marco ${k + 1}`, m.label); add(`milestones.${k}.detail`, `Detalhe do marco ${k + 1}`, m.detail, true); });
  add('notes', 'Notas do apresentador', slide.notes, true);
  return out;
}

/** Aplica textos editados à mão ({caminho: texto}) no slide index. Campo vazio opcional vira null. */
export function editTexts(result: GenerationResult, index: number, changes: Record<string, string>): Promise<GenerationResult> {
  const slides = [...result.deck.slides], slide = clone(slides[index]) as unknown as Record<string, any>;
  for (const [path, value] of Object.entries(changes)) {
    const keys = path.split('.'), last = keys.pop()!;
    let target = slide;
    for (const k of keys) target = target?.[k];
    if (!target || !(last in target)) throw new EditError(`Campo ${path} não existe neste slide.`);
    const text = value.trim();
    target[last] = text || (['title', 'label', 'name', 'value', 'date'].includes(last) ? target[last] : null);
  }
  slides[index] = slide as unknown as AltoSlide;
  return rebuild(result, slides);
}

/** Refaz o slide index com a IA (mesmo prompt, gramática e conferências da geração), seguindo a instrução. */
export async function redoSlide(result: GenerationResult, index: number, instruction: string, model: TextModel,
    options: {signal?: AbortSignal; onProgress?: (stage: string) => void} = {}): Promise<GenerationResult> {
  const slides = result.deck.slides, plan = result.outline.slides[index], current = slides[index];
  if (!plan || !current) throw new EditError('Slide fora da apresentação.');
  const ids = Object.keys(result.facts), recorder = new Recorder(model, 2, options.signal);
  const ctx: SlideContext = {request: result.request, deck: result.deck, facts: result.facts, ids,
    mode: ids.length ? 'with_facts' : 'without_facts', slideMode: result.slideMode, recorder, repairTruncated: false,
    summary: result.outline.slides.map((s, i) => `${i + 1}. ${s.tipo}: ${s.mensagem}`).join('\n'),
    progress: stage => options.onProgress?.(stage), before: slides.slice(0, index), after: slides.slice(index + 1),
    n: slides.length, signal: options.signal};
  const {kind: _k, notes: _n, line: _l, column: _c, ...visible} = current as AltoSlide & {line?: unknown; column?: unknown};
  const extra = `\nVersão atual deste slide: ${JSON.stringify(visible)}\n` + (instruction.trim()
    ? `Pedido do usuário para este slide: ${instruction.trim()}. Reescreva o slide atendendo ao pedido.`
    : 'Reescreva este slide com outra redação, mais clara.');
  const {accepted, diagnostics} = await writeSlide(ctx, {...plan, tipo: current.kind}, index, extra);
  const calls = [...result.calls, ...recorder.calls];
  if (!accepted) throw new EditError('A IA não conseguiu refazer o slide; a versão anterior foi mantida.', diagnostics);
  // Slide de imagem: a foto já baixada continua (a busca nova não é refeita aqui).
  if (current.image_file && accepted.kind === 'imagem') { accepted.image_file = current.image_file; accepted.image_query = current.image_query; }
  const rebuilt = await rebuild(result, slides.map((s, i) => (i === index ? accepted : s)));
  return {...rebuilt, calls};
}
