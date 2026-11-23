import {Text, TextInput, View} from 'react-native';
import {useState} from 'react';
import VoiceInput from '../VoiceInput';
import type {SourceChoice} from '../pipeline/sources';
import {Button, styles} from '../ui';
import {pickDocument} from '../storage/documents';
import {documentKind} from '../pipeline/documents';
export default function RequestScreen({request, setRequest, slides, setSlides, source, setSource, onGenerate}: {
  request: string; setRequest: (s: string | ((s: string) => string)) => void; slides: number; setSlides: (n: number) => void;
  source: SourceChoice; setSource: (s: SourceChoice) => void; onGenerate: () => void;
}) {
  const [partial, setPartial] = useState('');
  const [picking, setPicking] = useState(false), [error, setError] = useState('');
  async function chooseDocument() {
    setPicking(true); setError('');
    try {const document = await pickDocument(); if (document) setSource({mode: 'document', document});}
    catch (e) {setError(e instanceof Error ? e.message : String(e));}
    finally {setPicking(false);}
  }
  return <>
    <Text style={styles.label}>Sobre o que é a apresentação?</Text>
    <TextInput accessibilityLabel="Pedido da apresentação" style={[styles.input, {minHeight: 120}]} multiline maxLength={600}
      placeholder="Ex.: Explique energia solar residencial para moradores."
      value={partial ? `${request} ${partial}`.trim() : request}
      onChangeText={t => {setPartial(''); setRequest(t);}}/>
    <VoiceInput onFinalText={t => setRequest(current => (current.trim() ? `${current.trim()} ${t}` : t).slice(0, 600))} onPartialText={setPartial}/>
    <Text style={styles.label}>Número de slides</Text>
    <View style={styles.row}>{[4, 5, 6, 7, 8].map(n => <Button key={n} secondary={slides !== n} onPress={() => setSlides(n)}>{n}</Button>)}</View>
    <Text style={styles.label}>Fonte do conteúdo</Text>
    <View style={styles.row}>
      <Button secondary={source.mode !== 'none'} onPress={() => setSource({mode: 'none'})}>Sem pesquisa</Button>
      <Button secondary={source.mode !== 'paste'} onPress={() => setSource({mode: 'paste', text: ''})}>Colar texto</Button>
      <Button secondary={source.mode !== 'wikipedia'} onPress={() => setSource({mode: 'wikipedia', title: '', language: 'pt'})}>Wikipedia</Button>
      <Button disabled={picking} secondary={source.mode !== 'document'} onPress={() => void chooseDocument()}>{picking ? 'Recebendo documento…' : 'Escolher documento'}</Button>
    </View>
    {source.mode === 'none' ? <Text style={styles.warning}>conteúdo sem fontes</Text> : null}
    {error ? <Text style={styles.error}>{error}</Text> : null}
    {source.mode === 'document' ? <>
      <Text style={styles.label} selectable>{source.document.name}</Text>
      <Text style={styles.text}>{documentKind(source.document.name, source.document.mime).toUpperCase()} · {(source.document.bytes / 1024).toFixed(1)} KB</Text>
      <Text style={styles.text}>Até 10 MB e 200 mil caracteres. Extração local, até 6 trechos. PDF precisa de texto selecionável. O pedido pode ficar vazio para apresentar os pontos principais.</Text>
    </> : null}
    {source.mode === 'paste' ? <>
      <TextInput accessibilityLabel="Texto da fonte" style={[styles.input, {minHeight: 160}]} multiline maxLength={20000} placeholder="Cole o trecho de referência" value={source.text} onChangeText={text => setSource({...source, text})}/>
      <Text style={styles.text}>Usaremos os primeiros 2600 caracteres, com até 3 fatos cujos trechos foram conferidos literalmente.</Text>
    </> : null}
    {source.mode === 'wikipedia' ? <>
      <TextInput accessibilityLabel="Título da página Wikipedia" style={styles.input} maxLength={180} placeholder="Título exato da página, ex.: Energia solar" value={source.title} onChangeText={title => setSource({...source, title})}/>
      <View style={styles.row}>{(['pt', 'en'] as const).map(language => <Button key={language} secondary={source.language !== language} onPress={() => setSource({...source, language})}>{language === 'pt' ? 'Português' : 'English'}</Button>)}</View>
      <Text style={styles.text}>Requer internet. O pedido e a extração continuam no aparelho; só o título da página é enviado à Wikipedia.</Text>
    </> : null}
    <Button disabled={picking || (!request.trim() && source.mode !== 'document') || (source.mode === 'paste' && !source.text.trim()) || (source.mode === 'wikipedia' && !source.title.trim())} onPress={onGenerate}>Gerar apresentação</Button>
    <Button secondary onPress={() => {setRequest(''); setPartial('');}}>Limpar pedido</Button>
  </>;
}
