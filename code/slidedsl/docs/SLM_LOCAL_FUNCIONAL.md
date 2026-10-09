# SlideDSL com SLM local no Windows

Fontes: [FONTES.md](../refs/FONTES.md). O sistema existente foi estendido: a GLC,
o parser Lark, a AST, a semântica, a IR, o compilador PptxGenJS e o editor continuam
sendo a cadeia de validação e exportação. Não há seleção de um deck manual.

## Executar a demonstração com um comando

Na pasta `code/slidedsl`, com o ambiente do projeto instalado:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_slm_windows.ps1 -Strict
```

O script inicia Ollama se necessário, baixa a tag ausente, gera cinco slides com
`qwen3:4b-instruct`, salva evidências e exporta PPTX. Inicia o editor em localhost:8000
e abre `/?demo=1`, carregando o programa efetivamente gerado. Cada execução usa uma
pasta nova em `outputs/demo_local/run-<id>/`. `-NoEditor` executa a geração sem abrir
o navegador. Se a apresentação falhar, o comando termina com erro e os registros
ficam disponíveis; não abre um exemplo manual em seu lugar.

Pedido personalizado e modo direto:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_slm_windows.ps1 -Request 'Crie cinco slides sobre reciclagem, com títulos, explicações curtas e formas decorativas.'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo_slm_windows.ps1 -Mode direct -Strict
```

O pedido padrão é [demo_slm_local.txt](../benchmark/prompts/demo_slm_local.txt), uma
introdução ao sistema. O pedido original mais complexo de contraste, proximidade,
camadas e comparação é usado separadamente na avaliação, sem substituir seu texto.

## Modos e contrato

**A, `direct`:** o SLM produz código SlideDSL de um slide. O parser recebe a saída
inteira; Markdown, comandos inventados e texto antes/depois do programa não são
recortados. O número pode ser o global solicitado ou 1. A análise isolada usa 1 e
a montagem usa 1..5; essa normalização estrutural é registrada em `normalization`
e `original_ast.json`, sem alterar textos, referências, dimensões ou operações.
O `raw.txt` continua com os bytes recebidos em `message.content`.

**B, `json`:** Ollama recebe um JSON Schema em `format`, também incluído na mensagem.
O SLM gera `title`, `texts`, `shapes`, `images` e `operations`, incluindo conteúdo,
IDs, coordenadas, dimensões, cores e operações. O schema restringe títulos, tipos,
tokens, quantidade de elementos e caminho local de imagem; não contém os slides
do pedido nem os seus textos. Pydantic verifica novamente o objeto recebido.
O conversor imprime comandos pelo printer existente. A ordem contratual é formas,
imagens, título, textos, operações explícitas; não reajusta geometria nem referências.
A SlideDSL produzida passa pelo parser e pela semântica existentes. Somente sua
IR validada chega ao compilador. Não há exportação direta do JSON do SLM para PPTX.

Ambos usam uma solicitação por slide e até duas respostas adicionais quando falha
a validação. Cada reparo recebe o pedido, a resposta anterior e diagnósticos com
evidências; D010 inclui também a altura mínima sugerida pela estimativa. Exemplos
de jardinagem ensinam a sintaxe, sem fornecer uma apresentação pronta para a tarefa.
O foco de cada slide é extraído de `Slide N:` do próprio pedido quando esse padrão
existe. Pedidos sem essa marcação também são aceitos.

Temperatura padrão 0,1, contexto 8192, saída máxima 4096 tokens por chamada, seed 42
na demo e timeout 300 s. `/api/show` descobre os controles de thinking; nesta tag
instrucional as respostas observadas usam `think=false` e não trazem thinking.
`qwen3:4b` do experimento anterior é outra tag/digest e não é um alias utilizado aqui.

