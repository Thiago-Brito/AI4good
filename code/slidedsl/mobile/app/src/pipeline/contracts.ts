import exported from './prompts.json' with {type: 'json'};
import type {JsonSchema} from './types.js';
export const prompts = exported;
export function schemaWithFacts(schema: unknown, ids: string[]): JsonSchema {
  return JSON.parse(JSON.stringify(schema), (key, value) =>
    key === 'enum' && Array.isArray(value) && value[0] === '__FACT_IDS__' ? ids : value);
}
// Validação independente do decoder: também cobre modelos simulados e JSON truncado.
export function schemaErrors(value: unknown, schema: JsonSchema, path = '$'): string[] {
  const errors: string[] = [];
  const add = (s: string) => errors.push(`${path}: ${s}`);
  if (schema.enum && !(schema.enum as unknown[]).includes(value)) add('valor fora do enum');
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return [`${path}: objeto esperado`];
    const obj = value as Record<string, unknown>;
    for (const key of (schema.required ?? []) as string[]) if (!(key in obj)) add(`campo obrigatório ${key}`);
    for (const [key, sub] of Object.entries((schema.properties ?? {}) as Record<string, JsonSchema>)) {
      if (key in obj) errors.push(...schemaErrors(obj[key], sub, `${path}.${key}`));
    }
  } else if (schema.type === 'array') {
    if (!Array.isArray(value)) return [`${path}: lista esperada`];
    if (schema.minItems !== undefined && value.length < Number(schema.minItems)) add('poucos itens');
    if (schema.maxItems !== undefined && value.length > Number(schema.maxItems)) add('itens demais');
    if (schema.items) value.forEach((v, i) => errors.push(...schemaErrors(v, schema.items as JsonSchema, `${path}.${i}`)));
  } else if (schema.type === 'string') {
    if (typeof value !== 'string') return [`${path}: texto esperado`];
    const n = Array.from(value).length;
    if (schema.minLength !== undefined && n < Number(schema.minLength)) add('texto curto demais');
    if (schema.maxLength !== undefined && n > Number(schema.maxLength)) add('texto longo demais');
  } else if (schema.type === 'number') {
    if (typeof value !== 'number' || !Number.isFinite(value)) add('número esperado');
    else if (schema.minimum !== undefined && value < Number(schema.minimum)) add('abaixo do mínimo');
  }
  return errors;
}
