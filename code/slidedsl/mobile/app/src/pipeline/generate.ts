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
  /** Detalhes literais (modelo pequeno), para refazer um slide do mesmo jeito. */
  literalDetails?: boolean;
}
export class GenerationError extends Error {
  constructor(message: string, readonly diagnostics: Diagnostic[]) { super(message); }
}
// Conversion of the Python json_to_slide field mapping; data is schema-validated first.
export function jsonToSlide(kind: SlideKind | 'ciclo', data: Record<string, any>): AltoSlide {
  const text = (key: string) => (data[key] as string | undefined)?.trim() || null;
  const items = (values: any[] = []) => values.map(v => ({label: v.rotulo.trim(), detail: v.detalhe?.trim() || null}));
  // "ciclo" é etapas com cycle (como json_to_slide do PC): o compilador desenha as fases em círculo.
  return {...(kind === 'ciclo' ? {kind: 'etapas' as SlideKind, cycle: true} : {kind}), title: text('titulo'), subtitle: text('subtitulo'), author: text('autor'),
    text: text('texto'), caption: text('legenda'), unit: text('unidade'), notes: text('notas'), image_query: text('busca_imagem'),
    items: items(data.itens), values: (data.valores ?? []).map((v: any) => ({value: v.valor.trim(), label: v.legenda.trim()})),
    sides: (data.lados ?? []).map((v: any) => ({name: v.nome.trim(), items: items(v.itens)})),
    milestones: (data.marcos ?? []).map((v: any) => ({date: v.data.trim(), label: v.rotulo.trim(), detail: v.detalhe?.trim() || null})),
    bars: (data.barras ?? []).map((v: any) => ({label: v.rotulo.trim(), value: v.valor})),
    sources: [...new Set<string>(data.fontes ?? [])]};
}
export interface PlanSlide {tipo: SlideKind | 'ciclo'; mensagem: string; objetivo: string; fatos?: string[]}
const TRAILING = new Set(['a', 'o', 'as', 'os', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das', 'em', 'no', 'na', 'nos', 'nas',
  'para', 'por', 'pelo', 'pela', 'com', 'sem', 'e', 'ou', 'que', 'se', 'ao', 'aos', 'à', 'às', 'é', 'sobre', 'entre', 'até', 'sob']);
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
/** Item de tópico a partir da afirmação de um fato: rótulo = primeira oração (até 48), detalhe = o resto (até 170). */
export function factItem(claim: string): {rotulo: string; detalhe?: string} {
  const text = claim.trim().replace(/\.$/, '');
  if (text.length <= 48) return {rotulo: text};
  const cut = text.search(/[,:;]\s|\s[—–-]\s/);
  // Sem vírgula/travessão no lugar certo: corta perto do meio, para o detalhe levar o resto da frase.
  const head = cut > 8 && cut <= 48 ? text.slice(0, cut) : shortTitle(text, Math.min(48, Math.max(24, Math.ceil(text.length / 2))));
  const rest = text.slice(head.length).replace(/^[\s,:;—–-]+/, '');
  // Sobra de 1–2 palavras ("o trabalho") não vira detalhe solto.
  const detalhe = rest.split(/\s+/).length >= 3 ? shortTitle(rest[0].toUpperCase() + rest.slice(1), 170) : '';
  return detalhe ? {rotulo: head, detalhe} : {rotulo: head};
}
/** Slide montado pelo compilador quando a IA falha após o reparo (teste no emulador, 23/11/2026:
 * a capa do Qwen3 0.6B continuou inválida e a geração inteira era abortada). Capa: título do roteiro;
 * demais tipos: divisória com a mensagem planejada. Sem nova chamada ao modelo. */
