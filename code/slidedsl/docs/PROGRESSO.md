# Progresso de implementação

## 2026-10-08 — início / fase 0
Lidos integralmente AGENTS.md da raiz, AGENTS.md do projeto acadêmico e a especificação.
Criado repositório vazio em code/slidedsl. Nenhum protótipo consultado ou reutilizado.
Comandos executados: git init; python --version (3.12.10); node --version (22.13.1);
python -m venv .venv. Node 24 será provisionado localmente sem alterar o sistema.
Próximo passo: dependências, evidências oficiais e parser.

## Fase 0 — concluída
Ambiente Python 3.12.10 instalado via pip -e .[dev]; Node portátil 24.14.0.
Dependências públicas requereram execução fora do sandbox de rede e foram instaladas.
Tentativa inicial de pip no sandbox não completou; fallback urllib encontrou bloqueio de TLS.
PptxGenJS 4.0.1 instalado; lockfiles preservados. Pesquisa oficial e matriz materializadas.
Texpace consultado por árvore/API e cinco snapshots; licença MIT registrada.
Comandos: pip install -e .[dev], npm install, python scripts/research_matrix.py.

## Fase 1 — concluída
Lark LALR, AST Pydantic, printer e diagnósticos com linha/coluna implementados.
Correção mínima da gramática: TEMA explícito preserva o valor que literais anônimos descartavam.
Executado pytest tests/test_grammar.py -q: 21 passed.
Executado slidedsl ast examples/minimo.sld --out outputs/ast_minimo.json: sucesso.
Próximo passo: semântica, IR, geometria e depois extensões v1.1.

## 2026-10-08 — Fase 2
Núcleo v1 validado: 47 testes passaram. Extensões 1.1 acrescentadas depois: grupos, eixos, distribuição, camadas, tokens, blocos e anotações. Suite: 68 passed. JSON Schema gerado; roundtrip AST/IR/DSL preserva cena e relações. Próximo passo: regras D001–D010.

## 2026-10-08 — Fase 3
Regras D001–D010 implementadas e testadas, configurações YAML e diagnósticos com evidência. Executado pytest -q: 83 passed, incluindo limites, contraste conhecido/indeterminado, alinhamento com tolerância, proximidade, densidade, união de oclusões, Z, dimensões e overflow aproximado. Próximo: PptxGenJS.

## 2026-10-08 — Fase 4
Backend Node 24/PptxGenJS 4.0.1 integrado. Executados pytest -q: 89 passed; npm test do renderer: 2 passed; CLI validate/ast/ir/compile: sucesso. outputs/apresentacao.pptx tem exatamente 5 XMLs de slide, texto/formas/imagem editáveis e imagem acima do retângulo no slide 4. Corrigido uso de shapeName obsoleto para objectName após teste detectar ID ausente no XML. Slide 2 mantém D002 intencional para ensinar contraste. Próximo: IA e benchmark.

## 2026-10-08 — Fase 5
Ollama /api/chat e OpenAI Chat Completions implementados com timeout, seed/temperatura, metadados e falhas sem expor headers/chaves. Prompt único com gramática e dois exemplos. Smoke test generate --provider mock executado com raw preservado, saída válida e proteção contra overwrite; testes HTTP usam MockTransport e verificam requisições reais dos adaptadores. Sem serviço Ollama nem OPENAI_API_KEY neste ambiente; chamadas reais não executadas. Próximo: benchmark.

## 2026-10-08 — Fase 6
Harness A/B pareado e C com até dois reparos, rubric 17 itens, AST/IR/raw/PPTX/JSONL/CSV e primeira/final tentativa separados. Executado pytest -q: 98 passed. Benchmark real solicitado com 5 repetições para quatro modelos: todos NAO_EXECUTADO; outputs/reports registra motivos e não tem métricas inventadas. Correção de margem do gabarito detectada pela rubrica. Próximo: editor visual real.

## 2026-10-08 — Fase 7
Editor React Flow real e API FastAPI concluídos. Executado pytest -q: 102 passed; build Vite/TypeScript e ESLint passaram. Playwright: 3 passed (8.3s), importando 5 slides, editando texto, validando, exportando DSL/PPTX e corrigindo X=1300 para X=80; portas incompatíveis rejeitadas. Capturas em outputs/editor_demo.png, editor_antes.png, editor_depois.png e preview_slide_1..5.png. Playwright 1.52 apresentou hang no carregador Node 24; atualizado e fixado 1.60.0, teste passou em Node 24.14.0. Layout do grafo inclui grupos e relações; build usa editor-assets para não conflitar com assets locais. Próximo: pacote de defesa, scripts Windows, auditoria final.

