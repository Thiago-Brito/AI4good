// Bancada do pipeline do APP (TypeScript) no PC: JSON Schema × SlideDSL Alto sob gramática.
//
// Roda o mesmo generate() do aplicativo contra o llama-server, imitando o llama.rn do celular
// (src/llm/llamaRn.ts): template de chat com raciocínio desligado + "/no_think", contexto 4096,
// n_predict = min(1400, sobra do contexto), temperatura 0,2, cache de prefixo, e restrição por
// json_schema (modo json) ou grammar (modo gramatica). Documento: o mesmo .txt do teste no celular,
// lido por extractBytes (código do app). O tempo no celular é PROJETADO a partir dos tokens
// processados e gerados, com as velocidades medidas no moto g(8) power lite (docs/RESULTADOS_T4.md).
//
// Pré-requisito: llama-server -m Qwen3-1.7B-Q4_K_M.gguf -ngl 99 -c 4096 -np 1 --jinja --port 8080 \
//   --cache-ram 0 --slot-save-path <pasta>   (sem cache de prompts entre gerações; erase por geração)
// Uso (na cópia de build, depois de `npm test`, que compila outputs/tests):
//   node bench/app_bench.mjs --docs <pasta dos .txt> --requests <format_requests.json> --out <pasta> [--seeds 11,22]
import fs from 'node:fs/promises';
import path from 'node:path';
import {generate} from '../outputs/tests/pipeline/generate.js';
import {extractBytes} from '../outputs/tests/pipeline/documents.js';

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const BASE = arg('url', 'http://127.0.0.1:8080');
const DOCS = arg('docs'), REQUESTS = arg('requests'), OUT = arg('out');
const SEEDS = arg('seeds', '11,22').split(',').map(Number);
const MODES = arg('modes', 'json,gramatica').split(',');
const ONLY = arg('only', '');
// Modelos pequenos no app novo: detalhes = frases dos fatos (App.tsx liga sozinho para arquivos < 2 GB).
const LITERAL = process.argv.includes('--detalhe-literal');
// Padrão: medianas medidas no celular com o 1.7B (RESULTADOS_T4.md). Outro modelo: --phone-prompt-tps / --phone-gen-tps.
const PHONE = {prompt_tps: Number(arg('phone-prompt-tps', '3.88')), gen_tps: Number(arg('phone-gen-tps', '1.49'))};
if (!DOCS || !REQUESTS || !OUT) throw Error('Use --docs, --requests e --out.');

