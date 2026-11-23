export type JsonSchema = Record<string, unknown>;
export interface Usage {
  input_tokens: number | null;
  output_tokens: number | null;
  prefill_ms: number | null;
  decode_ms: number | null;
  timings?: Record<string, number>;
}
export interface TextModel {
  complete(input: {system: string; user: string; schema: JsonSchema; signal?: AbortSignal}):
    Promise<{text: string; usage: Usage}>;
}
export interface CallRecord extends Usage {
  call: number;
  stage: 'roteiro' | 'slide' | 'document_extract';
  slide: number | null;
  attempt: number;
  repair: boolean;
  status: 'success' | 'failed' | 'cancelled';
  wall_ms: number;
  error?: string;
}
export function checkCancelled(signal?: AbortSignal): void {
  if (signal?.aborted) throw new Error('Operação cancelada.');
}
