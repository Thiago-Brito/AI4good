# APK — rodada 3: documentos no aparelho

Data: 23/11/2026. Contrato: `PLANO_CODEX_TCC_APK3_DOCUMENTOS.md`, T1–T5.
Fontes registradas previamente em [refs/APK_DOCUMENTOS_FONTES.md](../refs/APK_DOCUMENTOS_FONTES.md).

## Implementado — marcos T1–T4

- T1: seletor existente Expo DocumentPicker; modo `document`; plugin local
  `plugins/withDocuments.js` registra SEND/VIEW com PDF/DOCX/TXT/MD, singleTask.
  Módulo Expo local captura intent inicial e novos intents, resolve nome/MIME
  e copia `content://`/`file://` em blocos para cache privado, com teto real de
  10 MiB mesmo quando o provedor omite o tamanho. Recebimento abre Pedido com
  nome visível; durante geração, a seleção espera seu encerramento.
- T2: UTF-8 estrito com BOM e fallback Latin-1; DOCX via JSZip, XML limitado
  incrementalmente a 4 MiB por entrada, parágrafos, entidades, tabs, quebras e
  estilos Heading/Título (inclusive nomes em `styles.xml`). Sem DTD, macros ou
  execução de campos. Títulos são metadados e não fatos. Teto de 200 mil
  caracteres; arquivos vazios e formatos inválidos falham em português.
- PDF: escolhida **opção (a), módulo Expo local Kotlin + PdfBox-Android
  2.0.27.0**. Extrai página a página, conta caracteres durante a escrita,
  fecha arquivo e documento com `use`. PDF sem camada textual falha com
  “PDF sem texto selecionável”. Não há OCR. PDF protegido/corrompido tem erro
  explícito. PDF.js demandaria compatibilidade adicional de APIs web/worker
  no Hermes. A dependência Android tem versão estável antiga; não se afirma
  manutenção recente. Nenhum documento é enviado a servidor.
- T3: módulo TS puro porta trechos de 900 caracteres, título, página e número;
  TF-IDF segue a fórmula lexical de `documents.py`. Consulta geral/vazia
  distribui trechos pelas seções até o final, em ordem; consulta específica
  sem correspondência falha. Até seis chamadas `document_extract`, conferência
  literal por trecho, deduplicação e rejeição de novos números. Seções com
  fatos sugerem o roteiro geral. Citações `documento:<nome>#trecho-<n>`;
  pedido vazio recebe “Apresente os pontos principais do documento <nome>”.
  Tetos: `1+2*N`, `2+2*N` ou `7+2*N` chamadas conforme a fonte.
- T4: nome/tipo/tamanho no Pedido; páginas (PDF), caracteres, trechos e fatos
  no progresso/resultado; estágios Lendo documento, Extraindo fatos i/n,
  Planejando roteiro e Slide i/n. `slidedsl.custo.v1` recebe metadados e
  chamadas de extração, inclusive resultados parciais em falha/cancelamento.

Dependências: JSZip 3.10.1 passa de transitiva a direta, pois o app agora o
importa; expo-modules-core 58.1.0 é declarado diretamente para a ponte nativa
(a mesma versão já instalada pelo SDK). Nova dependência de extração PDF:
`com.tom-roush:pdfbox-android:2.0.27.0`. Não há novo parser npm.

## Preservação e escopo

O Python e o núcleo TS não foram alterados. `llamaRn.ts` conserva prompt já
formatado e `response_format` estrito, sem `messages` na completion. SHA-256
inicial: `825f392f1b28675649266948f42738da919f0ce7a8923c434d7ef8d79f0b7d75`.
Sem commit, push, stash, download de GGUF ou npm install no C:.
Artefatos e dependências ficam em D:. Os arquivos de roadmap/progresso existentes
foram preservados: a regra específica herdada dos planos APK 1/2 os reserva
ao revisor; os marcos desta execução ficam neste relatório.

## Medido — T5

Typecheck passou; testes Node do app **50/50**, sem falhas/skips (4,61 s),
e núcleo **43/43**, sem falhas/skips (3,28 s). Contratos exportados do Python:
`export_mobile_prompts.py --check` passou. O arquivo `llamaRn.ts` conserva o
mesmo SHA-256 inicial.

Suíte Python completa: **718 passaram**, um aviso de depreciação do AnyIO,
em **123,75 s**, sem falhas. Cache e basetemp explicitamente em D:.

O teste de documento gerou **31.287 caracteres**, seis seções e cinco slides
editáveis (ZIP inspecionado): arquivo de **31.294 bytes**, **36 trechos**, seis
selecionados. Foram **17 chamadas**: seis extrações, roteiro,
cinco conteúdos e cinco reparos, exatamente o teto. Seis citações inventadas
foram rejeitadas. O maior prompt teve **2.725 tokens simulados** pelo orçamento
conservador do teste (bytes UTF-8 / 2 + 64); não é tokenização Qwen medida.
O adaptador real preservado mede `formatted.prompt` com o tokenizador nativo
antes de cada completion, reserva 32 tokens e exige ao menos 512 livres;
pedidos excessivos são recusados antes da inferência. O teste não executa JNI.

