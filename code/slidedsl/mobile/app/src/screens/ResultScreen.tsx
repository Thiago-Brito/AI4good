import {useState} from 'react';
import {Text, View} from 'react-native';
import type {Slide} from '@slidedsl/core';
import type {GenerationResult} from '../pipeline/generate';
import {Button, styles} from '../ui';
function Thumbnail({slide}: {slide: Slide}) {
  const [width, setWidth] = useState(280), scale = width / 1280;
  return <View accessibilityLabel={`Miniatura do slide ${slide.number}`} onLayout={e => setWidth(e.nativeEvent.layout.width)}
    style={{width: '100%', aspectRatio: 16 / 9, backgroundColor: '#F6F8FC', overflow: 'hidden', borderWidth: 1, borderColor: '#CBD5E1'}}>
    {[...slide.elements].sort((a, b) => a.z - b.z).map(e => {
      const box = {position: 'absolute' as const, left: e.x * scale, top: e.y * scale, width: e.width * scale, height: e.height * scale};
      if (e.type === 'text') return <Text key={e.id} style={[box, {fontSize: (e.font_size ?? 12) * 96 / 72 * scale,
        color: e.color ?? '#14233D', fontWeight: e.bold ? '700' : '400', textAlign: e.align, padding: 2 * scale}]}>{e.text}</Text>;
      if (e.type === 'arrow') return <Text key={e.id} style={[box, {color: e.color ?? '#14233D', fontSize: e.height * scale, textAlign: 'center'}]}>↓</Text>;
      return <View key={e.id} style={[box, {backgroundColor: e.color ?? '#CBD5E1', borderRadius: e.type === 'ellipse' ? 999 : e.rounded ? 4 : 0}]}/>;
    })}
  </View>;
}
export default function ResultScreen({result, file, onSave, onShare}: {result: GenerationResult; file: string; onSave: () => void; onShare: () => void}) {
  return <>
    <Text style={styles.heading}>{result.deck.title}</Text>
    <Text style={styles.text}>{result.ir.slides.length} slides · {result.calls.length} chamadas · {(result.wall_ms / 1000).toFixed(1)} s</Text>
    {result.source.warning ? <Text style={styles.warning}>{result.source.warning}</Text> : null}
    {result.source.source ? <Text style={styles.text} selectable>Fonte: {result.source.source.title}{'\n'}{result.source.source.url}</Text> : null}
    {result.source.document ? <Text style={styles.text}>{result.source.document.type.toUpperCase()} · {result.source.document.pages === null ? 'Paginação não disponível' : `${result.source.document.pages} páginas`} · {result.source.document.characters} caracteres · {result.source.document.chunks_used}/{result.source.document.chunks_total} trechos · {result.source.document.facts_used} fatos</Text> : null}
    <Text style={styles.text}>Prévia geométrica simples. O PowerPoint mantém textos e formas editáveis.</Text>
    {result.ir.slides.map(slide => <View key={slide.number} style={styles.card}><Text style={styles.label}>Slide {slide.number}</Text><Thumbnail slide={slide}/></View>)}
    <Button onPress={onSave}>Salvar .pptx em uma pasta</Button>
    <Button secondary onPress={onShare}>Compartilhar .pptx</Button>
    <Text style={{fontSize: 12, color: '#475467'}} selectable>Arquivo local: {file}</Text>
    {result.diagnostics.filter(d => d.severity === 'AVISO').map((d, i) => <Text key={i} style={styles.warning}>{d.code} · slide {d.slide ?? '—'}: {d.message}</Text>)}
  </>;
}
