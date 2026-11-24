import {useState} from 'react';
import {Text, TextInput, View} from 'react-native';
import type {Slide} from '@slidedsl/core';
import type {GenerationResult} from '../pipeline/generate';
import {editableFields, THEMES} from '../pipeline/edit';
import {Button, styles} from '../ui';
/** Ações de edição; App aplica, recompila, salva o .pptx e guarda a versão anterior para o desfazer. */
export interface SlideEditor {
  busy: boolean; canUndo: boolean; undo: () => void;
  move: (from: number, to: number) => void; remove: (index: number) => void;
  editTexts: (index: number, changes: Record<string, string>) => void;
  redo: (index: number, instruction: string) => void;
  setTheme: (theme: (typeof THEMES)[number]) => void;
  removePhoto: (index: number) => void; changePhoto: (index: number, query: string) => void;
}
function SlideCard({result, slide, index, editor}: {result: GenerationResult; slide: Slide; index: number; editor: SlideEditor}) {
  const [mode, setMode] = useState<'view' | 'text' | 'ai' | 'photo'>('view'), [instruction, setInstruction] = useState('');
  const current = result.deck.slides[index], [photoQuery, setPhotoQuery] = useState(current.image_query ?? '');
  const fields = editableFields(result.deck.slides[index]), [draft, setDraft] = useState<Record<string, string>>({});
  const n = result.deck.slides.length, kind = result.deck.slides[index].kind;
  return <View style={styles.card}>
    <Text style={styles.label}>Slide {slide.number} · {kind}</Text>
    <Thumbnail slide={slide}/>
    <View style={styles.row}>
      <Button secondary disabled={editor.busy || index === 0} onPress={() => editor.move(index, index - 1)}>↑</Button>
      <Button secondary disabled={editor.busy || index === n - 1} onPress={() => editor.move(index, index + 1)}>↓</Button>
      <Button secondary={mode !== 'text'} disabled={editor.busy} onPress={() => {setDraft({}); setMode(mode === 'text' ? 'view' : 'text');}}>Editar texto</Button>
      <Button secondary={mode !== 'ai'} disabled={editor.busy} onPress={() => setMode(mode === 'ai' ? 'view' : 'ai')}>Refazer com IA</Button>
      <Button secondary disabled={editor.busy || n <= 2} onPress={() => editor.remove(index)}>Excluir</Button>
      {kind === 'imagem' ? <Button secondary={mode !== 'photo'} disabled={editor.busy} onPress={() => setMode(mode === 'photo' ? 'view' : 'photo')}>Foto</Button> : null}
    </View>
    {mode === 'photo' ? <>
      <TextInput accessibilityLabel={`Busca da foto do slide ${slide.number}`} style={styles.input} maxLength={120}
        placeholder="O que a foto mostra, em inglês (ex.: solar panels roof)" value={photoQuery} onChangeText={setPhotoQuery}/>
      <View style={styles.row}>
        <Button disabled={editor.busy || !photoQuery.trim()} onPress={() => {editor.changePhoto(index, photoQuery); setMode('view');}}>Trocar foto</Button>
        <Button secondary disabled={editor.busy || !current.image_file} onPress={() => {editor.removePhoto(index); setMode('view');}}>Remover foto</Button>
      </View>
      <Text style={styles.text}>Foto livre do Openverse/NASA com crédito; precisa de internet.</Text>
    </> : null}
    {mode === 'text' ? <>
      {fields.map(f => <View key={f.path} style={{gap: 4}}>
        <Text style={styles.text}>{f.label}</Text>
        <TextInput accessibilityLabel={`${f.label} do slide ${slide.number}`} style={[styles.input, f.multiline && {minHeight: 80}]}
          multiline={f.multiline} value={draft[f.path] ?? f.value} onChangeText={text => setDraft(d => ({...d, [f.path]: text}))}/>
      </View>)}
      <Button disabled={editor.busy || !Object.keys(draft).length} onPress={() => {editor.editTexts(index, draft); setMode('view');}}>Salvar texto</Button>
    </> : null}
    {mode === 'ai' ? <>
      <TextInput accessibilityLabel={`Instrução para refazer o slide ${slide.number}`} style={[styles.input, {minHeight: 80}]} multiline maxLength={300}
        placeholder="Ex.: use um exemplo do dia a dia; deixe mais curto" value={instruction} onChangeText={setInstruction}/>
      <Text style={styles.text}>Carrega o modelo e reescreve só este slide (1 chamada + 1 reparo), com as mesmas regras da geração.</Text>
      <Button disabled={editor.busy} onPress={() => {editor.redo(index, instruction); setMode('view');}}>Refazer este slide</Button>
    </> : null}
  </View>;
}
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
export default function ResultScreen({result, file, onSave, onShare, editor}: {result: GenerationResult; file: string; onSave: () => void; onShare: () => void; editor: SlideEditor}) {
  return <>
    <Text style={styles.heading}>{result.deck.title}</Text>
    <Text style={styles.text}>{result.ir.slides.length} slides · {result.calls.length} chamadas · {(result.wall_ms / 1000).toFixed(1)} s</Text>
    {result.source.warning ? <Text style={styles.warning}>{result.source.warning}</Text> : null}
    {result.source.source ? <Text style={styles.text} selectable>Fonte: {result.source.source.title}{'\n'}{result.source.source.url}</Text> : null}
    {result.source.document ? <Text style={styles.text}>{result.source.document.type.toUpperCase()} · {result.source.document.pages === null ? 'Paginação não disponível' : `${result.source.document.pages} páginas`} · {result.source.document.characters} caracteres · {result.source.document.chunks_used}/{result.source.document.chunks_total} trechos · {result.source.document.facts_used} fatos</Text> : null}
    <Text style={styles.text}>Prévia geométrica simples. Edite slide a slide; o PowerPoint é refeito a cada mudança.</Text>
    <Text style={styles.label}>Estilo</Text>
    <View style={styles.row}>{THEMES.map(t => <Button key={t} secondary={(result.deck.theme ?? 'claro') !== t} disabled={editor.busy} onPress={() => editor.setTheme(t)}>{t}</Button>)}</View>
    {editor.canUndo ? <Button secondary disabled={editor.busy} onPress={editor.undo}>Desfazer última edição</Button> : null}
    {result.ir.slides.map((slide, index) => <SlideCard key={`${slide.number}-${result.deck.slides[index]?.title}`} result={result} slide={slide} index={index} editor={editor}/>)}
    <Button onPress={onSave}>Salvar .pptx em uma pasta</Button>
    <Button secondary onPress={onShare}>Compartilhar .pptx</Button>
    <Text style={{fontSize: 12, color: '#475467'}} selectable>Arquivo local: {file}</Text>
    {result.diagnostics.filter(d => d.severity === 'AVISO').map((d, i) => <Text key={i} style={styles.warning}>{d.code} · slide {d.slide ?? '—'}: {d.message}</Text>)}
  </>;
}
