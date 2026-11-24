// Fotos livres para slides "imagem" (opcional; precisa de internet). Mesmas fontes e licenças do PC
// (src/slidedsl/media.py search_provider): Openverse (CC BY, BY-SA, CC0, domínio público) e NASA.
// O Wikimedia Commons fica de fora: recusa (403) clientes sem contato no User-Agent.
// A foto entra no PowerPoint como data URI e o crédito (autor · licença) vai no slide e nas notas.
import type {AltoDeck, Images} from '@slidedsl/core';

export interface ImageCandidate {provider: 'openverse' | 'nasa'; title: string; url: string; page: string; author: string; license: string; license_url: string}
export type FetchJson = (url: string, signal?: AbortSignal) => Promise<unknown>;
export type FetchBytes = (url: string, signal?: AbortSignal) => Promise<Uint8Array>;
export interface ImageSource {fetchJson: FetchJson; fetchBytes: FetchBytes}
export interface DeckImages {info: Images; data: Record<string, string>; log: {slide: number; query: string; result: string}[]}

const MAX_BYTES = 8 * 1024 * 1024;
const SEARCH_MS = 15000, DOWNLOAD_MS = 20000, SLIDE_MS = 60000;

/** Sinal que aborta após `ms` ou quando o externo abortar (sem AbortSignal.any/timeout, ausentes no Hermes). */
function deadline(ms: number, outer?: AbortSignal): {signal: AbortSignal; done: () => void} {
  const controller = new AbortController(), stop = () => controller.abort();
  const timer = setTimeout(stop, ms);
  outer?.addEventListener('abort', stop);
  if (outer?.aborted) stop();
  return {signal: controller.signal, done: () => { clearTimeout(timer); outer?.removeEventListener('abort', stop); }};
}
async function limited<T>(ms: number, outer: AbortSignal | undefined, run: (signal: AbortSignal) => Promise<T>): Promise<T> {
  const d = deadline(ms, outer);
  try {
    return await Promise.race([run(d.signal), new Promise<never>((_, reject) =>
      d.signal.addEventListener('abort', () => reject(Error('tempo esgotado')), {once: true}))]);
  } finally { d.done(); }
}
const NASA_TERMS = 'https://www.nasa.gov/nasa-brand-center/images-and-media/';
const LICENSES: Record<string, string> = {by: 'CC BY', 'by-sa': 'CC BY-SA', cc0: 'CC0', pdm: 'Domínio público'};
const qs = (params: Record<string, string | number>) => Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');

export async function searchImages(query: string, fetchJson: FetchJson, signal?: AbortSignal): Promise<ImageCandidate[]> {
  const q = query.trim().slice(0, 200);
  if (!q) return [];
  const found: ImageCandidate[] = [];
  const openverse = limited(SEARCH_MS, signal, s => fetchJson('https://api.openverse.org/v1/images/?' + qs({q, page_size: 8, license: 'by,by-sa,cc0,pdm', extension: 'jpg,png', mature: 'false'}), s))
    .then((data: any) => {
      for (const i of data?.results ?? []) if (LICENSES[i.license] && i.url) found.push({provider: 'openverse', title: String(i.title ?? ''),
        url: i.url, page: i.foreign_landing_url ?? '', author: String(i.creator ?? ''), license: LICENSES[i.license], license_url: i.license_url ?? ''});
    }).catch(() => {});
  const nasa = limited(SEARCH_MS, signal, s => fetchJson('https://images-api.nasa.gov/search?' + qs({q, media_type: 'image', page_size: 8}), s))
    .then((data: any) => {
      for (const entry of (data?.collection?.items ?? []).slice(0, 8)) {
        const i = entry.data?.[0], link = (entry.links ?? []).find((l: any) => l.render === 'image')?.href;
        if (i && link) found.push({provider: 'nasa', title: String(i.title ?? ''), url: link, page: `https://images.nasa.gov/details/${i.nasa_id}`,
          author: String(i.photographer ?? i.center ?? 'NASA'), license: 'NASA (uso educacional)', license_url: NASA_TERMS});
      }
    }).catch(() => {});
  await Promise.all([openverse, nasa]);
  // Título que contém palavras da busca primeiro; Openverse antes da NASA no empate.
  const words = q.toLowerCase().split(/\s+/).filter(w => w.length > 2);
  const score = (c: ImageCandidate) => words.filter(w => c.title.toLowerCase().includes(w)).length * 2 + (c.provider === 'openverse' ? 1 : 0);
  return found.sort((a, b) => score(b) - score(a));
}

