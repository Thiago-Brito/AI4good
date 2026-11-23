# APK — rodada 2: geração no app

Data de início: 22/11/2026. Contrato: `docs/PLANO_CODEX_TCC_APK2_APP.md`, T1–T6.
Fontes registradas antes deste relatório em [refs/APK_APP_FONTES.md](../refs/APK_APP_FONTES.md).

## Implementado

- **T1 — modelo:** catálogo Qwen3 0.6B/1.7B/4B, Q4_K_M público, URL, tamanho em
  bytes e SHA-256 publicados e conferidos nos ponteiros LFS. Sugestão conservadora
  por RAM: 0.6B quando desconhecida/<6 GiB; 1.7B a partir de 6 GiB. 4B bloqueado
  quando RAM desconhecida/<12 GiB. Downloads em `documentDirectory`, progresso,
  Wi-Fi padrão, pausa/retomada persistida, conferência nativa de SHA-256 e exclusão.
  Mudança de rede, segundo plano e saída da tela pausam. Retomada é manual.
- **T1 — integração nativa:** só `src/llm/llamaRn.ts` conhece llama.rn. API instalada
  0.13.0-rc.12 inspecionada antes de usar: JSON Schema via `response_format`,
  `initLlama`, `getFormattedChat`, `tokenize`, `completion`, `stopCompletion`,
  `release`. Contexto 4096; CPU padrão, GPU opcional, thinking desligado. O adaptador
  mede o prompt e ajusta a saída até 1400 tokens; recusa menos de 512 livres.
- **T2 — pipeline:** módulos TS puros, com `TextModel` injetado. Roteiro → um slide
  por chamada → `buildAlto` → no máximo um reparo localizado → compilação final →
  `renderPptx`. Erros persistentes impedem exportação; avisos persistentes aparecem
  no resultado. Sem melhor de N, extração de tópicos ou verificador por modelo.
  Tetos `1 + 2*N` (sem fontes) e `2 + 2*N` (com extração). Schemas também são
  verificados depois do decoder. Cancelamento e falhas mantêm registros das chamadas.
- **T2 — contratos:** `scripts/export_mobile_prompts.py` importa as constantes e
  funções Python atuais e gera `src/pipeline/prompts.json`, incluindo SHA-256 dos
  arquivos de origem. `--check` acusa divergência. O TS só lê o JSON exportado.
  O Python existente e o núcleo da rodada 1 não foram alterados.
- **T3 — fontes:** sem pesquisa por padrão, aviso “conteúdo sem fontes” na tela e
  nas notas. Texto colado ou resumo REST da Wikipedia pt/en, título exato, sem chave.
  Uma chamada de extração, até três fatos aceitos, trecho literal normalizado,
  rejeição de números novos, trechos truncados, títulos, baixa relevância e duplicatas.
  Fonte com zero fatos válidos falha explicitamente. Texto limitado a 2600 caracteres
  para caber no contexto. Parafraseamento semântico não é verificado nesta rodada.
- **T4 — telas:** pedido com ditado original preservado (limpeza do reconhecedor
  ao sair), seleção 4–8 slides e fonte, modelo, progresso/cancelar, resultado com
  miniaturas desenhadas da IR em Views, salvar com SAF e compartilhar com Expo Sharing.
- **T5 — dados:** exportação `slidedsl.custo.v1` em sucesso/falha/cancelamento,
  chamadas com etapa/slide/tentativa/reparo/status, tokens de entrada/saída,
  prefill/decode/wall e timings brutos. Totais por etapa e deck, desconhecidos
  contabilizados sem inventar zero, GGUF/SHA/configuração, aparelho/RAM/Android,
  bateria antes/depois. Temperatura `null`, com motivo: Expo Battery não a expõe.
- **T6 — build:** fontes espelhadas para D:, pacote local `file:../slidedsl-core`,
  build explícito do núcleo, typecheck e testes antes do prebuild. Metro observa
  o pacote irmão, JSONs são módulos e o mapa browser do PptxGenJS é preservado.
  O script valida os destinos absolutos antes de `/MIR` e preserva `outputs/`.
  Hardlinks antigos da libc++ do Expo são preservados em D:/outputs do build e
  substituídos por cópias independentes antes da limpeza do Gradle.
  `android_env.ps1` também dirige temporários Metro/Hermes/Java para D:.

## Medido

