/**
 * Escrita dos slides em SlideDSL Alto sob gramática (modo `gramatica`), alternativa ao JSON Schema.
 *
 * A gramática GBNF de cada tipo é derivada do MESMO schema JSON do slide (prompts.json): mesmos campos,
 * mesmos limites folgados de tamanho e de quantidade, mesmos IDs de fatos. Só muda a sintaxe, como no
 * teste de mecanismo de restrição do PC (gramática −32% tokens de saída e −26% tempo, mesma validade).
 * O bloco Alto lido volta ao objeto do JSON, e o app segue igual (schemaErrors, jsonToSlide, compilador).
 * A ordem dos campos segue src/slidedsl/grammar/slidedsl_alto.lark.
 */
import type {JsonSchema} from './types.js';

type Field =
  | {kind: 'str'; key: string; word: string}
  | {kind: 'items'; key: string; word: 'item' | 'valor' | 'marco' | 'barra'}
  | {kind: 'sides'; key: string}
  | {kind: 'sources'; key: string}
  | {kind: 'notes'; key: string};

const SINGLE: Record<string, string> = {titulo: 'titulo', subtitulo: 'subtitulo', autor: 'autor',
  texto: 'texto', unidade: 'unidade', legenda: 'legenda'};
// Ordem da gramática Alto por tipo (somente os tipos que o app gera).
const ORDER: Record<string, string[]> = {
  capa: ['titulo', 'subtitulo', 'autor', 'notas'],
  secao: ['titulo', 'subtitulo', 'notas'],
  topicos: ['titulo', 'itens', 'fontes', 'notas'],
  etapas: ['titulo', 'itens', 'fontes', 'notas'],
  conclusao: ['titulo', 'itens', 'fontes', 'notas'],
  numeros: ['titulo', 'valores', 'fontes', 'notas'],
  comparacao: ['titulo', 'lados', 'fontes', 'notas'],
  linha_do_tempo: ['titulo', 'marcos', 'fontes', 'notas'],
  citacao: ['texto', 'autor', 'fontes', 'notas'],
  grafico: ['titulo', 'unidade', 'barras', 'fontes', 'notas'],
};
const ITEM_WORD: Record<string, 'item' | 'valor' | 'marco' | 'barra'> =
  {itens: 'item', valores: 'valor', marcos: 'marco', barras: 'barra'};
// Campos de cada registro, na ordem posicional da Alto.
const RECORD_KEYS: Record<string, string[]> = {item: ['rotulo', 'detalhe'], valor: ['valor', 'legenda'],
  marco: ['data', 'rotulo', 'detalhe'], barra: ['rotulo', 'valor']};

export function altoKinds(): string[] { return Object.keys(ORDER); }

/** Limites que a validação A005 do compilador cobra (src/slidedsl/alto.py, validate_alto). */
export const COMPILER_LIMITS = {
  titulo: 80, subtitulo: 140, autor: 80, texto: 260, unidade: 40, notas: 1500,
  item: {rotulo: 48, detalhe: 170}, valor: {valor: 14, legenda: 170}, lado: {nome: 40, rotulo: 48, detalhe: 80},
  marco: {data: 16, rotulo: 36, detalhe: 90}, barra: {rotulo: 24},
} as const;

/** Cópia do schema com o maxLength de cada campo reduzido ao limite do compilador (modo gramatica_limites).
 * Ataca a falha mais comum (A005, texto longo demais) na própria decodificação; o custo é o texto poder
 * ser cortado no limite, o que a bancada mede. */
