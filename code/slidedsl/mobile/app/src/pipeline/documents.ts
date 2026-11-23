import JSZip from 'jszip';
export const MAX_DOCUMENT_BYTES = 10 * 1024 * 1024;
export const MAX_DOCUMENT_CHARS = 200_000;
export const MAX_EXTRACT_CALLS = 6;
export type DocumentKind = 'txt' | 'md' | 'docx' | 'pdf';
export interface DocumentFile {uri: string; name: string; bytes: number; mime: string}
export interface DocumentPart {text: string; heading?: string; headingOnly?: boolean; page?: number}
export interface DocumentChunk {id: string; passage: number; text: string; heading: string; page: number | null}
export interface DocumentText extends DocumentFile {kind: DocumentKind; characters: number; pages: number | null; encoding: string; chunks: DocumentChunk[]}
export const DOCUMENT_MIMES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown', 'text/x-markdown'];
export function documentKind(name: string, mime = ''): DocumentKind {
  const suffix = name.split('.').pop()?.toLowerCase();
  if (['txt', 'md', 'docx', 'pdf'].includes(suffix ?? '')) return suffix as DocumentKind;
  const i = DOCUMENT_MIMES.indexOf(mime.toLowerCase());
  if (i >= 0) return (['pdf', 'docx', 'txt', 'md', 'md'] as const)[i];
  throw Error('Formato não suportado. Escolha PDF, DOCX, TXT ou MD.');
}
export function validateDocument(file: DocumentFile): DocumentKind {
  if (!Number.isFinite(file.bytes) || file.bytes < 0 || file.bytes > MAX_DOCUMENT_BYTES) throw Error('O documento deve ter no máximo 10 MB.');
  return documentKind(file.name, file.mime);
}
// Hermes não precisa de TextDecoder. UTF-8 estrito; sequências inválidas usam Latin-1.
export function decodeText(bytes: Uint8Array): {text: string; encoding: string} {
  let text = '', valid = true;
  for (let i = 0; i < bytes.length;) {
    const a = bytes[i++]; let cp = a, count = 0, min = 0;
    if (a >= 0xc2 && a <= 0xdf) {cp = a & 31; count = 1; min = 0x80;}
    else if (a >= 0xe0 && a <= 0xef) {cp = a & 15; count = 2; min = 0x800;}
    else if (a >= 0xf0 && a <= 0xf4) {cp = a & 7; count = 3; min = 0x10000;}
    else if (a > 0x7f) {valid = false; break;}
    if (i + count > bytes.length) {valid = false; break;}
    for (let j = 0; j < count; j++) {const b = bytes[i++]; if ((b & 0xc0) !== 0x80) {valid = false; break;} cp = (cp << 6) | (b & 63);}
    if (!valid || cp < min || cp > 0x10ffff || (cp >= 0xd800 && cp <= 0xdfff)) {valid = false; break;}
    text += String.fromCodePoint(cp);
  }
  if (!valid) {text = ''; for (const b of bytes) text += String.fromCharCode(b);}
  return {text: text.replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n'), encoding: valid ? 'UTF-8' : 'Latin-1'};
}
function entities(text: string): string {
  return text.replace(/&([^;]+);/g, (_, code: string) => {
    const known: Record<string, string> = {amp: '&', lt: '<', gt: '>', quot: '"', apos: "'"};
    if (code in known) return known[code];
    const n = code.startsWith('#x') ? parseInt(code.slice(2), 16) : code.startsWith('#') ? Number(code.slice(1)) : NaN;
    if (!Number.isInteger(n) || n <= 0 || n > 0x10ffff || (n >= 0xd800 && n <= 0xdfff)) throw Error('Entidade XML inválida no DOCX.');
    return String.fromCodePoint(n);
  });
}
// Leitor de eventos XML restrito: não resolve DTD/entidades externas nem executa campos.
function xmlEvents(xml: string, visit: (name: string, closing: boolean, attrs: Record<string, string>, text?: string) => void) {
  if (/<!DOCTYPE|<!ENTITY/i.test(xml)) throw Error('DOCX com DTD não é suportado.');
  const stack: string[] = [];
  const tokens = xml.match(/<!--[\s\S]*?-->|<\?[\s\S]*?\?>|<!\[CDATA\[[\s\S]*?\]\]>|<[^>"']*(?:(?:"[^"]*"|'[^']*')[^>"']*)*>|[^<]+/g) ?? [];
  if (tokens.join('') !== xml) throw Error('XML inválido no DOCX.');
  for (const token of tokens) {
    if (token.startsWith('<!--') || token.startsWith('<?')) continue;
    if (!token.startsWith('<') || token.startsWith('<![CDATA[')) {visit('', false, {}, token.startsWith('<![CDATA[') ? token.slice(9, -3) : entities(token)); continue;}
    const m = token.match(/^<(\/)?([\w:.-]+)([\s\S]*?)\/?\s*>$/);
    if (!m) throw Error('XML inválido no DOCX.');
    const full = m[2], name = full.split(':').pop()!, closing = !!m[1], self = /\/\s*>$/.test(token);
    const attrs: Record<string, string> = {};
    for (const a of m[3].matchAll(/([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)) attrs[a[1].split(':').pop()!] = entities(a[2] ?? a[3]);
    if (closing) {if (stack.pop() !== full) throw Error('XML inválido no DOCX.');}
    else if (!self) stack.push(full);
    visit(name, closing, attrs);
    if (self) visit(name, true, {});
  }
  if (stack.length) throw Error('XML incompleto no DOCX.');
}
async function boundedXml(zip: JSZip, path: string, optional = false): Promise<string> {
  const entry = zip.file(path);
  if (!entry) {if (optional) return ''; throw Error('DOCX inválido: word/document.xml ausente.');}
  const max = 4 * 1024 * 1024;
  const data = await new Promise<Uint8Array>((resolve, reject) => {
    const chunks: Uint8Array[] = []; let size = 0, failed = false;
    // API pública documentada, ausente nas declarações TS do JSZip 3.10.1.
    interface XmlStream {on(event: string, cb: (...args: any[]) => void): XmlStream; pause(): XmlStream; resume(): XmlStream}
    const stream = (entry as typeof entry & {internalStream(type: 'uint8array'): XmlStream}).internalStream('uint8array');
    stream.on('data', (chunk: Uint8Array) => {
      size += chunk.length;
      if (size > max) {failed = true; stream.pause(); reject(Error('XML do DOCX excede o limite de 4 MB.'));}
      else chunks.push(chunk);
    }).on('error', reject).on('end', () => {
      if (failed) return;
      const out = new Uint8Array(size); let offset = 0;
      for (const chunk of chunks) {out.set(chunk, offset); offset += chunk.length;} resolve(out);
    }).resume();
  });
  const decoded = decodeText(data);
  if (decoded.encoding !== 'UTF-8') throw Error('O XML do DOCX deve usar UTF-8.');
  return decoded.text;
}
export async function docxParts(bytes: Uint8Array): Promise<DocumentPart[]> {
  let zip: JSZip;
  try {zip = await JSZip.loadAsync(bytes);} catch {throw Error('DOCX inválido ou corrompido.');}
  const styles = new Map<string, string>(); let styleId = '';
  xmlEvents(await boundedXml(zip, 'word/styles.xml', true), (name, closing, attrs) => {
    if (name === 'style') styleId = closing ? '' : attrs.styleId ?? '';
    if (name === 'name' && !closing && styleId) styles.set(styleId, attrs.val ?? '');
  });
  const parts: DocumentPart[] = []; let paragraph = '', style = '', inP = false, inText = false, heading = '', characters = 0;
  xmlEvents(await boundedXml(zip, 'word/document.xml'), (name, closing, attrs, text) => {
    if (text !== undefined) {if (inP && inText) paragraph += text; return;}
    if (name === 'p' && !closing) {inP = true; paragraph = ''; style = '';}
    if (name === 'pStyle' && !closing) style = attrs.val ?? '';
    if (name === 't') inText = !closing;
    if (inP && !closing && (name === 'tab' || name === 'br' || name === 'cr')) paragraph += name === 'tab' ? '\t' : '\n';
    if (name === 'p' && closing) {
      inP = false;
      if (paragraph.trim()) {
        characters += paragraph.length;
        if (characters > MAX_DOCUMENT_CHARS) throw Error('O documento excede 200 mil caracteres extraídos.');
        const headingOnly = /^(heading|t[ií]tulo|title)(?:\s*\d+)?$/i.test(style) || /^(heading|t[ií]tulo|title)(?:\s*\d+)?$/i.test(styles.get(style) ?? '');
        if (headingOnly) heading = paragraph.trim().slice(0, 160);
        parts.push({text: paragraph, heading, headingOnly});
      }
    }
  });
  return parts;
}
export function makeDocument(file: DocumentFile, parts: DocumentPart[], encoding: string, pages: number | null = null): DocumentText {
  const kind = validateDocument(file), chunks: DocumentChunk[] = [];
  const characters = parts.reduce((n, p) => n + p.text.length, 0);
  if (characters > MAX_DOCUMENT_CHARS) throw Error('O documento excede 200 mil caracteres extraídos.');
  let heading = '';
  for (const part of parts) {
    if (part.heading !== undefined) heading = part.heading;
    if (part.headingOnly) continue;
    for (const paragraph of part.text.split(/\n\s*\n/)) {
      // Markdown e títulos do Word viram metadados, nunca fatos isolados.
      let lines: string[] = [];
      const append = () => {
        const body = lines.join('\n').trim(); lines = [];
        for (let offset = 0; offset < body.length; offset += 900) {
          const text = body.slice(offset, offset + 900).trim();
          if (text) {const passage = chunks.length + 1; chunks.push({id: `c${passage}`, passage, text, heading: heading.slice(0, 160), page: part.page ?? null});}
        }
      };
      for (const line of paragraph.split('\n')) {
        const match = line.match(/^#{1,6}\s+(.+)/);
        if (match) {append(); heading = match[1].trim();} else lines.push(line);
      }
      append();
    }
  }
  if (!chunks.length) throw Error(kind === 'pdf' ? 'PDF sem texto selecionável' : 'Documento sem texto extraível.');
  return {...file, kind, characters, pages, encoding, chunks};
}
export async function extractBytes(file: DocumentFile, bytes: Uint8Array): Promise<DocumentText> {
  const kind = validateDocument({...file, bytes: Math.max(file.bytes, bytes.length)});
  if (kind === 'pdf') throw Error('A extração de PDF requer o módulo Android.');
  if (kind === 'docx') return makeDocument(file, await docxParts(bytes), 'UTF-8');
  const decoded = decodeText(bytes);
  return makeDocument(file, [{text: decoded.text}], decoded.encoding);
}
const normalized = (text: string) => text.toLowerCase().normalize('NFKD').replace(/\p{M}/gu, '');
const tokens = (text: string) => normalized(text).match(/[a-z0-9]{3,}/g) ?? [];
export function genericDocumentRequest(request: string): boolean {
  const s = normalized(request).trim().replace(/[.!?]+$/, '');
  return !s || /^(?:resuma|apresente|explique|sintetize)(?:\s+(?:este|esse|o|um))?\s+(?:documento|arquivo)(?:\s+.*)?$/.test(s) || s.startsWith('apresente os pontos principais do documento ');
}
export function retrieveDocument(doc: DocumentText, request: string, limit = MAX_EXTRACT_CALLS): DocumentChunk[] {
  const chunks = doc.chunks;
  if (genericDocumentRequest(request)) {
    const sections = new Map<string, DocumentChunk[]>();
    for (const c of chunks) {const key = c.heading || (c.page ? `Página ${c.page}` : 'Documento'); if (!sections.has(key)) sections.set(key, []); sections.get(key)!.push(c);}
    const groups = [...sections.values()], selected: DocumentChunk[] = [];
    // Escolhe seções distribuídas até o fim; depois distribui amostras dentro delas.
    const chosen = groups.length <= limit ? groups : Array.from({length: limit}, (_, i) => groups[Math.round(i * (groups.length - 1) / (limit - 1 || 1))]);
    for (let round = 0; selected.length < Math.min(limit, chunks.length); round++) {
      let added = false;
      for (const group of chosen) {
        const available = group.filter(c => !selected.includes(c));
        if (!available.length) continue;
        const candidate = round === 0 ? available[0] : round === 1 ? available[available.length - 1] : available[Math.floor(available.length / 2)];
        selected.push(candidate); added = true; if (selected.length === limit) break;
      }
      if (!added) break;
    }
    return selected.sort((a, b) => a.passage - b.passage);
  }
  const words = new Set(tokens(request)), frequency = new Map<string, number>();
  for (const c of chunks) for (const word of new Set(tokens(c.text))) frequency.set(word, (frequency.get(word) ?? 0) + 1);
  return chunks.map(c => {
    const counts = new Map<string, number>(); for (const w of tokens(c.text)) counts.set(w, (counts.get(w) ?? 0) + 1);
    const score = [...words].reduce((n, w) => n + Math.log(1 + chunks.length / (1 + (frequency.get(w) ?? 0))) * Math.min(3, counts.get(w) ?? 0), 0);
    return {c, score};
  }).filter(x => x.score > 0).sort((a, b) => b.score - a.score || a.c.passage - b.c.passage).slice(0, limit).map(x => x.c);
}
export function documentMetadata(doc: DocumentText) {
  return {name: doc.name, type: doc.kind, mime: doc.mime, bytes: doc.bytes, characters: doc.characters, pages: doc.pages, encoding: doc.encoding, chunks_total: doc.chunks.length};
}
