import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {altoToJson, slideGrammar, altoKinds, altoFormatHint, extractBlock} from '../outputs/tests/pipeline/altoText.js';
import {generate, jsonToSlide} from '../outputs/tests/pipeline/generate.js';
import {schemaErrors, schemaWithFacts, prompts} from '../outputs/tests/pipeline/contracts.js';

const usage = {input_tokens: 100, output_tokens: 50, prefill_ms: 20, decode_ms: 30};
const schemaFor = (kind, ids = ['F1', 'F2']) =>
  schemaWithFacts(prompts.slide_schemas[kind][ids.length ? 'with_facts' : 'without_facts'], ids);
const fixtures = JSON.parse(await fs.readFile(new URL('./fixtures/alto_slides.json', import.meta.url), 'utf8'));

// Mesma comparação para os dois lados: textos sem espaços nas pontas, vazio = ausente.
const s = v => (typeof v === 'string' ? v.trim() || null : v ?? null);
const items = list => (list ?? []).map(i => ({label: s(i.label), detail: s(i.detail)}));
function normal(x) {
  return {kind: x.kind, title: s(x.title), subtitle: s(x.subtitle), author: s(x.author), text: s(x.text),
    unit: s(x.unit), notes: s(x.notes), items: items(x.items),
    values: (x.values ?? []).map(v => ({value: s(v.value), label: s(v.label)})),
    sides: (x.sides ?? []).map(d => ({name: s(d.name), items: items(d.items)})),
    milestones: (x.milestones ?? []).map(m => ({date: s(m.date), label: s(m.label), detail: s(m.detail)})),
    bars: (x.bars ?? []).map(b => ({label: s(b.label), value: Number(b.value)})),
    sources: [...new Set(x.sources ?? [])]};
}

test(`paridade do leitor Alto com o parser Python (${fixtures.cases.length} slides do corpus)`, () => {
  assert.ok(fixtures.cases.length >= 300);
  const failures = [];
  for (const c of fixtures.cases) {
    try {
      const got = normal(jsonToSlide(c.kind, altoToJson(c.kind, c.text, schemaFor(c.kind))));
      assert.deepEqual(got, normal(c.expected));
    } catch (e) {
      failures.push(`${c.kind}: ${e.message.split('\n')[0]}\n${c.text.slice(0, 200)}`);
    }
  }
  assert.equal(failures.length, 0, failures.slice(0, 3).join('\n---\n'));
  const kinds = new Set(fixtures.cases.map(c => c.kind));
  for (const k of altoKinds()) assert.ok(kinds.has(k), `sem caso de paridade para ${k}`);
});

test('gramática por tipo: raiz no bloco do tipo, limites do schema e IDs de fatos reais', () => {
  for (const kind of altoKinds()) {
    const g = slideGrammar(kind, schemaFor(kind));
    assert.match(g, new RegExp(`^root ::= ws "${kind}" ws "\\{"`));
    assert.ok(g.includes('chr ::='), kind);
    if (prompts.slide_schemas[kind].with_facts.properties.fontes) assert.match(g, /fato ::= "F1" \| "F2"/);
    if (prompts.slide_schemas[kind].with_facts.properties.notas) assert.match(g, /ws "notas" ws s-0-2000/);
  }
  const topicos = slideGrammar('topicos', schemaFor('topicos'));
  assert.match(topicos, /r-item\{2,5\}/);
  assert.match(topicos, /ws "titulo" ws s-4-160/);
  assert.match(slideGrammar('comparacao', schemaFor('comparacao')), /r-lado\{2,2\}/);
  // Sem fatos não há regra de fontes (o JSON exigiria lista vazia).
  assert.doesNotMatch(slideGrammar('topicos', schemaFor('topicos', [])), /fontes/);
});