export function withCompilerLimits(schema: JsonSchema): JsonSchema {
  const out = JSON.parse(JSON.stringify(schema)) as JsonSchema, p = props(out);
  const cap = (s: JsonSchema | undefined, limit: number) => {
    if (s && s.type === 'string') s.maxLength = Math.min(num(s.maxLength, limit), limit);
  };
  for (const key of ['titulo', 'subtitulo', 'autor', 'texto', 'unidade', 'notas'] as const) cap(p[key], COMPILER_LIMITS[key]);
  const recs: [string, Record<string, number>][] = [['itens', COMPILER_LIMITS.item], ['valores', COMPILER_LIMITS.valor],
    ['marcos', COMPILER_LIMITS.marco], ['barras', COMPILER_LIMITS.barra]];
  for (const [key, limits] of recs) {
    const rp = props((p[key]?.items ?? {}) as JsonSchema);
    for (const [k, v] of Object.entries(limits)) cap(rp[k], v);
  }
  const side = props((p.lados?.items ?? {}) as JsonSchema);
  if (p.lados) {
    cap(side.nome, COMPILER_LIMITS.lado.nome);
    const ip = props(((side.itens as JsonSchema)?.items ?? {}) as JsonSchema);
    cap(ip.rotulo, COMPILER_LIMITS.lado.rotulo); cap(ip.detalhe, COMPILER_LIMITS.lado.detalhe);
  }
  return out;
}

function fields(kind: string): Field[] {
  const order = ORDER[kind];
  if (!order) throw Error(`Tipo sem gramática Alto no app: ${kind}`);
  return order.map((key): Field => key in SINGLE ? {kind: 'str', key, word: SINGLE[key]}
    : key in ITEM_WORD ? {kind: 'items', key, word: ITEM_WORD[key]}
    : key === 'lados' ? {kind: 'sides', key} : key === 'fontes' ? {kind: 'sources', key} : {kind: 'notes', key});
}

const props = (s: JsonSchema) => (s.properties ?? {}) as Record<string, JsonSchema>;
const required = (s: JsonSchema) => new Set((s.required ?? []) as string[]);
const num = (v: unknown, d: number) => (v === undefined ? d : Number(v));

/** Gramática GBNF de UM bloco de slide; o bloco termina no `}` final (geração para ali). */
export function slideGrammar(kind: string, schema: JsonSchema): string {
  const rules = new Map<string, string>();
  const strRule = (s: JsonSchema | undefined) => {
    const lo = num(s?.minLength, 0), hi = num(s?.maxLength, 600);
    const name = `s-${lo}-${hi}`;
    rules.set(name, `"\\"" chr{${lo},${hi}} "\\""`);
    return name;
  };
  const p = props(schema), req = required(schema), parts: string[] = [];
  for (const f of fields(kind)) {
    const sub = p[f.key];
    if (!sub) continue;
    if (f.kind === 'str' || f.kind === 'notes') {
      const word = f.kind === 'notes' ? 'notas' : f.word;
      const line = `ws "${word}" ws ${strRule(sub)}`;
      // Chave obrigatória no JSON = palavra obrigatória aqui (o texto pode ser vazio se o JSON aceita "").
      // Assim o modo gramática não ganha tokens só por poder omitir campos, como `notas`.
      parts.push(req.has(f.key) ? line : `(${line})?`);
    } else if (f.kind === 'items') {
      const rec = sub.items as JsonSchema, rp = props(rec), rreq = required(rec);
      const args = RECORD_KEYS[f.word].map(k => {
        const s = rp[k];
        if (!s) return '';
        const v = s.type === 'number' ? 'numero' : strRule(s);
        const optional = s.type !== 'number' && !(rreq.has(k) && num(s.minLength, 0) > 0);
        return optional ? `(ws ${v})?` : `ws ${v}`;
      }).filter(Boolean).join(' ');
      rules.set(`r-${f.word}`, `ws "${f.word}" ${args}`);
      parts.push(`r-${f.word}{${num(sub.minItems, 1)},${num(sub.maxItems, 8)}}`);
    } else if (f.kind === 'sides') {
      const side = sub.items as JsonSchema, sp = props(side), items = sp.itens.items as JsonSchema;
      const ip = props(items);
      rules.set('r-side-item', `ws "item" ws ${strRule(ip.rotulo)} ws ${strRule(ip.detalhe)}`);
      rules.set('r-lado', `ws "lado" ws ${strRule(sp.nome)} ws "{" r-side-item{${num((sp.itens as JsonSchema).minItems, 1)},${num((sp.itens as JsonSchema).maxItems, 4)}} ws "}"`);
      parts.push(`r-lado{${num(sub.minItems, 2)},${num(sub.maxItems, 2)}}`);
    } else if (f.kind === 'sources') {
      const ids = ((sub.items as JsonSchema)?.enum ?? []) as string[];
      if (!ids.length || ids[0] === '__FACT_IDS__') continue;
      rules.set('fato', ids.map(id => JSON.stringify(id)).join(' | '));
      const max = num(sub.maxItems, 4);
      parts.push(`(ws "fontes" ws fato (ws "," ws fato){0,${Math.max(0, max - 1)}})?`);
    }
  }
  rules.set('numero', '[0-9]{1,12} ("." [0-9]{1,6})?');
  rules.set('chr', '[^"\\\\\\x00-\\x1F] | "\\\\" ["\\\\/bfnrt]');
  rules.set('ws', '[ \\t\\n]{0,20}');
  const root = `root ::= ws "${kind}" ws "{" ${parts.join(' ')} ws "}"`;
  return [root, ...[...rules].map(([k, v]) => `${k} ::= ${v}`)].join('\n');
}