async function post(endpoint, body, signal) {
  const r = await fetch(BASE + endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body), signal});
  if (!r.ok) throw Error(`llama-server ${endpoint}: HTTP ${r.status} ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

/** Modelo no formato TextModel do app, equivalente ao llamaRn.ts. */
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
      return {text: r.content ?? '', usage: {input_tokens: r.tokens_evaluated ?? null, output_tokens: r.tokens_predicted ?? null,
        prefill_ms: t.prompt_ms ?? null, decode_ms: t.predicted_ms ?? null, timings: {...t}}};
    },
  };
}

const sum = (rows, f) => rows.reduce((n, c) => n + (Number(f(c)) || 0), 0);
function summarize(calls) {
  const slide = calls.filter(c => c.stage === 'slide'), extract = calls.filter(c => c.stage === 'document_extract');
  const promptN = rows => sum(rows, c => c.timings?.prompt_n ?? c.input_tokens);
  const genN = rows => sum(rows, c => c.output_tokens);
  const phone = rows => (promptN(rows) / PHONE.prompt_tps + genN(rows) / PHONE.gen_tps) / 60;
  return {chamadas: calls.length, reparos: calls.filter(c => c.repair).length,
    falhas_chamada: calls.filter(c => c.status !== 'success').length,
    tokens_entrada: sum(calls, c => c.input_tokens), tokens_saida: genN(calls), prompt_processado: promptN(calls),
    slide_tokens_entrada: sum(slide, c => c.input_tokens), slide_tokens_saida: genN(slide), slide_prompt_processado: promptN(slide),
    extracao_prompt_processado: promptN(extract), extracao_tokens_saida: genN(extract),
    celular_extracao_min: Math.round(phone(extract) * 10) / 10,
    pc_ms: Math.round(sum(calls, c => c.wall_ms)),
    celular_min: Math.round(phone(calls) * 10) / 10, celular_slides_min: Math.round(phone(slide) * 10) / 10};
}

const FIELDS = ['run_id', 'request_id', 'mode', 'seed', 'status', 'valido', 'slides_compilador', 'chamadas', 'reparos',
  'falhas_chamada', 'tokens_entrada', 'tokens_saida', 'prompt_processado', 'slide_tokens_entrada', 'slide_tokens_saida',
  'slide_prompt_processado', 'extracao_prompt_processado', 'extracao_tokens_saida', 'celular_extracao_min', 'fatos',
  'fatos_rejeitados', 'pc_ms', 'celular_min', 'celular_slides_min', 'erro'];
const csvCell = v => (v === undefined || v === null ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));

async function main() {
  await fs.mkdir(OUT, {recursive: true});
  const csv = path.join(OUT, 'results.csv');
  let done = new Set();
  try { done = new Set((await fs.readFile(csv, 'utf8')).split('\n').slice(1).map(l => l.split(',')[0]).filter(Boolean)); }
  catch { await fs.writeFile(csv, FIELDS.join(',') + '\n'); }
  const data = JSON.parse(await fs.readFile(REQUESTS, 'utf8'));
  const requests = data.requests.filter(r => !ONLY || ONLY.split(',').includes(r.id));
  // Ordem sorteada e reproduzível (mesma semente de ordem do benchmark).
  let state = data.order_seed >>> 0;
  const rand = () => ((state = (state * 1664525 + 1013904223) >>> 0) / 2 ** 32);
  const plan = requests.flatMap(r => MODES.flatMap(mode => SEEDS.map(seed => ({r, mode, seed}))))
    .map(x => ({x, k: rand()})).sort((a, b) => a.k - b.k).map(({x}) => x);
  for (const [n, {r, mode, seed}] of plan.entries()) {
    const id = `${r.id}__${mode}__s${seed}`;
    if (done.has(id)) continue;
    const theme = r.id.split('_')[0], name = `${theme}.txt`;
    const bytes = new Uint8Array(await fs.readFile(path.join(DOCS, name)));
    const file = {uri: name, name, bytes: bytes.length, mime: 'text/plain'};
    const row = {run_id: id, request_id: r.id, mode, seed, status: 'failed', valido: false};
    let calls = [];
    // Cada geração começa com o cache vazio, como no celular (o modelo é carregado a cada geração).
    // Servidor iniciado com --cache-ram 0 e --slot-save-path para permitir o erase.
    await post('/slots/0?action=erase', {});
    process.stdout.write(`[${n + 1}/${plan.length}] ${id} ... `);
    try {
      // gramatica_limites = medido sem reparo de texto cortado; gramatica_limites_reparo = com o reparo.
      // Sufixo "+frases": leitura do documento por frases numeradas (sentences.ts) em vez de JSON com trecho copiado.
      const [slidePart, extractPart] = mode.split('+');
      const slideMode = slidePart.startsWith('gramatica_limites') ? 'gramatica_limites' : slidePart;
      const result = await generate({request: r.prompt, slides: 5, model: serverModel(seed), slideMode,
        repairTruncated: slidePart === 'gramatica_limites_reparo', extractMode: extractPart === 'frases' ? 'frases' : 'json', literalDetails: LITERAL,
        source: {mode: 'document', document: file}, readDocument: async () => extractBytes(file, bytes),
        onCalls: c => { calls = c; }});
      calls = result.calls;
      const f001 = result.diagnostics.filter(d => d.code === 'F001').length;
      Object.assign(row, {status: 'success', valido: !result.diagnostics.some(d => d.severity === 'ERRO'),
        slides_compilador: f001});
      await fs.writeFile(path.join(OUT, `${id}.pptx`), new Uint8Array(result.pptx));
      await fs.writeFile(path.join(OUT, `${id}.deck.json`), JSON.stringify(result.deck, null, 1));
      await fs.writeFile(path.join(OUT, `${id}.facts.json`), JSON.stringify({facts: result.facts, rejected: result.source.rejected}, null, 1));
      Object.assign(row, {fatos: Object.keys(result.facts).length, fatos_rejeitados: result.source.rejected.length});
      row.erro = result.diagnostics.filter(d => d.code === 'F001').map(d => d.message).join(' | ').slice(0, 200);
    } catch (e) {
      row.erro = (e instanceof Error ? e.message : String(e)).slice(0, 200);
    }
    Object.assign(row, summarize(calls));
    await fs.writeFile(path.join(OUT, `${id}.calls.json`), JSON.stringify(calls, null, 1));
    await fs.appendFile(csv, FIELDS.map(k => csvCell(row[k])).join(',') + '\n');
    console.log(`${row.status} valido=${row.valido} chamadas=${row.chamadas} saída=${row.tokens_saida} celular≈${row.celular_min} min`);
  }
}
await main();
