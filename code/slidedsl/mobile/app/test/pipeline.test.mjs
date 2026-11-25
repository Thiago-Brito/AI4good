import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import JSZip from 'jszip';
import {generate, GenerationError, jsonToSlide} from '../outputs/tests/pipeline/generate.js';
import {schemaErrors, schemaWithFacts, prompts} from '../outputs/tests/pipeline/contracts.js';
import {verifyFact, collectFacts, wikipedia} from '../outputs/tests/pipeline/sources.js';
import {Recorder, costBreakdown} from '../outputs/tests/pipeline/usage.js';
import {testData} from '../outputs/tests/pipeline/testData.js';
import {models, modelAllowed, suggestedModel} from '../outputs/tests/models.js';
const usage = {input_tokens: 100, output_tokens: 50, prefill_ms: 20, decode_ms: 30, timings: {prompt_ms: 20, predicted_ms: 30}};
const item = (label, detail) => ({rotulo: label, detalhe: detail});
const content = kind => kind === 'capa' ? {titulo: 'Planejar ajuda a equipe', subtitulo: 'Decisões locais para organizar o trabalho.', autor: '', notas: ''} : {
  titulo: kind === 'conclusao' ? 'Escolha a próxima atividade' : 'A equipe confere cada entrega',
  itens: [item('Escopo definido', 'A equipe confere as tarefas antes de iniciar o trabalho.'),
    item('Revisão frequente', 'Cada entrega recebe uma revisão antes da apresentação.'),
    ...(kind === 'conclusao' ? [] : [item('Registro disponível', 'O grupo consulta o registro quando precisa retomar uma decisão.')])],
  fontes: [], notas: 'Explique as condições necessárias para realizar cada atividade.',
};
const fact = {afirmacao: 'A equipe confere as tarefas antes de iniciar o trabalho.', tipo: 'definicao', valor: '',
  trecho: 'A equipe confere as tarefas antes de iniciar o trabalho.', autor: '', relevancia: 'alta'};
