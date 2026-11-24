// Paridade com o PC: as saídas esperadas vêm do Python (scripts/export_editorial_cases.py).
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {stripFactIds, sentenceCase, capitalizeFirst, properWords, cleanVisible} from '../outputs/tests/pipeline/editorial.js';
import {fallbackQueries} from '../outputs/tests/pipeline/images.js';

const cases = JSON.parse(await fs.readFile(new URL('./fixtures/editorial_cases.json', import.meta.url), 'utf8'));

test('limpeza de texto igual à do PC', () => {
  for (const [input, expected] of cases.strip) assert.equal(stripFactIds(input, cases.ids), expected, input);
  assert.deepEqual([...properWords(cases.request)].sort(), cases.keep);
  for (const [input, expected] of cases.case) assert.equal(sentenceCase(input, cases.keep), expected, input);
  for (const [input, expected] of cases.capitalize) assert.equal(capitalizeFirst(input), expected, input);
  for (const [input, expected] of cases.fallback_queries) assert.deepEqual(fallbackQueries(input), expected, input);
});

test('cleanVisible tira IDs de fatos de todos os campos visíveis', () => {
  const slide = {kind: 'topicos', title: 'Como Funciona O Ciclo Da Água', items: [{label: 'transpiração', detail: 'As plantas liberam água, como em F1.'}],
    sides: [], values: [{value: '70%', label: 'uso agrícola conforme F2'}], milestones: []};
  cleanVisible(slide, ['F1', 'F2'], 'ciclo da água');
  assert.equal(slide.title, 'Como funciona o ciclo da água');
  assert.deepEqual(slide.items[0], {label: 'Transpiração', detail: 'As plantas liberam água.'});
  assert.equal(slide.values[0].label, 'uso agrícola');
});