`complete` exige `done=true`, `done_reason=stop` e content não vazio. Esse indicador
mede encerramento da API, não qualidade factual nem completude de cada frase.
Sintaxe, semântica, erros fatais de design, avisos e PPTX são indicadores separados.
Na validação padrão, avisos não bloqueiam o compilador; `-Strict`/`--strict` também
bloqueia D002/D008/D010 com gravidade AVISO. INFORMAÇÃO continua sendo registrada.
Uma apresentação validada pode descumprir partes do pedido ou conter texto incorreto.

## Evidências e reprodução

Cada execução salva `configuration.json`, `model_show.json`, `system.txt`,
`request.txt`, `report.json` e, para cada slide/rodada, `user.txt`, `request.json`,
`response.json`, `raw.txt`, métricas, diagnósticos, DSL, AST e IR quando alcançados.
Depois de cinco slides aceitos: `presentation.sld`, `ast.json`, `ir.json`,
`diagnostics.json`, `presentation.pptx` e inspeção dos objetos nativos.

Os corpos completos de resposta incluem o thinking separado quando retornado;
ele nunca é usado como código. Hash de `raw.txt` cobre bytes exatos UTF-8. Hashes
de mensagens/programa nos relatórios cobrem texto UTF-8 com LF, normalizado pelo
I/O textual Python; arquivos textuais no Windows podem ter CRLF. O manifesto do
editor verifica o hash dos bytes do arquivo, inclusive suas quebras de linha.

```powershell
.\.venv\Scripts\python.exe scripts/diagnose_ollama.py
.\.venv\Scripts\python.exe scripts/inspect_slm_delivery.py outputs/demo_local/windows_strict
.\.venv\Scripts\slidedsl.exe validate outputs/demo_local/windows_strict/presentation.sld --strict
.\.venv\Scripts\slidedsl.exe evaluate-local --prompt-file benchmark/prompts/tarefa_cinco_slides.txt --repetitions 5 --out outputs/nova_avaliacao
```

`evaluate-local` executa qwen3:4b-instruct, qwen3:0.6b e qwen2.5:3b-instruct,
nos modos direct/json, com seeds 42..46 pareadas por repetição. Salva JSON e CSV
por apresentação e relatório por modelo/modo. `--resume` reutiliza apenas execuções
completas sob configuração idêntica. Execuções parciais e saídas existentes são
preservadas e não são sobrescritas. A geração em uma pasta nova é a forma de repetir
uma execução parcial. Os conjuntos antigos A/B/C continuam intactos.

## Editor e testes

`/api/local-demo` resolve exclusivamente arquivos .sld em outputs e verifica o
manifesto. `/?demo=1` importa essa fonte pela mesma API usada no editor. É possível
selecionar objetos, modificar texto/geometria, validar, exportar DSL e baixar um
novo PPTX. O original gerado não é editado automaticamente.

O teste opcional de navegador exige uma execução real já concluída:

```powershell
$env:SLIDEDSL_REAL_DEMO='outputs/demo_local/windows_strict'
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test_windows.ps1
```

Sem essa variável, o teste de artefato SLM é marcado como ignorado; os testes offline
continuam independentes de modelos e não são contados como gerações reais.
O manifesto deve apontar para a pasta informada; a CLI demo-local publica o último
resultado compilado. Capturas do editor são previews geométricos, não renderizações
pelo aplicativo PowerPoint. A auditoria ZIP/XML confirma objetos editáveis e textos,
sem substituir revisão humana de conteúdo ou aparência.

## Correção de acesso Windows

A auditoria encontrou um PPTX gerado pelo processo isolado que herdou a DACL privada
de TemporaryDirectory, impedindo o usuário de ler o resultado. O compilador agora
cria o arquivo de publicação na pasta de destino e faz a troca atômica ali, herdando
as permissões da entrega. `normalize_artifact_access.py` permite republicar apenas
PPTX de subpastas explícitas de outputs, conferindo hash antes/depois. Os arquivos
recuperados conservaram todos os bytes; manifestos artifact_access registram isso.
Não foram reescritas respostas, AST, IR nem resultados de geração para essa correção.
