import {initLlama, type LlamaContext} from 'llama.rn';
import type {TextModel, Usage} from '../pipeline/types';
import {checkCancelled} from '../pipeline/types';
export interface LocalModel extends TextModel {release(): Promise<void>}
export async function loadModel(path: string, gpu = false, onProgress?: (n: number) => void): Promise<LocalModel> {
  const context: LlamaContext = await initLlama({model: path, n_ctx: 4096,
    n_batch: 256, n_gpu_layers: gpu ? 99 : 0, use_mmap: true}, onProgress);
  return {
    async complete({system, user, schema, grammar, signal}) {
      checkCancelled(signal);
      const abort = () => { void context.stopCompletion().catch(() => {}); };
      signal?.addEventListener('abort', abort, {once: true});
      try {
        const messages = [{role: 'system', content: system}, {role: 'user', content: `${user}\n/no_think`}];
        const response_format = {type: 'json_schema' as const, json_schema: {strict: true, schema}};
        const formatted = await context.getFormattedChat(messages, undefined,
          {jinja: true, enable_thinking: false});
        checkCancelled(signal);
        const tokens = await context.tokenize(formatted.prompt);
        const available = 4096 - tokens.tokens.length - 32;
        if (available < 512) throw Error('Pedido e fontes excedem o contexto de 4096 tokens. Encurte o pedido ou o texto da fonte.');
        checkCancelled(signal);
        // Passar `prompt` (já formatado com o raciocínio desligado) e não `messages`: com
        // messages+jinja o formato de chat do Qwen3 monta uma gramática que admite um bloco
        // <think> antes do JSON. Sem messages, o llama.rn envia `json_schema` ao llama.cpp,
        // que o converte em gramática estrita desde o primeiro token (teste no emulador, 23/11/2026).
        // Modo gramática: a GBNF do slide em SlideDSL Alto restringe desde o primeiro token, como o
        // JSON Schema convertido (o llama.rn dá prioridade a `grammar` quando ambos existem).
        const result = await context.completion({
          prompt: formatted.prompt, ...(grammar ? {grammar} : {response_format}),
          n_predict: Math.min(1400, available), temperature: 0.2, seed: 42,
        });
        // Preserve observed usage even for cancellation or truncated output; Recorder checks JSON.
        const usage: Usage = {input_tokens: result.tokens_evaluated ?? null,
          output_tokens: result.tokens_predicted ?? null,
          prefill_ms: result.timings?.prompt_ms ?? null, decode_ms: result.timings?.predicted_ms ?? null,
          timings: result.timings ? {...result.timings} : undefined};
        return {text: result.context_full || result.truncated || result.interrupted ? '' : (result.content || result.text), usage};
      } finally { signal?.removeEventListener('abort', abort); }
    },
    release: () => context.release(),
  };
}