## 2026-10-08 — Fase 8
Scripts setup/test/demo executados em Windows. Setup reproduziu dependências fixadas.
Primeiro test_windows falhou no tmp compartilhado por permissões (90 passed/15 errors);
corrigido para tmp/cache exclusivos em outputs/tests. Reexecução completa: 105 pytest
passed (3.82s, um aviso de depreciação transitiva), 2 Node passed, 3 Playwright passed
(8.2s), lint/format e build passaram. Catálogo operacoes compilado após restaurar
alinhamento depois da transformação de grupo. Demo: 5 slides, 25 textos, 8 formas,
1 imagem, rubrica manual 17/17 e roundtrip equivalente. Entregues DEFESA_PROFESSOR,
RESULTADOS, EDITOR, árvore e README; pesquisa/matriz atualizadas com teste local.
Benchmark reexecutado em outputs/reports_final: quatro NAO_EXECUTADO (Ollama ausente,
chave OpenAI ausente), sem métricas fictícias. COM preview indisponível. Engenharia
0–8 concluída; única etapa experimental pendente depende dos provedores reais.
Smoke test da versão build em FastAPI confirmou HTTP 200 no HTML, JS/CSS e imagem
local. Inventário final contém 114 arquivos de fonte/configuração/testes/referências,
com normalização explícita de finais de linha no Git para o Windows.

## 2026-10-08 — instalação Ollama e início do experimento local
Pedido explícito do usuário para instalar e executar os Qwen3. Consultadas fontes
oficiais e o pacote winget Ollama.Ollama 0.40.1; instalação concluiu com hash verificado.
Downloads qwen3:0.6b (522 MB) e qwen3:4b (2,5 GB) concluídos; versão, digests e
detalhes salvos em outputs/ollama/. O serviço reiniciou ao terminar a instalação,
interrompendo o primeiro pull; a repetição retomou e completou os dois downloads.
Detectados 16 GiB RAM e RTX 3060 12 GiB; inferência local confirmada na GPU.
Corrigidos acentos corrompidos no prompt técnico, sem alterar pedido literal.
Fixados contexto 16384 e saída máxima 8192 no adaptador, iguais para ambos;
Ruff check/format e 9 testes de models/benchmark passaram (1.34s).
Iniciado benchmark real com cinco repetições A/B/C em outputs/reports_ollama_20261008;
resultados finais serão registrados após concluir todas as chamadas.

## 2026-10-08 — experimento local concluído
Descoberta em /api/show: 0.6b permite thinking false/true; 4b só permite true.
Corrigido adaptador para descobrir e registrar controles e valor efetivo, mantendo
prompts intactos e usando message.content da API. Piloto 4b incompatível arquivado
em discarded_unsupported_thinking; respostas não foram editadas ou recortadas.
Adicionado benchmark --resume com verificação de prompts/configuração/identidade/
hash/digest/parâmetros e proteção contra sobrescrever repetições incompletas.
Retomada preservou as cinco repetições reais completas do 0.6b e suas durações;
4b executou cinco repetições com controle suportado. Ambos EXECUTADO, sem falha de
transporte: 0/5 parse inicial/final, 10 reparos cada, nenhum PPTX de modelo. Conjunto
final: 30 respostas de geração, 50 arquivos raw por duplicação pareada A/B/C.
0.6b: 15/15 terminações length; 4b: 11 length e 4 stop. Dois hashes iniciais distintos
por modelo. Médias iniciais: 63.503s e 111.633s. Sem IR válida, design não foi avaliado.
Executado test_windows.ps1: 108 pytest passed (4.39s, 1 aviso transitivo), 2 Node
passed, 3 Playwright passed (8.2s); lint/format e build passaram. Relatório final em
outputs/reports_ollama_20261008; instalação/metadados em outputs/ollama. Atualizados
RESULTADOS, EXPERIMENTO, DEFESA, README e roadmaps; criados OLLAMA_LOCAL e
RESULTADOS_OLLAMA. OpenAI permanece pendente de credencial; bloqueio local resolvido.

