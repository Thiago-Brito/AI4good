import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import JSZip from 'jszip';
import {decodeText, extractBytes, makeDocument, retrieveDocument, genericDocumentRequest, validateDocument, MAX_DOCUMENT_BYTES, MAX_DOCUMENT_CHARS} from '../outputs/tests/pipeline/documents.js';
import {collectDocument} from '../outputs/tests/pipeline/sources.js';
import {Recorder} from '../outputs/tests/pipeline/usage.js';
import {generate} from '../outputs/tests/pipeline/generate.js';
import {testData} from '../outputs/tests/pipeline/testData.js';
const file = (name = 'projeto.md', bytes = 100) => ({name, bytes, mime: name.endsWith('.docx') ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' : 'text/plain', uri: 'file:///cache/input'});
const utf8 = text => new TextEncoder().encode(text);
const usage = {input_tokens: 100, output_tokens: 50, prefill_ms: 20, decode_ms: 30};
const quote = 'A equipe confere as tarefas antes de iniciar o trabalho.';
const fact = (text = quote) => ({afirmacao: text, trecho: text, tipo: 'definicao', valor: '', autor: '', relevancia: 'alta'});
async function docx(xml, styles) {
  const zip = new JSZip(); zip.file('word/document.xml', xml); if (styles) zip.file('word/styles.xml', styles);
  return zip.generateAsync({type: 'uint8array', compression: 'DEFLATE'});
}
test('TXT UTF-8 com BOM e Latin-1; UTF-8 inválido não introduz substituição silenciosa', async () => {
  const text = '\uFEFFIntrodução\r\n\r\nA equipe confere a revisão.';
  const doc = await extractBytes(file('notas.txt'), utf8(text));
  assert.equal(doc.encoding, 'UTF-8'); assert.equal(doc.chunks.length, 2);
  assert.equal(doc.chunks[0].text, 'Introdução');
  const latin = Uint8Array.from([65, 32, 97, 231, 227, 111, 32, 233, 32, 108, 111, 99, 97, 108, 46]);
  const decoded = decodeText(latin); assert.equal(decoded.text, 'A ação é local.'); assert.equal(decoded.encoding, 'Latin-1');
  assert.equal(decodeText(Uint8Array.from([0xc0, 0x80])).encoding, 'Latin-1');
});
test('MD preserva seções, numera trechos e separa títulos do conteúdo', async () => {
  const doc = await extractBytes(file(), utf8(`# Introdução\n${quote}\n\n## Método\nO grupo registra cada decisão em um arquivo local.`));
  assert.deepEqual(doc.chunks.map(c => c.heading), ['Introdução', 'Método']);
  assert.deepEqual(doc.chunks.map(c => c.passage), [1, 2]);
  assert.ok(doc.chunks.every(c => !c.text.startsWith('#')));
});
test('DOCX real gerado no teste: parágrafos, estilos Heading/Título, entidades, tabs e quebras', async () => {
  const xml = '<w:document xmlns:w="urn:test"><w:body><w:p><w:pPr><w:pStyle w:val="H1"/></w:pPr><w:r><w:t>Método &amp; avaliação</w:t></w:r></w:p><w:p><w:r><w:t>A equipe &#233; local.</w:t><w:tab/><w:t>Revisa tudo.</w:t><w:br/><w:t>Fim.</w:t></w:r></w:p><w:p><w:pPr><w:pStyle w:val="Ttulo2"/></w:pPr><w:r><w:t>Resultados</w:t></w:r></w:p><w:p><w:r><w:t>Os participantes revisam as tarefas do projeto.</w:t></w:r></w:p></w:body></w:document>';
  const styles = '<w:styles xmlns:w="urn:test"><w:style w:styleId="H1"><w:name w:val="Heading 1"/></w:style><w:style w:styleId="Ttulo2"><w:name w:val="Título 2"/></w:style></w:styles>';
  const data = await docx(xml, styles), doc = await extractBytes(file('teste.docx', data.length), data);
  assert.equal(doc.kind, 'docx'); assert.match(doc.chunks[0].text, /A equipe é local\.\tRevisa tudo\.\nFim\./);
  assert.equal(doc.chunks.at(-1).heading, 'Resultados'); assert.equal(doc.chunks[0].heading, 'Método & avaliação');
});
test('DOCX corrompido, XML ausente/malformado, DTD e XML expandido acima do limite falham', async () => {
  await assert.rejects(extractBytes(file('x.docx'), utf8('não é ZIP')), /corrompido/);
  const zip = new JSZip(); zip.file('outro.xml', 'x');
  await assert.rejects(extractBytes(file('x.docx'), await zip.generateAsync({type: 'uint8array'})), /ausente/);
  for (const xml of ['<w:p><w:t>texto</w:p>', '<!DOCTYPE doc><w:p/>']) await assert.rejects(extractBytes(file('x.docx'), await docx(xml)), /XML|DTD/);
  await assert.rejects(extractBytes(file('x.docx'), await docx(`<p>${'x'.repeat(4 * 1024 * 1024 + 1)}</p>`)), /4 MB/);
});
test('limites de bytes e caracteres, extensão desconhecida e documentos sem texto', async () => {
  assert.throws(() => validateDocument(file('x.txt', MAX_DOCUMENT_BYTES + 1)), /10 MB/);
  await assert.rejects(extractBytes(file(), utf8('x'.repeat(MAX_DOCUMENT_CHARS + 1))), /200 mil/);
  assert.throws(() => validateDocument({...file('x.exe'), mime: 'application/octet-stream'}), /Formato/);
  await assert.rejects(extractBytes(file(), utf8('   ')), /sem texto/);
  assert.throws(() => makeDocument({...file('x.pdf'), mime: 'application/pdf'}, [{text: '\n'}], 'PDFBox', 1), /PDF sem texto selecionável/);
});
test('PDF: contrato puro preserva páginas e recusa extração JS sem módulo Android', async () => {
  const input = {...file('x.pdf'), mime: 'application/pdf'};
  const doc = makeDocument(input, [{page: 1, text: quote}, {page: 2, text: 'O grupo registra cada decisão em um arquivo local.'}], 'PDFBox', 2);
  assert.equal(doc.pages, 2); assert.deepEqual(doc.chunks.map(c => c.page), [1, 2]);
  await assert.rejects(extractBytes(input, utf8('%PDF')), /módulo Android/);
});
function longDocument() {
  const sections = ['Introdução', 'Objetivo', 'Método', 'Avaliação', 'Resultados', 'Limitações'];
  return sections.map((name, i) => `## ${name}\n${(`A equipe ${['planeja', 'organiza', 'confere', 'avalia', 'registra', 'revisa'][i]} as atividades antes de apresentar cada entrega. `).repeat(80)}`).join('\n\n');
}
test('consulta geral cobre seções até o final em ordem; consulta específica usa TF-IDF', async () => {
  const bytes = utf8(longDocument()), doc = await extractBytes(file('projeto.md', bytes.length), bytes);
  assert.ok(doc.characters > 30000); assert.ok(doc.chunks.every(c => c.text.length <= 900));
  for (const request of ['', 'resuma este documento', 'apresente este documento']) {
    const chunks = retrieveDocument(doc, request);
    assert.equal(chunks.length, 6); assert.equal(new Set(chunks.map(c => c.heading)).size, 6);
    assert.equal(chunks.at(-1).heading, 'Limitações'); assert.deepEqual(chunks.map(c => c.passage), [...chunks.map(c => c.passage)].sort((a,b) => a-b));
  }
  const chunks = retrieveDocument(doc, 'Explique como a equipe avalia as atividades');
  assert.ok(chunks[0].text.includes('avalia'));
  assert.equal(retrieveDocument(doc, 'astronáutica extraterrestre').length, 0);
  assert.equal(genericDocumentRequest('Detalhe o método usado no estudo'), false);
});
test('documento sem seções distribui amostras e inclui seu fim', async () => {
  const doc = await extractBytes(file('x.txt'), utf8('Texto de abertura.\n\n' + ('O grupo organiza suas atividades com antecedência.\n\n').repeat(100) + 'Fim do estudo: a equipe registra as limitações.'));
  const chunks = retrieveDocument(doc, 'resuma este documento');
  assert.equal(chunks.length, 6); assert.match(chunks.at(-1).text, /Fim do estudo/);
});
test('conferência literal local rejeita invenção, número de outro trecho e duplicatas', async () => {
  const doc = makeDocument(file(), [{text: quote, heading: 'Método'}, {text: 'O projeto recebe 42 avaliações dos participantes.', heading: 'Resultados'}], 'UTF-8');
  const recorder = new Recorder({complete: async input => ({text: JSON.stringify({fatos: input.user.includes(quote) ? [fact(), {...fact(), afirmacao: 'A equipe confere 42 tarefas antes de iniciar o trabalho.'}, {...fact(), trecho: 'Esta passagem não existe em lugar algum.'}] : [fact()]}), usage})}, 6);
  const result = await collectDocument(doc, 'resuma este documento', recorder);
  assert.equal(Object.keys(result.facts).length, 1); assert.equal(result.rejected.length, 3);
  assert.equal(result.facts.F1.url, 'documento:projeto.md#trecho-1');
  assert.equal(result.document.chunks_used, 2);
});
test('zero fatos documentais válidos e cancelamento interrompem explicitamente', async () => {
  const doc = makeDocument(file(), [{text: quote}], 'UTF-8');
  const model = {complete: async () => ({text: JSON.stringify({fatos: [fact('Uma afirmação inventada que nunca esteve neste documento.')] }), usage})};
  await assert.rejects(collectDocument(doc, '', new Recorder(model, 6)), /Nenhum fato/);
  const controller = new AbortController(); controller.abort();
  await assert.rejects(collectDocument(doc, '', new Recorder(model, 6), controller.signal), /cancelada/);
});
class DocumentModel {
  inputs = []; tokens = []; bad = new Set();
  async complete(input) {
    this.inputs.push(input);
    // Tokenizador simulado conservador para português comum; não mede GGUF real.
    const count = Math.ceil(utf8(input.system + input.user).length / 2) + 64;
    this.tokens.push(count); assert.ok(count + 512 + 32 <= 4096, `Contexto simulado excessivo: ${count}`);
    let value;
    if (input.schema.properties.fatos) {
      const passage = input.user.split('TRECHO:\n')[1];
      const sentence = passage.match(/A equipe [^.]+\./)[0];
      value = {fatos: [fact(sentence), fact('Uma frase inventada sem nenhuma base no documento original.')]};
    } else if (input.schema.properties.slides) {
      value = {titulo: 'Trabalho organizado', slides: Array.from({length: 5}, (_, i) => ({tipo: i === 0 ? 'capa' : i === 4 ? 'conclusao' : 'topicos', mensagem: 'A equipe organiza cada entrega', objetivo: 'Como a equipe confere cada entrega?', fatos: [`F${Math.min(i + 1, 6)}`]}))};
    } else {
      const i = Number(input.user.match(/Escreva o slide (\d+)/)[1]), cover = i === 1;
      value = cover ? {titulo: 'Planejar ajuda a equipe', subtitulo: 'Decisões locais para organizar o trabalho.', autor: '', notas: ''} : {
        titulo: i === 5 ? 'Escolha a próxima atividade' : 'A equipe confere cada entrega',
        itens: [{rotulo: 'Escopo definido', detalhe: quote}, {rotulo: 'Revisão frequente', detalhe: 'Cada entrega recebe uma revisão antes da apresentação.'}, ...(i === 5 ? [] : [{rotulo: 'Registro disponível', detalhe: 'O grupo consulta o registro quando precisa retomar uma decisão.'}])], fontes: [`F${i}`], notas: 'Explique as condições necessárias para realizar cada atividade.'};
      if (!this.bad.has(i)) {this.bad.add(i); value.titulo = 'x'.repeat(100);}
    }
    return {text: JSON.stringify(value), usage: {...usage, input_tokens: count}};
  }
}
test('documento >30 mil caracteres → deck editável de 5 slides: 6 extrações, até 1 reparo/slide, contexto simulado limitado', async () => {
  const bytes = utf8(longDocument()), doc = await extractBytes(file('projeto.md', bytes.length), bytes), model = new DocumentModel(), progress = [], updates = [];
  assert.ok(doc.characters > 30000);
  const result = await generate({request: '', slides: 5, source: {mode: 'document', document: file('projeto.md', bytes.length)}, model,
    readDocument: async () => doc, onProgress: p => progress.push(p.stage), onDocument: d => updates.push(d)});
  assert.equal(result.calls.filter(c => c.stage === 'document_extract').length, 6);
  assert.equal(result.max_calls, 17); assert.equal(result.calls.length, 17); assert.equal(result.ir.slides.length, 5);
  assert.equal(result.diagnostics.filter(d => d.severity === 'ERRO').length, 0);
  assert.equal(result.source.rejected.length, 6); assert.equal(result.source.document.facts_used, 6);
  assert.match(model.inputs[6].user, /Limitações/); assert.match(model.inputs[6].user, /Apresente os pontos principais/);
  assert.ok(progress.includes('Lendo documento')); assert.ok(progress.includes('Extraindo fatos 2/6')); assert.ok(progress.includes('Slide 3/5'));
  assert.equal(updates.at(-1).chunks_used, 6);
  const zip = await JSZip.loadAsync(result.pptx), slides = Object.keys(zip.files).filter(n => /^ppt\/slides\/slide\d+\.xml$/.test(n));
  assert.equal(slides.length, 5); assert.match(await zip.file(slides[1]).async('string'), /<a:t>/);
  assert.ok(result.ir.slides[1].notes.includes('projeto.md'));
  const report = testData({calls: result.calls, device_start: null, device_end: null, model: {simulated: true}, status: 'success', wall_ms: result.wall_ms, slides: 5, diagnostics: result.diagnostics, source_mode: 'document', document: result.source.document});
  assert.equal(report.by_stage.document_extract.calls, 6); assert.equal(report.document.characters, doc.characters); assert.equal(report.max_calls, 17);
  await fs.mkdir('outputs/evidence', {recursive: true});
  await fs.writeFile('outputs/evidence/document-5-slides.pptx', new Uint8Array(result.pptx));
  await fs.writeFile('outputs/evidence/document-custo.json', JSON.stringify(report, null, 2));
  await fs.writeFile('outputs/evidence/document-context.json', JSON.stringify({simulated: true, characters: doc.characters, max_input_tokens: Math.max(...model.tokens), calls: model.tokens}, null, 2));
});

// PDF do próprio TCC (teste de 25/11/2026, docs/TESTE_TCC_DOCUMENTO_LONGO.md): 10 páginas reais extraídas.
const tccDoc = async () => {
  const fixture = JSON.parse(await fs.readFile(new URL('./fixtures/tcc_paginas.json', import.meta.url), 'utf8'));
  return makeDocument({name: 'tcc.pdf', bytes: 1000, mime: 'application/pdf', uri: 'file:///tcc.pdf'},
    fixture.paginas.map(p => ({text: p.text, page: p.page})), 'PDFBox', 23);
};
test('PDF: junta hifenização, tira cabeçalhos corridos e para nas referências', async () => {
  const doc = await tccDoc(), all = doc.chunks.map(c => c.text).join('\n');
  assert.doesNotMatch(all, /[￾­]/);
  assert.match(all, /depender de serviços pagos/);           // "depen￾der"
  assert.doesNotMatch(all, /T\. Barbosa/);                    // "12 T. Barbosa"
  assert.doesNotMatch(all, /apresentações editáveis \d+/);    // "SlideDSL: geração local ... 13"
  assert.doesNotMatch(all, /arxiv\.org|doi\.org/i);           // página 23 = referências
  assert.ok(doc.chunks.every(c => c.page < 22), 'nada depois de "Referências"');
});
test('PDF: seções numeradas viram seções de nível 1, com o resumo à parte', async () => {
  const doc = await tccDoc();
  const sections = [...new Set(doc.chunks.map(c => c.section).filter(Boolean))];
  assert.equal(sections[0], 'Resumo');
  assert.ok(sections.includes('1 Introdução') && sections.includes('6 Resultados') && sections.includes('8 Conclusão'), sections.join(' | '));
  assert.ok(doc.chunks.some(c => c.heading.startsWith('6.7') && c.section === '6 Resultados'));
  assert.ok(!sections.some(s => /Barbosa|Referências/.test(s)));
});
test('PDF: pedido genérico lê o resumo e espalha pelas seções; pedido de banca cobre resultados e limitações', async () => {
  const doc = await tccDoc();
  const generic = retrieveDocument(doc, '');
  assert.equal(generic.length, 6);
  assert.equal(generic[0].section, 'Resumo');
  assert.ok(new Set(generic.map(c => c.section)).size >= 5);
  const banca = retrieveDocument(doc, 'Apresente este TCC para a banca: o problema, a proposta do SlideDSL, a versão no celular, os principais resultados dos testes e as limitações do trabalho.');
  const secs = banca.map(c => c.section);
  assert.equal(secs[0], 'Resumo');
  assert.ok(secs.includes('6 Resultados'), secs.join(' | '));
  assert.ok(secs.includes('7 Discussão e limitações'), secs.join(' | '));
  assert.ok(Math.max(...[...new Set(secs)].map(s => secs.filter(x => x === s).length)) <= 2);
});
test('TXT e MD não passam pela detecção de seções do PDF (bancadas inalteradas)', async () => {
  const doc = makeDocument(file('agua.txt'), [{text: '1 Evaporação\n\nO sol aquece a água dos rios.\n\nReferências\n\nAutor, 2020.'}], 'UTF-8');
  assert.ok(doc.chunks.every(c => c.section === undefined));
  assert.match(doc.chunks.map(c => c.text).join('\n'), /Autor, 2020/);
});
