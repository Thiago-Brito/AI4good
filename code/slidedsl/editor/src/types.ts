export type Element = {
  id: string;
  type: "rectangle" | "ellipse" | "text" | "image";
  x: number;
  y: number;
  width: number;
  height: number;
  z: number;
  text: string | null;
  file: string | null;
  font_size: number | null;
  font_face: string;
  color: string | null;
  role: "titulo" | "corpo" | "decoracao" | "background" | null;
  role_origin: string | null;
  source_line: number | null;
  source_column: number | null;
};
export type Group = {
  id: string;
  members: string[];
  label: string | null;
  source_line: number | null;
};
export type RelationKind =
  | "below"
  | "right"
  | "left"
  | "align_right"
  | "center"
  | "top";
export type Relation = {
  kind: RelationKind;
  target: string;
  reference: string;
  margin: number;
  source_line: number | null;
  source_column: number | null;
};
export type Slide = {
  number: number;
  elements: Element[];
  groups: Group[];
  relations: Relation[];
};
export type Deck = {
  schema_version: "1.1";
  title: string;
  theme: "claro" | "escuro";
  canvas: { width: 1280; height: 720; unit: "px_logico" };
  slides: Slide[];
};
export type Diagnostic = {
  code: string;
  severity: "ERRO" | "AVISO" | "INFORMAÇÃO";
  message: string;
  slide: number | null;
  element: string | null;
  line: number | null;
  column: number | null;
  suggestion: string;
  evidence: Record<string, unknown>;
};
export type Report = { valid: boolean; diagnostics: Diagnostic[] };