/** Caminhos de texto que chegaram exatamente ao maxLength do schema: com o limite na gramática, a
 * decodificação fecha a string no limite, e o texto sai cortado no meio (bancada de 24/11: 31 de 677 campos). */
export function truncatedPaths(data: unknown, schema: JsonSchema, path = ''): {path: string; limit: number}[] {
  if (schema.type === 'string' && typeof data === 'string') {
    const limit = num(schema.maxLength, Infinity);
    return Array.from(data).length >= limit ? [{path, limit}] : [];
  }
  if (schema.type === 'array' && Array.isArray(data) && schema.items)
    return data.flatMap((v, i) => truncatedPaths(v, schema.items as JsonSchema, `${path}.${i}`));
  if (schema.type === 'object' && data && typeof data === 'object')
    return Object.entries(props(schema)).flatMap(([k, s]) =>
      k in (data as Record<string, unknown>) ? truncatedPaths((data as Record<string, unknown>)[k], s, path ? `${path}.${k}` : k) : []);
  return [];
}

// ---------------------------------------------------------------------------
// Leitura do bloco Alto

type Tok = {t: 'word' | 'str' | 'num' | 'fact' | 'sym'; v: string};

function tokenize(text: string): Tok[] {
  const out: Tok[] = [];
  const re = /\s+|\/\/[^\n]*|("(?:[^"\\]|\\.)*")|(F[0-9]+)(?![\w])|([0-9]+(?:\.[0-9]+)?)(?![\w])|([A-Za-z_][\w]*)|([{},])/gy;
  let m: RegExpExecArray | null, pos = 0;
  while (pos < text.length) {
    re.lastIndex = pos;
    m = re.exec(text);
    if (!m || m.index !== pos) throw Error(`Sintaxe inválida na SlideDSL Alto perto de: ${text.slice(pos, pos + 20)}`);
    pos = re.lastIndex;
    if (m[1] !== undefined) out.push({t: 'str', v: JSON.parse(m[1]) as string});
    else if (m[2] !== undefined) out.push({t: 'fact', v: m[2]});
    else if (m[3] !== undefined) out.push({t: 'num', v: m[3]});
    else if (m[4] !== undefined) out.push({t: 'word', v: m[4]});
    else if (m[5] !== undefined) out.push({t: 'sym', v: m[5]});
  }
  return out;
}

/** Recorta o primeiro bloco `kind { ... }` (tolera texto antes/depois, como o parser Python). */
export function extractBlock(raw: string, kind: string): string {
  const text = raw.replace(/^```\w*|```$/gm, '').trim();
  const start = text.search(new RegExp(`(^|[^\\w])${kind}\\s*\\{`));
  if (start < 0) throw Error(`Bloco ${kind} não encontrado na resposta.`);
  const from = text.indexOf(kind, start);
  let depth = 0, inString = false, escape = false;
  for (let k = from; k < text.length; k++) {
    const c = text[k];
    if (inString) { escape = c === '\\' && !escape; if (c === '"' && !escape) inString = false; continue; }
    if (c === '"') inString = true;
    else if (c === '{') depth++;
    else if (c === '}' && --depth === 0) return text.slice(from, k + 1);
  }
  return text.slice(from);
}