O build anterior `build4.log` encerrou com sucesso; processos Java observados
durante a implementação desapareceram antes de iniciar o build desta rodada.
O script agora também recusa execução se encontrar Java ativo, antes da cópia.
A primeira tentativa desta rodada foi interrompida ao observar que o espelho
excluía toda pasta chamada `android`, inclusive a do módulo local. Foram encerrados
somente os dois processos Java iniciados por essa tentativa. A exclusão foi
restrita aos caminhos absolutos da raiz, na origem **e** no destino, preservando
pastas geradas e `outputs/`; o script também exige o Gradle do módulo copiado.
Não foi entregue o APK incompleto dessa tentativa. APK e verificações finais
estão registrados abaixo.

A correção da cópia foi exercitada em uma árvore pequena em D:: **3/3
verificações** (fontes `modules/local/android` copiadas, `android/` gerado e
`outputs/` do destino preservados). Evidência: `apk3-copy-verification.json`.
O `.gitignore` do app também foi ancorado em `/android/` e `/ios/`, para que
o código nativo local seja versionável; só seu `build/` e `.gradle/` são ignorados.

Na segunda tentativa, o autolinking real resolveu
`br.slidedsl.documents.SlideDocumentsModule` (evidência `apk3-autolinking.json`),
o módulo compilou em Kotlin e o Metro empacotou **679 módulos**. A execução usou
Node **22.13.1**, conforme o ambiente/plano APK 1; JDK 17 e SDK Expo 58.

Essa tentativa falhou em R8 por `com.gemalto.jp2.JP2Decoder`, decodificador
JPEG2000 opcional documentado pelo PdfBox-Android. O `consumer-rules.pro` local
aplica somente `-dontwarn` para essa classe (a regra indicada pelo R8), sem
desligar otimização nem adicionar o antigo JCenter. O fluxo não renderiza
imagens JPX. A retomada usa `-SkipPrebuild`: configuração Expo preservada e
gradlew existente obrigatório, com o mesmo typecheck/testes e cópia de fontes;
isso evita repetir a compilação nativa já concluída. O daemon Kotlin ocioso
criado por esta tentativa foi encerrado antes de iniciar outro build.

Na retomada, o teste legado de exclusão de modelo falhou (49/50): alterações
concorrentes em `storage/models.ts` e `App.tsx`, feitas durante o build anterior,
acrescentaram o cache `.verified.json` e `ensureVerified`. Essas alterações foram
preservadas. A expectativa antiga de três exclusões foi atualizada para conferir
os quatro caminhos completos; nenhum comportamento de modelos foi revertido.
Essa tentativa parou antes do Gradle e seu log foi preservado em
`apk3-build-attempt3.log`.

## Build final e integridade — T5 concluída

**BUILD SUCCESSFUL em 13 min 58 s**, exit code 0, **416 tarefas** (37 executadas,
379 atualizadas), com `scripts/mobile_build.ps1 -SkipPrebuild`. O script repetiu
typecheck e **50/50 testes do app**, sem falhas/skips (3,53 s), antes do Gradle.
O build do núcleo também foi executado pelo script. Nenhum novo build foi
iniciado enquanto havia outro processo Java ativo.

APK: **`D:/slidedsl-mobile/SlideDSL-release.apk`**,
**189.372.592 bytes (180,60 MiB)**. SHA-256:
`dde975c3d2a04ebccaa8dd2ca101fb7d2e46f4dba6c15aa109c772cbaedb93b1`.

- AAPT: `br.slidedsl.app`, versão **0.3.0**, versionCode **3**, minSdk 24,
  targetSdk 36, ABIs **arm64-v8a / x86_64**. Manifesto binário confirma
  singleTask e filtros SEND/VIEW para os cinco MIME suportados.
- `apksigner verify --verbose`: exit 0, assinatura **v2 válida**, um assinante.
- CRC de todos os arquivos ZIP passou; **zero GGUF** dentro do APK.
- Bundle Hermes **7.984.360 bytes**, idêntico ao arquivo gerado pelo Gradle.
  Metro: **679 módulos**. Mapa Hermes final: **667 entradas de fontes**, com
  pipeline/documentos, adaptador de armazenamento, telas e `llamaRn.ts` presentes.
- **19 recursos do PdfBox** presentes, inclusive glyphlist; strings da ponte
  `SlideDocuments`, `extractPdf` e `takePendingDocument` presentes no DEX.
- **30/30 arquivos de runtime/configuração** iguais byte a byte entre fonte e
  cópia de build; dependências também conferidas. Hash protegido de
  `llamaRn.ts` continua exatamente igual ao inicial.