| Verificação | Resultado |
| --- | --- |
| Typecheck do app (`tsc --noEmit`) | passou |
| `export_mobile_prompts.py --check` | passou |
| Ruff no novo exportador | passou |
| Testes Node do app | **36/36**, sem falhas ou skips |
| Pipeline, fonte, cancelamento, dados e catálogo | 24 testes |
| Adaptadores reais com fronteiras nativas simuladas + resolver Metro | 12 testes |
| Núcleo, corpus versionado e ZIP/browser | **43/43**, sem falhas ou skips |
| Python completo, sem alterações de comportamento | **718 passaram**, 2 avisos, 145,84 s |
| APK desta rodada | **gerado**, release 0.2.0, assinatura v2 válida |

O deck simulado de cinco slides passou sem erros Alto/design e fez seis chamadas;
um slide com título inválido no Alto fez sete, com exatamente um reparo contendo
A005; todos os cinco precisando reparar fizeram onze, teto completo. Um slide que
continua inválido encerra na segunda tentativa. Os ZIPs foram abertos e conferidos:
cinco XMLs de slides, objetos de texto e formas editáveis. Foram também gerados
decks de quatro e oito slides. Estes números medem o modelo simulado, não os GGUF.

Os onze testes de adaptador exercitam o arquivo real `llamaRn.ts` e o gerenciador
real de downloads por transpilação com módulos nativos substituídos: parâmetros,
contexto, limite de tokens, stopCompletion, uso parcial, Wi-Fi, espaço, checksum,
promoção do parcial, retomada entre instâncias, pausa por troca de rede e exclusão.
Não executam JNI nem o gerenciador de downloads Android real.

O primeiro build desta rodada falhou no Metro porque imports ESM `.js` apontavam
para fontes TS. O resolver agora mapeia apenas os arquivos fonte existentes para
`.ts`, mantendo JS compilado e JSON. Teste específico e export Android real passaram:
**673 módulos**, bytecode Hermes **8,4 MB**. O mapa do build confirmou explicitamente
`VoiceInput.tsx`, `pipeline/generate.ts`, `slidedsl-core/dist/index.js`,
`font_metrics.json` (7.303.826 caracteres no sourcesContent) e PptxGenJS ESM.
Evidências: `apk2-metro.log`, `apk2-bundle-verification.json` e mapa de fontes do Gradle.

A segunda tentativa parou ao limpar `libc++_shared.so` de um cache nativo antigo do
Expo, hardlink do SDK. O arquivo foi movido para `outputs/native-preserved` e a
mesma preservação de hardlinks foi incorporada ao script de build. O SDK e os
resultados anteriores não foram removidos. Logs anteriores preservados em
`apk2-build-attempt1.log` e `apk2-build-attempt2.log`.

A primeira tentativa de rodar os testes do núcleo numa cópia irmã falhou porque
o teste antigo espera `../../../renderer/render.mjs`. A cópia de verificação em
`D:/slidedsl-mobile/outputs/core-check/` preserva a estrutura original packages/
renderer/ e usa o TypeScript 5.9.3 do núcleo; a execução final teve 43 sucessos.
Nenhum teste do núcleo ou renderer existente foi editado.

Pytest usou basetemp em D:. Avisos: alias BlockingPortal depreciado e tentativa
sem permissão de gravar o cache preexistente do pytest no C:. A suíte passou.
Não houve `npm install` em `mobile/app` no C:, download de pesos na máquina,
commit, push, stash ou remoção de resultados anteriores.

## Arquivos desta rodada

Novos em `mobile/app/`: `README.md`, `.gitignore`, `package-lock.json`,
`metro.config.js`, `tsconfig.test.json`, `test/prepare.cjs`,
`test/pipeline.test.mjs`, `test/native-contracts.test.mjs`;
`src/models.ts`, `src/device.ts`, `src/ui.tsx`, `src/llm/llamaRn.ts`;
`src/storage/models.ts`, `exports.ts`;
`src/screens/ModelScreen.tsx`, `RequestScreen.tsx`, `ResultScreen.tsx`;
`src/pipeline/types.ts`, `contracts.ts`, `usage.ts`, `sources.ts`, `generate.ts`,
`testData.ts` e `prompts.json`.

Fora do app: `scripts/export_mobile_prompts.py`, `refs/APK_APP_FONTES.md` e este
relatório. Alterados: `App.tsx`, `src/VoiceInput.tsx` (somente abort ao desmontar),
`package.json`, `app.json`, `tsconfig.json`, `scripts/android_env.ps1` e
`scripts/mobile_build.ps1`. Assets, entrada Expo e núcleo da rodada 1 preservados.

## Evidências e reprodução

Evidências grandes ficam em D:, fora do repositório:

