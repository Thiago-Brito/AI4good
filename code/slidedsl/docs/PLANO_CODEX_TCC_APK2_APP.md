# Plano Codex — APK, rodada 2: geração no app (llama.rn + núcleo TS + voz)

Depende da rodada 1 ([PLANO_CODEX_TCC_APK1_CORE.md](PLANO_CODEX_TCC_APK1_CORE.md)): `packages/slidedsl-core`
com `buildAlto` e `renderPptx` em paridade com o Python.

## Estado de partida (22/11/2026)

- App Expo SDK 58 / React Native 0.88.1 em `mobile/app/` (fonte; `android/` é gerado por
  `expo prebuild` e não é versionado). Build: `scripts/mobile_build.ps1` copia para
  `D:\slidedsl-mobile\app` e roda Gradle (ambiente: `scripts/android_env.ps1`, JDK 17 e SDK em `D:\android`).
- Já instalados: `llama.rn@0.13.0-rc.12` (JNI pré-compilado arm64-v8a/x86_64), `expo-speech-recognition`
  (ditado pt-BR; usado em `src/VoiceInput.tsx`), `expo-file-system`, `expo-sharing`, `expo-device`,
  `expo-build-properties`, `pptxgenjs@4.0.1`.
- Tela atual: pedido por texto ou voz; botão "Gerar" ainda inativo.

## Regras

- Mesmas regras da rodada 1 (não mudar o Python; relatório em `docs/APK_APP_RELATORIO.md`; sem commit).
- Não colocar `node_modules`, `android/` ou APK no repositório. Não baixar modelos GGUF para o repositório.
- Toda lógica de pipeline em módulos TS puros testáveis em Node com modelo simulado
  (`mobile/app/src/pipeline/*.ts` + testes `node:test`), separada das telas. Os módulos do
  pipeline não importam `react-native` nem `llama.rn` diretamente: recebem um adaptador
  (`TextModel` com `complete({system,user,grammar|schema}) → {text, usage}`); só
  `src/llm/llamaRn.ts` conhece o llama.rn.
- **Disco C: tem ~4 GB livres.** Não rodar `npm install` em `mobile/app` (no C:/OneDrive). Antes de
  qualquer comando npm/Gradle: `. .\scripts\android_env.ps1` (cache npm, Gradle e SDK em D:). Para
  typecheck e testes que precisem de `node_modules` do app, sincronizar e rodar em
  `D:\slidedsl-mobile\app` (o `scripts/mobile_build.ps1` faz a cópia; robocopy manual também serve).
- O app consome o núcleo como `"@slidedsl/core": "file:../slidedsl-core"` (o build script copia
  `packages/slidedsl-core` para `D:\slidedsl-mobile\slidedsl-core`). Conferir que o Metro resolve o
  pacote (pode exigir `metro.config.js` com `watchFolders`) e que `font_metrics.json` entra no bundle.
- Rodar `scripts/mobile_build.ps1` só em T6 (no fim). Se houver um processo `java`/Gradle ativo de
  outro build, esperar terminar.

## Tarefas

### T1. Modelo no aparelho
- Tela "Modelo": opções Qwen3 0.6B (leve), 1.7B (recomendado), 4B (≥ 12 GB RAM), GGUF Q4_K_M de um
  repositório público no Hugging Face (registrar URL, tamanho e SHA-256 numa tabela `models.ts`;
  conferir que os arquivos existem).
- Sugestão pelo total de RAM (`expo-device`), download com progresso, só Wi-Fi por padrão, retomável,
  checksum, armazenado em `documentDirectory`, botão para apagar.
- `initLlama` com `n_ctx` modesto (4096) e uso de GPU desligado por padrão (opção).

### T2. Pipeline modo celular (`src/pipeline/`)
Portar de `alto_generation.py` o fluxo mínimo, com o perfil celular (Teste 7 do plano):
roteiro (OUTLINE_SYSTEM + `outline_schema`) → um slide por chamada (CONTENT_SYSTEM + `slide_schema`) →
`buildAlto` → no máximo **1 reparo** por slide com os diagnósticos → `renderPptx`.
Sem melhor de N, sem verificação de sustentação.
- Restrição de saída: JSON Schema convertido em GBNF (`convertJsonSchemaToGrammar` do llama.rn, ou o
  parâmetro de schema que a versão instalada aceitar). Conferir no código do llama.rn instalado.
- Prompts e schemas: gerar a partir do Python por script (`scripts/export_mobile_prompts.py`) para
  não divergir; o TS só lê o JSON exportado.
- Registrar por chamada: etapa, tokens de entrada/saída, `timings` do llama.cpp, tempo de parede,
  reparo sim/não (mesmos nomes de campo da Fase 0: `input_tokens`, `output_tokens`, `prefill_ms`,
  `decode_ms`, `wall_ms`).
- Teste em Node com modelo simulado: deck de 5 slides válido, reparo acionado por um slide inválido,
  limite de chamadas respeitado.

### T3. Fontes
- Padrão: sem pesquisa, com aviso "conteúdo sem fontes".
- Opção "colar texto": o usuário cola um texto e os fatos saem dele (portar a extração mínima de
  `documents.py` com conferência literal do trecho, `verify_fact`).
- Opção "Wikipedia" (com internet): API REST pt/en, sem chave; fatos com trecho literal conferido.

### T4. Telas
pedido (texto/voz, já existe) → escolha de nº de slides (4–8) e fonte → progresso por etapa com
cancelamento → resultado com miniaturas simples (a partir da IR, desenhadas com Views) → salvar e
compartilhar `.pptx` (`expo-sharing`).

### T5. Dados de teste
Botão "Exportar dados do teste": JSON com aparelho (modelo, RAM, Android), modelo GGUF, chamadas
(tokens, timings), total do deck, bateria e temperatura quando disponíveis. Formato compatível com
`custo.json` (`slidedsl.custo.v1`).

### T6. Build e verificação
- `scripts/mobile_build.ps1` gera o APK sem erro. Typecheck (`tsc --noEmit`) e testes Node passam.
- Relatório com o que foi testado em Node e o que só um aparelho pode confirmar.
