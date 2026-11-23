// Executa os adaptadores reais com fronteiras nativas simuladas; não é teste JNI.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import ts from 'typescript';
import {checkCancelled} from '../outputs/tests/pipeline/types.js';
async function load(path, imports) {
  const source = await fs.readFile(path, 'utf8');
  const {outputText} = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}});
  const module = {exports: {}};
  new Function('require', 'module', 'exports', outputText)(name => {
    assert.ok(name in imports, `Import nativo inesperado: ${name}`); return imports[name];
  }, module, module.exports);
  return module.exports;
}
async function llama(overrides = {}) {
  const seen = {}, context = {
    getFormattedChat: async (messages, _, params) => {seen.format = params; return {prompt: 'prompt'};},
    tokenize: async () => ({tokens: Array(100).fill(1)}),
    completion: async params => {seen.params = params; return {content: '{"ok":true}', text: 'ignored',
      tokens_evaluated: 100, tokens_predicted: 10, timings: {prompt_ms: 25, predicted_ms: 50}};},
    stopCompletion: async () => {seen.stopped = true;}, release: async () => {seen.released = true;}, ...overrides,
  };
  const mod = await load('src/llm/llamaRn.ts', {'llama.rn': {initLlama: async params => {seen.init = params; return context;}}, '../pipeline/types': {checkCancelled}});
  return {seen, context, mod};
}
test('adaptador llama real: CPU padrão, contexto 4096, JSON Schema nativo e timings', async () => {
  const {mod, seen} = await llama(), model = await mod.loadModel('file:///model.gguf');
  const result = await model.complete({system: 'sistema', user: 'pedido', schema: {type: 'object'}});
  assert.equal(seen.init.n_ctx, 4096); assert.equal(seen.init.n_gpu_layers, 0);
  // Raciocínio desligado na formatação; a completion recebe o prompt pronto e não `messages`,
  // para o llama.rn mandar json_schema ao llama.cpp como gramática estrita (sem bloco <think>).
  assert.equal(seen.format.enable_thinking, false); assert.equal(seen.format.response_format, undefined);
  assert.equal(seen.params.prompt, 'prompt'); assert.equal(seen.params.messages, undefined);
  assert.equal(seen.params.response_format.type, 'json_schema');
  assert.deepEqual(seen.params.response_format.json_schema.schema, {type: 'object'});
  assert.equal(result.usage.prefill_ms, 25); assert.equal(result.usage.decode_ms, 50);
  assert.equal(result.usage.input_tokens, 100); assert.equal(result.text, '{"ok":true}');
  await model.release(); assert.equal(seen.released, true);
});
test('adaptador llama: GPU só mediante opção e limite real de tokens de saída', async () => {
  const {mod, seen} = await llama({tokenize: async () => ({tokens: Array(3200).fill(1)})});
  await (await mod.loadModel('path', true)).complete({system: '', user: '', schema: {}});
  assert.equal(seen.init.n_gpu_layers, 99); assert.equal(seen.params.n_predict, 864);
});
test('adaptador llama: prompt excessivo é recusado antes da inferência', async () => {
  const {mod, seen} = await llama({tokenize: async () => ({tokens: Array(3900).fill(1)})});
  await assert.rejects((await mod.loadModel('path')).complete({system: '', user: '', schema: {}}), /4096 tokens/);
  assert.equal(seen.params, undefined);
});
test('adaptador llama: cancelamento durante completion chama stopCompletion e conserva uso', async () => {
  const controller = new AbortController();
  const {mod, seen} = await llama({completion: async () => {
    controller.abort(); return {content: '', interrupted: true, tokens_evaluated: 4, tokens_predicted: 2, timings: {prompt_ms: 1, predicted_ms: 2}};
  }});
  const result = await (await mod.loadModel('path')).complete({system: '', user: '', schema: {}, signal: controller.signal});
  assert.equal(seen.stopped, true); assert.equal(result.text, ''); assert.equal(result.usage.output_tokens, 2);
});
const spec = {id: 'test-model', bytes: 1000, sha256: 'a'.repeat(64), url: 'https://huggingface.co/test/resolve/main/m.gguf'};
async function storage(options = {}) {
  const files = new Map(), tasks = [], deleted = [], listeners = {};
  const state = {type: 'WIFI', isConnected: true, isInternetReachable: true, ...options.network};
  const path = 'file:///docs/models/test-model.gguf';
  const nativeFS = {
    documentDirectory: 'file:///docs/',
    getInfoAsync: async path => files.has(path) ? {exists: true, size: files.get(path).size ?? 0} : {exists: false},
    makeDirectoryAsync: async () => {}, getFreeDiskStorageAsync: async () => options.free ?? 1e10,
    readAsStringAsync: async p => files.get(p).text,
    writeAsStringAsync: async (p, text) => {files.set(p, {text});},
    deleteAsync: async p => {deleted.push(p); files.delete(p);},
    moveAsync: async ({from, to}) => {files.set(to, files.get(from)); files.delete(from);},
    createDownloadResumable: (url, fileUri, opts, progress, resumeData) => {
      let resolveDownload;
      const task = {resumeData, downloadAsync: async () => {
        files.set(fileUri, {size: options.wait ? 300 : spec.bytes, sha: options.badHash ? 'b' : spec.sha256});
        if (options.wait) return new Promise(resolve => {resolveDownload = resolve;});
        progress({totalBytesWritten: spec.bytes, totalBytesExpectedToWrite: spec.bytes});
        return {status: 200, uri: fileUri};
      }, pauseAsync: async () => {resolveDownload?.(undefined); return {url, fileUri, options: {}, resumeData: 'saved-offset'};}};
      tasks.push(task); return task;
    },
  };
  class File {
    constructor(path) {this.path = path;}
    get exists() {return files.has(this.path);}
    get size() {return files.get(this.path)?.size;}
    async digest(algorithm) {assert.equal(algorithm, 'SHA-256'); return files.get(this.path).sha;}
  }
  const mod = await load('src/storage/models.ts', {'expo-file-system': {File}, 'expo-file-system/legacy': nativeFS,
    'expo-network': {NetworkStateType: {WIFI: 'WIFI'}, getNetworkStateAsync: async () => state,
      addNetworkStateListener: cb => {listeners.network = cb; return {remove() {delete listeners.network;}};}},
    'react-native': {AppState: {addEventListener: (event, cb) => {listeners.app = cb; return {remove() {delete listeners.app;}};}}}});
  return {mod, files, tasks, path, options, listeners, deleted};
}
async function waitForTask(s) {for (let i = 0; i < 20 && !s.tasks.length; i++) await new Promise(r => setTimeout(r, 0)); assert.equal(s.tasks.length, 1);}
test('download padrão recusa rede celular antes de criar arquivo', async () => {
  const s = await storage({network: {type: 'CELLULAR'}});
  await assert.rejects(new s.mod.ModelDownload().start(spec, true, () => {}), /Wi-Fi/);
  assert.equal(s.tasks.length, 0);
});
test('download permitido fora do Wi-Fi confere SHA-256 e promove o arquivo parcial', async () => {
  const s = await storage({network: {type: 'CELLULAR'}}), events = [];
  assert.equal(await new s.mod.ModelDownload().start(spec, false, (n, msg) => events.push(msg)), true);
  assert.equal(await s.mod.isDownloaded(spec), true); assert.ok(s.files.has(s.path));
  assert.ok(!s.files.has(s.path + '.part')); assert.ok(events.includes('Conferindo SHA-256'));
  assert.equal(Object.keys(s.listeners).length, 0);
});
test('checksum incorreto não torna o modelo utilizável', async () => {
  const s = await storage({badHash: true});
  await assert.rejects(new s.mod.ModelDownload().start(spec, true, () => {}), /SHA-256/);
  assert.equal(await s.mod.isDownloaded(spec), false); assert.ok(!s.files.has(s.path));
});
test('espaço insuficiente interrompe antes do download', async () => {
  const s = await storage({free: 10});
  await assert.rejects(new s.mod.ModelDownload().start(spec, true, () => {}), /Espaço/);
  assert.equal(s.tasks.length, 0);
});
test('pausa persiste resumeData; outra instância retoma após reinício', async () => {
  const s = await storage({wait: true}), download = new s.mod.ModelDownload();
  const pending = download.start(spec, true, () => {}); await waitForTask(s); await download.pause();
  assert.equal(await pending, false);
  assert.equal(JSON.parse(s.files.get(s.path + '.resume.json').text).resumeData, 'saved-offset');
  s.options.wait = false;
  assert.equal(await new s.mod.ModelDownload().start(spec, true, () => {}), true);
  assert.equal(s.tasks[1].resumeData, 'saved-offset');
});
test('perda do Wi-Fi pausa automaticamente; listeners são removidos', async () => {
  const s = await storage({wait: true}), download = new s.mod.ModelDownload();
  const pending = download.start(spec, true, () => {}); await waitForTask(s);
  s.listeners.network({type: 'CELLULAR', isConnected: true});
  assert.equal(await pending, false); assert.equal(Object.keys(s.listeners).length, 0);
});
test('modelo existente pode ser conferido offline e apagado com parciais', async () => {
  const s = await storage({network: {isConnected: false}});
  s.files.set(s.path, {size: spec.bytes, sha: spec.sha256});
  assert.equal(await new s.mod.ModelDownload().start(spec, true, () => {}), true);
  assert.equal(s.tasks.length, 0); await s.mod.deleteModel(spec);
  assert.equal(await s.mod.isDownloaded(spec), false);
  assert.deepEqual(new Set(s.deleted), new Set([s.path, s.path + '.part', s.path + '.resume.json', s.path + '.verified.json']));
});
test('Metro resolve .js para TS fonte e mantém JS/JSON compilados do núcleo', async () => {
  const path = await import('node:path');
  const nativeFS = await import('node:fs');
  const source = await fs.readFile('metro.config.js', 'utf8'), module = {exports: {}};
  new Function('require', 'module', '__dirname', source)(name => {
    if (name === 'path') return path;
    if (name === 'fs') return nativeFS;
    if (name === 'expo/metro-config') return {getDefaultConfig: () => ({resolver: {}})};
    throw Error(name);
  }, module, process.cwd());
  const config = module.exports;
  const context = {originModulePath: path.resolve('src/pipeline/testData.ts'), resolveRequest: (ctx, name) => name};
  assert.equal(config.resolver.resolveRequest(context, './usage.js', 'android'), './usage.ts');
  assert.equal(config.resolver.resolveRequest(context, './prompts.json', 'android'), './prompts.json');
  const compiled = {...context, originModulePath: path.resolve('../slidedsl-core/dist/index.js')};
  assert.equal(config.resolver.resolveRequest(compiled, './render.js', 'android'), './render.js');
  assert.ok(config.watchFolders.includes(path.resolve('../slidedsl-core')));
});
