// Motor "igual ao celular" para o PC: roda o MESMO generate() do app (gramática com limites + leitura por
// frases numeradas + slide de reserva do compilador) contra um llama-server, imitando o llama.rn
// (template sem raciocínio + "/no_think", contexto 4096, temperatura 0,2). Chamado pelo servidor Python
// (src/slidedsl/motor_celular.py), que depois compila o deck com o compilador do PC para o editor.
//
// Saída: uma linha JSON por evento no stdout ({"evento":"progresso",...}) e, em --out:
//   deck.json (AltoDeck), fatos.json, chamadas.json, diagnosticos.json, fonte.json, apresentacao_celular.pptx
// Uso (na cópia de build, depois de `npm test`):
//   node bench/motor_pc.mjs --pedido "..." --slides 5 [--documento arquivo.txt|.md|.docx|.paginas.json] --out <pasta>
//   (.paginas.json = {"nome": "x.pdf", "paginas": [{"page": 1, "text": "..."}]}: um PDF já extraído por página, como o
//   módulo Android entrega; passa pela limpeza de PDF do app — teste do TCC, docs/TESTE_TCC_DOCUMENTO_LONGO.md)
//     [--url http://127.0.0.1:8080] [--semente 11] [--extracao frases|json] [--slides-modo gramatica_limites|json] [--imagens] [--detalhe-literal]
import fs from 'node:fs/promises';
import path from 'node:path';
import {generate} from '../outputs/tests/pipeline/generate.js';
import {extractBytes, makeDocument} from '../outputs/tests/pipeline/documents.js';
import {redoSlide} from '../outputs/tests/pipeline/edit.js';

const arg = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : fallback; };
const BASE = arg('url', 'http://127.0.0.1:8080');
const OUT = arg('out'), REQUEST = arg('pedido', ''), DOC = arg('documento');
const N = Number(arg('slides', '5')), SEED = Number(arg('semente', '11'));
const EXTRACT = arg('extracao', 'frases'), SLIDE_MODE = arg('slides-modo', 'gramatica_limites');
const PHOTOS = process.argv.includes('--imagens');
const LITERAL = process.argv.includes('--detalhe-literal');
if (!OUT) throw Error('Use --out.');
// Refazer um slide com o código do celular (edit.ts redoSlide): --refazer <n> --estado <json> grava refeito.json.
const REDO = Number(arg('refazer', '0')), STATE = arg('estado');
const AGENT = 'SlideDSL/1.1 (local educational presentation tool; limited interactive search)';
const emit = (evento, data = {}) => process.stdout.write(JSON.stringify({evento, ...data}) + '\n');

