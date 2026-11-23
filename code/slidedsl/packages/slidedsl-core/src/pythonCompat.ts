// @ts-nocheck
// Semântica numérica e de coleções necessária ao porte, sem I/O/plataforma.
const keyword = Symbol('keyword arguments');
export const kw = value => ({[keyword]: value});
export const unkw = value => value?.[keyword]??value;
export function bind(args, names, defaults, varargs=false, kwargs=false) {
  args = [...args];
  const named = args.at(-1)?.[keyword] ? args.pop()[keyword] : {};
  const result = names.map((n,i) => n in named ? named[n] : i < args.length ? args[i] : defaults[i]);
  if (varargs) result.push(args.slice(names.length));
  if (kwargs) result.push(Object.fromEntries(Object.entries(named).filter(([n]) => !names.includes(n))));
  return result;
}
export const truth = v => v instanceof Set ? v.size > 0 : Array.isArray(v) || typeof v === 'string' ? v.length > 0 : v && typeof v === 'object' ? Object.keys(v).length > 0 : !!v;
export const and = fs => { let v; for(const f of fs) { v=f(); if(!truth(v)) break; } return v; };
export const or = fs => { let v; for(const f of fs) { v=f(); if(truth(v)) break; } return v; };
export const iter = v => v instanceof Set || Array.isArray(v) || typeof v === 'string' ? v : Object.keys(v);
export const len = v => v instanceof Set ? v.size : v.length ?? Object.keys(v).length;
export const list = (v=[]) => [...iter(v)];
export const tuple = list;
export const set = (v=[]) => new Set(iter(v));
export const bool = truth;
export const str = v => v === null ? 'None' : typeof v === 'boolean' ? v ? 'True' : 'False' : String(v);
export const float = Number;
export const int = (v, radix=10) => typeof v==='number' ? Math.trunc(v) : parseInt(v,radix);
export const abs = Math.abs;
export function round(v, digits=0) { const f=10**digits, x=v*f, lo=Math.floor(x), r=x-lo; return (r===.5 ? lo%2===0 ? lo : lo+1 : Math.round(x))/f; }
export const at = (v,k) => (Array.isArray(v)||typeof v==='string') && typeof k==='number' ? v.at(k) : v[k];
export const slice = (v,a=null,b=null,step=null) => {const r=v.slice(a??0,b??undefined); return step===-1 ? [...r].reverse() : r;};
export const eq = (a,b) => a===b || Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>eq(v,b[i]));
export const contains = (a,b) => a instanceof Set ? a.has(b) : Array.isArray(a) ? a.some(v=>eq(v,b)) : typeof a==='string' ? a.includes(b) : b in a;
export function cmp(op,a,b) {switch(op) {
  case 'Eq': case 'Is': return eq(a,b); case 'NotEq': case 'IsNot': return !eq(a,b);
  case 'In': return contains(b,a); case 'NotIn': return !contains(b,a);
  case 'Lt': return compare(a,b)<0; case 'Gt': return compare(a,b)>0;
  case 'LtE': return a instanceof Set ? [...a].every(x=>contains(b,x)) : compare(a,b)<=0;
  case 'GtE': return compare(a,b)>=0;
}}
export function bin(op,a,b) {switch(op) {
  case 'Add': return Array.isArray(a) ? a.concat(b) : a+b;
  case 'Sub': return a instanceof Set ? new Set([...a].filter(x=>!b.has(x))) : a-b;
  case 'Mult': return Array.isArray(a) ? Array.from({length:b},()=>a).flat() : a*b;
  case 'Div': return a/b; case 'FloorDiv': return Math.floor(a/b); case 'Mod': return ((a%b)+b)%b;
  case 'Pow': return a**b; case 'BitOr': return new Set([...a,...b]); case 'BitAnd': return new Set([...a].filter(x=>b.has(x)));
}}
export function range(...a) {let start=0,stop=a[0],step=1;if(a.length>1)[start,stop,step=1]=a;const r=[];for(let i=start;step>0?i<stop:i>stop;i+=step)r.push(i);return r;}
export const enumerate = (v,start=0) => list(v).map((x,i)=>[i+start,x]);
export const zip = (...args) => range(Math.min(...args.map(len))).map(i=>args.map(a=>at(a,i)));
export const any = v => list(v).some(truth);
export const all = v => list(v).every(truth);
export const sum = (v,start=0) => list(v).reduce((a,b)=>a+b,start);
export function compare(a,b) {if(Array.isArray(a)&&Array.isArray(b)){for(let i=0;i<Math.min(a.length,b.length);i++){const d=compare(a[i],b[i]);if(d)return d;}return a.length-b.length;}return a<b?-1:a>b?1:0;}
export function sorted(v, opts=kw({})) {const {key=x=>x,reverse=false}=opts[keyword]??{};return list(v).sort((a,b)=>compare(key(a),key(b))*(reverse?-1:1));}
function extremum(args, direction) {const opts=args.at(-1)?.[keyword]?args.pop()[keyword]:{};const values=args.length===1?list(args[0]):args;if(!values.length){if('default'in opts)return opts.default;throw Error('empty extremum');}const key=opts.key??(x=>x);return values.reduce((a,b)=>compare(key(b),key(a))*direction>0?b:a);}
export const max = (...args) => extremum(args,1);
export const min = (...args) => extremum(args,-1);
export const next = (v, fallback=undefined) => list(v)[0] ?? fallback;
export const getattr = (o,k,fallback=null) => o[k]??fallback;
export const setattr = (o,k,v) => {o[k]=v;};
export const isinstance = (v,t) => t===str ? typeof v==='string' : v instanceof t;
export const dict = (...args) => {const named=args.at(-1)?.[keyword]?args.pop()[keyword]:{};return {...(args[0]??{}),...named};};
export const replace = (obj,opts) => Object.assign(Object.create(Object.getPrototypeOf(obj)),obj,opts[keyword]);
export const pstdev = v => {const avg=sum(v)/len(v);return Math.sqrt(sum(v.map(x=>(x-avg)**2))/len(v));};
export const combinations = (v,n) => {if(n!==2)throw Error('combinations');return v.flatMap((a,i)=>v.slice(i+1).map(b=>[a,b]));};
export const urlsplit = v => {try {return {hostname:new URL(v).hostname};}catch{return {hostname:null};}};
export const math = {floor:Math.floor,ceil:Math.ceil,hypot:Math.hypot,isfinite:Number.isFinite};
export const unicodedata = {normalize:(form,s)=>s.normalize(form)};
export const format = (v,spec='',conversion=-1) => spec==='02d' ? String(v).padStart(2,'0') : spec===',.2f' ? Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2,useGrouping:true}) : conversion===114 ? JSON.stringify(v) : String(v);
function regex(pattern, flags=0, anchored=false) {
  // Python \w is Unicode, JS \w is ASCII even with /u.
  pattern=pattern.replace('[\\W_]','[^\\p{L}\\p{N}]');
  let inside=false, expanded='';
  for(let i=0;i<pattern.length;i++){
    const c=pattern[i];
    if(c==='\\'&&i+1<pattern.length){const n=pattern[++i];expanded+=n==='w'?(inside?'\\p{L}\\p{N}_':'[\\p{L}\\p{N}_]'):n==='W'?'[^\\p{L}\\p{N}_]':'\\'+n;continue;}
    if(c==='[')inside=true;if(c===']')inside=false;expanded+=c;
  }
  pattern=expanded;
  return new RegExp(anchored?'^(?:'+pattern+')$':pattern, 'u'+(flags?'i':''));
}
const matchObject = m => m ? {group:(i=0)=>m[i]??null} : null;
export const re = {
  I:1,IGNORECASE:1,
  compile:(pattern,flags=0)=>({match:s=>matchObject(regex('^(?:'+pattern+')',flags).exec(s))}),
  match:(pattern,s,flags=0)=>matchObject(regex('^(?:'+pattern+')',flags).exec(s)),
  search:(pattern,s,flags=0)=>matchObject(regex(pattern,flags).exec(s)),
  fullmatch:(pattern,s,flags=0)=>matchObject(regex(pattern,flags,true).exec(s)),
  findall:(pattern,s)=>[...s.matchAll(new RegExp(regex(pattern).source,'gu'))].map(m=>m[0]),
  finditer:(pattern,s,flags=0)=>[...s.matchAll(new RegExp(regex(pattern,flags).source,'gu'+(flags?'i':'')))].map(matchObject),
  split:(pattern,s)=>s.split(regex(pattern)),
  sub:(pattern,replacement,s,options=0)=>s.replace(new RegExp(regex(pattern, typeof options==='object'?options[keyword]?.flags:options).source,'gu'+((typeof options==='object'?options[keyword]?.flags:options)?'i':'')),replacement),
};
export function method(o,name,...args) {
  const opts=args.at(-1)?.[keyword]?args.at(-1)[keyword]:{};
  switch(name){
    case 'append': return o.push(args[0]); case 'clear': return Array.isArray(o)?o.splice(0):o.clear();
    case 'get': return o[args[0]]??args[1]??null; case 'items': return Object.entries(o); case 'values': return Object.values(o); case 'keys': return Object.keys(o);
    case 'update': if(o instanceof Set){for(const x of iter(args[0]))o.add(x);}else Object.assign(o,args[0]);return;
    case 'setdefault': return o[args[0]]??(o[args[0]]=args[1]);
    case 'model_dump': return {...o};
    case 'split': if(typeof o==='string') return args.length ? o.split(args[0]) : o.trim()?o.trim().split(/\s+/u):[]; break;
    case 'splitlines': return o.split(/\r?\n/);
    case 'join': return list(args[0]).join(o);
    case 'startswith': return Array.isArray(args[0])?args[0].some(x=>o.startsWith(x)):o.startsWith(args[0]);
    case 'endswith': return Array.isArray(args[0])?args[0].some(x=>o.endsWith(x)):o.endsWith(args[0]);
    case 'casefold': case 'lower': return o.toLowerCase(); case 'upper': return o.toUpperCase();
    case 'islower': return /\p{Ll}/u.test(o)&&!/[\p{Lu}\p{Lt}]/u.test(o);
    case 'isupper': return /\p{Lu}/u.test(o)&&!/[\p{Ll}\p{Lt}]/u.test(o);
    case 'strip': case 'rstrip': {
      if(!args.length) return name==='strip'?o.trim():o.trimEnd();
      const chars=new Set(args[0]);let a=0,b=o.length;if(name==='strip')while(a<b&&chars.has(o[a]))a++;while(b>a&&chars.has(o[b-1]))b--;return o.slice(a,b);
    }
    case 'rsplit': {const [sep,limit]=args;if(limit===undefined)return o.split(sep);const a=o.split(sep);return [a.slice(0,-limit).join(sep),...a.slice(-limit)];}
    case 'replace': return o.split(args[0]).join(args[1]);
    case 'encode': return o.replace(/[^\x00-\x7F]/g,''); case 'decode': return o;
    case 'sort': return o.sort((a,b)=>compare((opts.key??(x=>x))(a),(opts.key??(x=>x))(b))*(opts.reverse?-1:1));
  }
  if(typeof o?.[name]!=='function')throw Error('Método não suportado: '+name);
  return o[name](...args);
}
