import {StatusBar} from 'expo-status-bar';
import {useEffect, useRef, useState} from 'react';
import {ActivityIndicator, ScrollView, Text, View} from 'react-native';
import * as Device from 'expo-device';
import {ExpoSpeechRecognitionModule} from 'expo-speech-recognition';
import RequestScreen from './src/screens/RequestScreen';
import ModelScreen from './src/screens/ModelScreen';
import ResultScreen from './src/screens/ResultScreen';
import {Button, styles} from './src/ui';
import {suggestedModel, modelAllowed} from './src/models';
import {ensureVerified, isDownloaded, modelUri} from './src/storage/models';
import {exportTestData, PPTX_MIME, savePptx, shareFile, storePptx} from './src/storage/exports';
import {loadModel, type LocalModel} from './src/llm/llamaRn';
import {generate, GenerationError, type GenerationResult, type Progress} from './src/pipeline/generate';
import type {SourceChoice, DocumentUsage} from './src/pipeline/sources';
import {deleteDocument, onIncomingDocument, pendingDocument, readDocument} from './src/storage/documents';
import {documentKind, documentMetadata, type DocumentFile, type DocumentText} from './src/pipeline/documents';
import type {CallRecord} from './src/pipeline/types';
import {testData} from './src/pipeline/testData';
import {deviceSnapshot} from './src/device';
export default function App() {
  const [screen, setScreen] = useState<'request' | 'model' | 'progress' | 'result'>('request');
  const [request, setRequest] = useState(''), [slides, setSlides] = useState(5);
  const [source, setSource] = useState<SourceChoice>({mode: 'none'});
  const [selected, setSelected] = useState(suggestedModel(Device.totalMemory)), [gpu, setGpu] = useState(false);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState('');
  const [progress, setProgress] = useState<Progress>({stage: '', total: slides});
  const [result, setResult] = useState<GenerationResult | null>(null), [file, setFile] = useState('');
  const [data, setData] = useState<ReturnType<typeof testData> | null>(null);
  const [calls, setCalls] = useState(0);
  const active = useRef<AbortController | null>(null);
  const queuedDocument = useRef<DocumentFile | null>(null);
  const [documentInfo, setDocumentInfo] = useState<DocumentUsage | null>(null);
  function acceptDocument(document: DocumentFile) {
    setSource({mode: 'document', document}); setDocumentInfo(null); setScreen('request');
    setMessage(`Documento selecionado: ${document.name}`);
  }
  useEffect(() => {
    let mounted = true;
    async function receive() {
      try {
        const document = await pendingDocument();
        if (!document) return;
        if (!mounted) {await deleteDocument(document); return;}
        if (active.current) {
          if (queuedDocument.current) await deleteDocument(queuedDocument.current);
          queuedDocument.current = document;
          setMessage(`Documento recebido: ${document.name}. Será selecionado ao encerrar a geração atual.`);
        } else acceptDocument(document);
      } catch (e) {if (mounted) setMessage(e instanceof Error ? e.message : String(e));}
    }
    const subscription = onIncomingDocument(() => void receive());
    void receive();
    return () => {mounted = false; subscription.remove();};
  }, []);
  const documentUri = source.mode === 'document' ? source.document.uri : null;
  useEffect(() => {
    return () => {if (documentUri) void deleteDocument({uri: documentUri, name: '', mime: '', bytes: 0}).catch(() => {});};
  }, [documentUri]);
  async function act(action: () => Promise<unknown>) {
    try {await action();} catch (e) {setMessage(e instanceof Error ? e.message : String(e));}
  }
  async function run() {
    if (active.current) return;
    const abort = new AbortController(); active.current = abort;
    setBusy(true); setMessage(''); setResult(null); setFile(''); setData(null); setCalls(0); setDocumentInfo(null); setScreen('progress');
    setProgress({stage: 'Preparando modelo', total: slides});
    const started = Date.now();
    let llm: LocalModel | null = null, records: CallRecord[] = [], status = 'failed', diagnostics: unknown = [], error = '';
    let snapshot: unknown = null;
    let documentData: unknown = source.mode === 'document' ? {name: source.document.name, type: documentKind(source.document.name, source.document.mime), bytes: source.document.bytes, mime: source.document.mime} : undefined;
    try {
      ExpoSpeechRecognitionModule.abort();
      snapshot = await deviceSnapshot();
      if (!modelAllowed(selected, Device.totalMemory)) throw Error('O modelo 4B exige pelo menos 12 GB de RAM.');
      if (!await isDownloaded(selected)) throw Error('Baixe o modelo na tela Modelo antes de gerar.');
      let document: DocumentText | undefined;
      if (source.mode === 'document') {
        setProgress({stage: 'Lendo documento', total: slides});
        document = await readDocument(source.document, abort.signal);
        const info = {...documentMetadata(document), chunks_used: 0, facts_used: 0, passages: [], max_extract_calls: 6, sections: []};
        documentData = info; setDocumentInfo(info);
      }
      await ensureVerified(selected, () => setProgress({stage: 'Conferindo SHA-256 do modelo (só na primeira vez)', total: slides}));
      if (abort.signal.aborted) throw Error('Operação cancelada.');
      setProgress({stage: 'Carregando modelo', total: slides});
      llm = await loadModel(modelUri(selected), gpu, n => setProgress({stage: `Carregando modelo · ${Math.round(n)}%`, total: slides}));
      const generated = await generate({request, slides, source, model: llm, signal: abort.signal,
        readDocument: async (file, signal) => document ?? readDocument(file, signal),
        onDocument: info => {documentData = info; setDocumentInfo(info);},
        onProgress: setProgress, onCalls: c => {records = c; setCalls(c.length);},
        fetchJson: async (url, signal) => {
          const response = await fetch(url, {signal, headers: {'Accept': 'application/json'}});
          if (!response.ok) throw Error(`Wikipedia: HTTP ${response.status}.`);
          return response.json();
        }});
      if (abort.signal.aborted) throw Error('Operação cancelada.');
      const uri = await storePptx(generated.pptx);
      setResult(generated); setFile(uri); diagnostics = generated.diagnostics; status = 'success'; setScreen('result');
    } catch (e) {
      status = abort.signal.aborted ? 'cancelled' : 'failed';
      error = e instanceof Error ? e.message : String(e);
      if (e instanceof GenerationError) diagnostics = e.diagnostics;
      setMessage(error); setScreen('request');
    } finally {
      if (llm) {try {await llm.release();} catch (e) {setMessage(`Falha ao liberar modelo: ${String(e)}`);}}
      const end = await deviceSnapshot();
      setData(testData({calls: records, device_start: snapshot, device_end: end,
        model: {...selected, quantization: 'Q4_K_M', n_ctx: 4096, gpu}, status,
        wall_ms: Date.now() - started, slides, diagnostics, error: error || undefined, source_mode: source.mode, document: documentData}));
      active.current = null; setBusy(false);
      if (queuedDocument.current) {const document = queuedDocument.current; queuedDocument.current = null; acceptDocument(document);}
    }
  }
  return <ScrollView contentContainerStyle={styles.page} keyboardShouldPersistTaps="handled">
    <Text style={styles.title}>SlideDSL</Text>
    <Text style={styles.text}>Apresentações editáveis geradas no próprio celular.</Text>
    <View style={styles.row}>
      <Button secondary={screen !== 'request'} disabled={busy} onPress={() => setScreen('request')}>Pedido</Button>
      <Button secondary={screen !== 'model'} disabled={busy} onPress={() => setScreen('model')}>Modelo</Button>
      {result ? <Button secondary={screen !== 'result'} disabled={busy} onPress={() => setScreen('result')}>Resultado</Button> : null}
    </View>
    {message ? <Text accessibilityLiveRegion="polite" style={styles.error}>{message}</Text> : null}
    {screen === 'request' ? <><Text style={styles.text}>Selecionado: {selected.label}</Text><RequestScreen request={request} setRequest={setRequest} slides={slides} setSlides={setSlides} source={source} setSource={setSource} onGenerate={() => void run()}/></> : null}
    {screen === 'model' ? <ModelScreen selected={selected} onSelect={setSelected} gpu={gpu} setGpu={setGpu}/> : null}
    {screen === 'progress' ? <>
      <ActivityIndicator size="large"/><Text accessibilityLiveRegion="polite" style={styles.heading}>{progress.stage}</Text>
      {documentInfo ? <Text style={styles.text}>{documentInfo.name} · {documentInfo.type.toUpperCase()} · {documentInfo.pages === null ? 'sem paginação' : `${documentInfo.pages} páginas`} · {documentInfo.characters} caracteres · {documentInfo.chunks_used}/{documentInfo.chunks_total} trechos · {documentInfo.facts_used} fatos</Text> : null}
      <Text style={styles.text}>{progress.slide ? `Slide ${progress.slide}/${progress.total} · ` : ''}{calls} chamadas realizadas</Text>
      <Button secondary onPress={() => {active.current?.abort(); setProgress(p => ({...p, stage: 'Cancelando; aguardando liberação do modelo'}));}}>Cancelar</Button>
    </> : null}
    {screen === 'result' && result ? <ResultScreen result={result} file={file} onShare={() => void act(() => shareFile(file, PPTX_MIME))}
      onSave={() => void act(async () => {if (await savePptx(file)) setMessage('PowerPoint salvo na pasta escolhida.');})}/> : null}
    {data ? <Button secondary disabled={busy} onPress={() => void act(() => exportTestData(data))}>Exportar dados do teste</Button> : null}
    <StatusBar style="dark"/>
  </ScrollView>;
}
