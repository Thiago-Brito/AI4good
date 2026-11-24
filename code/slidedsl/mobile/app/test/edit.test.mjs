// Edição slide a slide (src/pipeline/edit.ts): mover, excluir, editar texto, refazer com IA; recusa inválidos.
import test from 'node:test';
import assert from 'node:assert/strict';
import {generate} from '../outputs/tests/pipeline/generate.js';
import {moveSlide, deleteSlide, editTexts, editableFields, redoSlide, EditError} from '../outputs/tests/pipeline/edit.js';

const usage = {input_tokens: 10, output_tokens: 5, prefill_ms: 1, decode_ms: 1};
const item = (rotulo, detalhe) => ({rotulo, detalhe});
const content = (kind, title) => kind === 'capa' ? {titulo: title ?? 'Planejar ajuda a equipe', subtitulo: 'Decisões locais para organizar o trabalho.', autor: '', notas: ''} : {
  titulo: title ?? (kind === 'conclusao' ? 'Escolha a próxima atividade' : 'A equipe confere cada entrega'),
  itens: [item('Escopo definido', 'A equipe confere as tarefas antes de iniciar o trabalho.'),
    item('Revisão frequente', 'Cada entrega recebe uma revisão antes da apresentação.')], fontes: [], notas: 'Notas.'};
function mock(titles = {}) {
  const inputs = [];
  return {inputs, async complete(input) {
    inputs.push(input);
    if (input.schema.properties.slides) {
      const n = input.schema.properties.slides.minItems;
      return {text: JSON.stringify({titulo: 'Trabalho organizado', slides: Array.from({length: n}, (_, i) => ({
        tipo: i === 0 ? 'capa' : i === n - 1 ? 'conclusao' : 'topicos', mensagem: `Mensagem ${i + 1}`, objetivo: 'Objetivo'}))}), usage};
    }
    const i = Number(input.user.match(/Escreva o slide (\d+)/)[1]), kind = input.user.match(/\(tipo (\w+)\)/)[1];
    return {text: JSON.stringify(content(kind, titles[i])), usage};
  }};
}
const made = () => generate({model: mock(), request: 'Explique como organizar o trabalho em equipe.', slides: 5, source: {mode: 'none'}});

test('mover e excluir recompilam e mantêm o roteiro alinhado', async () => {
  const r = await made();
  const moved = await moveSlide(r, 1, 3);
  assert.equal(moved.deck.slides[3], r.deck.slides[1]);
  assert.equal(moved.outline.slides[3].mensagem, 'Mensagem 2');
  assert.equal(moved.ir.slides.length, 5);
  assert.notEqual(moved.pptx, r.pptx);
  const fewer = await deleteSlide(moved, 2);
  assert.equal(fewer.deck.slides.length, 4);
  assert.equal(fewer.outline.slides.length, 4);
  assert.equal(r.deck.slides.length, 5, 'o original fica intacto para desfazer');
});

test('editar texto aplica no slide e recusa texto que o compilador não aceita', async () => {
  const r = await made();
  const fields = editableFields(r.deck.slides[1]);
  assert.ok(fields.some(f => f.path === 'items.0.detail'));
  const edited = await editTexts(r, 1, {title: 'Revisões evitam retrabalho', 'items.0.label': 'Escopo claro'});
  assert.equal(edited.deck.slides[1].title, 'Revisões evitam retrabalho');
  assert.equal(edited.deck.slides[1].items[0].label, 'Escopo claro');
  await assert.rejects(editTexts(r, 1, {title: 'x'.repeat(300)}), EditError);
});

test('refazer usa o prompt da geração com a instrução e substitui só aquele slide', async () => {
  const r = await made();
  const model = mock({3: 'Reuniões curtas alinham a equipe'});
  const redone = await redoSlide(r, 2, 'fale de reuniões curtas', model);
  assert.ok(model.inputs.length <= 2, "1 chamada + no máximo 1 reparo");
  assert.match(model.inputs[0].user, /Escreva o slide 3 \(tipo topicos\)/);
  assert.match(model.inputs[0].user, /Pedido do usuário para este slide: fale de reuniões curtas/);
  assert.match(model.inputs[0].user, /Escreva uma versão NOVA deste slide/);
  assert.equal(redone.deck.slides[2].title, 'Reuniões curtas alinham a equipe');
  assert.equal(redone.deck.slides[1], r.deck.slides[1]);
  assert.equal(redone.calls.length, r.calls.length + model.inputs.length);
});

test('refazer que continua inválido mantém a versão anterior', async () => {
  const r = await made();
  await assert.rejects(redoSlide(r, 2, '', mock({3: 'x'.repeat(200)})), /versão anterior foi mantida/);
});

test('refazer que devolve o mesmo texto tenta de novo e, se repetir, avisa em vez de dizer que refez', async () => {
  const r = await made();
  const same = mock();  // devolve exatamente o conteúdo original do slide 3
  await assert.rejects(redoSlide(r, 2, 'mude', same), /devolveu o mesmo slide/);
  assert.ok(same.inputs.length >= 2);
  assert.match(same.inputs.at(-1).user, /repetiu a versão atual/);
});

