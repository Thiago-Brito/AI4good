import type {Facts} from '@slidedsl/core';
import {prompts, schemaErrors} from './contracts.js';
import {Recorder} from './usage.js';
import {checkCancelled} from './types.js';
import {documentMetadata, genericDocumentRequest, readingPlan, type DocumentChunk, type DocumentFile, type DocumentText} from './documents.js';
import {FRASES_LITERAL_SYSTEM, FRASES_SYSTEM, MAX_SENTENCES, factGrammar, numberedSentences, parseFactLines, splitSentences, type ExtractMode} from './sentences.js';
export type SourceChoice = {mode: 'none'} | {mode: 'paste'; text: string} |
  {mode: 'wikipedia'; title: string; language: 'pt' | 'en'} | {mode: 'document'; document: DocumentFile};
export interface FactInput {afirmacao: string; trecho: string; valor?: string; tipo?: string; autor?: string; relevancia?: string}
export function normalize(text: string): string {
  return text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').replace(/[“”«»"']/g, '').replace(/\s+/g, ' ').trim();
}
function numbers(text: string): string[] { return text.match(/\d+(?:[.,]\d+)*(?:\s*%)?/g)?.map(x => x.replace(/\s/g, '')) ?? []; }
export function verifyFact(item: FactInput, passage: string): string | null {
  const quote = item.trecho?.trim() ?? '', claim = item.afirmacao?.trim() ?? '';
  // Documents.py requires literal containment in addition to research.verify_fact.
  if (normalize(quote).length < 10 || !normalize(passage).includes(normalize(quote))) return 'trecho não encontrado literalmente no texto';
  if (/(\.\.\.|…)\s*$/.test(quote) || /�/.test(quote + claim)) return 'trecho incompleto ou com caracteres inválidos';
  if (/^\s*#/.test(quote)) return 'título de seção não é fato';
  if (claim.split(/\s+/).length < 6) return 'afirmação incompleta (menos de 6 palavras)';
  if (item.relevancia === 'baixa') return 'pouco relevante para o assunto central';
  if (numbers(item.valor ?? '').some(n => !numbers(quote).includes(n))) return 'valor não aparece no trecho citado';
  if (numbers(claim).some(n => !numbers(passage).includes(n))) return 'número da afirmação não está no texto';
  if (item.tipo === 'citacao' && (!item.autor || !normalize(passage).includes(normalize(item.autor)))) {
    item.tipo = 'definicao'; item.autor = '';
  }
  return null;
}
export interface Passage {title: string; url: string; text: string}
const frasesSystem = (mode: ExtractMode) => mode === 'frases_resumo' ? FRASES_SYSTEM : FRASES_LITERAL_SYSTEM;
/** Uma chamada de extração. `json`: o modelo devolve fatos com o trecho copiado; `frases`: escolhe frases numeradas. */
export async function extractFacts(recorder: Recorder, header: string, text: string, mode: ExtractMode = 'json'): Promise<FactInput[]> {
  if (mode !== 'json') {
    const sentences = splitSentences(text);
    if (!sentences.length) return [];
    const {value} = await recorder.grammar('document_extract', frasesSystem(mode), `${header}\nFRASES:\n${numberedSentences(sentences)}`,
      prompts.extract_schema, factGrammar(sentences.length, 6, mode === 'frases_resumo'), out => parseFactLines(out, sentences));
    return value;
  }
  const raw = await recorder.json('document_extract', prompts.extract_system, `${header}\nTRECHO:\n${text}`, prompts.extract_schema);
  const errors = schemaErrors(raw, prompts.extract_schema);
  if (errors.length) throw Error(`Extração fora do formato: ${errors.join('; ')}`);
  return (raw as {fatos: FactInput[]}).fatos;
}
/** Uma leitura de vários trechos vizinhos (documento curto lido inteiro). Cada fato volta com o trecho de onde veio:
 * a conferência literal e a seção continuam por trecho. Em `frases`, a numeração corre pelos trechos, com o título da
 * seção entre eles (sem número, o modelo não pode escolhê-lo). */
export async function extractBatch(recorder: Recorder, header: string, batch: DocumentChunk[], mode: ExtractMode = 'json'):
    Promise<{item: FactInput; chunk: DocumentChunk}[]> {
  const title = (c: DocumentChunk) => c.section || c.heading;
  if (mode !== 'json') {
    const sentences: string[] = [], owner: DocumentChunk[] = [], lines: string[] = [];
    let last = '';
    for (const c of batch) {
      for (const s of splitSentences(c.text)) {
        if (sentences.length >= MAX_SENTENCES) break;
        if (title(c) && title(c) !== last) {lines.push(`(Seção: ${title(c)})`); last = title(c);}
        sentences.push(s); owner.push(c); lines.push(`[${sentences.length}] ${s}`);
      }
    }
    if (!sentences.length) return [];
    const {value} = await recorder.grammar('document_extract', frasesSystem(mode), `${header}\nFRASES:\n${lines.join('\n')}`,
      prompts.extract_schema, factGrammar(sentences.length, 6, mode === 'frases_resumo'), out => parseFactLines(out, sentences));
    return value.map(item => ({item, chunk: owner[sentences.indexOf(item.trecho)] ?? batch[0]}));
  }
  const text = batch.map(c => `${title(c) ? `Seção: ${title(c)}\n` : ''}${c.text}`).join('\n\n');
  const raw = await recorder.json('document_extract', prompts.extract_system, `${header}\nTRECHO:\n${text}`, prompts.extract_schema);
  const errors = schemaErrors(raw, prompts.extract_schema);
  if (errors.length) throw Error(`Extração fora do formato: ${errors.join('; ')}`);
  return (raw as {fatos: FactInput[]}).fatos.map(item => {
    const quote = normalize(item.trecho ?? '');
    return {item, chunk: batch.find(c => quote && normalize(c.text).includes(quote)) ?? batch[0]};
  });
}
export type FetchText = (url: string, signal?: AbortSignal) => Promise<unknown>;
export type ReadDocument = (file: DocumentFile, signal?: AbortSignal) => Promise<DocumentText>;
export interface DocumentUsage extends ReturnType<typeof documentMetadata> {
  chunks_used: number; facts_used: number; passages: number[]; max_extract_calls: number;
  sections: {title: string; facts: string[]}[];
  /** Documento curto lido inteiro, na ordem: as seções valem para qualquer pedido, não só o pedido geral. */
  complete?: boolean;
}
export interface CollectedFacts {facts: Facts; rejected: {item: FactInput; reason: string}[]; source: Passage | null; warning: string | null; document?: DocumentUsage}
export async function collectDocument(doc: DocumentText, request: string, recorder: Recorder, signal?: AbortSignal,
  progress?: (stage: string) => void, onDocument?: (doc: DocumentUsage) => void, mode: ExtractMode = 'json'): Promise<CollectedFacts> {
  const plan = readingPlan(doc, request), selected = plan.batches.flat();
  if (!selected.length) throw Error('Nenhum trecho relevante para o pedido. Use um pedido geral ou palavras presentes no documento.');
  const facts: Facts = {}, rejected: CollectedFacts['rejected'] = [], seen = new Set<string>();
  const metadata: DocumentUsage = {...documentMetadata(doc), chunks_used: 0, facts_used: 0, passages: [], max_extract_calls: 6, sections: [], complete: plan.complete};
  onDocument?.({...metadata});
  for (const [i, batch] of plan.batches.entries()) {
    checkCancelled(signal); progress?.(`Extraindo fatos ${i + 1}/${plan.batches.length}`);
    // Um trecho por leitura: o mesmo prompt de antes. Vários (documento curto): os trechos vizinhos juntos.
    const items = batch.length === 1 ? (await extractFacts(recorder,
      `Pedido: ${request}\nDocumento: ${doc.name}\nSeção: ${batch[0].heading}\nTrecho ${batch[0].passage}${batch[0].page ? `, página ${batch[0].page}` : ''}`, batch[0].text, mode))
      .map(item => ({item, chunk: batch[0]}))
      : await extractBatch(recorder, `Pedido: ${request}\nDocumento: ${doc.name}\nTrechos ${batch[0].passage} a ${batch.at(-1)!.passage}`, batch, mode);
    metadata.chunks_used += batch.length; metadata.passages.push(...batch.map(c => c.passage));
    for (const {item, chunk} of items) {
      // Números e citação devem estar no mesmo trecho, não em outra seção do documento.
      const reason = verifyFact(item, chunk.text), key = normalize(item.afirmacao);
      if (reason || seen.has(key) || normalize(item.trecho) === normalize(chunk.heading)) {rejected.push({item, reason: reason ?? (seen.has(key) ? 'duplicada' : 'título de seção não é fato')}); continue;}
      seen.add(key); const id = `F${Object.keys(facts).length + 1}`;
      facts[id] = {claim: item.afirmacao, quote: item.trecho, kind: item.tipo, value: item.valor ?? '', author: item.autor ?? '', relevance: item.relevancia,
        source_id: `S${chunk.passage}`, source_title: doc.name, url: `documento:${doc.name}#trecho-${chunk.passage}`};
      const title = chunk.section || chunk.heading || (chunk.page ? `Página ${chunk.page}` : 'Documento');  // seção de nível 1 do PDF
      let section = metadata.sections.find(s => s.title === title);
      if (!section) {section = {title, facts: []}; metadata.sections.push(section);}
      section.facts.push(id);
    }
    metadata.facts_used = Object.keys(facts).length;
    onDocument?.({...metadata, passages: [...metadata.passages], sections: metadata.sections.map(s => ({...s, facts: [...s.facts]}))});
  }
  if (!Object.keys(facts).length) throw Error('Nenhum fato com trecho literal válido no documento.');
  // A recuperação específica é ranqueada; o roteiro geral segue a ordem documental.
  const order = new Map<string, number>();
  for (const c of doc.chunks) {const key = c.section || c.heading || (c.page ? `Página ${c.page}` : 'Documento'); if (!order.has(key)) order.set(key, c.passage);}
  if (genericDocumentRequest(request) || plan.complete) metadata.sections.sort((a, b) => (order.get(a.title) ?? 0) - (order.get(b.title) ?? 0));
  return {facts, rejected, document: metadata, source: {title: doc.name, url: `documento:${doc.name}`, text: ''},
    warning: selected.length < doc.chunks.length ? `Documento amostrado: ${selected.length} de ${doc.chunks.length} trechos; até 6 chamadas de extração.` : null};
}
export async function wikipedia(title: string, language: 'pt' | 'en', fetchJson: FetchText, signal?: AbortSignal): Promise<Passage> {
  if (!['pt', 'en'].includes(language) || !title.trim() || title.length > 180) throw Error('Informe o título de uma página da Wikipedia pt/en.');
  checkCancelled(signal);
  const endpoint = `https://${language}.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.trim().replace(/ /g, '_'))}`;
  const value = await fetchJson(endpoint, signal) as {title?: string; extract?: string; type?: string; content_urls?: {desktop?: {page?: string}}};
  checkCancelled(signal);
  if (!value || value.type === 'disambiguation' || typeof value.extract !== 'string' || !value.extract.trim()) throw Error('Página não encontrada, ambígua ou sem resumo. Escolha um título mais específico.');
  return {title: value.title || title, text: value.extract.slice(0, 2600), url: value.content_urls?.desktop?.page || `https://${language}.wikipedia.org/wiki/${encodeURIComponent(title)}`};
}
export async function collectFacts(choice: SourceChoice, request: string, recorder: Recorder,
  fetchJson?: FetchText, signal?: AbortSignal, readDocument?: ReadDocument,
  progress?: (stage: string) => void, onDocument?: (doc: DocumentUsage) => void, mode: ExtractMode = 'json'): Promise<CollectedFacts> {
  const facts: Facts = {};
  const rejected: {item: FactInput; reason: string}[] = [];
  if (choice.mode === 'none') return {facts, rejected, source: null, warning: 'conteúdo sem fontes'};
  if (choice.mode === 'document') {
    if (!readDocument) throw Error('Leitor de documento indisponível.');
    progress?.('Lendo documento');
    return collectDocument(await readDocument(choice.document, signal), request, recorder, signal, progress, onDocument, mode);
  }
  let source: Passage;
  if (choice.mode === 'paste') {
    if (!choice.text.trim()) throw Error('Cole o texto da fonte.');
    source = {title: 'Texto colado', url: 'documento:texto-colado#trecho-1', text: choice.text.trim().slice(0, 2600)};
  } else {
    if (!fetchJson) throw Error('Wikipedia requer internet.');
    source = await wikipedia(choice.title, choice.language, fetchJson, signal);
  }
  const items = await extractFacts(recorder, `Pedido: ${request}\nDocumento: ${source.title}`, source.text, mode);
  const seen = new Set<string>();
  for (const item of items) {
    const reason = verifyFact(item, source.text);
    const key = normalize(item.afirmacao);
    if (reason || seen.has(key)) { rejected.push({item, reason: reason ?? 'duplicada'}); continue; }
    seen.add(key);
    facts[`F${Object.keys(facts).length + 1}`] = {claim: item.afirmacao, quote: item.trecho,
      kind: item.tipo, value: item.valor ?? '', author: item.autor ?? '', relevance: item.relevancia,
      source_id: 'S1', source_title: source.title, url: source.url};
    if (Object.keys(facts).length >= 3) break;
  }
  if (!Object.keys(facts).length) throw Error('Nenhum fato com trecho literal válido. Revise a fonte ou selecione sem pesquisa.');
  return {facts, rejected, source, warning: choice.mode === 'paste' && choice.text.trim().length > 2600 ? 'Extração limitada aos primeiros 2600 caracteres.' : null};
}
