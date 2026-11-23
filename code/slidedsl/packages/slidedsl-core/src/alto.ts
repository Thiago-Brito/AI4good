import { validate_alto } from './port.js';
import type { Diagnostic, Facts } from './ir.js';
export type SlideKind = 'capa'|'secao'|'topicos'|'numeros'|'comparacao'|'etapas'|'linha_do_tempo'|'citacao'|'grafico'|'imagem'|'conclusao';
export interface Item { label: string; detail?: string|null }
export interface AltoSlide {
  kind: SlideKind; title?: string|null; subtitle?: string|null; author?: string|null;
  text?: string|null; caption?: string|null; unit?: string|null;
  image_file?: string|null; image_query?: string|null;
  items?: Item[]; values?: {value:string;label:string}[];
  sides?: {name:string;items:Item[]}[]; milestones?: {date:string;label:string;detail?:string|null}[];
  bars?: {label:string;value:number}[]; cycle?: boolean; sources?: string[];
  notes?: string|null; line?: number|null; column?: number|null;
}
export interface AltoDeck { title: string; theme?: 'claro'|'escuro'|'editorial'|'vibrante'|'natural'|'noturno'; slides: AltoSlide[] }
export function normalizeDeck(deck: AltoDeck): AltoDeck {
  return {theme:'claro',...deck,slides:deck.slides.map(s=>({title:null,subtitle:null,author:null,text:null,caption:null,unit:null,image_file:null,image_query:null,items:[],values:[],sides:[],milestones:[],bars:[],cycle:false,sources:[],notes:null,line:null,column:null,...s}))};
}
export function validateAlto(deck: AltoDeck, facts: Facts|null = null): Diagnostic[] {
  return validate_alto(normalizeDeck(deck), facts);
}