- `D:/slidedsl-mobile/outputs/apk2-build.log` — build da rodada 2.
- `D:/slidedsl-mobile/outputs/apk2-app-tests.log` — 36 testes do app.
- `D:/slidedsl-mobile/outputs/apk2-core-tests.log` — 43 testes do núcleo.
- `D:/slidedsl-mobile/outputs/apk2-pytest.log` — 718 testes Python.
- `D:/slidedsl-mobile/app/outputs/evidence/mock-5-slides.pptx` e `mock-custo.json`.
- `D:/slidedsl-mobile/outputs/apk2-typecheck.log`, `apk2-install.log` — verificações iniciais.

Reprodução: [README do app](../mobile/app/README.md). Ao mudar prompts Python,
execute o exportador e depois `--check`. O build só deve iniciar após o build
anterior encerrar; o `build1.log` já registrava `BUILD SUCCESSFUL` antes de T6.
Dependências novas: Expo Network/Battery nas versões do SDK 58, para Wi-Fi e bateria.
Lockfile versionável no app; nenhuma árvore node_modules/android/APK/GGUF no repo.

## Build final e integridade do APK

**BUILD SUCCESSFUL em 8 min 49 s**, exit code 0, 378 tarefas (350 executadas,
28 atualizadas). APK: `D:/slidedsl-mobile/SlideDSL-release.apk`,
**183.232.772 bytes (174,744 MiB)**. SHA-256:
`f83feb14dda4bbba9c397726464a0735c267be50ca9ccc48a18123f8241406d6`.

AAPT conferiu `br.slidedsl.app`, versão **0.2.0**, versionCode 1, minSdk 24,
targetSdk 36 e ABIs **arm64-v8a / x86_64**. `apksigner verify --verbose` saiu 0:
assinatura APK v2 válida, um assinante. O CRC de todos os arquivos ZIP passou,
não há GGUF dentro do APK, e `assets/index.android.bundle` (7.909.060 bytes)
é idêntico ao bundle produzido pelo Gradle. **21 arquivos de runtime/configuração**
foram comparados byte a byte entre fonte e cópia de build, todos iguais.

Evidências finais em `D:/slidedsl-mobile/outputs/`: `apk2-apk-verification.json`,
`apk2-apk-badging.log`, `apk2-apk-signature.log`, `apk2-bundle-verification.json`,
`apk2-source-manifest.json` e `apk2-build.log`. Os 36 testes e o typecheck também
passaram dentro da execução final do script. O APK anterior foi substituído pelo
novo no caminho de saída contratado; nenhum resultado em outputs foi apagado.

O build final começou antes de se detectar que o daemon Kotlin ainda tentava um
marcador no cache antigo do C:; a escrita foi negada e o compilador terminou por
fallback sem daemon. Também houve avisos de depreciação do Gradle/Android e de
métricas Android indisponíveis. Depois, `android_env.ps1` passou a definir
`user.home` Java e `kotlin.daemon.options=runFilesPath=...` em D:. Uma execução
Java com **a classe real configureDaemonOptions do Kotlin 2.2.10 instalado**
confirmou `D:/android/kotlin-daemon`, `D:/android/java-home` e temporário
`D:/android/tmp`. Evidência: `apk2-java-cache-check.log`. Essa última correção
muda somente caches; não se repetiu a compilação completa depois dela.

## O que só o aparelho confirma

- Download HTTPS dos pesos completos, alternância Wi-Fi/celular, pausa/retomada
  Android e após fechamento/segundo plano, checksum nativo dos arquivos grandes.
- Carga dos três GGUF, JSON Schema→gramática no llama.cpp real, qualidade pt-BR,
  taxa de reparos, viabilidade de contexto 4096, RAM/latência, aquecimento/bateria,
  GPU e ABI arm64. O corte por RAM é uma heurística, não medição de desempenho.
- Voz pt-BR offline/online e instalação do pacote de voz, permissões do microfone,
  ciclo de vida e interação com a geração. O serviço online do Android pode usar rede.
- Wikipedia em rede Android real; os testes de pt/en usam respostas simuladas.
- Cancelamento JNI, liberação da memória e nova geração após cancelar. Durante
  init/hash, cancelar aguarda a operação nativa retornar; completion usa stopCompletion.
- SAF, compartilhamento e abertura do PPTX em PowerPoint/LibreOffice, fontes reais,
  editabilidade e aparência. Miniaturas Views são esquemáticas.
- ADB local não iniciou o daemon neste ambiente; não houve instalação em aparelho.
  Não foi alegada inferência real nem consumo real dos GGUF.

A regra específica herdada da rodada 1 reserva `ROADMAP.md` e `docs/PROGRESSO.md`
ao revisor. Ambos já tinham alterações locais e foram preservados; os marcos
T1–T6 desta execução ficam neste relatório, sem sobrepor o trabalho existente.