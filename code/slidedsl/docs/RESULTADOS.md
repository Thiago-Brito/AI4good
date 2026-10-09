# Resultados executados — 2026-10-08

Atualização incremental: `qwen3:4b-instruct` gerou cinco slides reais e o projeto
exportou PPTX com objetos editáveis, preservando respostas/AST/IR/diagnósticos em
outputs/demo_local. O comando Windows e a edição do artefato real no navegador
foram executados. Regressão atual: 123 Python, 2 Node, 4 Playwright passaram.
Ver [fluxo local](SLM_LOCAL_FUNCIONAL.md) e [diagnóstico anterior](DIAGNOSTICO_OLLAMA.md).
As evidências históricas abaixo continuam distintas da nova geração pelo SLM.
Avaliação concluída: 30 apresentações tentadas, 317 respostas auditadas, quatro PPTX
no modo JSON do pedido complexo. A demonstração direta de cinco slides passou na
validação estrita sem diagnósticos. Ver [RESULTADOS_INCREMENTAIS.md](RESULTADOS_INCREMENTAIS.md).

Implementação nova em `code/slidedsl`, sem consultar ou reutilizar protótipos.
Todas as fases de engenharia 0–8 foram executadas. Os dois Qwen3 foram instalados
e executados localmente; resultados empíricos em [RESULTADOS_OLLAMA.md](RESULTADOS_OLLAMA.md).
O experimento remoto continua condicionado à credencial OpenAI.
Fontes registradas em [refs/FONTES.md](../refs/FONTES.md), histórico por fase em
[PROGRESSO.md](PROGRESSO.md) e arquivos em [ARVORE.md](ARVORE.md).

## Verificação real

| Verificação | Resultado observado |
|---|---|
| `setup_windows.ps1 -SkipBrowserDownload` | Concluiu instalação fixada e Node portátil |
| Python / Node usados | 3.12.10 / 24.14.0 |
| Ruff check e format --check | Passaram |
| ESLint e Prettier do editor | Passaram |
| TypeScript e Vite build | Passaram; 193 módulos transformados |
| pytest pelo script Windows após geração incremental | 123 passaram, 1 aviso, 5,43 s |
| Renderer `npm test` | 2 passaram; geometria inválida e ZIP real |
| Renderer `node --check` | Passou |
| Playwright/Chrome com artefato SLM real | 4 passaram, 18,3 s |
| Editor build servido por FastAPI | HTML, JS/CSS e imagem local responderam HTTP 200 |
| `demo_windows.ps1` | Validação, AST, IR, PPTX e auditoria concluíram |
| Catálogo `examples/operacoes.sld` | Compilou um slide editável |

A primeira execução integrada encontrou permissões incompatíveis no diretório
temporário compartilhado do pytest: 90 passaram e 15 tiveram erro de preparação.
O script passou a criar temporários/cache únicos em `outputs/tests/`; a repetição
completa passou. O aviso restante é a depreciação de um alias AnyIO usado pelo
Starlette TestClient, sem falha funcional. Não foi suprimido.

O teste de navegador importa cinco slides, edita o título, valida, exporta DSL,
reimporta pela API e baixa um PPTX. Outro teste mostra D001 com X=1300, corrige
para X=80, revalida e exporta; o terceiro verifica tipos de portas e escopo do slide.
Nenhum erro JavaScript foi observado no percurso principal.

## Apresentação entregue

[outputs/apresentacao.pptx](../outputs/apresentacao.pptx) é um PowerPoint real,
com exatamente cinco slides: capa, contraste, proximidade, camadas e comparação.
A inspeção dos XMLs encontrou 25 objetos de texto, oito formas e uma imagem,
preservando IDs e ordem final da imagem acima do retângulo no slide 4.
O conteúdo não é uma imagem única por slide.