test('bloco Alto vira o mesmo objeto do JSON e passa no schema; campos vazios aceitos', () => {
  const schema = schemaFor('topicos');
  const text = 'Aqui está:\n```\ntopicos {\n  titulo "A equipe confere cada entrega"\n  item "Escopo" "A equipe confere as tarefas antes de iniciar."\n  item "Revisão" "Cada entrega recebe revisão."\n  fontes F1, F2\n  notas ""\n}\n```';
  const data = altoToJson('topicos', text, schema);
  assert.deepEqual(schemaErrors(data, schema), []);
  assert.deepEqual(data.fontes, ['F1', 'F2']);
  assert.equal(data.notas, '');
  const capa = altoToJson('capa', 'capa { titulo "Planejar ajuda" subtitulo "" autor "" notas "" }', schemaFor('capa'));
  assert.deepEqual(schemaErrors(capa, schemaFor('capa')), []);
  const graf = altoToJson('grafico', 'grafico { titulo "Consumo por região" unidade "kWh" barra "Norte" 18 barra "Sul" 30.5 fontes F1 notas "x" }', schemaFor('grafico'));
  assert.deepEqual(graf.barras, [{rotulo: 'Norte', valor: 18}, {rotulo: 'Sul', valor: 30.5}]);
  assert.match(extractBlock('lixo topicos { titulo "a" } depois', 'topicos'), /^topicos \{ titulo "a" \}$/);
});

test('sintaxe inválida gera erro claro (vira P002 e reparo no pipeline)', () => {
  assert.throws(() => altoToJson('topicos', 'topicos { titulo "x" item }', schemaFor('topicos')), /Sintaxe inválida/);
  assert.throws(() => altoToJson('topicos', 'nada aqui', schemaFor('topicos')), /não encontrado/);
  assert.throws(() => altoToJson('topicos', 'topicos { titulo "x" item "a" "b" extra }', schemaFor('topicos')), /Sintaxe inválida/);
  // Texto depois do bloco é ignorado, como no parser Python (_parse_slide_text).
  assert.equal(altoToJson('topicos', 'topicos { titulo "x" item "a" "b" } depois', schemaFor('topicos')).titulo, 'x');
});