Evidências finais em `D:/slidedsl-mobile/outputs/`: `apk3-build.log`,
`apk3-apk-verification.json`, `apk3-apk-badging.log`, `apk3-apk-manifest.log`,
`apk3-apk-signature.log` e `apk3-source-manifest.json`. Verificador local:
`verify_apk3.py`. Os logs de tentativas anteriores foram preservados.
Avisos remanescentes são de depreciação do Gradle/Expo/Android, configuração de
tema opcional e código OpenCL do llama.cpp; não impediram a compilação final.

Primeira verificação: typecheck passou; testes 49/50. O gerador do documento
de teste produzia 25.437 caracteres, abaixo dos 30 mil exigidos; corrigido para
mais de 30 mil, com asserção também no teste de ponta a ponta. Não era falha
da recuperação. O JSZip tem `internalStream` público ausente nas declarações
TS; foi tipada apenas essa fronteira documentada.

## Arquivos e reprodução

Criados: `src/pipeline/documents.ts`, `src/storage/documents.ts`,
`plugins/withDocuments.js`, `modules/slidedsl-documents/` (config, package,
Gradle, consumer-rules, manifesto e módulo Kotlin), `test/documents.test.mjs` e
`test/documents-native.test.mjs`, todos em `mobile/app/`; este relatório e
`refs/APK_DOCUMENTOS_FONTES.md`.

Alterados em `mobile/app/`: `App.tsx`, `app.json`, `package.json`, lockfile, `.gitignore`,
`README.md`, `src/pipeline/sources.ts`, `generate.ts`, `testData.ts`,
`src/screens/RequestScreen.tsx`, `ResultScreen.tsx` e a expectativa antiga em
`test/native-contracts.test.mjs`.
`scripts/mobile_build.ps1` ganhou a proteção de Java ativo, cópia correta do
Android do módulo local e conferência de presença das fontes nativas.

Comandos executados (PowerShell, raiz do repositório):

```powershell
. ./scripts/android_env.ps1
.venv/Scripts/python.exe scripts/export_mobile_prompts.py --check
# Typecheck e testes do app rodados na cópia isolada em D:; repetidos no build.
Push-Location D:/slidedsl-mobile/outputs/apk3-check/app
npm run typecheck
npm test
Pop-Location
# Estrutura de teste preserva o caminho relativo do renderer exigido pelo núcleo.
Push-Location D:/slidedsl-mobile/outputs/core-check/packages/slidedsl-core
npm test
Pop-Location
.venv/Scripts/python.exe -m pytest -q --basetemp=D:/slidedsl-mobile/outputs/apk3-pytest-temp -o cache_dir=D:/slidedsl-mobile/outputs/apk3-pytest-cache
# Somente após Get-Process java não retornar processos:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/mobile_build.ps1
# Retomada final após corrigir somente a regra R8, com configuração Expo igual:
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/mobile_build.ps1 -SkipPrebuild
.venv/Scripts/python.exe D:/slidedsl-mobile/outputs/verify_apk3.py
```

Evidências: `D:/slidedsl-mobile/outputs/apk3-{typecheck,app-tests,core-tests,pytest}.log`,
`apk3-build.log`, `apk3-build-attempt1.log`, `apk3-build-attempt2.log`,
`apk3-build-attempt3.log`; decks e dados em
`D:/slidedsl-mobile/app/outputs/evidence/document-{5-slides.pptx,custo.json,context.json}`.
A cópia isolada em `outputs/apk3-check/app/outputs/evidence/` também os preserva.

## O que só o aparelho confirma

- Recebimento por Arquivos/Drive/WhatsApp/e-mail, cold start e app já aberto,
  permissões temporárias, provedores remotos e nome/MIME retornados por cada um.
  Node testa o adaptador e plugin reais com fronteiras simuladas; não Android.
- Extração real PdfBox em PDF textual, escaneado, criptografado, fontes/colunas
  diferentes e páginas grandes. Testes Node verificam apenas o contrato de
  páginas e erro sem texto; não executam o PdfBox-Android.
- DOCX/TXT/MD no Hermes e leitura nativa do provedor. Fixtures Node são ZIPs
  DOCX pequenos gerados no teste; não representam todo o padrão OOXML
  (cabeçalhos, rodapés, notas e imagens não são extraídos).
- Geração GGUF real, qualidade das paráfrases, tokenização Qwen, latência,
  RAM, aquecimento, bateria e cancelamento JNI. Cancelar cópia/leitura PDF
  aguarda a operação nativa retornar. Semântica de cada paráfrase não é provada
  pela conferência literal; a seleção de seis trechos é uma amostragem.
- SAF, compartilhamento e abertura/editabilidade/aparência no PowerPoint.
  Não foi alegada inferência de modelo real nem consumo real de GGUF nesta rodada.
