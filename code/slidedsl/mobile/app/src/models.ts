// Sizes and SHA-256 are the published LFS pointer values; refs/APK_APP_FONTES.md.
// url vazio = modelo só por importação (arquivo .gguf copiado para o aparelho).
export interface ModelSpec {id: string; label: string; url: string; bytes: number; sha256: string; minRamGB: number;
  /** Treinado só no modo gramática (gramatica_limites + frases): o JSON fica desligado para ele. */
  grammarOnly?: boolean}
export const models: ModelSpec[] = [
  {id: 'qwen3-0.6b', label: 'Qwen3 0.6B · leve', minRamGB: 3, bytes: 484220000,
    url: 'https://huggingface.co/QuantFactory/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B.Q4_K_M.gguf',
    sha256: '7af3fdf842f87b24672f8a7f1dd50404043f0bfb71093ff91c31d2b49df4631d'},
  {id: 'qwen3-1.7b', label: 'Qwen3 1.7B · recomendado', minRamGB: 6, bytes: 1107409472,
    url: 'https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/resolve/main/Qwen3-1.7B-Q4_K_M.gguf',
    sha256: 'b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897'},
  {id: 'qwen3-4b', label: 'Qwen3 4B · exige ≥ 12 GB RAM', minRamGB: 12, bytes: 2497280256,
    url: 'https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf',
    sha256: '7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5'},
  // Qwen3 0.6B destilado do 4B com LoRA no pipeline do app (docs/RESULTADOS_T8.md); arquivo local, não publicado.
  {id: 'qwen3-0.6b-slidedsl', label: 'Qwen3 0.6B SlideDSL (LoRA) · importar .gguf', minRamGB: 3, bytes: 396704608,
    url: '', sha256: 'a58cebfb0e26b7dc70e53f7388bae0df9112d98c6c91cb915f2c8b3ee0a77b53', grammarOnly: true},
];
export function suggestedModel(ram: number | null): ModelSpec { return ram !== null && ram >= 6 * 1024 ** 3 ? models[1] : models[0]; }
export function modelAllowed(model: ModelSpec, ram: number | null): boolean { return model.id !== 'qwen3-4b' || (ram !== null && ram >= 12 * 1024 ** 3); }