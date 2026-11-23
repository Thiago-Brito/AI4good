import {File} from 'expo-file-system';
import * as FS from 'expo-file-system/legacy';
import * as Network from 'expo-network';
import {AppState} from 'react-native';
import type {ModelSpec} from '../models';
export function modelUri(model: ModelSpec): string {
  if (!FS.documentDirectory) throw Error('Armazenamento do app indisponível.');
  return `${FS.documentDirectory}models/${model.id}.gguf`;
}
export async function isDownloaded(model: ModelSpec): Promise<boolean> {
  const info = await FS.getInfoAsync(modelUri(model));
  return info.exists && info.size === model.bytes;
}
export async function verifyModel(model: ModelSpec, path = modelUri(model)): Promise<void> {
  const file = new File(path);
  if (!file.exists || file.size !== model.bytes) throw Error('Tamanho do modelo incorreto. Retome ou refaça o download.');
  if ((await file.digest('SHA-256')).toLowerCase() !== model.sha256) throw Error('SHA-256 do modelo não confere. Apague e baixe novamente.');
}
/** Instala um GGUF escolhido no aparelho (sem internet: copiado por cabo, cartão etc.).
 * Mesmas garantias do download: tamanho e SHA-256 do catálogo conferidos antes de usar. */
export async function importModel(model: ModelSpec, sourceUri: string, sourceSize: number | null | undefined,
  onProgress: (message: string) => void): Promise<void> {
  if (typeof sourceSize === 'number' && sourceSize !== model.bytes) {
    throw Error(`Arquivo de ${(sourceSize / 1e9).toFixed(2)} GB não é o ${model.label} (${(model.bytes / 1e9).toFixed(2)} GB).`);
  }
  const path = modelUri(model);
  await FS.makeDirectoryAsync(`${FS.documentDirectory}models`, {intermediates: true});
  if (await FS.getFreeDiskStorageAsync() < model.bytes + 64 * 1024 ** 2) throw Error('Espaço insuficiente para importar o modelo.');
  await FS.deleteAsync(path + '.part', {idempotent: true});
  onProgress('Copiando arquivo do modelo');
  await FS.copyAsync({from: sourceUri, to: path + '.part'});
  onProgress('Conferindo SHA-256');
  try { await verifyModel(model, path + '.part'); } catch (e) {
    await FS.deleteAsync(path + '.part', {idempotent: true});
    throw e;
  }
  await FS.deleteAsync(path, {idempotent: true});
  await FS.moveAsync({from: path + '.part', to: path});
  await FS.deleteAsync(path + '.resume.json', {idempotent: true});
  await markVerified(model);
  onProgress('Modelo importado e conferido');
}
/** Registro da conferência SHA-256: o hash (lento para 0,5–2,5 GB) é calculado uma vez, ao baixar
 * ou importar; nas gerações basta tamanho + data do arquivo baterem com o registro. */