/** Bloco Alto de um slide → objeto no formato do schema JSON (campos ausentes viram "" ou []). */
export function altoToJson(kind: string, raw: string, schema: JsonSchema): Record<string, unknown> {
  const toks = tokenize(extractBlock(raw, kind));
  let i = 0;
  const peek = () => toks[i], fail = (what: string): never => {
    const t = toks[i];
    throw Error(`Sintaxe inválida na SlideDSL Alto: esperado ${what}, encontrado ${t ? JSON.stringify(t.v) : 'fim'}.`);
  };
  const take = (t: Tok['t'], v?: string) => {
    const tok = toks[i];
    if (!tok || tok.t !== t || (v !== undefined && tok.v !== v)) fail(v ?? t);
    i++;
    return tok.v;
  };
  const isWord = (v: string) => peek()?.t === 'word' && peek().v === v;
  take('word', kind); take('sym', '{');
  const out: Record<string, unknown> = {};
  const p = props(schema);
  for (const f of fields(kind)) {
    if (f.kind === 'str' || f.kind === 'notes') {
      const word = f.kind === 'notes' ? 'notas' : f.word;
      if (isWord(word)) { i++; out[f.key] = take('str'); }
    } else if (f.kind === 'items') {
      const keys = RECORD_KEYS[f.word], list: Record<string, unknown>[] = [];
      while (isWord(f.word)) {
        i++;
        const rec: Record<string, unknown> = {};
        keys.forEach((k, n) => {
          if (f.word === 'barra' && k === 'valor') rec[k] = Number(take('num'));
          else if (peek()?.t === 'str') rec[k] = take('str');
          else if (n === 0 || (f.word !== 'marco' && k !== 'detalhe')) fail(`texto (${k})`);
        });
        list.push(rec);
      }
      out[f.key] = list;
    } else if (f.kind === 'sides') {
      const sides: Record<string, unknown>[] = [];
      while (isWord('lado')) {
        i++;
        const nome = take('str'); take('sym', '{');
        const itens: Record<string, unknown>[] = [];
        while (isWord('item')) { i++; const rotulo = take('str'); itens.push(peek()?.t === 'str' ? {rotulo, detalhe: take('str')} : {rotulo}); }
        take('sym', '}');
        sides.push({nome, itens});
      }
      out[f.key] = sides;
    } else if (f.kind === 'sources') {
      const ids: string[] = [];
      if (isWord('fontes')) {
        i++;
        const ref = () => { const t = peek(); if (t?.t === 'fact' || t?.t === 'str') { i++; ids.push(t.v); } else fail('fonte'); };
        ref();
        while (peek()?.t === 'sym' && peek().v === ',') { i++; ref(); }
      }
      out[f.key] = ids;
    }
  }
  take('sym', '}');
  if (i !== toks.length) fail('fim do bloco');
  // Mesmo formato do JSON: obrigatórios aceitos vazios ficam "" (texto) ou [] (lista).
  for (const key of required(schema)) {
    if (key in out) continue;
    const s = p[key];
    if (s?.type === 'string' && num(s.minLength, 0) === 0) out[key] = '';
    else if (s?.type === 'array' && num(s.minItems, 0) === 0) out[key] = [];
  }
  for (const rec of (out.marcos as Record<string, unknown>[] | undefined) ?? []) rec.detalhe ??= '';
  return out;
}

const EXAMPLE_VALUES: Record<string, string> = {
  titulo: 'Afirmação curta do slide', subtitulo: 'Promessa da apresentação', autor: 'Quem disse',
  texto: 'Frase literal do fato', unidade: 'unidade da medida', notas: 'Duas a quatro frases para o apresentador.',
};

