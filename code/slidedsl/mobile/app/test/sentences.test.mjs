import test from 'node:test';
import assert from 'node:assert/strict';
import {splitSentences, numberedSentences, factGrammar, parseFactLines, factValue} from '../outputs/tests/pipeline/sentences.js';
import {collectFacts} from '../outputs/tests/pipeline/sources.js';
import {Recorder} from '../outputs/tests/pipeline/usage.js';
import {generate} from '../outputs/tests/pipeline/generate.js';

const usage = {input_tokens: 100, output_tokens: 20, prefill_ms: 10, decode_ms: 10};
const text = 'Fonte 1: Ciclo da Água - Toda Matéria\nhttps://www.exemplo.com/ciclo\n' +
  'A agricultura usa muita água doce. Ela representa 70% do consumo mundial, segundo a FAO.\n' +
  '- Indústrias usam cerca de 19% da água.\n# Título\nOk.';
const line = (n, claim, tipo = 'numero', rel = 'alta', autor = '') =>
  `fato ${n} afirmacao "${claim}" tipo ${tipo}${autor ? ` autor "${autor}"` : ''} relevancia ${rel}`;

test('frases: quebra em fim de frase e em linhas; ignora títulos, URLs, marcadores e frases curtas', () => {
  assert.deepEqual(splitSentences(text), ['A agricultura usa muita água doce.',
    'Ela representa 70% do consumo mundial, segundo a FAO.', 'Indústrias usam cerca de 19% da água.']);
  assert.deepEqual(splitSentences('O valor de 3.5 mil subiu. Depois caiu bastante.'), ['O valor de 3.5 mil subiu.', 'Depois caiu bastante.']);
  assert.match(numberedSentences(['Uma frase.', 'Outra frase.']), /^\[1\] Uma frase\.\n\[2\] Outra frase\.$/);
});

test('gramática: números de frase crescentes e existentes, tipos/relevâncias válidos, sem valor, até 6 linhas', () => {
  const g = factGrammar(3);
  assert.match(g, /^root ::= s0-6$/m);
  // Números crescentes: depois da frase 1 só vêm 2 ou 3; depois da 3, nada.
  assert.match(g, /^s0-6 ::= \("fato 1" corpo s1-5 \| "fato 2" corpo s2-5 \| "fato 3" corpo s3-5\)\?$/m);
  assert.match(g, /^s1-5 ::= \("fato 2" corpo s2-4 \| "fato 3" corpo s3-4\)\?$/m);
  assert.match(g, /^s3-5 ::= ""$/m);
  assert.match(factGrammar(9, 2), /^s5-0 ::= ""$/m);
  assert.match(g, /tipo ::= "numero" \|/);
  assert.match(g, /afirm ::= "\\"" chr\{30,240\} "\\""/);
  assert.match(g, /" tipo " tipo \(" autor " autor\)\? " relevancia " rel "\\n"/);
  assert.doesNotMatch(g, /valor/);
});

test('parse: trecho = frase original; valor calculado; linhas inválidas e repetidas são ignoradas', () => {
  const s = splitSentences(text);
  const out = parseFactLines([
    line(2, 'A agricultura representa 70% do consumo mundial de água.'),
    line(2, 'Repetida, mesma frase escolhida de novo.'),
    line(9, 'Frase que não existe no trecho numerado.'),
    line(3, 'Tipo inválido no fato escolhido aqui.', 'inventado'),
    line(1, 'Texto com \\"aspas\\" escapadas aqui.', 'citacao', 'media', 'FAO'),
    'fato 2 numero alta "formato antigo posicional" "70%" ""',
  ].join('\n'), s);
  assert.equal(out.length, 2);
  assert.equal(out[0].trecho, s[1]); assert.equal(out[0].valor, '70%'); assert.equal(out[0].tipo, 'numero');
  assert.equal(out[1].afirmacao, 'Texto com "aspas" escapadas aqui.'); assert.equal(out[1].trecho, s[0]);
  assert.equal(out[1].autor, 'FAO'); assert.equal(out[1].valor, '');
  assert.equal(factValue('Usa 45% e depois 70% da água', 'Ela representa 70% do consumo.'), '70%');
});

class FrasesMock {
  constructor(lines) { this.lines = lines; this.inputs = []; }
  async complete(input) {
    this.inputs.push(input);
    if (input.schema.properties.fatos) {
      assert.ok(input.grammar, 'extração por frases sem gramática');
      assert.match(input.user, /FRASES:\n\[1\] /);
      assert.doesNotMatch(input.user, /TRECHO:/);
      return {text: this.lines, usage};
    }
    throw Error('não usado');
  }
}

test('collectFacts em modo frases: citação literal passa no verifyFact; número fora do texto é rejeitado', async () => {
  const model = new FrasesMock(line(2, 'A agricultura representa 70% do consumo mundial de água.') + '\n' +
    line(3, 'As indústrias usam 45% da água disponível no mundo.') + '\n');
  const res = await collectFacts({mode: 'paste', text}, 'Uso da água', new Recorder(model, 2), undefined, undefined,
    undefined, undefined, undefined, 'frases');
  assert.equal(Object.keys(res.facts).length, 1);
  assert.equal(res.facts.F1.quote, 'Ela representa 70% do consumo mundial, segundo a FAO.');
  assert.equal(res.facts.F1.value, '70%');
  assert.match(res.rejected[0].reason, /número/);
});

test('generate: extractMode padrão continua json (sem gramática na extração)', async () => {
  const inputs = [];
  const model = {async complete(input) { inputs.push(input); throw Error('parar'); }};
  await assert.rejects(generate({model, request: 'Uso da água', slides: 5, source: {mode: 'paste', text}}));
  assert.equal(inputs[0].grammar, undefined); assert.match(inputs[0].user, /TRECHO:/);
});
