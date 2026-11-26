// Porte para o app das correções do PC na leitura de documento (26/11), sem chamadas a mais.
import test from 'node:test';
import assert from 'node:assert/strict';
import {extractBytes, readingPlan, SHORT_DOCUMENT_CHARS, MAX_EXTRACT_CALLS} from '../outputs/tests/pipeline/documents.js';
import {collectDocument} from '../outputs/tests/pipeline/sources.js';
import {Recorder} from '../outputs/tests/pipeline/usage.js';
import {ensureSectionResults, factWeight, outlineFacts, outlineFromSections} from '../outputs/tests/pipeline/generate.js';

const file = (name = 'notas.md', bytes = 100) => ({name, bytes, mime: 'text/plain', uri: 'file:///cache/input'});
const utf8 = text => new TextEncoder().encode(text);
const usage = {input_tokens: 100, output_tokens: 50, prefill_ms: 20, decode_ms: 30};
const SECTIONS = ['Diferencial', 'Regras', 'Teste 1', 'Teste 2', 'Teste 3', 'Teste 4', 'Limitações'];
// Como o .md do professor: 7 seções curtas, várias listas (muitos trechos pequenos).
const shortDoc = () => SECTIONS.map((s, i) =>
  `## ${s}\nA seção ${s} explica a pergunta do teste número ${i + 1}.\n\n- O resultado da seção ${s} foi ${i + 1} de 24 decks.\n\n- A equipe registrou a seção ${s} com cuidado.`).join('\n\n');

test('documento curto: lido inteiro, na ordem, em no máximo 6 leituras de trechos vizinhos', async () => {
  const bytes = utf8(shortDoc()), doc = await extractBytes(file('notas.md', bytes.length), bytes);
  assert.ok(doc.chunks.length > MAX_EXTRACT_CALLS);
  const plan = readingPlan(doc, 'Um slide para cada teste, com o resultado');
  assert.equal(plan.complete, true);
  assert.equal(plan.batches.length, MAX_EXTRACT_CALLS);
  assert.deepEqual(plan.batches.flat().map(c => c.passage), doc.chunks.map(c => c.passage));  // todos, na ordem
  // Longo: continua a escolha de até 6 trechos, um por leitura.
  const long = SECTIONS.map(s => `## ${s}\n${'A equipe registra as decisões do projeto em um arquivo. '.repeat(60)}`).join('\n\n');
  const lb = utf8(long), ldoc = await extractBytes(file('longo.md', lb.length), lb);
  assert.ok(ldoc.characters > SHORT_DOCUMENT_CHARS);
  const lplan = readingPlan(ldoc, 'resuma este documento');
  assert.equal(lplan.complete, false); assert.ok(lplan.batches.every(b => b.length === 1)); assert.ok(lplan.batches.length <= 6);
});

test('leitura em lote: mesmas 6 chamadas; cada fato fica com a seção e o trecho de onde veio', async () => {
  const bytes = utf8(shortDoc()), doc = await extractBytes(file('notas.md', bytes.length), bytes);
  const inputs = [];
  const model = {complete: async input => {
    inputs.push(input);
    // Modo frases: escolhe toda frase com "resultado".
    const lines = input.user.split('\n').filter(l => /^\[\d+\]/.test(l));
    const out = lines.filter(l => l.includes('resultado')).slice(0, 6).map(l => {
      const n = l.match(/^\[(\d+)\]/)[1], s = l.replace(/^\[\d+\]\s*/, '');
      return `fato ${n} afirmacao "${s.replace(/"/g, '')}" tipo numero relevancia alta\n`;
    }).join('');
    return {text: out, usage};
  }};
  const result = await collectDocument(doc, 'Um slide para cada teste, com o resultado', new Recorder(model, 6), undefined, undefined, undefined, 'frases');
  assert.equal(inputs.length, 6);
  assert.ok(inputs.every(i => i.user.length < 2600), 'cada leitura cabe no contexto do celular');
  assert.equal(result.document.complete, true);
  assert.equal(result.warning, null);
  assert.deepEqual(result.document.sections.map(s => s.title), SECTIONS);  // todas as seções, na ordem
  for (const [id, f] of Object.entries(result.facts)) {
    const section = result.document.sections.find(s => s.facts.includes(id)).title;
    assert.ok(f.quote.includes(`seção ${section} `), `${id} na seção ${section}`);
    const passage = Number(f.url.split('#trecho-')[1]);
    assert.ok(doc.chunks.find(c => c.passage === passage).text.includes(f.quote));
  }
});

