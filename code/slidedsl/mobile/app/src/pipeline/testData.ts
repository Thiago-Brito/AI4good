import type {CallRecord} from './types.js';
import {costBreakdown} from './usage.js';
export function testData(input: {calls: CallRecord[]; device_start: unknown; device_end: unknown;
  model: unknown; status: string; wall_ms: number; slides: number; diagnostics: unknown;
  error?: string; source_mode: string; document?: unknown; slide_mode?: string}) {
  return {...costBreakdown(input.calls), ...input, profile: 'celular',
    recorded_at: new Date().toISOString(), max_repairs_per_slide: 1,
    max_calls: 1 + 2 * input.slides + (input.source_mode === 'none' ? 0 : input.source_mode === 'document' ? 6 : 1)};
}
