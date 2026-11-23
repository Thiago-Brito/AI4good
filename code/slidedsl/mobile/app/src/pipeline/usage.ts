import type {CallRecord, JsonSchema, TextModel} from './types.js';
import {checkCancelled} from './types.js';
export class Recorder {
  readonly calls: CallRecord[] = [];
  constructor(private model: TextModel, readonly maxCalls: number,
    private signal?: AbortSignal, private onCall?: (calls: CallRecord[]) => void) {}
  async json(stage: CallRecord['stage'], system: string, user: string, schema: JsonSchema,
    slide: number | null = null, attempt = 0): Promise<unknown> {
    checkCancelled(this.signal);
    if (this.calls.length >= this.maxCalls) throw new Error('Limite de chamadas atingido.');
    const started = Date.now();
    const record: CallRecord = {call: this.calls.length + 1, stage, slide, attempt,
      repair: stage === 'slide' && attempt > 0, status: 'failed', wall_ms: 0,
      input_tokens: null, output_tokens: null, prefill_ms: null, decode_ms: null};
    this.calls.push(record);
    try {
      const result = await this.model.complete({system, user, schema, signal: this.signal});
      Object.assign(record, result.usage);
      checkCancelled(this.signal);
      const parsed: unknown = JSON.parse(result.text);
      record.status = 'success';
      return parsed;
    } catch (e) {
      record.status = this.signal?.aborted ? 'cancelled' : 'failed';
      record.error = e instanceof Error ? e.message : String(e);
      throw e;
    } finally {
      record.wall_ms = Date.now() - started;
      this.onCall?.(this.calls.map(c => ({...c})));
    }
  }
}
const fields = ['input_tokens', 'output_tokens', 'reasoning_tokens', 'wall_ms', 'prefill_ms',
  'decode_ms', 'load_ms', 'server_total_ms'] as const;
export function costBreakdown(calls: CallRecord[]) {
  const totals = (rows: CallRecord[]): Record<string, number | null> => {
    const out: Record<string, number | null> = {calls: rows.length, failed_calls: rows.filter(c => c.status !== 'success').length};
    for (const key of fields) {
      const known = rows.map(r => (r as unknown as Record<string, unknown>)[key]).filter((v): v is number => typeof v === 'number');
      out[key] = known.length ? Math.round(known.reduce((a, b) => a + b, 0) * 1000) / 1000 : null;
      out[`${key}_unknown_calls`] = rows.length - known.length;
    }
    return out;
  };
  const groups: Record<string, CallRecord[]> = {};
  for (const c of calls) (groups[c.repair ? 'reparo' : c.stage] ??= []).push(c);
  return {schema: 'slidedsl.custo.v1', total: totals(calls),
    by_stage: Object.fromEntries(Object.entries(groups).map(([k, rows]) => [k, totals(rows)]))};
}
