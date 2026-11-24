// Diagramas no slide (compilador): a IA escolhe "ciclo" e o slide sai com caixas em círculo e setas; etapas com →.
import test from 'node:test';
import assert from 'node:assert/strict';
import {generate} from '../outputs/tests/pipeline/generate.js';

const usage = {input_tokens: 1, output_tokens: 1, prefill_ms: 1, decode_ms: 1};
const phases = ['Evaporação', 'Condensação', 'Precipitação', 'Escoamento'];
const model = {async complete(input) {
  if (input.schema.properties.slides) {
    const n = input.schema.properties.slides.minItems, kinds = ['capa', 'ciclo', 'etapas', 'conclusao'];
    return {text: JSON.stringify({titulo: 'O ciclo da água', slides: Array.from({length: n}, (_, i) => ({
      tipo: kinds[i] ?? 'topicos', mensagem: `Mensagem do slide ${i + 1}`, objetivo: 'Objetivo do slide'}))}), usage};
  }
  const kind = input.user.match(/\(tipo (\w+)\)/)[1];
  const itens = (n, w) => Array.from({length: n}, (_, k) => ({rotulo: `${w} ${k + 1}`.slice(0, 20), detalhe: `A fase ${k + 1} acontece com a água em movimento.`}));
  const data = kind === 'capa' ? {titulo: 'O ciclo da água', subtitulo: 'Como a água circula.', autor: '', notas: ''}
    : kind === 'ciclo' ? {titulo: 'A água circula sem parar', itens: phases.map((p, k) => ({rotulo: p, detalhe: `A fase ${k + 1} move a água.`})), fontes: [], notas: ''}
    : kind === 'etapas' ? {titulo: 'Tratamento em três etapas', itens: itens(3, 'Etapa'), fontes: [], notas: ''}
    : {titulo: 'Economize água em casa', itens: itens(2, 'Ação'), fontes: [], notas: ''};
  return {text: JSON.stringify(data), usage};
}};

test('ciclo escolhido pela IA vira etapas com cycle e é desenhado em círculo; etapas com setas →', async () => {
  const r = await generate({model, request: 'Explique o ciclo da água.', slides: 4, source: {mode: 'none'}});
  assert.equal(r.deck.slides[1].kind, 'etapas');
  assert.equal(r.deck.slides[1].cycle, true);
  const els = r.ir.slides[1].elements, of = k => els.filter(e => e.id.includes(`_${k}_`));
  assert.equal(of('etapa').length, 4);
  assert.equal(of('seta').length, 4);
  const flow = r.ir.slides[2].elements.filter(e => e.id.includes('_seta_')).map(e => e.text);
  assert.deepEqual(flow, ['→', '→']);
});