/** Instrução de formato para o prompt. A gramática já impõe cada palavra-chave na ordem certa; por isso
 * a versão curta (padrão) só diz isso em uma linha. No piloto de 24/11 (Qwen3 1.7B), o exemplo completo
 * aumentou o prompt de cada slide em ~120 tokens, o que no celular custa quase o que a sintaxe economiza. */
export function altoFormatHint(kind: string, schema: JsonSchema, full = false): string {
  if (!full) {
    const p = props(schema);
    // Só "…" como marcador: com palavras ("rótulo", "detalhe") o 0.6B e o 1.7B copiavam o marcador como conteúdo
    // (bancada de 24/11: 17 de 24 apresentações do 1.7B). O papel de cada texto vai numa frase à parte.
    const shape: Record<string, [string, string]> = {
      item: ['item "…" "…"', 'em item, o 1º texto é um rótulo curto e o 2º uma frase que o explica'],
      valor: ['valor "…" "…"', 'em valor, o 1º texto é o número e o 2º o que ele mede'],
      marco: ['marco "…" "…" "…"', 'em marco, os textos são data, nome do marco e detalhe'],
      barra: ['barra "…" 10', 'em barra, o texto é o nome da barra e o número é o valor']};
    const roles: string[] = [];
    const parts = fields(kind).filter(f => p[f.key]).map(f => {
      if (f.kind === 'str') return `${f.word} "…"`;
      if (f.kind === 'notes') return 'notas "…"';
      if (f.kind === 'items') { roles.push(shape[f.word][1]); return `${shape[f.word][0]} …`; }
      if (f.kind === 'sides') { roles.push(`em lado, o texto é o nome da alternativa; ${shape.item[1]}`); return 'lado "…" { item "…" "…" } lado "…" { … }'; }
      return ((p[f.key].items as JsonSchema)?.enum as string[] | undefined)?.[0]?.startsWith('F') ? 'fontes F1, F2' : '';
    }).filter(Boolean);
    const role = roles.length ? ` (${roles.join('; ')}; escreva conteúdo real, nunca os nomes dos campos)` : '';
    return `Responda SOMENTE com o bloco SlideDSL Alto deste slide (a gramática impõe a sintaxe): ${kind} { ${parts.join(' ')} }${role}`;
  }
  return altoFormatExample(kind, schema);
}

function altoFormatExample(kind: string, schema: JsonSchema): string {
  const p = props(schema), lines = [`${kind} {`];
  for (const f of fields(kind)) {
    if (!p[f.key]) continue;
    if (f.kind === 'str') lines.push(`  ${f.word} "${EXAMPLE_VALUES[f.key] ?? '...'}"`);
    else if (f.kind === 'notes') lines.push(`  notas "${EXAMPLE_VALUES.notas}"`);
    else if (f.kind === 'items') {
      const ex = {item: 'item "Rótulo curto" "Uma frase concreta que explica o rótulo."',
        valor: 'valor "90%" "O que o número mede"', marco: 'marco "2014" "Rótulo do marco" "Detalhe curto"',
        barra: 'barra "Rótulo" 42'}[f.word];
      lines.push(`  ${ex}`, `  ${ex}`);
    } else if (f.kind === 'sides') {
      lines.push('  lado "Alternativa A" {', '    item "Aspecto" "Como é em A."', '  }',
        '  lado "Alternativa B" {', '    item "Aspecto" "Como é em B."', '  }');
    } else if (f.kind === 'sources') {
      const ids = ((p[f.key].items as JsonSchema)?.enum ?? []) as string[];
      if (ids.length && ids[0] !== '__FACT_IDS__') lines.push(`  fontes ${ids.slice(0, 2).join(', ')}`);
    }
  }
  lines.push('}');
  return `Responda SOMENTE com o bloco SlideDSL Alto deste slide, sem comentários. Os campos são os mesmos descritos acima (item "rótulo" "detalhe"; fontes com IDs F#; notas). Formato:\n${lines.join('\n')}`;
}
