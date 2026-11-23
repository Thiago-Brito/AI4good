# APK — rodada 1: núcleo TypeScript

Data: 22/11/2026. Contrato: [PLANO_CODEX_TCC_APK1_CORE.md](PLANO_CODEX_TCC_APK1_CORE.md),
T1–T5. Fontes registradas antes deste texto em
[refs/APK_CORE_FONTES.md](../refs/APK_CORE_FONTES.md).

## Implementado

- **T1:** `scripts/export_parity.py` descobre os exemplos e todos os
  `outputs/**/apresentacao.slda` acessíveis. Exporta entrada Alto, fatos, dimensões
  e metadados de imagens, IR ou `null`, diagnósticos e manifesto com exclusões e
  erros de acesso. Seleção determinística de até 25 fixtures por cobertura de
  tipos, layouts realmente executados, famílias e estilos.
- **T1, tipografia:** `src/data/font_metrics.json` contém as seis famílias de
  `text_metrics.FAMILIES`, normal/negrito, Latin-1, pontuação e caracteres do corpus.
  Há avanços/kerning a 16384 px, SHA-256 das fontes, altura-x e tabelas exatas dos
  rasters de 10–96 pt inteiros usados pelo Builder. Regras e temas foram
  exportados dos YAML para JSON.
- **T2:** `packages/slidedsl-core` é um pacote TypeScript ESM com tipos públicos
  Alto/IR, `validateAlto` e `buildAlto(deck, facts, images)`. O resultado inclui
  IR 1.1 e diagnósticos. Layouts, decisões editoriais, grade, seleção de variantes,
  geometria, ocupação e D001–D010 foram portados.
- **T2, manutenção:** `scripts/port_core.py` traduz as funções puras atuais para
  `src/port.ts`, com fluxo de controle TypeScript e auxiliares explícitos em
  `pythonCompat.ts`. O pacote não contém um interpretador Python, subprocessos,
  I/O ou consultas às referências de paridade. Modelos públicos têm interfaces;
  o trecho gerado usa `@ts-nocheck`, de modo que a compilação não prova a tipagem
  interna do porte. A equivalência é verificada pelos testes de execução.
- **T2, semântica:** o Builder emite AST `add`/`notes`; esse caminho gera a IR
  diretamente. As linhas/colunas equivalentes ao printer/parser Python são
  preservadas sem imprimir ou analisar a DSL no app.
- **T3:** comparação recursiva exige mesmas chaves, strings, IDs, ordem, Z e
  diagnósticos na mesma sequência (código e severidade). Números têm tolerância
  absoluta de 1e-6. `npm run parity:full` grava a primeira diferença de cada
  falha em `outputs/parity/relatorio.json` e sai com código 1 se houver falhas.
- **T4:** `renderPptx(ir, {images})` retorna `Promise<ArrayBuffer>`, com imagens
  PNG/JPEG em data URI, textos e formas editáveis, notas e o mesmo mapeamento
  geométrico do renderer existente. O chamador decide como salvar o arquivo.
- **T5:** este relatório, README do pacote e evidências locais de execução.

O Python usa `round(pt*96/72*4)` com empate para o inteiro par. Nesta máquina,
Pillow/FreeType usa BASIC: avanços individuais têm arredondamento para pixels
inteiros, e os pares acrescentam ajustes em 1/64 px. A largura final divide por
4 e aplica margem 1.04 (1.14 no fallback). Escalar somente a medida grande
produziu diferenças de layout; as tabelas por raster eliminaram as diferenças
medidas. As quebras mantêm os pisos legados de Arial e o comportamento por
família de `text_height`/`needed_height`.

## Medido

| Verificação | Resultado |
| --- | --- |
| Fixtures versionáveis selecionadas | **24/24, 100%** |
| Fixtures que chegam à IR | 10 decks, 63 slides, 775 elementos |
| Fixtures com erro Alto e IR nula | 14, também exigem diagnósticos idênticos |
| Corpus, medição intermediária após primeiro pytest | 254/254, 100% |
| **Corpus final, após o último pytest e nova exportação** | **261/261, 100%**, sem classes de falha restantes |
| Corpus final com IR / sem IR | **247/247** cenas equivalentes; **14/14** interrupções Alto equivalentes |
| Casos independentes de largura e altura de texto | 300, seis famílias × dois pesos × cinco tamanhos × cinco textos |
| Comparação ZIP dos renderers | 10 decks de fixtures (63 slides), mais cena com texto, retângulo, elipse, seta e imagem |
| Execução sem APIs de Node | ZIP com texto e imagem gerado em contexto VM isolado, usando PptxGenJS browser |
| `pytest` completo | **718 passaram**, 2 avisos, 137.75 s |
| `npm test` em `renderer/` | **2 passaram**, sem falhas |
| `npm test` no pacote novo | **43 passaram**, sem falhas ou skips; inclui build TypeScript |
| Ruff nos dois scripts novos | passou |

