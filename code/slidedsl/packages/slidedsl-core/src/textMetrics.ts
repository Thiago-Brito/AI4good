// @ts-nocheck
import data from './data/font_metrics.json' with { type: 'json' };
import { bind, round } from './pythonCompat.js';
const families = data.families;
const charIndex = Object.fromEntries(data.characters.map((c,i)=>[c,i]));
const pairIndexes = new WeakMap();
for(const family of Object.values(families))for(const entry of Object.values(family.weights)) {
  pairIndexes.set(entry,Object.fromEntries((entry.pairs??Object.keys(entry.kerning??{})).map((pair,i)=>[pair,i])));
}
export function optical_size(...args) {
  const [nominal,family='Arial',minimum=0,effective=0]=bind(args,['nominal','family','minimum','effective_minimum'],[undefined,'Arial',0,0]);
  const ratio=(families[family]??families.Arial).x_height_ratio;
  return Math.max(minimum,round(nominal/ratio),Math.ceil(effective/ratio));
}
export function text_width(...args) {
  const [value,size,bold,family]=bind(args,['value','size','bold','family'],[undefined,undefined,false,'Arial']);
  const entry=(families[family]??families.Arial).weights[bold?'1':'0'];
  if(entry.missing)return [...value].length*size*96/72*(bold?.65:.58);
  const raster=round(size*96/72*4),chars=[...value];
  const table=entry.rasters?.[String(raster)];
  let width=0;
  for(let i=0;i<chars.length;i++) {
    width += table?.advances[charIndex[chars[i]]] ?? round((entry.advances[chars[i]]??entry.advances['?'])*raster*(entry.layout_engine===0?1:64))/(entry.layout_engine===0?1:64);
    if(i){const pair=chars[i-1]+chars[i];width += table ? table.kerning[Array.isArray(table.kerning)?pairIndexes.get(entry)[pair]:pair]??0 : round((entry.kerning[pair]??0)*raster*64)/64;}
  }
  return width/4*(family in families?entry.margin:1.14);
}
function legacyHeight(value,width,size) {
  const px=size*96/72,capacity=Math.max(1,Math.floor((width-16)/(.52*px)));
  return Math.ceil(value.split('\n').reduce((a,s)=>a+Math.max(1,Math.ceil([...s].length/capacity)),0)*px*1.2+18);
}
export function text_height(...args) {
  const [value,width,size,bold,family]=bind(args,['value','width','size','bold','family'],[undefined,undefined,undefined,false,'Arial']);
  const available=Math.max(1,width-16);let lines=0;
  for(const paragraph of value.split('\n')) {
    lines++;let current='';
    for(const word of paragraph.trim()?paragraph.trim().split(/\s+/u):[]) {
      const proposed=current?current+' '+word:word;
      if(current&&text_width(proposed,size,bold,family)>available){lines++;current=word;}else current=proposed;
    }
  }
  const measured=Math.ceil(lines*size*96/72*1.2+18);
  return family==='Arial'||(families[family]??families.Arial).weights[bold?'1':'0'].missing?Math.max(legacyHeight(value,width,size),measured):measured;
}
export const textWidth=text_width, textHeight=text_height, opticalSize=optical_size;
