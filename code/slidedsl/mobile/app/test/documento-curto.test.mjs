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

test('leitura literal: o modelo só escolhe a frase; a afirmação é a frase original, sem rótulo', async () => {
  const {factGrammar, parseFactLines, literalClaim} = await import('../outputs/tests/pipeline/sentences.js');
  const g = factGrammar(3, 6, false);
  assert.doesNotMatch(g, /afirmacao/);
  assert.match(g, /corpo ::= " tipo " tipo/);
  const s = ['Resultado: o lado A teve 1 de 24 apresentações.', 'O ajuste foi treinado com 1.876 exemplos que o modelo de 4B escreveu.'];
  const out = parseFactLines('fato 1 tipo numero relevancia alta\nfato 2 tipo numero relevancia alta\n', s);
  assert.deepEqual(out.map(f => f.afirmacao), ['O lado A teve 1 de 24 apresentações.', s[1]]);
  assert.equal(out[0].trecho, s[0]); assert.equal(out[1].valor, '1.876');
  assert.equal(literalClaim('Teste 1: garantia sobre o arquivo.'), 'Teste 1: garantia sobre o arquivo.');  // rótulo com número fica
});

test('palavra cortada perto do limite sai; palavra inteira fica', async () => {
  const {trimTruncated, knownWords} = await import('../outputs/tests/pipeline/generate.js');
  const schema = {type: 'string', maxLength: 48};
  const known = knownWords(['Cada pedido roda com 2 sementes: 24 apresentações por condição.']);
  assert.equal(trimTruncated('Cada pedido roda com 24 apresentações por condi', schema, known), 'Cada pedido roda com 24 apresentações');
  assert.equal(trimTruncated('Cada pedido roda com 24 apresentações por cond.', schema, known), 'Cada pedido roda com 24 apresentações por cond.');
  assert.equal(trimTruncated('Cada pedido roda com 24 apresentações condição', schema, known), 'Cada pedido roda com 24 apresentações condição');
  assert.equal(trimTruncated('Texto curto e longe do limite', schema, known), 'Texto curto e longe do limite');
});

test('detalhe literal: cada detalhe vira a frase do fato que combina com ele; número invertido some', async () => {
  const {literalizeDetails} = await import('../outputs/tests/pipeline/generate.js');
  const facts = {
    F1: {claim: 'O modelo gerou em média 1.380 tokens escrevendo código e 1.344 escrevendo SlideDSL.', quote: 'x'},
    F2: {claim: 'O tempo foi 19,8 s escrevendo código e 19,6 s escrevendo SlideDSL.', quote: 'y'},
    F3: {claim: 'O pipeline completo custa cerca de 5 vezes mais, em troca de mais apresentações válidas.', quote: 'z'},
  };
  const slide = {kind: 'topicos', title: 'Teste 2: custo', sources: ['F1'], items: [
    {label: 'Tokens gerados', detail: 'O modelo gerou 1.380 tokens de entrada e 1.344 de saída.'},
    {label: 'Tempo médio', detail: 'O tempo foi de 19,6 s com código.'},
    {label: 'Sem detalhe'}]};
  const out = literalizeDetails(slide, 'topicos', ['F1', 'F2', 'F3'], facts);
  assert.equal(out.items[0].detail, facts.F1.claim);
  assert.equal(out.items[1].detail, facts.F2.claim);
  assert.equal(out.items[2].detail, undefined);  // não acrescenta detalhe
  assert.deepEqual(out.sources, ['F1', 'F2']);
  assert.equal(out.items[0].label, 'Tokens gerados');  // o rótulo é do modelo
  // Comparação: até 80 caracteres, cortado na pausa; legenda de valor só com fato que tem o número.
  const cmp = literalizeDetails({kind: 'comparacao', title: 'x', sources: [], sides: [{name: 'Código', items: [{label: 'Tokens', detail: 'gerou 1.380 tokens'}]}]}, 'comparacao', ['F1'], facts);
  assert.ok(cmp.sides[0].items[0].detail.length <= 80); assert.match(cmp.sides[0].items[0].detail, /1\.380 tokens/);
  const num = literalizeDetails({kind: 'numeros', title: 'x', sources: [], values: [{value: '5 vezes', label: 'custo maior'}, {value: '42', label: 'tokens gerados'}]}, 'numeros', ['F1', 'F3'], facts);
  assert.equal(num.values[0].label, facts.F3.claim);
  assert.equal(num.values[1].label, 'tokens gerados');  // nenhum fato tem 42
  // Sem fato parecido: fica como está.
  const none = {kind: 'topicos', title: 'x', sources: [], items: [{label: 'Outra coisa', detail: 'Assunto que não aparece nos fatos.'}]};
  assert.equal(literalizeDetails(none, 'topicos', ['F1'], facts), none);
});

test('frase cortada não termina com parêntese aberto', async () => {
  const {closeParens} = await import('../outputs/tests/pipeline/generate.js');
  assert.equal(closeParens('No SlideDSL, o modelo escreve só a intenção (tipo de slide, título'), 'No SlideDSL, o modelo escreve só a intenção');
  assert.equal(closeParens('B superou A em 13 pares contra 1 (McNemar, p = 0,002)'), 'B superou A em 13 pares contra 1 (McNemar, p = 0,002)');
});

test('detalhe literal: item sem fato parecido sai quando sobram 2 itens com fato', async () => {
  const {literalizeDetails} = await import('../outputs/tests/pipeline/generate.js');
  const facts = {F1: {claim: 'O lado A teve 1 de 24 apresentações e o lado B teve 13 de 24.', quote: 'q'},
    F2: {claim: 'B superou A em 13 pares contra 1, com p = 0,002.', quote: 'q'}};
  const slide = {kind: 'topicos', title: 'x', sources: [], items: [
    {label: 'Resultado', detail: 'O lado A teve 1 de 24 apresentações.'}, {label: 'Inventado', detail: 'A plataforma ainda não provou nada disso.'},
    {label: 'Comparação', detail: 'B superou A em 13 pares.'}]};
  const out = literalizeDetails(slide, 'topicos', ['F1', 'F2'], facts);
  assert.deepEqual(out.items.map(i => i.label), ['Resultado', 'Comparação']);
  // Só 1 item com fato: nada sai (o slide precisa de 2).
  const one = literalizeDetails({...slide, items: slide.items.slice(0, 2)}, 'topicos', ['F1'], facts);
  assert.equal(one.items.length, 2);
});

test('texto copiado do prompt sai do slide; título legítimo com "Regras" fica', async () => {
  const {promptLeak, dropPromptLeaks} = await import('../outputs/tests/pipeline/generate.js');
  assert.ok(promptLeak('Regras do tipo: 2 a 5 itens paralelos (3 é o ideal)'));
  assert.ok(promptLeak('Fatos para este slide:'));
  assert.ok(promptLeak('SlideDSL Alto: Microsserviços escalam só o que está sob carga'));
  assert.ok(promptLeak('Regras do tipo'));
  assert.ok(!promptLeak('Regras comuns a todos os testes'));
  assert.ok(!promptLeak('Teste 1: garantia sobre o arquivo'));
  const slide = dropPromptLeaks({kind: 'topicos', title: 'Regras do tipo: 2 a 5 itens', items: [
    {label: 'Fatos para este slide:', detail: 'Fatos para este slide:'}, {label: 'A', detail: 'Frase um do documento.'}, {label: 'B', detail: 'Frase dois.'}]},
    'Regras comuns a todos os testes');
  assert.equal(slide.title, 'Regras comuns a todos os testes');
  assert.deepEqual(slide.items.map(i => i.label), ['A', 'B']);
});
