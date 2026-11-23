import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import ts from 'typescript';
import {createRequire} from 'node:module';
import * as documents from '../outputs/tests/pipeline/documents.js';
import {checkCancelled} from '../outputs/tests/pipeline/types.js';
const require = createRequire(import.meta.url);
async function adapter(options = {}) {
  const seen = {}, handlers = {};
  const native = {
    importDocument: async (...args) => {seen.imported = args; return options.file;},
    takePendingDocument: async () => options.file ?? null,
    deleteDocument: async uri => {seen.deleted = uri;},
    extractPdf: async uri => {seen.pdf = uri; return {pages: 1, parts: [{page: 1, text: options.pdfText ?? 'A equipe confere cada entrega antes da apresentação.'}]};},
    addListener: (event, listener) => {handlers[event] = listener; return {remove: () => delete handlers[event]};},
  };
  const imports = {'expo-modules-core': {NativeModule: class {}, requireNativeModule: name => {assert.equal(name, 'SlideDocuments'); return native;}},
    'expo-document-picker': {getDocumentAsync: async input => {seen.picker = input; return options.picked ?? {canceled: true};}},
    'expo-file-system': {File: class {async bytes() {return new TextEncoder().encode('A revisão das atividades ocorre antes da entrega.');}}},
    '../pipeline/documents': documents, '../pipeline/types': {checkCancelled}};
  const source = await fs.readFile('src/storage/documents.ts', 'utf8');
  const {outputText} = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}});
  const module = {exports: {}};
  new Function('require', 'module', 'exports', outputText)(name => {assert.ok(name in imports, name); return imports[name];}, module, module.exports);
  return {mod: module.exports, seen, handlers};
}
test('picker real com fronteira simulada: MIME, cancelamento, tamanho e cópia nativa limitada', async () => {
  const cancelled = await adapter(); assert.equal(await cancelled.mod.pickDocument(), null);
  const file = {name: 'x.pdf', mime: 'application/pdf', bytes: 40, uri: 'file:///private/x'};
  const asset = {name: file.name, mimeType: file.mime, size: 40, uri: 'content://drive/x'};
  const a = await adapter({file, picked: {canceled: false, assets: [asset]}});
  assert.deepEqual(await a.mod.pickDocument(), file); assert.equal(a.seen.picker.copyToCacheDirectory, false);
  assert.deepEqual(a.seen.imported, [asset.uri, asset.name, asset.mimeType]);
  const b = await adapter({picked: {canceled: false, assets: [{...asset, size: documents.MAX_DOCUMENT_BYTES + 1}]}});
  await assert.rejects(b.mod.pickDocument(), /10 MB/); assert.equal(b.seen.imported, undefined);
});
test('adaptador real: PDF nativo, texto puro, cancelamento, evento e limpeza de arquivo privado', async () => {
  const a = await adapter(), pdf = {name: 'x.pdf', mime: 'application/pdf', bytes: 40, uri: 'file:///private/x'};
  const doc = await a.mod.readDocument(pdf); assert.equal(doc.pages, 1); assert.equal(doc.chunks[0].page, 1);
  const text = await a.mod.readDocument({...pdf, name: 'x.txt', mime: 'text/plain'}); assert.equal(text.encoding, 'UTF-8');
  const controller = new AbortController(); controller.abort(); await assert.rejects(a.mod.readDocument(pdf, controller.signal), /cancelada/);
  let events = 0; const subscription = a.mod.onIncomingDocument(() => events++); a.handlers.onDocument(); subscription.remove(); assert.equal(events, 1);
  assert.equal(await a.mod.pendingDocument(), null); await a.mod.deleteDocument(pdf); assert.equal(a.seen.deleted, pdf.uri);
  const empty = await adapter({pdfText: ''}); await assert.rejects(empty.mod.readDocument(pdf), /PDF sem texto selecionável/);
});
test('plugin real: filtros SEND/VIEW idempotentes, launcher preservado, PDF/DOCX/TXT/MD e singleTask', () => {
  const plugin = require('../plugins/withDocuments.js');
  const manifest = {manifest: {application: [{activity: [{$: {'android:name': '.MainActivity'}, 'intent-filter': [{action: [{$: {'android:name': 'android.intent.action.MAIN'}}]}]}]}]}};
  // O withAndroidManifest instala um mod executável sobre o manifesto de teste.
  const config = plugin({name: 'SlideDSL', slug: 'slidedsl'}), mod = config.mods.android.manifest;
  return (async () => {
    let input = {modResults: manifest, modRequest: {platform: 'android', modName: 'manifest', introspect: true}, name: 'SlideDSL', slug: 'slidedsl'};
    input = await mod(input); input = await mod(input);
    const main = input.modResults.manifest.application[0].activity[0];
    assert.equal(main.$['android:launchMode'], 'singleTask'); assert.equal(main['intent-filter'].length, 3);
    const send = main['intent-filter'].find(f => f.action[0].$['android:name'].endsWith('.SEND'));
    assert.deepEqual(send.data.map(d => d.$['android:mimeType']), documents.DOCUMENT_MIMES);
    assert.ok(main['intent-filter'].some(f => f.action[0].$['android:name'].endsWith('.VIEW')));
  })();
});