As fixtures cobrem os **11 tipos de slide**, com layouts efetivamente executados,
os **seis estilos** e as quatro famílias encontradas nas IR do corpus:
Calibri, Cambria, Georgia e Trebuchet MS. Arial e Verdana também têm tabelas
exportadas e casos de medição. Não se deve confundir os 14 casos com IR nula
com decks renderizáveis: eles verificam a interrupção correta pela validação.

O número do corpus é uma fotografia do filesystem: eram 247 decks na primeira
varredura; cada execução completa do pytest cria mais sete `apresentacao.slda`
em seu novo `--basetemp`. A medição final e sua decomposição estão no manifesto
e em `outputs/parity/relatorio.json`.

A varredura registrou **119 diretórios inacessíveis**, sobretudo resultados
antigos de testes. Não houve exclusão por erro de parser nas varreduras
executadas. O denominador de paridade inclui os decks efetivamente encontrados
e exportados; não afirma cobertura de arquivos que o sistema operacional
impediu de enumerar. Os caminhos e motivos constam do manifesto.

## Reprodução

Na raiz, Python 3.12 e Node **v22.13.1** / npm 10.9.2:

```powershell
.venv/Scripts/python.exe -m pytest -q --basetemp=outputs/tests/t225000
.venv/Scripts/python.exe scripts/export_parity.py
.venv/Scripts/python.exe scripts/port_core.py
.venv/Scripts/python.exe -m ruff check scripts/export_parity.py scripts/port_core.py

# Necessário neste sandbox Windows para evitar realpath dos ancestrais sem acesso.
$env:NODE_OPTIONS='--preserve-symlinks --preserve-symlinks-main'
Set-Location renderer
npm test
Set-Location ../packages/slidedsl-core
npm ci --cache ../../outputs/npm-cache
npm test
npm run parity:full
```

Use um `t<hhmmss>` novo em cada reprodução do pytest; não reutilize a pasta da
execução acima. Para repetir a exportação com as mesmas fontes sem remedi-las,
use `scripts/export_parity.py --skip-fonts`. Execute a paridade completa depois
que a exportação terminar. O lockfile npm fixa as dependências; só foram
declaradas `pptxgenjs`, `typescript` e `@types/node`.

Evidências: `outputs/apk-core-pytest.log`, `outputs/apk-core-renderer.log`,
`outputs/apk-core-tests.log`, `outputs/apk-core-export.log`,
`outputs/parity/manifest.json`, `outputs/parity/relatorio.json` e os PPTX
em `outputs/apk-core-render/`. Nenhum arquivo de `outputs/` foi apagado.

Os avisos do pytest são a depreciação `BlockingPortal` do Starlette/AnyIO e a
impossibilidade de escrever o cache antigo de pytest. Não houve falha de teste.

## Fora desta rodada e pendências

- App React Native, integração llama.rn/JSON Schema→GBNF, Metro, instalação em
  Android e medição em aparelho: **não executados**. O teste de VM comprova a
  geração sem APIs de Node, mas não substitui um teste React Native. PptxGenJS
  declara um mapa `browser`; sua resolução no Metro precisa ser confirmada.
- Parser/printer Alto e 1.1, comandos arbitrários da DSL de baixo nível, IA,
  pesquisa, download/abertura de imagens e leitura de arquivos ficam fora do
  pacote, conforme o caminho do app definido no plano. O analisador TS cobre
  os comandos emitidos pelo Builder Alto. D001–D010 operam sobre a IR.
- `svg_diagrams.py` não foi portado: o layout Alto atual não o chama. Os
  gráficos e etapas desse caminho usam formas editáveis.
- Caracteres fora da tabela usam a largura de `?`; shaping de outros alfabetos,
  precisão de tamanhos fora dos rasters exportados e comportamento visual do
  Office não foram medidos. A paridade desta rodada é relativa ao compilador
  Python e às fontes registradas nesta máquina.
- O acesso aos 119 diretórios registrados depende das permissões do ambiente.
- `npm audit` observou duas entradas de severidade alta, `image-size` e seu
  dependente PptxGenJS 4.0.1, por parsers JXL/HEIF/ICNS do pacote transitivo.
  Registro em `outputs/apk-core-npm-audit.json`. A atualização dessa cadeia
  deve ser avaliada separadamente; este porte mantém a versão do renderer.

Próxima rodada sugerida: um app React Native mínimo que importe o pacote,
valide JSON produzido por llama.rn, mostre os diagnósticos e compartilhe o
ArrayBuffer como PPTX. Usar as mesmas fixtures no aparelho e medir tempo,
memória das tabelas tipográficas e exportação PNG/JPEG antes de ampliar a UI.

`ROADMAP.md`, `docs/PROGRESSO.md`, os módulos Python existentes e
`renderer/render.mjs` foram preservados por esta rodada. Não houve commit,
push ou stash.