async function markVerified(model: ModelSpec): Promise<void> {
  const info = await FS.getInfoAsync(modelUri(model));
  if (!info.exists) return;
  await FS.writeAsStringAsync(modelUri(model) + '.verified.json',
    JSON.stringify({sha256: model.sha256, size: info.size, mtime: info.modificationTime}));
}
export async function ensureVerified(model: ModelSpec, onSlowCheck?: () => void): Promise<void> {
  const path = modelUri(model);
  const info = await FS.getInfoAsync(path);
  if (!info.exists || info.size !== model.bytes) throw Error('Tamanho do modelo incorreto. Retome ou refaça o download.');
  try {
    const mark = JSON.parse(await FS.readAsStringAsync(path + '.verified.json'));
    if (mark.sha256 === model.sha256 && mark.size === info.size && mark.mtime === info.modificationTime) return;
  } catch { /* sem registro: conferir agora */ }
  onSlowCheck?.();
  await verifyModel(model);
  await markVerified(model);
}
export async function deleteModel(model: ModelSpec): Promise<void> {
  for (const suffix of ['', '.part', '.resume.json', '.verified.json']) await FS.deleteAsync(modelUri(model) + suffix, {idempotent: true});
}
export class ModelDownload {
  private task: FS.DownloadResumable | null = null;
  private pausePromise: Promise<void> | null = null;
  private paused = false;
  private resumePath = '';
  private model: ModelSpec | null = null;
  async pause(): Promise<void> {
    if (!this.task) return;
    if (this.pausePromise) return this.pausePromise;
    this.paused = true;
    const task = this.task;
    this.pausePromise = (async () => {
      const state = await task.pauseAsync();
      await FS.writeAsStringAsync(this.resumePath, JSON.stringify({sha256: this.model!.sha256, ...state}));
    })();
    try { await this.pausePromise; } finally { this.pausePromise = null; }
  }
  async start(model: ModelSpec, wifiOnly: boolean, onProgress: (fraction: number, message: string) => void): Promise<boolean> {
    if (this.task) throw Error('Já existe um download ativo.');
    if (await isDownloaded(model)) { await verifyModel(model); onProgress(1, 'Modelo já baixado e conferido'); return true; }
    const allowed = (state: Network.NetworkState) => state.isConnected === true && state.isInternetReachable !== false && (!wifiOnly || state.type === Network.NetworkStateType.WIFI);
    if (!allowed(await Network.getNetworkStateAsync())) throw Error(wifiOnly ? 'Conecte ao Wi-Fi para baixar o modelo.' : 'Conecte à internet para baixar o modelo.');
    const path = modelUri(model);
    await FS.makeDirectoryAsync(`${FS.documentDirectory}models`, {intermediates: true});
    const partial = await FS.getInfoAsync(path + '.part');
    const needed = model.bytes - (partial.exists ? partial.size : 0) + 128 * 1024 ** 2;
    if (await FS.getFreeDiskStorageAsync() < needed) throw Error('Espaço insuficiente para baixar o modelo.');
    this.resumePath = path + '.resume.json'; this.model = model; this.paused = false;
    let state: FS.DownloadPauseState | null = null;
    if ((await FS.getInfoAsync(this.resumePath)).exists) {
      const saved = JSON.parse(await FS.readAsStringAsync(this.resumePath));
      if (saved.sha256 === model.sha256 && saved.url === model.url && saved.fileUri === path + '.part') state = saved;
    }
    this.task = FS.createDownloadResumable(model.url, path + '.part', {}, p => {
      onProgress(Math.min(1, p.totalBytesWritten / (p.totalBytesExpectedToWrite > 0 ? p.totalBytesExpectedToWrite : model.bytes)), 'Baixando modelo');
    }, state?.resumeData);
    let pauseError: Error | null = null;
    const autoPause = () => { void this.pause().then(() => onProgress(0, 'Download pausado; toque em baixar/retomar.')).catch(e => { pauseError = e; }); };
    const network = Network.addNetworkStateListener(s => { if (!allowed(s)) autoPause(); });
    const app = AppState.addEventListener('change', s => { if (s !== 'active') autoPause(); });
    try {
      const response = await this.task.downloadAsync();
      if (this.pausePromise) await this.pausePromise;
      if (pauseError) throw pauseError;
      if (this.paused || !response) return false;
      if (response.status !== 200 && response.status !== 206) throw Error(`Download recusado: HTTP ${response.status}.`);
      onProgress(1, 'Conferindo SHA-256');
      await verifyModel(model, path + '.part');
      await FS.moveAsync({from: path + '.part', to: path});
      await FS.deleteAsync(this.resumePath, {idempotent: true});
      await markVerified(model);
      onProgress(1, 'Modelo baixado e conferido');
      return true;
    } catch (e) {
      if (!this.paused && this.task) {
        try { await this.pause(); } catch { /* a retry can restart when resume data is unavailable */ }
      }
      throw e;
    } finally { network.remove(); app.remove(); this.task = null; this.model = null; }
  }
}