Fonte manual: [examples/cinco_slides.sld](../examples/cinco_slides.sld).
A rubrica do gabarito atingiu 17/17 itens; isso é cobertura estrutural e lexical
do exemplo, não resultado de geração por modelo nem nota estética. A auditoria
[delivery.json](../outputs/delivery.json) registra contagens, hashes, tamanhos e
equivalência semântica IR → DSL → IR. AST, IR e diagnósticos estão em
`outputs/ast.json`, `outputs/deck.json` e `outputs/validation.json`.

O slide 2 contém baixo contraste proposital e gera D002. Validação básica aceita
esse aviso; strict retorna falha. Não há erro fatal no gabarito. O asset PNG foi
criado para o projeto e tem licença registrada em `assets/LICENCA.md`.

Capturas: `outputs/editor_demo.png`, `editor_antes.png`, `editor_depois.png` e
`preview_slide_1.png` até `preview_slide_5.png`. Os previews de camadas e comparação
foram inspecionados visualmente. São previews geométricos do editor; não constituem
renderização pelo PowerPoint. PowerPoint COM não está instalado, portanto seu preview
opcional não foi executado.

## Estado dos modelos

Executado `slidedsl benchmark --models qwen3:0.6b,qwen3:4b,gpt-4.1-mini,gpt-4.1
--repetitions 5 --out outputs/reports_final`. Os relatórios JSON, JSONL, CSV,
configuração e análise foram materializados, sem respostas de modelos nessa primeira
verificação. Posteriormente, Ollama foi instalado e o experimento local concluiu
cinco repetições A/B/C por modelo em `outputs/reports_ollama_20261008/`.

| Modelo | Estado | Bloqueio |
|---|---|---|
| qwen3:0.6b | EXECUTADO | 5 repetições; 0/5 parse inicial e final, 10 reparos |
| qwen3:4b | EXECUTADO | 5 repetições; 0/5 parse inicial e final, 10 reparos |
| gpt-4.1-mini | NAO_EXECUTADO | OPENAI_API_KEY ausente |
| gpt-4.1 | NAO_EXECUTADO | OPENAI_API_KEY ausente |

O relatório atual [ANALISE.md](../outputs/reports_ollama_20261008/ANALISE.md) tem taxas
baseadas nas respostas reais, sem falhas de transporte. Todas falharam no parser;
semântica e design não foram alcançados, e nenhum PPTX de modelo foi gerado. O gabarito
manual permanece separado. Regimes de thinking diferentes, limite de tokens e
repetições sob seed fixa restringem conclusões; [análise completa](RESULTADOS_OLLAMA.md).
MockTransport e mock continuam sendo exclusivamente testes de infraestrutura.

## Reproduzir e abrir

A partir de `code/slidedsl`, em PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/setup_windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_windows.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_windows.ps1
.\.venv\Scripts\slidedsl.exe serve --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. Os scripts funcionam com caminhos com espaços e não
dependem de ativar a venv nem de alterar a política global do PowerShell. Após
instalar dependências, compilador, editor e testes não exigem provedores de IA.
Mais comandos em [README.md](../README.md), protocolo em [EXPERIMENTO.md](EXPERIMENTO.md)
e roteiro em [DEFESA_PROFESSOR.md](DEFESA_PROFESSOR.md).

## Escopo e limites

Implementados: gramática v1/v1.1, AST, IR com schema, semântica, geometria,
D001–D010, renderer PptxGenJS, CLI, FastAPI, editor React Flow, adapters e benchmark.
Canva/Google foram pesquisados e seus adaptadores futuros descritos; o backend
executável v1 é PptxGenJS. Nenhuma conta externa foi autenticada.

Grupos são lógicos, exportados como componentes editáveis; relações são executadas
sequencialmente, sem restrições reativas. Exportação DSL materializa a cena, sem
histórico das operações. Overflow e preview textual são aproximados; contraste pode
ser indeterminado. Não há importação de PPTX, animações, avaliação humana, validação
de beleza; a comparação empírica local está restrita ao protocolo documentado.
O repositório guarda checkpoints
locais das fases; artefatos de execução ficam em `outputs/`, fora do Git.