class Mock {
  constructor({badFirst = [], alwaysBad = [], longTitle = [], garbage = [], n = 5, extract = [fact], overrideOutline, onComplete} = {}) {
    Object.assign(this, {badFirst, alwaysBad, longTitle, garbage, n, extract, overrideOutline, onComplete}); this.inputs = []; this.counts = {};
  }
  async complete(input) {
    this.inputs.push(input); this.onComplete?.(input, this);
    if (input.schema.properties.fatos) return {text: JSON.stringify({fatos: this.extract}), usage};
    if (input.schema.properties.slides) {
      const n = input.schema.properties.slides.minItems;
      const outline = {titulo: 'Trabalho organizado', slides: Array.from({length: n}, (_, i) => ({tipo: i === 0 ? 'capa' : i === n - 1 ? 'conclusao' : i % 2 ? 'topicos' : 'etapas', mensagem: 'A equipe organiza cada entrega', objetivo: 'Como a equipe confere cada entrega?',
        ...(input.schema.properties.slides.items.properties.fatos ? {fatos: ['F1']} : {})}))};
      this.overrideOutline?.(outline);
      return {text: JSON.stringify(outline), usage};
    }
    const i = Number(input.user.match(/Escreva o slide (\d+)/)[1]);
    const kind = input.user.match(/\(tipo (\w+)\)/)[1];
    this.counts[i] = (this.counts[i] ?? 0) + 1;
    if (this.garbage.includes(i)) return {text: '{}', usage};
    const data = content(kind);
    if (input.schema.properties.fontes?.items) data.fontes = ['F1'];
    if (this.alwaysBad.includes(i) || (this.badFirst.includes(i) && this.counts[i] === 1)) data.titulo = 'x'.repeat(100);
    if (this.longTitle.includes(i)) data.titulo = 'A equipe confere cada entrega com cuidado antes de apresentar o resultado final para toda a turma';
    return {text: JSON.stringify(data), usage};
  }
}
const base = model => ({model, request: 'Explique como organizar o trabalho em equipe.', slides: 5, source: {mode: 'none'}});
test('5 slides válidos: 1 roteiro + 5 conteúdos, ZIP editável e métricas reais do mock', async () => {
  const model = new Mock(), progress = [];
  const result = await generate({...base(model), onProgress: p => progress.push(p.stage)});
  assert.equal(result.ir.slides.length, 5);
  assert.equal(result.diagnostics.filter(d => d.severity === 'ERRO').length, 0);
  assert.equal(result.calls.length, 6);
  assert.equal(result.source.warning, 'conteúdo sem fontes');
  assert.ok(result.ir.slides.every(s => s.notes.includes('conteúdo sem fontes')));
  assert.ok(progress.includes('Gerando PowerPoint editável'));
  const zip = await JSZip.loadAsync(result.pptx);
  const slides = Object.keys(zip.files).filter(n => /^ppt\/slides\/slide\d+.xml$/.test(n));
  assert.equal(slides.length, 5);
  assert.match(await zip.file(slides[0]).async('string'), /<p:sp>/);
  assert.match(await zip.file(slides[1]).async('string'), /<a:t>/);
  await fs.mkdir('outputs/evidence', {recursive: true});
  await fs.writeFile('outputs/evidence/mock-5-slides.pptx', new Uint8Array(result.pptx));
  await fs.writeFile('outputs/evidence/mock-custo.json', JSON.stringify(testData({calls: result.calls, device_start: null, device_end: null, model: {simulated: true}, status: 'success', wall_ms: result.wall_ms, slides: 5, diagnostics: result.diagnostics, source_mode: 'none'}), null, 2));
});
test('um slide inválido aciona exatamente 1 reparo com diagnóstico e resposta anterior', async () => {
  const model = new Mock({badFirst: [3]});
  const result = await generate(base(model));
  assert.equal(result.calls.length, 7);
  assert.equal(result.calls.filter(c => c.repair).length, 1);
  assert.equal(model.counts[3], 2);
  assert.match(model.inputs.find(x => x.user.includes('Corrija os diagnósticos')).user, /A005/);
});
test('todos os slides precisam reparar: teto de 11 chamadas, sem melhor de N', async () => {
  const model = new Mock({badFirst: [1, 2, 3, 4, 5]});
  const result = await generate(base(model));
  assert.equal(result.calls.length, 11);
  assert.equal(result.max_calls, 11);
  assert.equal(result.calls.filter(c => c.repair).length, 5);
});
test('texto longo demais após o reparo: compilador encurta (F002) e mantém o conteúdo da IA', async () => {
  const model = new Mock({longTitle: [2]});
  const result = await generate(base(model));
  assert.equal(model.counts[2], 2);
  assert.deepEqual(result.diagnostics.filter(d => d.code === 'F001'), []);
  assert.equal(result.diagnostics.filter(d => d.code === 'F002').length, 1);
  const s = result.deck.slides[1];
  assert.equal(s.title, 'A equipe confere cada entrega com cuidado antes de apresentar o resultado final');
  assert.equal(s.items.length, 3);
  assert.equal(result.diagnostics.filter(d => d.severity === 'ERRO').length, 0);
});
test('falha sem ser de tamanho, com 2 fatos planejados: tópicos montados das afirmações (não divisória vazia)', async () => {
  const f2 = {...fact, afirmacao: 'Cada entrega recebe uma revisão antes da apresentação.', trecho: 'Cada entrega recebe uma revisão antes da apresentação.'};
  const model = new Mock({garbage: [3], extract: [fact, f2], overrideOutline: o => o.slides.forEach(s => { if (s.fatos) s.fatos = ['F1', 'F2']; })});
  const result = await generate({...base(model), source: {mode: 'paste', text: `${fact.trecho} ${f2.trecho}`}});
  const s = result.deck.slides[2];
  assert.equal(s.kind, 'topicos'); assert.deepEqual(s.sources, ['F1', 'F2']);
  assert.deepEqual(s.items.map(it => [it.label, it.detail]), [['A equipe confere as tarefas', 'Antes de iniciar o trabalho'],
    ['Cada entrega recebe', 'Uma revisão antes da apresentação']]);
  assert.equal(result.diagnostics.filter(d => d.code === 'F001').length, 1);
  assert.equal(result.diagnostics.filter(d => d.severity === 'ERRO').length, 0);
});
test('factItem: rótulo até 48 na palavra inteira, resto no detalhe', async () => {
  const {factItem} = await import('../outputs/tests/pipeline/generate.js');
  assert.deepEqual(factItem('A água evapora.'), {rotulo: 'A água evapora'});
  const it = factItem('A evaporação ocorre nos oceanos, que cobrem cerca de 70% da superfície terrestre.');
  assert.equal(it.rotulo, 'A evaporação ocorre nos oceanos');
  assert.equal(it.detalhe, 'Que cobrem cerca de 70% da superfície terrestre');
});
test('roteiro vê todos os fatos, não só os 3 primeiros (teste do TCC, 25/11/2026)', async () => {
  const frases = ['A equipe confere as tarefas antes de iniciar o trabalho.', 'Cada entrega recebe uma revisão antes da apresentação.',
    'O grupo consulta o registro quando precisa retomar uma decisão.', 'O quadro mostra as tarefas atrasadas da semana.'];
  const extract = frases.map(t => ({...fact, afirmacao: t, trecho: t}));
  const model = new Mock({extract});
  const result = await generate({...base(model), source: {mode: 'paste', text: frases.join(' ')}});
  const roteiro = model.inputs.find(x => x.schema.properties.slides).user;
  const accepted = Object.entries(result.facts);
  assert.ok(accepted.length >= 3, `fatos aceitos: ${accepted.length}`);  // o texto colado aceita até 3; os 32 estão no teste de outlineFacts
  for (const [id, f] of accepted) assert.ok(roteiro.includes(`${id} (`) && roteiro.includes(f.claim), id);
  const {outlineFacts} = await import('../outputs/tests/pipeline/generate.js');
  const many = Object.fromEntries(Array.from({length: 40}, (_, k) => [`F${k + 1}`, {claim: `Fato número ${k + 1} do documento.`, kind: 'dado', value: String(k)}]));
  const block = outlineFacts(many);
  assert.match(block, /^F1 \(dado\) \[valor: 0\]: Fato número 1/);
  assert.match(block, /F32 /); assert.doesNotMatch(block, /F33 /);  // até 32, como o PC
  assert.ok(outlineFacts(many, 200).length <= 200);
});
test('texto que bateu no limite da gramática perde só a palavra cortada', async () => {
  const {trimTruncated} = await import('../outputs/tests/pipeline/generate.js');
  const schema = {type: 'object', properties: {t: {type: 'string', maxLength: 36}, curto: {type: 'string', maxLength: 36},
    itens: {type: 'array', items: {type: 'object', properties: {rotulo: {type: 'string', maxLength: 20}}}}}};
  const out = trimTruncated({t: 'Desenvolver uma versão compacta do modelo SlideDSL'.slice(0, 36), curto: 'Texto curto',
    itens: [{rotulo: 'Integrar um compilador'.slice(0, 20)}]}, schema);
  assert.deepEqual(out, {t: 'Desenvolver uma versão compacta', curto: 'Texto curto', itens: [{rotulo: 'Integrar um'}]});
});
test('gramática do slide só aceita caracteres que o compilador mede (sem CJK)', async () => {
  const {slideGrammar} = await import('../outputs/tests/pipeline/altoText.js');
  const g = slideGrammar('topicos', prompts.slide_schemas.topicos.with_facts);
  const chr = g.split('\n').find(l => l.startsWith('chr ::='));
  assert.match(chr, /\\u024F/); assert.match(chr, /\\u22FF/); assert.doesNotMatch(chr, /\[\^/);
});
test('segundo erro do slide (não é tamanho): sem terceira tentativa; compilador monta o slide e o deck segue', async () => {
  const model = new Mock({garbage: [2]});
  const result = await generate(base(model));
  assert.equal(model.counts[2], 2);
  const fb = result.diagnostics.filter(d => d.code === 'F001');
  assert.equal(fb.length, 1); assert.equal(fb[0].slide, 2);
  assert.equal(result.deck.slides.length, 5);
  assert.match(result.deck.slides[1].notes, /montado pelo compilador/);
  assert.ok(result.pptx.byteLength > 1000);
});
test('roteiro com quantidade incorreta é rejeitado antes de gerar conteúdo', async () => {
  const model = new Mock({overrideOutline: o => o.slides.pop()});
  await assert.rejects(generate(base(model)), /Roteiro inválido/);
  assert.equal(model.inputs.length, 1);
});
test('roteiro sem capa é corrigido (fix_outline do Python) em vez de abortar', async () => {
  const model = new Mock({overrideOutline: o => o.slides[0].tipo = 'topicos'});
  const result = await generate(base(model));
  assert.equal(result.deck.slides[0].kind, 'capa');
  assert.equal(result.ir.slides.length, 5);
});
test('sem fontes esconde dados e imagens; IDs inexistentes são rejeitados pelo schema', () => {
  const s = prompts.outline_schemas['5'].without_facts;
  assert.ok(!s.properties.slides.items.properties.tipo.enum.includes('numeros'));
  assert.ok(!s.properties.slides.items.properties.tipo.enum.includes('imagem'));
  const schema = schemaWithFacts(prompts.slide_schemas.topicos.with_facts, ['F1']);
  assert.ok(schemaErrors({...content('topicos'), fontes: ['F999']}, schema).length);
  assert.equal(schemaErrors({...content('topicos'), fontes: ['F1']}, schema).length, 0);
});
test('cancelamento antes de começar não chama modelo', async () => {
  const controller = new AbortController(); controller.abort(); const model = new Mock();
  await assert.rejects(generate({...base(model), signal: controller.signal}), /cancelada/);
  assert.equal(model.inputs.length, 0);
});
test('cancelamento durante inferência registra chamada e impede continuação', async () => {
  const controller = new AbortController(); let calls = [];
  const model = new Mock({onComplete: () => controller.abort()});
  await assert.rejects(generate({...base(model), signal: controller.signal, onCalls: c => calls = c}), /cancelada/);
  assert.equal(model.inputs.length, 1); assert.equal(calls[0].status, 'cancelled');
  assert.equal(calls[0].input_tokens, 100);
});
test('falha de transporte registra métricas desconhecidas sem inventar zeros', async () => {
  const recorder = new Recorder({complete: async () => {throw Error('transporte');}}, 1);
  await assert.rejects(recorder.json('roteiro', '', '', {}), /transporte/);
  assert.equal(recorder.calls[0].status, 'failed'); assert.equal(recorder.calls[0].input_tokens, null);
  await assert.rejects(recorder.json('roteiro', '', '', {}), /Limite/);
});
test('JSON truncado preserva tokens e timings no registro da falha', async () => {
  const recorder = new Recorder({complete: async () => ({text: '{', usage})}, 1);
  await assert.rejects(recorder.json('slide', '', '', {}));
  assert.equal(recorder.calls[0].output_tokens, 50); assert.equal(recorder.calls[0].status, 'failed');
});
test('slidedsl.custo.v1: totais, reparo e contagem dos desconhecidos', () => {
  const row = {call: 1, stage: 'slide', slide: 1, attempt: 0, repair: false, status: 'success', wall_ms: 40, ...usage};
  const report = costBreakdown([row, {...row, attempt: 1, repair: true, input_tokens: null, status: 'failed'}]);
  assert.equal(report.schema, 'slidedsl.custo.v1'); assert.equal(report.total.input_tokens, 100);
  assert.equal(report.total.input_tokens_unknown_calls, 1); assert.equal(report.by_stage.reparo.calls, 1);
  assert.equal(report.total.failed_calls, 1); assert.equal(report.total.load_ms, null);
});
test('texto colado extrai e confere literalmente; inclui fonte nas notas do deck', async () => {
  const result = await generate({...base(new Mock()), source: {mode: 'paste', text: fact.trecho}});
  assert.equal(result.calls[0].stage, 'document_extract'); assert.equal(result.calls.length, 7);
  assert.equal(result.facts.F1.quote, fact.trecho); assert.equal(result.source.warning, null);
  assert.match(result.ir.slides[1].notes, /Texto colado/);
});
test('trechos inventados, números novos, título de seção e relevância baixa são rejeitados', () => {
  assert.match(verifyFact({...fact, trecho: 'Uma frase completamente inventada.'}, fact.trecho), /literalmente/);
  assert.match(verifyFact({...fact, afirmacao: 'A equipe confere 92 tarefas antes de iniciar o trabalho.'}, fact.trecho), /número/);
  assert.match(verifyFact({...fact, valor: '40%'}, fact.trecho), /valor/);
  assert.match(verifyFact({...fact, relevancia: 'baixa'}, fact.trecho), /relevante/);
  assert.match(verifyFact({...fact, trecho: '# Uma seção importante'}, '# Uma seção importante'), /título/);
});
test('normalização aceita acentos/aspas e citação sem autor vira definição', () => {
  const item = {...fact, tipo: 'citacao', autor: 'Pessoa ausente'};
  assert.equal(verifyFact(item, fact.trecho), null); assert.equal(item.tipo, 'definicao');
  assert.equal(verifyFact(fact, fact.trecho.toUpperCase()), null);
});
test('extração vazia ou sem âncora falha explicitamente; não inventa fonte', async () => {
  const recorder = new Recorder(new Mock({extract: [{...fact, trecho: 'Não existe esta passagem no documento.'}]}), 1);
  await assert.rejects(collectFacts({mode: 'paste', text: fact.trecho}, 'Pedido', recorder), /Nenhum fato/);
});
test('Wikipedia pt/en usa HTTPS REST, título codificado e texto recebido', async () => {
  for (const language of ['pt', 'en']) {
    let url;
    const source = await wikipedia('Energia solar', language, async u => {url = u; return {title: 'Energia solar', extract: fact.trecho};});
    assert.equal(source.text, fact.trecho); assert.ok(url.startsWith(`https://${language}.wikipedia.org/`));
    assert.ok(url.endsWith('Energia_solar'));
  }
});
test('Wikipedia rejeita desambiguação, vazio e idioma indevido', async () => {
  await assert.rejects(wikipedia('Solar', 'pt', async () => ({type: 'disambiguation', extract: 'x'})), /ambígua/);
  await assert.rejects(wikipedia('Solar', 'pt', async () => ({})), /sem resumo/);
  await assert.rejects(wikipedia('Solar', 'xx', async () => ({})), /pt\/en/);
});
test('Wikipedia passa o AbortSignal; falha de rede não chama modelo', async () => {
  const signal = new AbortController().signal; const recorder = new Recorder(new Mock(), 1);
  await assert.rejects(collectFacts({mode: 'wikipedia', title: 'Solar', language: 'pt'}, 'pedido', recorder,
    async (url, s) => {assert.equal(s, signal); throw Error('offline');}, signal), /offline/);
  assert.equal(recorder.calls.length, 0);
});
test('dados inválidos de entrada falham antes do modelo', async () => {
  for (const slides of [3, 9, 4.5]) await assert.rejects(generate({...base(new Mock()), slides}), /4 a 8/);
  await assert.rejects(generate({...base(new Mock()), request: ''}), /pedido/);
});
test('4 e 8 slides são suportados com teto proporcional', async () => {
  for (const n of [4, 8]) {
    const result = await generate({...base(new Mock()), slides: n});
    assert.equal(result.ir.slides.length, n); assert.equal(result.max_calls, 1 + 2 * n);
  }
});
test('conversão JSON mantém dados, cronologia, comparação e fontes', () => {
  const slide = jsonToSlide('linha_do_tempo', {titulo: ' Histórico ', marcos: [{data: '2020', rotulo: 'Marco', detalhe: ''}], fontes: ['F1', 'F1']});
  assert.equal(slide.title, 'Histórico'); assert.equal(slide.milestones[0].date, '2020'); assert.deepEqual(slide.sources, ['F1']);
  const comparison = jsonToSlide('comparacao', {titulo: 'Comparar', lados: [{nome: 'Opção', itens: [item('Escopo', 'A equipe confere o escopo antes de iniciar.')]}]});
  assert.equal(comparison.sides[0].items[0].label, 'Escopo');
});
test('modelo 4B bloqueado abaixo de 12 GiB; recomendação conservadora sem RAM', () => {
  assert.equal(modelAllowed(models[2], 11 * 1024 ** 3), false);
  assert.equal(modelAllowed(models[2], null), false); assert.equal(modelAllowed(models[2], 12 * 1024 ** 3), true);
  assert.equal(suggestedModel(null).id, models[0].id); assert.equal(suggestedModel(8 * 1024 ** 3).id, models[1].id);
  for (const model of models) {assert.match(model.sha256, /^[a-f0-9]{64}$/); assert.ok(model.bytes > 0); if (model.url) assert.match(model.url, /^https:\/\/huggingface.co\//);}
  assert.equal(models.filter(m => !m.url).map(m => m.id).join(), 'qwen3-0.6b-slidedsl');
});
test('pipeline não importa código nativo; todos os schemas vêm do exportador', async () => {
  for (const file of await fs.readdir('src/pipeline')) if (file.endsWith('.ts')) {
    const source = await fs.readFile(`src/pipeline/${file}`, 'utf8');
    assert.doesNotMatch(source, /from ['"](?:react-native|llama\.rn|expo-)/);
  }
  assert.equal(Object.keys(prompts.outline_schemas).length, 5);
  assert.equal(Object.keys(prompts.slide_schemas).length, 12);  // 10 tipos + ciclo + imagem (Fotos da internet)
  assert.equal(Object.keys(prompts.outline_schemas_imagens).length, 5);
});
test('título do fallback não termina em preposição ou artigo', async () => {
  const {shortTitle} = await import('../outputs/tests/pipeline/generate.js');
  assert.equal(shortTitle('A energia solar residencial é uma alternativa para a economia local', 46), 'A energia solar residencial é uma alternativa');
  assert.equal(shortTitle('Energia solar', 60), 'Energia solar');
});
test('fatos diferentes por slide e itens já escritos no pedido (teste da água no celular, 25/11/2026)', async () => {
  const {distributeFacts, writtenItems} = await import('../outputs/tests/pipeline/generate.js');
  const outline = {titulo: 'Ciclo', slides: [
    {tipo: 'capa', mensagem: 'm', objetivo: 'o', fatos: ['F1']},
    {tipo: 'topicos', mensagem: 'm', objetivo: 'o', fatos: ['F1', 'F2']},
    {tipo: 'etapas', mensagem: 'm', objetivo: 'o', fatos: ['F1', 'F2']},
    {tipo: 'comparacao', mensagem: 'm', objetivo: 'o', fatos: ['F2']},
    {tipo: 'conclusao', mensagem: 'm', objetivo: 'o', fatos: ['F1', 'F2']}]};
  const out = distributeFacts(outline, ['F1', 'F2', 'F3', 'F4', 'F5', 'F6']);
  assert.deepEqual(out.slides.map(s => s.fatos), [['F1'], ['F1', 'F2'], ['F3', 'F4'], ['F5', 'F6'], ['F1', 'F2']]);
  assert.deepEqual(outline.slides[2].fatos, ['F1', 'F2']);  // não altera o roteiro original
  // Sem fatos novos, mantém os planejados.
  assert.deepEqual(distributeFacts(outline, ['F1', 'F2']).slides[3].fatos, ['F2']);
  const w = writtenItems([{items: [{label: 'Evaporação'}, {label: 'Condensação'}]}, {sides: [{name: 'x', items: [{label: 'Gelo'}]}]}]);
  assert.equal(w, 'Evaporação; Condensação; Gelo');
  const model = new Mock();
  await generate(base(model));
  const slide3 = model.inputs.find(x => /Escreva o slide 3 /.test(x.user)).user;
  assert.match(slide3, /Itens já escritos em outros slides \(não repita estas ideias; use os fatos deste slide\): Escopo definido; Revisão frequente/);
});
test('item com o mesmo texto de outro: pede reparo e, se continuar, o compilador tira a cópia', async () => {
  class Dup extends Mock {
    async complete(input) {
      const r = await super.complete(input);
      if (/Escreva o slide 2 /.test(input.user)) {
        const d = JSON.parse(r.text);
        d.itens = [item('Evaporação', 'A água passa do estado líquido para o gasoso.'), item('Condensação', 'O vapor volta ao estado líquido nas nuvens.'),
          item('Precipitação', 'O vapor volta ao estado líquido nas nuvens.')];
        return {...r, text: JSON.stringify(d)};
      }
      return r;
    }
  }
  const model = new Dup();
  const result = await generate(base(model));
  assert.equal(model.counts[2], 2);  // houve reparo
  assert.match(model.inputs.find(x => x.user.includes('Corrija os diagnósticos')).user, /P004/);
  assert.deepEqual(result.deck.slides[1].items.map(i => i.label), ['Evaporação', 'Condensação']);
});