function fallbackSlide(kind: SlideKind | 'ciclo', plan: PlanSlide, deckTitle: string, deck: AltoDeck, facts: Facts): AltoSlide | null {
  // Com fatos planejados, tópicos montados das próprias afirmações do documento (teste no celular, 25/11/2026:
  // a divisória só com a mensagem foi julgada de pouca utilidade). Sem fatos, ou se não couber, a divisória.
  const planned = kind === 'capa' ? [] : (plan.fatos ?? []).filter(id => typeof facts[id]?.claim === 'string').slice(0, 4);
  if (planned.length >= 2) {
    const slide = jsonToSlide('topicos', {titulo: shortTitle(plan.mensagem, 60), fontes: planned,
      itens: planned.map(id => factItem(String(facts[id].claim)))});
    slide.notes = `Slide montado pelo compilador com os fatos ${planned.join(', ')} após falha da IA. Mensagem planejada: ${plan.mensagem}`;
    const built = buildAlto({...deck, slides: [...deck.slides, slide]}, facts);
    if (!built.diagnostics.some(d => d.slide === deck.slides.length + 1 && d.severity === 'ERRO')) return slide;
  }
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
const NUMERIC_KINDS = new Set(['numeros', 'grafico']);
/** Detalhes de itens, lados e marcos encurtados na palavra inteira; `maxItems` corta a lista de itens. */
export function shortenDetails(data: unknown, max: number, maxItems?: number): unknown {
  const d = JSON.parse(JSON.stringify(data)) as Record<string, any>;
  const cut = (it: Record<string, any>) => { if (typeof it.detalhe === 'string' && it.detalhe.length > max) it.detalhe = shortTitle(it.detalhe, max); };
  if (Array.isArray(d.itens)) { d.itens.forEach(cut); if (maxItems && d.itens.length > maxItems) d.itens = d.itens.slice(0, maxItems); }
  for (const side of d.lados ?? []) (side.itens ?? []).forEach(cut);
  (d.marcos ?? []).forEach(cut);
  return d;
}
/** Mesmo critério de number_tokens (alto.py) usado pelo A007: "1.300" → 1300, "6,5" → 6.5, "20 mil" → 20 e 20000. */
export function numberTokens(text: string | null | undefined): Set<string> {
  const found = new Set<string>();
  const clean = (text ?? '').replace(/\bF\d+\b/g, ' ');
  for (const m of clean.matchAll(/\d+(?:[.,]\d+)*(\s*mil\b)?/gi)) {
    const raw = m[0].replace(/\s*mil$/i, '');
    let value = /^\d{1,3}([.,]\d{3})+$/.test(raw) ? raw.replace(/[.,]/g, '') : raw.replace(/,/g, '.');
    value = value.replace(/\.$/, '');
    if (value.includes('.')) value = value.replace(/0+$/, '').replace(/\.$/, '');
    found.add(value);
    if (m[1]) found.add(String(Math.round(Number(value) * 1000)));
  }
  return found;
}
const contentWords = (t: string) => new Set(t.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').match(/[a-z]{4,}/g) ?? []);
/** Modelo pequeno: o detalhe de cada item (e de lado, marco e a legenda de valor) vira a frase do fato que mais combina
 * com ele (palavras e números em comum), um fato por campo; o modelo fica só com o rótulo. Bancada de 26/11: o 0.6B
 * escreveu "1.380 tokens de entrada e 1.344 de saída" quando o documento diz 1.380 com código e 1.344 com SlideDSL.
 * Limite: o do compilador com até 3 itens (170; 80 em comparação), 110 com mais itens, 70 em imagem; frase acima dele
 * termina na última pausa, sem parêntese aberto, e a frase que cabe inteira tem preferência. Campo sem fato parecido (menos de 2 pontos) fica como está;
 * só troca detalhes que existem (não acrescenta texto que pode não caber no layout). */
export function literalizeDetails(slide: AltoSlide, kind: string, candidates: string[], facts: Facts): AltoSlide {
  const pool = [...new Set(candidates)].filter(id => typeof facts[id]?.claim === 'string');
  if (!pool.length) return slide;
  const out: AltoSlide = JSON.parse(JSON.stringify(slide));
  type Slot = {text: string; limit: number; value?: string; obj?: object; set: (v: string) => void};
  const slots: Slot[] = [];
  for (const it of out.items ?? []) if (it.detail) slots.push({text: `${it.label} ${it.detail}`, limit: kind === 'imagem' ? 70 : kind === 'comparacao' ? 80 : (out.items?.length ?? 0) <= 3 ? 170 : 110, obj: it, set: v => { it.detail = v; }});
  for (const side of out.sides ?? []) for (const it of side.items) if (it.detail) slots.push({text: `${side.name} ${it.label} ${it.detail}`, limit: 80, obj: it, set: v => { it.detail = v; }});
  for (const m of out.milestones ?? []) if (m.detail) slots.push({text: `${m.date} ${m.label} ${m.detail}`, limit: 90, set: v => { m.detail = v; }});
  for (const v of out.values ?? []) slots.push({text: `${v.value} ${v.label}`, limit: (out.values?.length ?? 0) <= 2 ? 170 : 110, value: v.value, set: x => { v.label = x; }});
  const info = new Map(pool.map(id => { const f = `${facts[id].claim} ${facts[id].quote ?? ''}`; return [id, {nums: numberTokens(f), words: contentWords(f)}]; }));
  const score = (s: Slot, id: string) => {
    const {nums, words} = info.get(id)!;
    if (s.value && [...numberTokens(s.value)].some(t => !nums.has(t))) return 0;  // legenda de valor: o fato tem de ter o número
    let points = 0;
    for (const w of contentWords(s.text)) if (words.has(w)) points++;
    for (const t of numberTokens(s.text)) if (nums.has(t)) points += 3;
    return points >= 2 && Array.from(String(facts[id].claim)).length <= s.limit ? points + 1 : points;  // a frase que cabe inteira ganha
  };
  const pairs = slots.flatMap((s, i) => pool.map(id => ({i, id, points: score(s, id)}))).filter(p => p.points >= 2)
    .sort((a, b) => b.points - a.points || pool.indexOf(a.id) - pool.indexOf(b.id));
  const usedSlots = new Set<number>(), usedFacts: string[] = [], matched = new Set<object>();
  for (const p of pairs) {
    if (usedSlots.has(p.i) || usedFacts.includes(p.id)) continue;
    usedSlots.add(p.i); usedFacts.push(p.id); if (slots[p.i].obj) matched.add(slots[p.i].obj!);
    const claim = String(facts[p.id].claim).trim(), limit = slots[p.i].limit;
    slots[p.i].set(Array.from(claim).length <= limit ? claim : closeParens(String(trimTruncated(claim, {type: "string", maxLength: limit}))));
  }
  if (!usedFacts.length) return slide;
  // Item com detalhe que não combina com nenhum fato é texto do próprio modelo pequeno, onde ficaram os erros (bancada de
  // 26/11, 1.7B: "a plataforma ainda não provou que o modelo pequeno escreve frases erradas", sentido invertido). Sai se
  // sobrarem ao menos 2 itens (1 por lado na comparação).
  const keep = (it: {detail?: string | null}) => !it.detail || matched.has(it);
  if (out.items && out.items.filter(it => it.detail && matched.has(it)).length >= 2) out.items = out.items.filter(keep);
  for (const side of out.sides ?? []) if (side.items.some(it => it.detail && matched.has(it))) side.items = side.items.filter(keep);
  out.sources = [...new Set([...(out.sources ?? []), ...usedFacts])];
  return out;
}
/** Número certo com a citação errada (bancada 0.7.4: "87,2%" está no F1, o modelo citou F5/F6) não é número
 * inventado: se outro fato tem o número, o compilador acrescenta esse fato às fontes antes de validar. */
export function citeNumberFacts(slide: AltoSlide, facts: Facts): AltoSlide {
  // Valores e, desde 26/11, todos os textos que o A012 confere: com o documento curto lido inteiro há mais fatos com
  // números, e a citação errada custava um reparo por slide (bancada da água: 9 chamadas de slide contra 7–8).
  const values = [...(slide.values ?? []).map(v => v.value), ...(slide.bars ?? []).map(b => String(b.value)),
    slide.title, slide.subtitle, slide.caption, slide.text, slide.unit, slide.author, slide.notes,
    ...(slide.items ?? []).flatMap(it => [it.label, it.detail]),
    ...(slide.sides ?? []).flatMap(side => [side.name, ...side.items.flatMap(it => [it.label, it.detail])]),
    ...(slide.milestones ?? []).flatMap(m => [m.date, m.label, m.detail]),
    ...(slide.bars ?? []).map(b => b.label), ...(slide.values ?? []).map(v => v.label)]
    .filter((v): v is string => typeof v === 'string' && /\d/.test(v));
  if (!values.length) return slide;
  const tokens = new Map(Object.entries(facts).map(([id, f]) => [id, numberTokens(`${f.quote ?? ''} ${f.claim ?? ''}`)]));
  const sources = [...(slide.sources ?? [])];
  for (const value of values) {
    const cited = new Set(sources.flatMap(id => [...(tokens.get(id) ?? [])]));
    const missing = [...numberTokens(value)].filter(t => !cited.has(t));
    if (!missing.length || sources.length >= 4) continue;
    const hit = [...tokens].find(([id, t]) => !sources.includes(id) && missing.every(x => t.has(x)));
    if (hit) sources.push(hit[0]);
  }
  return sources.length === (slide.sources ?? []).length ? slide : {...slide, sources};
}
const wordKey = (w: string) => w.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').replace(/[^\p{L}\p{N}]/gu, '');
/** Palavras inteiras dos textos dados (fatos, pedido, roteiro), para reconhecer a palavra cortada pela gramática. */
export function knownWords(texts: string[]): Set<string> {
  return new Set(texts.flatMap(t => t.split(/\s+/).map(wordKey)).filter(Boolean));
}
/** Rótulos do prompt do slide que o modelo pequeno copia como título ("Regras do tipo", bancada de 26/11). */
const PROMPT_LABELS = new Set(['regras do tipo', 'regras', 'mensagem', 'objetivo', 'fatos para este slide', 'pedido original',
  'apresentacao', 'roteiro', 'titulos ja escritos', 'resposta anterior', 'itens ja escritos em outros slides', 'slidedsl alto',
  'corrija os diagnosticos mantendo o tipo']);
/** Texto copiado do prompt: igual a um rótulo, ou começando por "rótulo:" ("Regras do tipo: 2 a 5 itens…", "Fatos para
 * este slide:", "SlideDSL Alto: …"; 0.6B, bancada de 26/11). "Regras comuns a todos os testes" não é cópia. */
export function promptLeak(text: string | null | undefined): boolean {
  if (!text) return false;
  const low = text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').replace(/^['"“‘\s]+/, '').trim();
  if (PROMPT_LABELS.has(low.replace(/[^\p{L}\p{N}]+/gu, ' ').trim())) return true;
  return [...PROMPT_LABELS].some(l => low.startsWith(`${l}:`));
}
/** Tira do slide o que o modelo copiou do prompt: o título vira a mensagem planejada; itens copiados saem se sobrarem 2. */
export function dropPromptLeaks(slide: AltoSlide, message: string): AltoSlide {
  if (promptLeak(slide.title)) slide.title = shortTitle(message, 60);
  if (promptLeak(slide.subtitle)) slide.subtitle = null;
  const clean = (it: {label: string; detail?: string | null}) => !promptLeak(it.label) && !promptLeak(it.detail);
  if (slide.items && slide.items.filter(clean).length >= 2) slide.items = slide.items.filter(clean);
  for (const side of slide.sides ?? []) if (side.items.some(clean)) side.items = side.items.filter(clean);
  return slide;
}
/** Texto que chegou ao maxLength (a gramática fechou a string no limite): tira a palavra cortada. */
export function trimTruncated(data: unknown, schema: JsonSchema, known?: Set<string>): unknown {
  if (schema.type === 'string' && typeof data === 'string') {
    const max = schema.maxLength === undefined ? Infinity : Number(schema.maxLength);
    // Perto do limite, a gramática também fecha a string antes dele, quando o próximo pedaço de palavra não cabe
    // ("…24 apresentações por condi", 47 de 48; bancada de 26/11). Se a última palavra não existe inteira nos
    // fatos nem no pedido, ela foi cortada: sai.
    const len = Array.from(data).length, text = data.trim();
    if (known && len < max && len >= max - 6 && /\s/.test(text) && !/[.!?;:)"”%\d]$/.test(text)) {
      const words = text.split(/\s+/), last = wordKey(words[words.length - 1]);
      if (last.length >= 2 && !known.has(last)) return shortTitle(words.slice(0, -1).join(' '), max);
    }
    if (!(len >= max && /\s/.test(text))) return data;
    // Teste no celular (0.7.4): "…transforma água em vapor e volta ao" — melhor terminar na última pausa da
    // frase (vírgula, "e", "que", "mas"…) quando ela deixa ao menos metade do texto.
    const cut = shortTitle(data, max - 1);
    let best = -1;
    for (const m of cut.matchAll(/[,;:]\s|\s[—–-]\s|\s(?:e|que|mas|porque|pois|quando|onde|como|para)\s/g)) best = m.index!;
    return best >= max / 2 ? cut.slice(0, best).replace(/[\s,;:—–-]+$/, '') : cut;
  }
  if (schema.type === 'array' && Array.isArray(data) && schema.items) return data.map(v => trimTruncated(v, schema.items as JsonSchema, known));
  if (schema.type === 'object' && data && typeof data === 'object') {
    const props = (schema.properties ?? {}) as Record<string, JsonSchema>;
    return Object.fromEntries(Object.entries(data as Record<string, unknown>).map(([k, v]) => [k, k in props ? trimTruncated(v, props[k], known) : v]));
  }
  return data;
}
/** Fatos para o roteiro: TODOS (até 32, como o PC), só afirmação e valor, sem o trecho, para caber nos 4096
 * tokens. Antes o roteiro via só os 3 primeiros; com o PDF do TCC eram 32 fatos e o deck só falava do resumo. */
export function outlineFacts(facts: Facts, maxChars = 3600): string {
  const lines: string[] = [];
  let size = 0;
  // Documento curto lido inteiro (até 6 leituras × 6 fatos): com mais de 32 fatos, todos entram (até 80, como o
  // PC), com a afirmação mais curta para caber no mesmo espaço; antes os fatos das últimas seções ficavam de fora.
  const entries = Object.entries(facts), all = entries.length > 32 ? entries.slice(0, 80) : entries;
  const perLine = all.length > 32 ? Math.floor(maxChars / all.length) - 1 : Infinity;
  for (const [id, f] of all) {
    const value = f.value ? ` [valor: ${String(f.value)}]` : '';
    const head = `${id} (${String(f.kind ?? 'fato')})${value}: `;
    const line = head + String(f.claim ?? '').slice(0, Math.min(220, Math.max(40, perLine - head.length)));
    if (size + line.length > maxChars) break;
    lines.push(line); size += line.length + 1;
  }
  return lines.join('\n') || '(nenhum fato)';
}
/** Corta cada texto acima do maxLength do schema na última palavra inteira (sem artigo/preposição no fim). */
export function clipToLimits(data: unknown, schema: JsonSchema): unknown {
  if (schema.type === 'string' && typeof data === 'string') {
    const max = schema.maxLength === undefined ? Infinity : Number(schema.maxLength);
    return Array.from(data).length > max ? shortTitle(data, max) : data;
  }
  if (schema.type === 'array' && Array.isArray(data) && schema.items) return data.map(v => clipToLimits(v, schema.items as JsonSchema));
  if (schema.type === 'object' && data && typeof data === 'object') {
    const props = (schema.properties ?? {}) as Record<string, JsonSchema>;
    return Object.fromEntries(Object.entries(data as Record<string, unknown>).map(([k, v]) => [k, k in props ? clipToLimits(v, props[k]) : v]));
  }
  return data;
}
/** Fatos diferentes por slide: o roteiro do modelo pequeno manda os mesmos fatos a vários slides, e eles
 * repetem a mesma ideia (teste no celular, 25/11/2026: 3 slides sobre evaporação/condensação, 15 fatos
 * extraídos). Mantém os fatos planejados que ainda não foram usados e completa até 2 com os não usados, na
 * ordem do documento. A capa não recebe fatos aqui e a conclusão pode retomar (ela sintetiza). */
export function distributeFacts(outline: Outline, ids: string[]): Outline {
  if (!ids.length) return outline;
  const used = new Set<string>();
  const slides = outline.slides.map(s => ({...s, fatos: [...(s.fatos ?? [])]}));
  for (const s of slides) {
    if (s.tipo === 'capa' || s.tipo === 'conclusao') continue;
    const fresh = s.fatos.filter(id => !used.has(id));
    for (const id of ids) { if (fresh.length >= 2) break; if (!used.has(id) && !fresh.includes(id)) fresh.push(id); }
    if (fresh.length) s.fatos = fresh;
    s.fatos.forEach(id => used.add(id));
  }
  return {...outline, slides};
}
/** Rótulos já escritos nos outros slides, para o modelo não repetir a ideia (cabe em ~60 tokens). */
export function writtenItems(slides: AltoSlide[], max = 320): string {
  const labels = slides.flatMap(s => [...(s.items ?? []), ...(s.sides ?? []).flatMap(side => side.items), ...(s.milestones ?? [])].map(it => it.label));
  let out = '';
  for (const l of labels) { const next = out ? `${out}; ${l}` : l; if (next.length > max) break; out = next; }
  return out;
}
export interface Outline {titulo: string; slides: PlanSlide[]}
export type DocumentSection = {title: string; facts: string[]};
const RESULT_RE = /\d+\s+de\s+\d+|\bp\s*[=<]|\d\s*%|\bteve\b|\btiveram\b|superou|levou|levaram|caiu|subiu|aument|reduz|n[aã]o h[aá] diferen|sem diferen|contra \d|resultado/i;
/** Porte de fact_weight (alto_generation.py): 2 = resultado ("1 de 24", "p = 0,98", "levou 63 minutos"); 1 = outro
 * número; 0 = sem número. O tipo "numero" não separa método de resultado ("6 slides" e "1 de 24" vêm iguais). */
export function factWeight(fact: Facts[string] | undefined): number {
  if (!fact) return 0;
  if (RESULT_RE.test(`${String(fact.claim ?? '')} ${String(fact.quote ?? '')}`)) return 2;
  return /\d/.test(String(fact.claim ?? '')) ? 1 : 0;
}
/** Porte de outline_from_sections: quando o roteiro deixa uma seção do documento sem nenhum fato dela e as seções
 * cabem (capa + uma por slide), o roteiro segue as seções; o tipo de cada slide vem do roteiro do modelo na mesma
 * posição e a última seção vira a conclusão. Sem chamada ao modelo. */
export function outlineFromSections(outline: Outline, sections: DocumentSection[], n: number, facts: Facts): Outline {
  const slides = outline.slides;
  if (!(sections.length >= 2 && sections.length === n - 1) || !slides.length) return outline;
  const covered = new Set(slides.flatMap(s => s.fatos ?? []));
  if (sections.every(s => s.facts.some(id => covered.has(id)))) return outline;
  const content = slides.slice(1).filter(s => s.tipo !== 'capa' && s.tipo !== 'secao');
  const ranked = (ids: string[]) => [...ids].sort((a, b) => factWeight(facts[b]) - factWeight(facts[a]) || ids.indexOf(a) - ids.indexOf(b));
  const next: PlanSlide[] = [slides[0], ...sections.map((s, k) => {
    let tipo = content[k]?.tipo ?? 'topicos';
    if (k === sections.length - 1) tipo = 'conclusao'; else if (tipo === 'conclusao') tipo = 'topicos';
    return {tipo, mensagem: s.title, objetivo: s.title, fatos: ranked(s.facts).slice(0, 6)};
  })];
  return {...outline, slides: next};
}
/** Porte de ensure_section_results: cada slide de uma seção leva os resultados dela (depois os outros números), no
 * lugar dos fatos sem número, e eles vão na frente — o slide é escrito com os 3 primeiros fatos da lista. */
export function ensureSectionResults(outline: Outline, sections: DocumentSection[], facts: Facts, cap = 6): Outline {
  const sectionOf = new Map(sections.flatMap(s => s.facts.map(id => [id, s.title] as const)));
  const weight = (id: string) => sectionOf.has(id) ? factWeight(facts[id]) : 0;
  const slides = outline.slides.map((slide, k) => {
    if (k === 0) return slide;
    const ids = [...(slide.fatos ?? [])], counts = new Map<string, number>();
    for (const id of ids) if (sectionOf.has(id)) counts.set(sectionOf.get(id)!, (counts.get(sectionOf.get(id)!) ?? 0) + 1);
    if (!counts.size) return slide;
    const heading = [...counts].reduce((a, b) => b[1] > a[1] ? b : a)[0];
    for (const level of [2, 1]) {
      const wanted = sections.filter(s => s.title === heading).flatMap(s => s.facts).filter(id => weight(id) === level && !ids.includes(id));
      for (const id of wanted) {
        if (ids.length < cap) { ids.push(id); continue; }
        const weaker = [...ids].reverse().filter(j => weight(j) < level);
        if (!weaker.length) break;
        const worst = weaker.reduce((a, b) => weight(b) < weight(a) ? b : a);
        ids[ids.indexOf(worst)] = id;
      }
    }
    const order = [...ids];
    return {...slide, fatos: order.sort((a, b) => weight(b) - weight(a) || ids.indexOf(a) - ids.indexOf(b))};
  });
  return {...outline, slides};
}
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
  /** Modelo pequeno (0.6B, 1.7B): o detalhe de cada item, marco e valor passa a ser a frase do fato que mais combina
   * com ele; o modelo fica só com o rótulo. Bancada de 26/11: o 0.6B invertia números ao reescrever os detalhes. */
  literalDetails?: boolean;
}
/** O que writeSlide precisa da geração em curso (ou de uma apresentação pronta, ao refazer um slide). */
export interface SlideContext {
  request: string; deck: AltoDeck; facts: Facts; ids: string[]; mode: 'with_facts' | 'without_facts'; summary: string;
  slideMode: SlideMode; recorder: Recorder; repairTruncated: boolean; progress: (stage: string, slide?: number) => void;
  /** Slides antes e depois do slide i (na geração, `after` é vazio). */
  before: AltoSlide[]; after: AltoSlide[]; n: number; signal?: AbortSignal;
  /** Modelo pequeno: o detalhe de cada item vem da frase do fato citado (ver literalDetails). */
  literalDetails?: boolean;
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
  const base = `Pedido original: ${request}\nApresentação: ${deck.title}\nRoteiro:\n${summary}\nEscreva o slide ${i + 1} (tipo ${kind}).\nMensagem: ${plan.mensagem}\nObjetivo: ${plan.objetivo}\nRegras do tipo: ${(prompts.kind_rules as Record<string, string>)[kind]}\nFatos para este slide:\n${factsBlock(plan.fatos?.length ? plan.fatos : ids)}\nTítulos já escritos (não repetir): ${[...ctx.before, ...ctx.after].map(s => s.title).join('; ')}${(() => { const w = writtenItems([...ctx.before, ...ctx.after]); return w ? `\nItens já escritos em outros slides (não repita estas ideias; use os fatos deste slide): ${w}` : ''; })()}${extra}`;
  const limited = slideMode === 'gramatica_limites' ? withCompilerLimits(schema) : null;
  const grammar = slideMode === 'json' ? '' : slideGrammar(kind, limited ?? schema);
  const slideBase = grammar ? `${base}\n${altoFormatHint(kind, schema)}` : base;
  let accepted: AltoSlide | null = null, previous = '', diagnostics: Diagnostic[] = [], lastData: unknown = null;
  // Em slide de números/gráfico o número É o conteúdo: número fora dos fatos citados (A007) também bloqueia
  // depois do reparo, e o compilador monta o slide com os fatos (teste do TCC: "90%" e notas 4/4/4/5 inventados).
  const blocking = (d: Diagnostic) => d.severity === 'ERRO' || (NUMERIC_KINDS.has(kind) && d.code === 'A007');
  const accept = (data: unknown) => {
    let slide = jsonToSlide(kind, data as Record<string, any>);
    slide = dropPromptLeaks(slide, plan.mensagem);
    if (ctx.literalDetails && ids.length) slide = literalizeDetails(slide, kind, [...(plan.fatos ?? []), ...(slide.sources ?? [])], facts);
    if (ids.length) slide = citeNumberFacts(slide, facts);
    cleanVisible(slide, ids, request);  // como o PC: sem "conforme F2", caixa de frase, inicial maiúscula
    // The cover must not invent an author, as in alto_generation.py.
    if (kind === 'capa' && slide.author && !request.toLowerCase().includes(slide.author.toLowerCase())) slide.author = null;
    if (!ids.length) slide.notes = `conteúdo sem fontes\n${slide.notes ?? ''}`;
    const built = buildAlto({...deck, slides: [...ctx.before, slide, ...ctx.after]}, facts);
    return {slide, diagnostics: built.diagnostics.filter(d => d.slide == null || d.slide === i + 1)};
  };
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
        // Texto que bateu no limite da gramática termina no meio da palavra ("SlideD"): sem o reparo de
        // texto cortado (padrão no celular), fica só até a última palavra inteira (teste do TCC, 25/11/2026).
        if (limited && !ctx.repairTruncated) data = trimTruncated(data, limited, knownWords([request, deck.title, plan.mensagem, plan.objetivo, ...Object.values(facts).flatMap(f => [String(f.claim ?? ""), String(f.quote ?? "")])]));
        lastData = data;
        ({slide: accepted, diagnostics} = accept(data));
        // Dois itens com o mesmo texto no slide ("Precipitação — A água volta ao líquido por condensação", igual ao
        // item Condensação; teste da água, 25/11/2026): pede o reparo. Aviso: depois do reparo, aceita.
        const seenText = new Map<string, number>();
        [...(accepted?.items ?? []), ...(accepted?.sides ?? []).flatMap(side => side.items)].forEach((it, k) => {
          const key = (it.detail || it.label).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
          if (key.length > 15 && seenText.has(key)) diagnostics.push({code: 'P004', severity: 'AVISO', slide: i + 1,
            message: `O item ${k + 1} repete o texto do item ${seenText.get(key)! + 1}.`,
            suggestion: 'Escreva um texto próprio para cada item, com outro fato.'} as Diagnostic);
          else seenText.set(key, k);
        });
        // Slide de números com valor sem número, como "geram dependên" (teste do TCC).
        if (kind === 'numeros') (accepted?.values ?? []).forEach((v, k) => { if (!/\d/.test(v.value)) diagnostics.push({
          code: 'P003', severity: 'ERRO', slide: i + 1, evidence: {path: `valores.${k}.valor`},
          message: `Valor "${v.value}" sem número.`, suggestion: 'Use um número que aparece nos fatos citados.'} as Diagnostic); });
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
    if (attempt === 1 && (!accepted || diagnostics.some(blocking))) { accepted = null; break; }
  }
  // Item repetido que sobreviveu ao reparo (o 0.6B repete o mesmo texto): o compilador tira a cópia se ficarem
  // ao menos 2 itens, em vez de mostrar duas vezes a mesma frase.
  // Também rótulo repetido (A023 do compilador; visto no emulador com o 0.7.5: dois itens iguais sobreviveram ao reparo).
  if (accepted && diagnostics.some(d => d.code === 'P004' || d.code === 'A023') && (accepted.items?.length ?? 0) > 2) {
    const norm = (t?: string | null) => (t ?? '').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
    const seen = new Set<string>(), labels = new Set<string>();
    const items = accepted.items!.filter(it => {
      const k = norm(it.detail || it.label), l = norm(it.label);
      if ((k.length > 15 && seen.has(k)) || (l.length > 2 && labels.has(l))) return false;
      seen.add(k); labels.add(l); return true;
    });
    if (items.length >= 2 && items.length < accepted.items!.length) {
      const slide = {...accepted, items};
      const built = buildAlto({...deck, slides: [...ctx.before, slide, ...ctx.after]}, facts);
      const own = built.diagnostics.filter(d => d.slide == null || d.slide === i + 1);
      if (!own.some(blocking)) { accepted = slide; diagnostics = own; }
    }
  }
  // Teste no celular (25/11/2026, modo JSON): slides 3 e 5 viraram divisórias vazias só por rótulos longos (A005).
  // Se os únicos erros são de tamanho, o compilador encurta os campos na palavra inteira e fica o conteúdo da IA.
  // Bancada 0.7.4: o 0.6B escreve 5 itens com detalhes longos e nenhum layout comporta (A010). Mesmo remédio:
  // detalhes encurtados na palavra inteira (110, depois 80) e, só se ainda não couber, os 4 primeiros itens.
  const errors = diagnostics.filter(d => d.severity === 'ERRO');
  if (!accepted && lastData && errors.length && errors.every(d => d.code === 'A005' || d.code === 'A010')) {
    const clipped = clipToLimits(lastData, withCompilerLimits(schema));
    for (const candidate of [clipped, shortenDetails(clipped, 110), shortenDetails(clipped, 80), shortenDetails(clipped, 80, 4)]) {
      const salvage = accept(candidate);
      if (salvage.diagnostics.some(blocking)) continue;
      accepted = salvage.slide;
      diagnostics = [...salvage.diagnostics, {code: 'F002', severity: 'AVISO', slide: i + 1,
        message: `Slide ${i + 1}: textos encurtados pelo compilador após o reparo para caber no slide.`} as Diagnostic];
      break;
    }
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
  progress('Planejando roteiro');
  const withImages = !!options.images;
  const outlineSchema = schemaWithFacts(((withImages ? prompts.outline_schemas_imagens : prompts.outline_schemas) as Record<string, any>)[String(n)][mode], ids);
  // Seções valem no pedido geral e no documento curto lido inteiro (aí o pedido específico também cobre o documento todo).
  const sections: DocumentSection[] = genericDocumentRequest(request) || source.document?.complete ? source.document?.sections ?? [] : [];
  const sectionPrompt = sections.length ? `\nSeções do documento em ordem; cubra estes assuntos no roteiro, agrupando se necessário. A capa pode apresentar a primeira seção. Use os IDs correspondentes:\n${JSON.stringify(sections)}` : '';
  const raw = await recorder.json('roteiro', (withImages ? prompts.outline_system_imagens : prompts.outline_system)[mode],
    `Pedido: ${request}\nNúmero de slides: ${n}\nFatos da pesquisa:\n${outlineFacts(facts)}${sectionPrompt}${withImages && n >= 4 ? prompts.image_outline_hint : ''}`, outlineSchema);
  const outlineErrors = schemaErrors(raw, outlineSchema);
  if (outlineErrors.length) throw Error(`Roteiro inválido: ${outlineErrors.join('; ')}`);
  const fixed = fixOutline(raw as Outline, withImages);
  let outline = distributeFacts(fixed, ids);
  if (sections.length >= 2) {
    // A cobertura das seções se mede no roteiro do modelo, antes de distributeFacts completar os slides com outros fatos.
    const bySection = outlineFromSections(fixed, sections, n, facts);
    outline = ensureSectionResults(bySection === fixed ? outline : bySection, sections, facts);
  }
  const deck: AltoDeck = {title: outline.titulo, theme: 'claro', slides: []};
  const summary = outline.slides.map((s, i) => `${i + 1}. ${s.tipo}: ${s.mensagem}`).join('\n');
  const fallbackNotes: Diagnostic[] = [];
  for (let i = 0; i < n; i++) {
    const plan = outline.slides[i], kind = plan.tipo;
    const ctx: SlideContext = {request, deck, facts, ids, mode, summary, slideMode, recorder, repairTruncated: options.repairTruncated ?? false, literalDetails: options.literalDetails,
      progress: (stage, slide) => progress(stage, slide), before: deck.slides, after: [], n, signal};
    let {accepted, diagnostics} = await writeSlide(ctx, plan, i);
    fallbackNotes.push(...diagnostics.filter(d => d.code === 'F002'));
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
    wall_ms: Date.now() - start, max_calls: maxCalls, request, outline, slideMode, images, literalDetails: options.literalDetails};
}
/** Frase cortada não termina com parêntese aberto: "escreve só a intenção (tipo de slide, título" → "escreve só a intenção". */
export function closeParens(text: string): string {
  const open = text.lastIndexOf('(');
  return open > text.lastIndexOf(')') && open > 20 ? text.slice(0, open).replace(/[\s,;:—–-]+$/, '') : text;
}
