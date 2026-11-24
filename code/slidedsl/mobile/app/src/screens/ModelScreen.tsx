import {useEffect, useRef, useState} from 'react';
import {Switch, Text, View} from 'react-native';
import * as Device from 'expo-device';
import * as DocumentPicker from 'expo-document-picker';
import {models, modelAllowed, suggestedModel, type ModelSpec} from '../models';
import {deleteModel, importModel, isDownloaded, ModelDownload} from '../storage/models';
import {Button, styles} from '../ui';
export default function ModelScreen({selected, onSelect, gpu, setGpu, grammarSlides, setGrammarSlides}: {selected: ModelSpec; onSelect: (m: ModelSpec) => void; gpu: boolean; setGpu: (v: boolean) => void; grammarSlides: boolean; setGrammarSlides: (v: boolean) => void}) {
  const [wifi, setWifi] = useState(true), [busy, setBusy] = useState(false);
  const [ready, setReady] = useState<Record<string, boolean>>({}), [message, setMessage] = useState('');
  const [fraction, setFraction] = useState(0);
  const downloader = useRef(new ModelDownload()).current;
  const active = useRef(false);
  const refresh = async () => setReady(Object.fromEntries(await Promise.all(models.map(async m => [m.id, await isDownloaded(m)]))));
  useEffect(() => { void refresh().catch(e => setMessage(String(e))); return () => { void downloader.pause().catch(() => {}); }; }, [downloader]);
  async function download() {
    if (active.current) return;
    active.current = true; setBusy(true); setMessage('Preparando download');
    try {
      if (!modelAllowed(selected, Device.totalMemory)) throw Error('Qwen3 4B exige pelo menos 12 GB de RAM total informada.');
      await downloader.start(selected, wifi, (n, text) => {setFraction(n); setMessage(text);});
      await refresh();
    } catch (e) {setMessage(e instanceof Error ? e.message : String(e));}
    finally {active.current = false; setBusy(false);}
  }
  async function importFile() {
    if (active.current) return;
    active.current = true; setBusy(true); setMessage('Escolha o arquivo .gguf');
    try {
      if (!modelAllowed(selected, Device.totalMemory)) throw Error('Qwen3 4B exige pelo menos 12 GB de RAM total informada.');
      const picked = await DocumentPicker.getDocumentAsync({type: '*/*', copyToCacheDirectory: false, multiple: false});
      if (picked.canceled || !picked.assets?.length) { setMessage('Importação cancelada.'); return; }
      const asset = picked.assets[0];
      await importModel(selected, asset.uri, asset.size, setMessage);
      await refresh();
    } catch (e) {setMessage(e instanceof Error ? e.message : String(e));}
    finally {active.current = false; setBusy(false);}
  }
  return <>
    <Text style={styles.heading}>Modelo no aparelho</Text>
    <Text style={styles.text}>RAM: {Device.totalMemory ? `${(Device.totalMemory / 1024 ** 3).toFixed(1)} GB` : 'não informada'}. Sugestão: {suggestedModel(Device.totalMemory).label}.</Text>
    {models.map(m => <View key={m.id} style={styles.card}>
      <Button secondary={selected.id !== m.id} disabled={busy || !modelAllowed(m, Device.totalMemory)} onPress={() => onSelect(m)}>{m.label}</Button>
      <Text style={styles.text}>Q4_K_M · {(m.bytes / 1e9).toFixed(2)} GB · {ready[m.id] ? 'baixado' : 'não baixado'}</Text>
      <Text style={{fontSize: 11, color: '#475467'}} selectable>{m.url || 'Arquivo Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf (importar)'}</Text>
      <Text style={{fontSize: 11, color: '#475467'}} selectable>SHA-256: {m.sha256}</Text>
    </View>)}
    <View style={styles.row}><Switch accessibilityLabel="Baixar somente por Wi-Fi" value={wifi} onValueChange={setWifi} disabled={busy}/><Text style={styles.text}>Baixar somente por Wi-Fi</Text></View>
    <View style={styles.row}><Switch accessibilityLabel="Usar GPU" value={gpu} onValueChange={setGpu} disabled={busy}/><Text style={styles.text}>GPU experimental (padrão: desligada)</Text></View>
    <View style={styles.row}><Switch accessibilityLabel="Escrever slides em SlideDSL Alto" value={grammarSlides} onValueChange={setGrammarSlides} disabled={busy}/><Text style={styles.text}>Gramática: slides em SlideDSL Alto e leitura do documento por frases numeradas (padrão; desligue para JSON)</Text></View>
    <Text style={styles.text}>O download pausa ao sair desta tela, ir para segundo plano ou perder a rede permitida. Toque em baixar/retomar para continuar. A conferência SHA-256 ocorre antes do uso.</Text>
    <Button disabled={busy || !selected.url || !modelAllowed(selected, Device.totalMemory)} onPress={() => void download()}>{selected.url ? 'Baixar / retomar selecionado' : 'Este modelo só por importação'}</Button>
    <Button secondary disabled={busy || !modelAllowed(selected, Device.totalMemory)} onPress={() => void importFile()}>Importar arquivo .gguf do aparelho</Button>
    {busy ? <Button secondary onPress={() => {void downloader.pause().then(() => setMessage('Download pausado; pronto para retomar.')).catch(e => setMessage(String(e)));}}>Pausar download</Button> : null}
    <Button secondary disabled={busy} onPress={() => {void deleteModel(selected).then(refresh).then(() => setMessage('Modelo e download parcial apagados.')).catch(e => setMessage(String(e)));}}>Apagar selecionado</Button>
    <Text accessibilityLiveRegion="polite" style={styles.text}>{message}{busy ? ` · ${Math.round(fraction * 100)}%` : ''}</Text>
  </>;
}