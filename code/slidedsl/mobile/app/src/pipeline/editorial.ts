// Limpeza do texto visível, igual à do PC (alto_generation.py strip_fact_ids/clean_visible e editorial.py
// proper_words/sentence_case/capitalize_visible). Não reescreve o conteúdo do modelo: só tira IDs de fatos
// ("conforme F2"), converte Title Case em caixa de frase e põe inicial maiúscula.
import type {AltoSlide} from '@slidedsl/core';

const isUpper = (c: string) => c !== c.toLowerCase() && c === c.toUpperCase();
const isLower = (c: string) => c !== c.toUpperCase() && c === c.toLowerCase();

function factRefPattern(ids: Iterable<string>): RegExp | null {
  const list = [...new Set([...ids].filter(i => /^F\d+$/.test(i)))].sort((a, b) => b.length - a.length);
  if (!list.length) return null;
  const ref = `(?:${list.join('|')})`;
  return new RegExp(String.raw`\s*[,;(]?\s*(?:\b(?:conforme|segundo|de acordo com|como (?:mostra|previsto|` +
    String.raw`mostrado|destacado|indicado|visto) em|como em|ver|vide|fonte:?)\s+)?(?:destacado em\s+)?` +
    String.raw`\b${ref}\b(?:\s*(?:e|,)\s*${ref}\b)*\)?`, 'gi');
}

/** Remove menções a IDs de fatos do dossiê. Só IDs existentes, para não apagar "F1" (Fórmula 1). */
export function stripFactIds(text: string | null | undefined, ids: Iterable<string>): string | null | undefined {
  const pattern = factRefPattern(ids);
  if (!text || !pattern) return text;
  let cleaned = text.replace(pattern, '').replace(/\s+([.,;:!?])/g, '$1').replace(/\s{2,}/g, ' ').trim();
  cleaned = cleaned.replace(/^[,;:.]\s*/, '');  // "Segundo F3, o uso..." → "o uso..."
  if (cleaned && isLower(cleaned[0]) && isUpper(text[0])) cleaned = cleaned[0].toUpperCase() + cleaned.slice(1);
  return cleaned || text;
}

/** Palavras com maiúscula no meio da frase: evidência de nome próprio. */
export function properWords(text: string | null | undefined): Set<string> {
  const found = new Set<string>();
  for (const sentence of (text ?? '').split(/[.!?:]\s+|\n+/)) {
    for (const w of (sentence.match(/[\p{L}\p{N}_-]+/gu) ?? []).slice(1)) if (isUpper(w[0])) found.add(w.toLowerCase());
  }
  return found;
}

// Letras soltas que são artigo/conjunção/preposição; outras ("C", "R") podem ser nomes e ficam.
const SINGLE_LOWER = new Set(['A', 'O', 'E', 'À', 'É']);

/** Title Case → caixa de frase; preserva siglas, grafias mistas (GitHub) e nomes próprios atestados. */
export function sentenceCase(text: string | null | undefined, keep: Iterable<string> = []): string | null | undefined {
  const words = (text ?? '').split(/\s+/).filter(Boolean);
  const long = words.filter(w => [...w].length > 3), caps = long.filter(w => isUpper(w[0]));
  if (long.length < 2 || caps.length / long.length <= 0.7) return text;
  const kept = new Set([...keep].map(k => k.toLowerCase()));
  return words.map((w, k) => k === 0 || (!SINGLE_LOWER.has(w) && w === w.toUpperCase() && w !== w.toLowerCase()) ||
    kept.has(w.replace(/^[.,:;]+|[.,:;]+$/g, '').toLowerCase()) || [...w.slice(1)].some(isUpper) ? w : w.toLowerCase()).join(' ');
}

export function capitalizeFirst<T extends string | null | undefined>(text: T): T {
  return (text && isLower(text[0]) ? text[0].toUpperCase() + text.slice(1) : text) as T;
}

/** Aplica, nesta ordem, o que o PC aplica a cada slide aceito do modelo. */
export function cleanVisible(slide: AltoSlide, ids: Iterable<string>, request: string): AltoSlide {
  const idList = [...ids], s = (t: string | null | undefined) => stripFactIds(t, idList) ?? null;
  const c = (t: string | null | undefined) => capitalizeFirst(s(t));
  const items = [...(slide.items ?? []), ...(slide.sides ?? []).flatMap(side => side.items)];
  slide.title = c(slide.title); slide.subtitle = c(slide.subtitle); slide.caption = c(slide.caption); slide.unit = s(slide.unit);
  for (const it of items) { it.label = c(it.label) ?? ''; it.detail = c(it.detail); }
  for (const v of slide.values ?? []) v.label = s(v.label) ?? '';
  for (const m of slide.milestones ?? []) { m.label = c(m.label) ?? ''; m.detail = c(m.detail); }
  const keep = properWords(request);
  if (slide.title) slide.title = sentenceCase(slide.title, keep) ?? slide.title;
  for (const side of slide.sides ?? []) side.name = sentenceCase(capitalizeFirst(side.name), keep) ?? side.name;
  return slide;
}