test('peso do fato: resultado > outro número > sem número', () => {
  assert.equal(factWeight({claim: 'Só 1 de 24 decks teve erro.'}), 2);
  assert.equal(factWeight({claim: 'Não há diferença entre os modelos.'}), 2);
  assert.equal(factWeight({claim: 'Cada deck tem 6 slides.'}), 1);
  assert.equal(factWeight({claim: 'A equipe registra as decisões.'}), 0);
});

const facts = {
  F1: {claim: 'O diferencial é a garantia sobre o arquivo.'}, F2: {claim: 'As regras usam 12 pedidos fixos.'},
  F3: {claim: 'O teste 1 pergunta se o arquivo abre.'}, F4: {claim: 'No teste 1, só 1 de 24 decks falhou.'},
  F5: {claim: 'O teste 2 mede o custo por deck.'}, F6: {claim: 'O custo caiu 30% no teste 2.'},
};
const sections = [{title: 'Diferencial', facts: ['F1']}, {title: 'Regras', facts: ['F2']},
  {title: 'Teste 1', facts: ['F3', 'F4']}, {title: 'Teste 2', facts: ['F5', 'F6']}];

test('roteiro segue as seções quando o modelo deixa uma de fora e elas cabem', () => {
  const outline = {titulo: 'T', slides: [{tipo: 'capa', mensagem: 'c', objetivo: 'c', fatos: []},
    {tipo: 'topicos', mensagem: 'a', objetivo: 'a', fatos: ['F1']}, {tipo: 'numeros', mensagem: 'b', objetivo: 'b', fatos: ['F3']},
    {tipo: 'etapas', mensagem: 'd', objetivo: 'd', fatos: ['F3']}, {tipo: 'conclusao', mensagem: 'e', objetivo: 'e', fatos: ['F1']}]};
  const out = outlineFromSections(outline, sections, 5, facts);
  assert.deepEqual(out.slides.map(s => s.mensagem), ['c', 'Diferencial', 'Regras', 'Teste 1', 'Teste 2']);
  assert.deepEqual(out.slides.map(s => s.tipo), ['capa', 'topicos', 'numeros', 'etapas', 'conclusao']);
  assert.deepEqual(out.slides[3].fatos, ['F4', 'F3']);  // resultado na frente
  // Todas as seções cobertas, ou seções que não cabem: o roteiro do modelo fica.
  const full = {...outline, slides: outline.slides.map((s, k) => k ? {...s, fatos: [sections[k - 1].facts[0]]} : s)};
  assert.equal(outlineFromSections(full, sections, 5, facts), full);
  assert.equal(outlineFromSections(outline, sections, 6, facts), outline);
});

test('cada slide da seção leva os resultados dela, na frente', () => {
  const outline = {titulo: 'T', slides: [{tipo: 'capa', mensagem: 'c', objetivo: 'c', fatos: []},
    {tipo: 'topicos', mensagem: 'x', objetivo: 'x', fatos: ['F3']}, {tipo: 'topicos', mensagem: 'y', objetivo: 'y', fatos: ['F5', 'F1']}]};
  const out = ensureSectionResults(outline, sections, facts);
  assert.deepEqual(out.slides[1].fatos, ['F4', 'F3']);
  assert.deepEqual(out.slides[2].fatos, ['F6', 'F5', 'F1']);
  assert.deepEqual(ensureSectionResults(outline, sections, facts, 2).slides[2].fatos, ['F6', 'F5']);  // teto: troca o sem número
});

test('roteiro com 40 fatos mostra todos no mesmo espaço', () => {
  const many = Object.fromEntries(Array.from({length: 40}, (_, k) => [`F${k + 1}`, {claim: `Fato ${k + 1}: ${'texto longo do documento '.repeat(10)}`, kind: 'numero'}]));
  const block = outlineFacts(many);
  assert.match(block, /^F40 /m); assert.ok(block.length <= 3600);
});
