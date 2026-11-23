export interface Canvas { width: 1280; height: 720; unit: 'px_logico' }
export interface Element {
  id: string; type: 'text'|'rectangle'|'ellipse'|'image'|'arrow';
  x: number; y: number; width: number; height: number; z: number;
  text: string|null; file: string|null; font_size: number|null; font_face: string;
  color: string|null; role: 'titulo'|'corpo'|'decoracao'|'background'|null;
  role_origin: string|null; source_line: number|null; source_column: number|null;
  bold: boolean; align: 'left'|'center'|'right'; rounded: boolean;
}
export interface Group { id: string; members: string[]; label: string|null; source_line: number|null }
export interface Relation { kind: 'below'|'right'|'left'|'align_right'|'center'|'top'; target: string; reference: string; margin: number; source_line: number|null; source_column: number|null }
export interface Slide { number: number; elements: Element[]; groups: Group[]; relations: Relation[]; notes: string|null }
export interface Presentation { schema_version: '1.1'; title: string; theme: 'claro'|'escuro'; canvas: Canvas; slides: Slide[] }
export interface Diagnostic { code: string; severity: 'ERRO'|'AVISO'|'INFORMAÇÃO'; message: string; slide?: number|null; element?: string|null; line?: number|null; column?: number|null; evidence?: Record<string,unknown>; suggestion?: string }
export type Fact = { claim?: string; quote?: string; source_title?: string; url?: string; [key: string]: unknown };
export type Facts = Record<string, Fact>;
export interface ImageInfo { width?: number; height?: number; missing?: boolean; metadata?: Record<string,string> }
export type Images = Record<string, ImageInfo>;
