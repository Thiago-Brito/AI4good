# APK rodada 2 — fontes consultadas em 22/11/2026

- Contrato local: `docs/PLANO_CODEX_TCC_APK2_APP.md`, `docs/APK_CORE_RELATORIO.md`.
- Prompts/schemas: `src/slidedsl/alto_generation.py`; extração e verificação:
  `src/slidedsl/documents.py`, `src/slidedsl/research.py`.
- Custos: `src/slidedsl/model_usage.py`, esquema `slidedsl.custo.v1`.
- API efetivamente inspecionada: `D:/slidedsl-mobile/app/node_modules/llama.rn/src/index.ts`
  e `src/types.ts`, versão 0.13.0-rc.12. `CompletionResponseFormat` aceita
  `{type:'json_schema',json_schema:{strict:true,schema}}`; completion encaminha
  `json_schema` ao nativo quando não há grammar. Não há export público chamado
  `convertJsonSchemaToGrammar`. `initLlama`, `stopCompletion`, `release`,
  `enable_thinking:false` e timings foram conferidos no código instalado.
- Expo FileSystem instalado, 58.0.14: `File.digest('SHA-256')` calcula o hash
  nativamente; API legacy oferece `DownloadResumable`, `pauseAsync`, `resumeData` e SAF.
- Modelos GGUF Q4_K_M públicos, existência e ponteiros LFS consultados pelo navegador:
  - [0.6B / QuantFactory](https://huggingface.co/QuantFactory/Qwen3-0.6B-GGUF/blob/main/Qwen3-0.6B.Q4_K_M.gguf),
    [ponteiro](https://huggingface.co/QuantFactory/Qwen3-0.6B-GGUF/raw/main/Qwen3-0.6B.Q4_K_M.gguf):
    484220000 bytes, SHA-256 `7af3fdf842f87b24672f8a7f1dd50404043f0bfb71093ff91c31d2b49df4631d`.
  - [1.7B / Unsloth](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/blob/main/Qwen3-1.7B-Q4_K_M.gguf),
    [ponteiro](https://huggingface.co/unsloth/Qwen3-1.7B-GGUF/raw/main/Qwen3-1.7B-Q4_K_M.gguf):
    1107409472 bytes, SHA-256 `b139949c5bd74937ad8ed8c8cf3d9ffb1e99c866c823204dc42c0d91fa181897`.
  - [4B / Qwen](https://huggingface.co/Qwen/Qwen3-4B-GGUF/blob/main/Qwen3-4B-Q4_K_M.gguf),
    [ponteiro](https://huggingface.co/Qwen/Qwen3-4B-GGUF/raw/main/Qwen3-4B-Q4_K_M.gguf):
    2497280256 bytes, SHA-256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`.
  A conferência é dos metadados publicados, sem baixar os pesos nesta máquina.
- [MediaWiki REST API](https://www.mediawiki.org/wiki/API:REST_API): páginas pt/en
  por `/w/rest.php/v1/page/{title}/with_html`. A aplicação usa resumos REST
  `/api/rest_v1/page/summary/{title}` de pt/en.wikipedia.org e verifica as citações
  no texto efetivamente recebido. Nenhuma chave é necessária.

- Expo Network 58.0.5 e Battery 58.0.4: versões conferidas em
  `expo/bundledNativeModules.json`, APIs em `expo-network/build/Network.d.ts`,
  `Network.types.d.ts` e tipos instalados de `expo-battery`. Snapshot de bateria
  usa nível, estado e modo de economia; não há temperatura na API pública usada.
- Metro: export Android real e mapa de fontes em
  `D:/slidedsl-mobile/outputs/apk2-bundle-verification.json`, com núcleo, fontes,
  PptxGenJS e VoiceInput. A conferência é de inclusão no bundle, não execução JNI.
- Cache Kotlin: `kotlin-daemon-client-2.2.10.jar`, `DaemonParamsKt.configureDaemonOptions`
  e `DaemonOptions.runFilesPath`, inspecionados por javap e executados em uma sonda
  Java em outputs; confirma o parâmetro `kotlin.daemon.options=runFilesPath=...`.
