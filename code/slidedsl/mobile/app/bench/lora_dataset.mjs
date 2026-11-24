// Dataset de destilação: roda o generate() do APP (gramatica_limites + frases) com um modelo professor no
// llama-server (Qwen3 4B) e grava cada chamada (system, user, gramática, saída). Só entra no treino o que passa
// nas conferências do próprio app:
// - slide: chamada bem-sucedida, e o slide final NÃO foi montado pelo compilador (sem F001 naquele slide);
// - roteiro: apresentação gerada sem erro;
// - leitura por frases: só as linhas cujo fato passa no verifyFact (a saída é reescrita sem as demais).
// Temas diferentes dos da bancada (scripts/lora_documentos.py).
//
// Uso (na cópia de build, depois de `npm test`):
//   node bench/lora_dataset.mjs --docs <outputs/lora/documentos> --requests <outputs/lora/pedidos.json> --out <pasta>
import fs from 'node:fs/promises';
import path from 'node:path';
import {generate} from '../outputs/tests/pipeline/generate.js';
import {extractBytes} from '../outputs/tests/pipeline/documents.js';
import {parseFactLines} from '../outputs/tests/pipeline/sentences.js';
import {verifyFact} from '../outputs/tests/pipeline/sources.js';

const arg = (name, fallback) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : fallback; };
const BASE = arg('url', 'http://127.0.0.1:8080');
const DOCS = arg('docs'), REQUESTS = arg('requests'), OUT = arg('out');
const SEEDS = arg('seeds', '7').split(',').map(Number);
if (!DOCS || !REQUESTS || !OUT) throw Error('Use --docs, --requests e --out.');

async function post(endpoint, body) {
  const r = await fetch(BASE + endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (!r.ok) throw Error(`llama-server ${endpoint}: HTTP ${r.status} ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

/** Igual ao serverModel da bancada (imita o llama.rn), mas guarda entrada e saída de cada chamada. */
function loggingModel(seed, log) {
  return {
    async complete({system, user, schema, grammar}) {
      const {prompt} = await post('/apply-template', {messages: [{role: 'system', content: system},
        {role: 'user', content: `${user}\n/no_think`}], chat_template_kwargs: {enable_thinking: false}});
      const {tokens} = await post('/tokenize', {content: prompt});
      const available = 4096 - tokens.length - 32;
      if (available < 512) throw Error('Pedido e fontes excedem o contexto de 4096 tokens.');
      const r = await post('/completion', {prompt, n_predict: Math.min(1400, available), temperature: 0.2, seed,
        cache_prompt: true, ...(grammar ? {grammar} : {json_schema: schema})});
      const text = r.content ?? '';
      log.push({system, user, grammar: grammar ?? null, schema: grammar ? null : schema, output: text});
      return {text, usage: {input_tokens: r.tokens_evaluated ?? null, output_tokens: r.tokens_predicted ?? null,
        prefill_ms: r.timings?.prompt_ms ?? null, decode_ms: r.timings?.predicted_ms ?? null}};
    },
  };
}

/** Linhas de fato aceitas pelo verifyFact, na ordem original; passagem = frases numeradas do prompt. */
function cleanExtraction(user, output) {
  const sentences = [...user.matchAll(/^\[(\d+)\] (.*)$/gm)].map(m => m[2]);
  const passage = sentences.join(' '), kept = [];
  for (const line of output.split('\n')) {
    const [fact] = parseFactLines(line, sentences);
    if (fact && verifyFact(fact, passage) === null) kept.push(line.trim());
  }
  return kept;
}

async function main() {
  await fs.mkdir(OUT, {recursive: true});
  const file = path.join(OUT, 'amostras.jsonl'), doneFile = path.join(OUT, 'feitos.txt');
  const done = new Set((await fs.readFile(doneFile, 'utf8').catch(() => '')).split('\n').filter(Boolean));
  const reqs = JSON.parse(await fs.readFile(REQUESTS, 'utf8')).requests;
  // Pedidos com documento; e "sem pesquisa" nos pedidos de nível tema (o app também gera sem fonte).
  const plan = reqs.flatMap(r => [{r, source: 'document'}, ...(r.level === 'tema' ? [{r, source: 'none'}] : [])])
    .flatMap(p => SEEDS.map(seed => ({...p, seed})));
  let n = 0, kept = {slide: 0, roteiro: 0, document_extract: 0}, dropped = 0;
  for (const {r, source, seed} of plan) {
    const id = `${r.id}__${source}__s${seed}`;
    n++;
    if (done.has(id)) continue;
    await post('/slots/0?action=erase', {}).catch(() => {});
    const slides = 5 + (seed + r.id.length) % 2;  // 5 ou 6 slides
    const log = [];
    process.stdout.write(`[${n}/${plan.length}] ${id} ... `);
    try {
      const bytes = new Uint8Array(await fs.readFile(path.join(DOCS, r.doc)));
      const doc = {uri: r.doc, name: r.doc, bytes: bytes.length, mime: 'text/plain'};
      const result = await generate({request: r.prompt, slides, model: loggingModel(seed, log),
        slideMode: 'gramatica_limites', extractMode: 'frases',
        source: source === 'document' ? {mode: 'document', document: doc} : {mode: 'none'},
        readDocument: async () => extractBytes(doc, bytes)});
      const fallback = new Set(result.diagnostics.filter(d => d.code === 'F001').map(d => d.slide));
      const lines = [];
      result.calls.forEach((c, i) => {
        const s = log[i];
        if (!s || c.status !== 'success') { dropped++; return; }
        let output = s.output, ok = true;
        if (c.stage === 'slide') ok = !fallback.has(c.slide);
        else if (c.stage === 'document_extract') {
          const keep = cleanExtraction(s.user, s.output);
          ok = keep.length > 0; output = keep.map(l => l + '\n').join('');
        }
        if (!ok) { dropped++; return; }
        kept[c.stage]++;
        lines.push(JSON.stringify({id, stage: c.stage, slide: c.slide, attempt: c.attempt, system: s.system, user: s.user,
          grammar: s.grammar, output}));
      });
      if (lines.length) await fs.appendFile(file, lines.join('\n') + '\n');
      console.log(`ok slides_compilador=${fallback.size} amostras=${lines.length}`);
    } catch (e) {
      console.log(`falhou: ${(e instanceof Error ? e.message : String(e)).slice(0, 120)}`);
    }
    await fs.appendFile(doneFile, id + '\n');
  }
  console.log('aceitas', kept, 'descartadas', dropped);
}
await main();