async function post(endpoint, body, signal) {
  const r = await fetch(BASE + endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal});
  if (!r.ok) throw Error(`llama-server ${endpoint}: HTTP ${r.status} ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

/** TextModel do app sobre o llama-server, equivalente ao src/llm/llamaRn.ts. */
function serverModel(seed) {
  return {
    async complete({system, user, schema, grammar, signal}) {
      const {prompt} = await post('/apply-template', {messages: [{role: 'system', content: system},
        {role: 'user', content: `${user}\n/no_think`}], chat_template_kwargs: {enable_thinking: false}}, signal);
      const {tokens} = await post('/tokenize', {content: prompt}, signal);
      const available = 4096 - tokens.length - 32;
      if (available < 512) throw Error('Pedido e fontes excedem o contexto de 4096 tokens. Encurte o pedido ou o texto da fonte.');
      const r = await post('/completion', {prompt, n_predict: Math.min(1400, available), temperature: 0.2, seed,
        cache_prompt: true, ...(grammar ? {grammar} : {json_schema: schema})}, signal);
      const t = r.timings ?? {};
      // Pedido e resposta de cada chamada, para depurar por que um slide falhou (o app não guarda o texto).
      await fs.appendFile(path.join(OUT, 'respostas.jsonl'), JSON.stringify({user: user.slice(-1500), text: r.content ?? ''}) + '\n').catch(() => {});
      return {text: r.content ?? '', usage: {input_tokens: r.tokens_evaluated ?? null, output_tokens: r.tokens_predicted ?? null,
        prefill_ms: t.prompt_ms ?? null, decode_ms: t.predicted_ms ?? null, timings: {...t}}};
    },
  };
}

async function main() {
  await fs.mkdir(OUT, {recursive: true});
  await post('/slots/0?action=erase', {}).catch(() => {});
  let source = {mode: 'none'}, readDocument;
  if (DOC) {
    const bytes = new Uint8Array(await fs.readFile(DOC)), name = path.basename(DOC);
    const ext = path.extname(name).toLowerCase();
    const mime = ext === '.docx' ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : ext === '.md' ? 'text/markdown' : 'text/plain';
    if (name.endsWith('.paginas.json')) {
      const pages = JSON.parse(new TextDecoder().decode(bytes));
      const doc = {uri: DOC, name: pages.nome ?? name.replace('.paginas.json', '.pdf'), bytes: bytes.length, mime: 'application/pdf'};
      source = {mode: 'document', document: doc};
      readDocument = async () => makeDocument(doc, pages.paginas.map(p => ({text: p.text, page: p.page})), 'PDFBox', pages.paginas.length);
    } else {
      const doc = {uri: DOC, name, bytes: bytes.length, mime};
      source = {mode: 'document', document: doc};
      readDocument = async () => extractBytes(doc, bytes);
    }
  }
  const started = Date.now();
  const result = await generate({request: REQUEST, slides: N, model: serverModel(SEED), source, readDocument,
    slideMode: SLIDE_MODE, extractMode: EXTRACT, literalDetails: LITERAL,
    images: PHOTOS ? {
      fetchJson: async (url, signal) => { const r = await fetch(url, {signal, headers: {Accept: 'application/json', 'User-Agent': AGENT}}); if (!r.ok) throw Error(`HTTP ${r.status}`); return r.json(); },
      fetchBytes: async (url, signal) => { const r = await fetch(url, {signal, headers: {'User-Agent': AGENT}}); if (!r.ok) throw Error(`HTTP ${r.status}`); return new Uint8Array(await r.arrayBuffer()); }} : undefined,
    onProgress: p => emit('progresso', {etapa: p.stage, slide: p.slide ?? null, total: p.total})});
  const write = (name, data) => fs.writeFile(path.join(OUT, name), JSON.stringify(data, null, 1));
  await write('deck.json', result.deck);
  await write('roteiro.json', {request: result.request, slideMode: result.slideMode, outline: result.outline});
  await write('fatos.json', result.facts);
  await write('chamadas.json', result.calls);
  await write('diagnosticos.json', result.diagnostics);
  await write('fonte.json', {mode: result.source.mode, document: result.source.document ? {name: result.source.document.name,
    sections: result.source.document.sections ?? []} : null});
  await fs.writeFile(path.join(OUT, 'apresentacao_celular.pptx'), Buffer.from(result.pptx));
  // Fotos para o compilador do PC: arquivos em imagens/ e crédito em imagens.json.
  if (Object.keys(result.images.data).length) {
    await fs.mkdir(path.join(OUT, 'imagens'), {recursive: true});
    for (const [file, uri] of Object.entries(result.images.data)) await fs.writeFile(path.join(OUT, 'imagens', file), Buffer.from(uri.split(',')[1], 'base64'));
  }
  await write('imagens.json', {info: result.images.info, log: result.images.log});
  emit('concluido', {segundos: Math.round((Date.now() - started) / 100) / 10, chamadas: result.calls.length,
    slides_compilador: result.diagnostics.filter(d => d.code === 'F001').map(d => d.slide)});
}

/** Refaz o slide REDO (1-based) do deck atual vindo do PC, com o mesmo prompt/gramática do app. */
async function redo() {
  const st = JSON.parse(await fs.readFile(STATE, 'utf8'));
  const slides = st.deck.slides, saved = st.roteiro?.outline?.slides ?? [];
  // Roteiro salvo se o deck ainda tem o mesmo número de slides; senão (slide excluído/incluído) deriva dos títulos.
  const outline = saved.length === slides.length ? {titulo: st.deck.title, slides: saved}
    : {titulo: st.deck.title, slides: slides.map(s => ({tipo: s.cycle ? 'ciclo' : s.kind, mensagem: s.title ?? st.deck.title, objetivo: s.title ?? st.deck.title}))};
  const result = {deck: st.deck, facts: st.facts ?? {}, outline, request: st.roteiro?.request ?? st.deck.title,
    slideMode: st.roteiro?.slideMode ?? SLIDE_MODE, calls: [], diagnostics: [], images: {info: {}, data: {}, log: []}};
  const started = Date.now();
  const out = await redoSlide(result, REDO - 1, st.instrucao ?? '', serverModel(SEED),
    {onProgress: stage => emit('progresso', {etapa: stage, slide: REDO, total: slides.length})});
  await fs.writeFile(path.join(OUT, 'refeito.json'), JSON.stringify({slide: out.deck.slides[REDO - 1], calls: out.calls}, null, 1));
  emit('concluido', {segundos: Math.round((Date.now() - started) / 100) / 10, chamadas: out.calls.length});
}

(REDO ? redo() : main()).catch(e => { emit('erro', {mensagem: e instanceof Error ? e.message : String(e)}); process.exitCode = 1; });