test('dica de formato: linha curta por tipo (padrão) e exemplo completo opcional', () => {
  const short = altoFormatHint('comparacao', schemaFor('comparacao'));
  assert.match(short, /comparacao \{ titulo "…" lado "nome" \{ item "rótulo" "detalhe" \}/);
  assert.match(short, /fontes F1, F2 notas "…" \}$/);
  assert.match(altoFormatHint('numeros', schemaFor('numeros')), /valor "número" "legenda"/);
  assert.doesNotMatch(altoFormatHint('topicos', schemaFor('topicos', [])), /fontes/);
  assert.ok(short.length < 200);
  const full = altoFormatHint('comparacao', schemaFor('comparacao'), true);
  assert.match(full, /lado "Alternativa A" \{/);
  assert.match(full, /fontes F1, F2/);
});

// ---------------------------------------------------------------------------
// Pipeline completo no modo gramática, com modelo simulado que escreve Alto.

const q = v => JSON.stringify(v);
function toAlto(kind, d) {
  const lines = [`${kind} {`];
  if (d.titulo !== undefined) lines.push(`  titulo ${q(d.titulo)}`);
  if (kind === 'capa') lines.push(`  subtitulo ${q(d.subtitulo ?? '')}`, `  autor ${q(d.autor ?? '')}`);
  for (const i of d.itens ?? []) lines.push(`  item ${q(i.rotulo)} ${q(i.detalhe)}`);
  if (d.fontes?.length) lines.push(`  fontes ${d.fontes.join(', ')}`);
  lines.push(`  notas ${q(d.notas ?? '')}`, '}');
  return lines.join('\n');
}
const item = (label, detail) => ({rotulo: label, detalhe: detail});
const content = kind => kind === 'capa' ? {titulo: 'Planejar ajuda a equipe', subtitulo: 'Decisões locais para organizar o trabalho.', autor: '', notas: ''} : {
  titulo: kind === 'conclusao' ? 'Escolha a próxima atividade' : 'A equipe confere cada entrega',
  itens: [item('Escopo definido', 'A equipe confere as tarefas antes de iniciar o trabalho.'),
    item('Revisão frequente', 'Cada entrega recebe uma revisão antes da apresentação.')],
  fontes: [], notas: 'Explique as condições necessárias para realizar cada atividade.',
};
class AltoMock {
  constructor({brokenFirst = []} = {}) { this.brokenFirst = brokenFirst; this.inputs = []; this.counts = {}; }
  async complete(input) {
    this.inputs.push(input);
    if (input.schema.properties.slides) {
      const n = input.schema.properties.slides.minItems;
      const outline = {titulo: 'Trabalho organizado', slides: Array.from({length: n}, (_, i) => ({
        tipo: i === 0 ? 'capa' : i === n - 1 ? 'conclusao' : i % 2 ? 'topicos' : 'etapas',
        mensagem: 'A equipe organiza cada entrega', objetivo: 'Como a equipe confere cada entrega?'}))};
      return {text: JSON.stringify(outline), usage};
    }
    const i = Number(input.user.match(/Escreva o slide (\d+)/)[1]);
    const kind = input.user.match(/\(tipo (\w+)\)/)[1];
    this.counts[i] = (this.counts[i] ?? 0) + 1;
    assert.ok(input.grammar, 'chamada de slide sem gramática no modo gramatica');
    if (this.brokenFirst.includes(i) && this.counts[i] === 1) return {text: `${kind} { titulo "corte`, usage};
    return {text: toAlto(kind, content(kind)), usage};
  }
}
const request = model => ({model, request: 'Explique como organizar o trabalho em equipe.', slides: 5, source: {mode: 'none'}});

test('modo gramatica: 5 slides válidos, toda chamada de slide com GBNF e dica de formato', async () => {
  const model = new AltoMock();
  const result = await generate({...request(model), slideMode: 'gramatica'});
  assert.equal(result.ir.slides.length, 5);
  assert.equal(result.diagnostics.filter(d => d.severity === 'ERRO').length, 0);
  assert.equal(result.calls.length, 6);
  const slideCalls = model.inputs.filter(x => !x.schema.properties.slides);
  assert.equal(slideCalls.length, 5);
  assert.ok(slideCalls.every(x => x.grammar.startsWith('root ::=') && /Responda SOMENTE com o bloco SlideDSL Alto/.test(x.user)));
  // O roteiro continua em JSON (sem gramática), como no teste do PC.
  assert.equal(model.inputs[0].grammar, undefined);
});

test('modo gramatica: resposta cortada vira reparo com o texto anterior, e o deck sai válido', async () => {
  const model = new AltoMock({brokenFirst: [3]});
  const result = await generate({...request(model), slideMode: 'gramatica'});
  assert.equal(result.ir.slides.length, 5);
  assert.equal(result.calls.filter(c => c.repair).length, 1);
  assert.equal(model.counts[3], 2);
  assert.equal(result.calls.find(c => c.slide === 3 && c.attempt === 0).status, 'failed');
});

test('gramatica_limites: maxLength reduzido aos limites A005 do compilador, sem tocar no schema original', async () => {
  const {withCompilerLimits} = await import('../outputs/tests/pipeline/altoText.js');
  const base = schemaFor('comparacao'), lim = withCompilerLimits(base);
  assert.equal(lim.properties.titulo.maxLength, 80);
  assert.equal(lim.properties.notas.maxLength, 1500);
  assert.equal(lim.properties.lados.items.properties.nome.maxLength, 40);
  assert.equal(lim.properties.lados.items.properties.itens.items.properties.detalhe.maxLength, 80);
  assert.equal(base.properties.titulo.maxLength, 160);
  assert.match(slideGrammar('comparacao', lim), /ws "titulo" ws s-4-80/);
  const linha = withCompilerLimits(schemaFor('linha_do_tempo'));
  assert.equal(linha.properties.marcos.items.properties.rotulo.maxLength, 36);
  assert.equal(withCompilerLimits(schemaFor('grafico')).properties.barras.items.properties.rotulo.maxLength, 24);
  const model = new AltoMock();
  const result = await generate({...request(model), slideMode: 'gramatica_limites'});
  assert.equal(result.ir.slides.length, 5);
  assert.ok(model.inputs.filter(x => x.grammar).every(x => /s-4-80/.test(x.grammar)));
});

test('roteiro sem capa/conclusão é corrigido como no Python, em vez de abortar o deck', async () => {
  const {fixOutline} = await import('../outputs/tests/pipeline/generate.js');
  const fixed = fixOutline({titulo: 'T', slides: [{tipo: 'topicos'}, {tipo: 'capa'}, {tipo: 'etapas'}, {tipo: 'topicos'}]});
  assert.deepEqual(fixed.slides.map(s => s.tipo), ['capa', 'topicos', 'etapas', 'conclusao']);
  const bad = new AltoMock();
  const original = bad.complete.bind(bad);
  bad.complete = async input => {
    const out = await original(input);
    if (input.schema.properties.slides) {
      const o = JSON.parse(out.text);
      o.slides[0].tipo = 'topicos'; o.slides[o.slides.length - 1].tipo = 'etapas';
      return {...out, text: JSON.stringify(o)};
    }
    return out;
  };
  const result = await generate({...request(bad), slideMode: 'gramatica'});
  assert.equal(result.ir.slides.length, 5);
  assert.equal(result.deck.slides[0].kind, 'capa');
  assert.equal(result.deck.slides[4].kind, 'conclusao');
});

test('gramatica_limites: texto cortado no limite pede 1 reparo e, se persistir, o slide é aceito', async () => {
  const {truncatedPaths, withCompilerLimits} = await import('../outputs/tests/pipeline/altoText.js');
  const lim = withCompilerLimits(schemaFor('topicos'));
  const data = {titulo: 'x'.repeat(80), itens: [{rotulo: 'Ok', detalhe: 'y'.repeat(170)}], fontes: [], notas: ''};
  assert.deepEqual(truncatedPaths(data, lim).map(t => t.path), ['titulo', 'itens.0.detalhe']);
  class Cut extends AltoMock {
    async complete(input) {
      const out = await super.complete(input);
      if (input.grammar && /tipo topicos/.test(input.user)) return {...out, text: out.text.replace(/item "Escopo definido" "[^"]*"/, `item "Escopo definido" "${'A equipe confere '.repeat(10).slice(0, 170)}"`)};
      return out;
    }
  }
  const model = new Cut();
  const result = await generate({...request(model), slideMode: 'gramatica_limites', repairTruncated: true});
  assert.equal(result.ir.slides.length, 5);
  const repairs = model.inputs.filter(x => /Corrija os diagnósticos/.test(x.user));
  assert.ok(repairs.length >= 1 && repairs.every(x => /cortado no limite de 170/.test(x.user)));
  assert.equal(result.diagnostics.filter(d => d.code === 'F001').length, 0);
  const off = new Cut();
  // Padrão: sem reparo de texto cortado (não ajudou na bancada).
  const plain = await generate({...request(off), slideMode: 'gramatica_limites'});
  assert.equal(plain.calls.filter(c => c.repair).length, 0);
});

test('modo json continua o padrão e não envia gramática', async () => {
  const inputs = [];
  const json = {async complete(input) {
    inputs.push(input);
    if (input.schema.properties.slides) {
      const n = input.schema.properties.slides.minItems;
      return {text: JSON.stringify({titulo: 'Trabalho organizado', slides: Array.from({length: n}, (_, i) => ({
        tipo: i === 0 ? 'capa' : i === n - 1 ? 'conclusao' : 'topicos',
        mensagem: 'A equipe organiza cada entrega', objetivo: 'Como a equipe confere cada entrega?'}))}), usage};
    }
    return {text: JSON.stringify(content(input.user.match(/\(tipo (\w+)\)/)[1])), usage};
  }};
  const result = await generate(request(json));
  assert.equal(result.ir.slides.length, 5);
  assert.ok(inputs.every(x => x.grammar === undefined));
});