## Evolução local incremental — diagnóstico e implementação
Auditadas 30 respostas físicas originais, com 30/30 replays idênticos. P001 é
UnexpectedInput do parser Lark; preservadas linhas, colunas, tails, hashes, tokens
e thinking em outputs/diagnostico_ollama. Detectada diferença entre null em metrics
e zeros antigos em attempt para design não alcançado; novos registros mantêm null.
Baixadas tags qwen3:4b-instruct e qwen2.5:3b-instruct. Geração incremental usa cinco
solicitações independentes, mantendo pedido integral e foco extraído do próprio pedido.
JSON restrito é convertido em comandos pelo printer existente, depois reanalisado
por parser e semântica; nenhum PPTX direto de JSON. Até dois reparos, artefatos por
rodada, resposta HTTP completa e nenhuma substituição manual. Pilotos com overflow,
referências inválidas e título ausente preservados; ainda não são sucesso final.

## Demonstração real e regressão incremental
Cinco slides gerados por qwen3:4b-instruct/JSON em demonstracao e windows_demonstracao;
script único Windows concluiu geração, validação, AST, IR e PPTX. Auditoria verifica
raw contra message.content, hashes, cena de cada rodada selecionada e objetos/textos
nativos do PPTX. windows_demonstracao tem um aviso D010; não é aprovação estrita.
windows_strict executou --strict e recompilou cinco slides após um reparo de D010.
Teste de navegador abriu o artefato real, editou título, revalidou e exportou DSL/PPTX.
test_windows.ps1 passou com 123 Python, 2 Node e 4 Playwright; lint/format/build também.
JSON final separa title/texts/shapes/images/operations para reduzir ambiguidade;
impressão de formas/imagens antes dos textos é contrato explícito, não correção oculta.
Validação padrão e --strict mantêm a distinção da CLI existente; avisos são registrados.
Avaliação final do pedido original complexo está em execução, sem mudar prompts/modelos
durante as repetições e sem misturar seus resultados com a demo introdutória.

Modo direto também concluiu cinco slides reais, cinco chamadas, zero reparos e
zero diagnósticos; auditoria e edição/exportação no navegador passaram. JSON estrito
concluiu com seis chamadas e um reparo, mantendo informações de contraste indeterminado.
Capturas mostram que aprovação geométrica não garante ausência de problemas visuais.
Encontrada DACL privada do PPTX movido de TemporaryDirectory no processo isolado;
compilador passou a publicar por staging no destino, com herança de acesso Windows.
Recuperação dos binários existentes preservou os hashes. Host do usuário confirmou
leitura e auditoria. Regressão final após o ajuste: 123 Python (5.43s), 2 Node e
4 Playwright (18.3s), lint/format/build aprovados.

## Avaliação incremental concluída e entrega real
Concluídas 30 apresentações tentadas (3 modelos x 2 modos x 5 repetições), com
150 respostas iniciais e 167 reparos: 317 respostas reais auditadas contra content,
hashes, prompts, seeds, parâmetros e digest único por modelo. Nenhum vazio/transporte;
length: 0.6b direto 1, Qwen2.5 direto 7. PPTX no pedido complexo: modo direto 0/5
em cada modelo; JSON 4b-instruct 2/5, 0.6b 0/5 e Qwen2.5 2/5. Quatro PPTX nativos
auditados e acessíveis ao usuário Windows. Todos contêm avisos e reprovam strict.
Rubrica: 4b 14/17 nas duas compilações; Qwen2.5 8/17 e 10/17; nenhum 17/17.
Demonstração introdutória separada executou comando único completo Windows em
windows_direct_final: cinco chamadas, cinco slides, zero reparos/diagnósticos,
strict aprovado, 16 textos e oito formas. Abriu editor em produção; cinco previews
e fonte conferidos, nenhum erro JS. JSON strict também demonstrado com um reparo.
Documentados resultados, falhas, contraste indeterminado, frases potencialmente
cortadas pelo schema, diferenças de protocolo, seeds e limitações de tempo/cache.

## README didático e exemplo executável
README ampliado com fluxo parser/AST/semântica/IR/design/compilador/editor,
produções da GLC real, notação da gramática e distinção entre sintaxe e semântica.
Criado examples/introducao.sld, exemplo didático escrito manualmente, com dois
textos, posicionamento relativo e retângulo decorativo. Não faz parte da avaliação
SLM. Executados os comandos validate --strict, ast, ir, compile --strict e inspect:
todos retornaram zero. Validação sem diagnósticos; PowerPoint com um slide,
dois textos e uma forma editáveis. Evidências em outputs/readme/validation.json,
ast.json, ir.json e introducao.pptx. Esclarecidos os requisitos distintos da
demonstração manual offline e da geração por Ollama.
Acrescentado direcionamento explícito no README para o arquivo executável da GLC,
a função grammar_parser() e a documentação dos comandos.