/** Tipo e dimensões pelo cabeçalho (sem decodificar a imagem). */
export function imageSize(bytes: Uint8Array): {mime: 'image/png' | 'image/jpeg'; width: number; height: number} | null {
  if (bytes.length > 24 && bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4e && bytes[3] === 0x47) {
    const v = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    return {mime: 'image/png', width: v.getUint32(16), height: v.getUint32(20)};
  }
  if (bytes.length > 4 && bytes[0] === 0xff && bytes[1] === 0xd8) {
    let i = 2;
    while (i + 9 < bytes.length) {
      if (bytes[i] !== 0xff) { i++; continue; }
      const marker = bytes[i + 1], len = (bytes[i + 2] << 8) | bytes[i + 3];
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return {mime: 'image/jpeg', height: (bytes[i + 5] << 8) | bytes[i + 6], width: (bytes[i + 7] << 8) | bytes[i + 8]};
      }
      i += 2 + len;
    }
  }
  return null;
}

const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
export function base64(bytes: Uint8Array): string {
  let out = '';
  for (let i = 0; i < bytes.length; i += 3) {
    const n = (bytes[i] << 16) | ((bytes[i + 1] ?? 0) << 8) | (bytes[i + 2] ?? 0);
    out += B64[(n >> 18) & 63] + B64[(n >> 12) & 63] + (i + 1 < bytes.length ? B64[(n >> 6) & 63] : '=') + (i + 2 < bytes.length ? B64[n & 63] : '=');
  }
  return out;
}

/** Para cada slide "imagem" com busca: baixa a primeira foto válida (≥ 600 px) e liga ao slide (image_file).
 * Sem foto, o slide fica sem image_file e o compilador usa o layout de cartões (como no PC). Altera o deck. */
export async function resolveImages(deck: AltoDeck, source: ImageSource, signal?: AbortSignal,
    onProgress?: (stage: string) => void): Promise<DeckImages> {
  const result: DeckImages = {info: {}, data: {}, log: []};
  for (const [k, slide] of deck.slides.entries()) {
    if (slide.kind !== 'imagem' || !slide.image_query || slide.image_file) continue;
    onProgress?.(`Buscando foto do slide ${k + 1}`);
    let outcome = 'nenhuma foto livre encontrada';
    const slideTime = deadline(SLIDE_MS, signal);  // no máximo 1 min por slide, para não travar a geração
    for (const c of (await searchImages(slide.image_query, source.fetchJson, slideTime.signal)).slice(0, 4)) {
      if (slideTime.signal.aborted) { outcome = 'tempo esgotado na busca da foto'; break; }
      try {
        const bytes = await limited(DOWNLOAD_MS, slideTime.signal, s => source.fetchBytes(c.url, s));
        const size = bytes.length <= MAX_BYTES ? imageSize(bytes) : null;
        if (!size || Math.max(size.width, size.height) < 600) continue;
        const file = `foto_${k + 1}.${size.mime === 'image/png' ? 'png' : 'jpg'}`;
        result.info[file] = {width: size.width, height: size.height, metadata: {author: c.author, license: c.license,
          license_url: c.license_url, page: c.page, attribution: `${c.title} — ${c.author} (${c.provider})`}};
        result.data[file] = `data:${size.mime};base64,${base64(bytes)}`;
        slide.image_file = file;
        outcome = `${c.provider}: ${c.title}`.slice(0, 120);
        break;
      } catch { /* tenta a próxima */ }
    }
    slideTime.done();
    if (signal?.aborted) throw Error('Operação cancelada.');
    result.log.push({slide: k + 1, query: slide.image_query, result: outcome});
  }
  return result;
}
