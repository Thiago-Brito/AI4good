# Progresso de implementação

## Planejamento visual — entrega (11/10/2026)
Documento EVOLUCAO_PLANEJAMENTO_VISUAL.md reúne causas, literatura versus
heurísticas, composições, execuções reais, falhas preservadas e limites.
Auditoria reconferiu três respostas antes/depois, textos nativos e 61 hashes.
Capturas finais em captures_delivery/ conferiram a fonte e não tiveram erro JS.
Fotografia photo_delivery_04 usou provedor automático e imagem Moon CC BY 2.0,
1024×768, duas chamadas reais e PPTX com uma imagem e quatro textos nativos.
Regressão completa final: 224 Python, dois Node e onze Playwright; três testes de
imagens/contexto repetidos após ajustes e 18 testes CLI/visual após revisão final.
Validação do schema bruto precede a normalização, inclusive rejeitando campos
extras nos nós antes que possam ser descartados. Build e verificações passaram.
Resultados/caches mantidos fora do Git; entrega preparada na branch dsl-visual.

## Planejamento visual — implementação e inspeção (11/10/2026)
Intenções e estruturas escolhidas pela SLM em uma chamada; conteúdo em outra.
O compilador calcula oito composições nativas e preserva os textos. Geração real
delivery_03 usou capa/diagrama/comparação/cards/conclusão; duas chamadas, zero
reparos, PPTX estrito, quatro setas vetoriais. Capturas antes/depois e auditoria
em outputs/planning_visual/. Formulário simples, parâmetros técnicos recolhidos.
Busca automática real escolheu NASA/Openverse e baixou imagem CC BY 2.0 1024×768.
Primeira regressão: 223 Python, dois Node, onze Playwright; compilação/lint passaram.
Piloto adicional de fotografia revelou consulta muito ampla e altura insuficiente
do cabeçalho no fallback; corrigidos com preservação de conteúdo, em execução nova.
Renderização externa indisponível; inspeção do agente encontrou simplificações
factuais na conclusão. Não se declara avaliação estética/factual com participantes.

## Planejamento visual — início (11/10/2026)
Base e44961ed confirmada em origin/dsl-visual antes de código. Reproduzido pedido
exato: quatro title_content, uma comparação textual, nenhum diagrama; 2/2 slides
e margens, zero diagnósticos. Schema já permite componentes, mas não exige intenção
visual; prompt enfatiza layouts textuais. Critérios genéricos não medem adequação
da representação. Reprodução preservada em outputs/planning_visual/before_01/.

## Evolução visual/contextual — início (11/10/2026)
Pedido integral lido. Base 9b6a8edf80ce4b76c54c13bcbb7fc0e768aab847 limpa na SlideDSL e confirmada no remoto. Pastas não rastreadas de outros projetos excluídas do escopo. Fontes oficiais registradas antes da nova documentação. Histórico experimental preservado.

## Evolução SLM — análise e compilação de planos (10/10/2026)
Lidos roadmap, resultados incrementais, GLC, AST/IR, compilador, adaptador Ollama,
geração incremental, API, editor e chamadores. Base Python: 123 testes passaram.
Serviço local respondeu 0.40.2 com qwen3:4b-instruct instalado. Fontes oficiais
registradas em refs/FONTES.md antes da documentação desta etapa.
Acrescentados planejamento sem coordenadas/IDs, resolução determinística de três
layouts e referências lógicas, sem alterar a GLC ou o backend. Conteúdo não é
cortado para caber: excesso gera diagnóstico. Reparos autorizam apenas caminhos
afetados, preservando os demais elementos. Etapa: 24 testes passaram, incluindo
compilação/inspeção de objetos nativos para os três layouts e correção localizada.
Nova comparação A/B/C/D é separada do protocolo histórico; não há taxas novas
antes da execução real. Integração de interface e avaliação ainda em andamento.

## Evolução SLM — interface e demonstração real
Acrescentados GET /api/models, POST /api/generations e polling por ID. A fila usa
um trabalhador, persiste eventos e não sobrescreve execuções. O editor existente
recebe modelo, pedido, estratégia e validação estrita, exibindo diagnósticos e
carregando a fonte/IR gerada para edição e exportação.
Piloto qwen3:4b-instruct D gerou cinco slides de arquitetura em 17,77 s, sem reparos
ou diagnósticos; recompilação do plano offline também passou. O teste pelo formulário
gerou outro deck real, editou título, revalidou e exportou DSL/PPTX: seis Playwright
passaram em 31,8 s, incluindo o artefato histórico. Suíte integrada: 136 Python e
dois Node passaram, lint/format/TypeScript/build aprovados. Dois testes adicionais
do harness passaram. Evidência: outputs/evolution/ui_generation.json.
Comparação final iniciada com 2 pedidos x 4 estratégias x 5 seeds pareadas,
registro separado em outputs/evolution/experiment_20261010/. Fontes exatas desta
execução preservadas em sources_snapshot/. Resultados ainda não fechados.

## Evolução SLM — avaliação concluída e auditoria final
Concluídas 40 execuções reais com qwen3:4b-instruct: 2 pedidos x 4 estratégias x
5 seeds. Auditadas 122 respostas físicas, todas stop; sem falhas de transporte.
Validação estrita: A 0/10, B 0/10, C 10/10 e D 9/10 PPTX. Os 19 arquivos têm cenas
e textos nativos conferidos. Arquitetura: C/D 10/10 critérios em todas as seeds.
Design complexo: C 16,16,16,14,16/17; D 16,16,14,16,16/17. D rep 3 falhou após
dois patches que repetiram d2 inexistente. Nenhum resultado complexo atingiu 17/17.
Somente um dos dez pares C/D teve resposta inicial idêntica; não se atribuiu efeito
causal ao reparo. Fontes/código executados preservados; dados em evaluation.json/csv
e audit.json/csv de outputs/evolution/experiment_20261010/.
Corrigida agregação de design por slide alcançado (A: 43/50, 13 erros) e título
do draft rejeitado A/B. Auditoria preserva campos originais e registra cobertura
sob título canônico; respostas/programas/PPTX históricos não foram alterados.
Regressão integrada 140 Python/2 Node/7 Playwright passou; após um teste adicional
do título, Python completo passou com 141. Lint/format/TypeScript/build aprovados.
Atalho open_slm_editor_windows.ps1 executado com -NoBrowser; produção em localhost
carregou cinco slides reais sem erro JS. EVOLUCAO_SLM.md registra execução, métricas,
limites, recursos não implementados e próximos passos. Roadmap atualizado.

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

## Confiabilidade da geração — 11/10/2026
Snapshot anterior à implementação: c53bb4498a6aba2812e22014bd1cf66954abfd13,
commit e push confirmados em origin/dsl-visual. Código do projeto foi estendido.
Requisitos tipados, interpretação conservadora por slide e verificadores AST/IR
produzem evidências e R001. D tenta correções determinísticas autorizadas, patches
locais, rejeita regressões e repetições, registra estados e limita tentativas a 0–10.
Componentes cards/sequence/flow, slots compactos e cabeçalhos com altura calculada
preservam texto completo. V001–V003 complementam as dez regras de design.
Painel mostra requisitos e fases, permite corrigir plano e revalidar IR editada.
PowerPoint COM indisponível; previews de navegador não são renderização de PPTX.

Ablação final em outputs/reliability/experiment_20261011_final: quatro pedidos,
duas repetições, 32 avaliações sobre oito planos iniciais compartilhados, oito
chamadas reais qwen3:4b-instruct, 4.285 tokens de saída e 30 PPTX auditados.
Baseline/validador: 7/8 PPTX, 4/8 estrutura+requisitos e 60/68 critérios.
Determinístico/SLM permitido: 8/8 PPTX e 68/68 critérios; nenhuma chamada adicional
à SLM foi necessária no protocolo final. Complexo atingiu 17/17 nas duas repetições.
Executados dois protocolos intermediários preservados, com falhas que orientaram
ajustes gerais de direção de fluxo, reconhecimento, altura e controle de progresso.
Não se misturam taxas entre versões nem se afirma generalização estatística.
Auditoria conferiu HTTP/bytes, schemas, seeds, critérios fixos, snapshots, escopo,
rollbacks e texto nativo de todos os PPTX. Docs em EVOLUCAO_CONFIABILIDADE.md.
Regressão final: 160 Python, dois Node e oito Playwright; lint/formatação/build.
Falhas encontradas e corrigidas: API antiga no processo reutilizado, altura de seta,
overflow de cabeçalho, layout incoerente e negações simples no reconhecedor.
Evidências novas em outputs/reliability/ e outputs/tests/reliability-final.xml;
experimentos anteriores não foram modificados. Avaliação humana e maior amostra
continuam pendentes, assim como interpretação geral de português e reparo de plano
após mudanças manuais da IR.

## Evolução visual/contextual — 11/10/2026

Base limpa 9b6a8edf80ce4b76c54c13bcbb7fc0e768aab847 confirmada no remoto;
sem snapshot vazio. Estendidos parser/AST/IR/editor/renderer existentes.
Pesquisa oficial opcional, cache e proteção de downloads; Openverse/NASA reais,
Commons HTTP 403 documentado. Seis layouts proporcionais, seta vetorial nativa,
contexto opcional e referências TXT/MD/PDF com recuperação lexical local.
Restrito seleciona frases fornecidas, com auditoria de IDs/texto; não comprova
verdade factual. Correções preservam manualmente campos/adições/remoções por ID
e registram conflitos. V004–V006 e renderização externa opcional implementadas;
PowerPoint/LibreOffice ausentes, fallback geométrico explícito.

Experimento final contextual: cinco domínios, seed 42, 20 avaliações estruturais,
17 chamadas qwen3:4b-instruct, 4.161 tokens de saída e 20.915 de entrada.
A 1/5 PPTX; planos sem reparos/validador/determinístico 5/5 e 20/20 critérios
cada. Planos já corretos: nenhum ganho observado dos reparos. Imagem selecionada
compilou com aviso de baixa resolução; imagem pendente bloqueada. Livre/restrito
compilaram; três fragmentos rastreados no restrito. Humanos não avaliados.
Auditoria conferiu 462 hashes e conteúdo nativo de 38 PPTX com auxiliares.
Pilotos e primeira execução com falhas permanecem registrados em outputs/contextual/.

Regressão: 209 Python, dois Node, onze Playwright; lint/formatação/TypeScript/build.
Revisão final acrescentou upload de imagem própria offline, com permissão declarada,
validação compartilhada, seleção por slot e exclusão; testes API/navegador separados.
Teste real de navegador gerou com imagem/documento, editou, preservou a edição
no reparo e exportou DSL/PPTX. Evidências e limites em
docs/EVOLUCAO_VISUAL_CONTEXTUAL.md, outputs/contextual/ e
outputs/tests/contextual-final.xml. Pendentes avaliação humana, Office real,
maior amostra, GPU, conectores ancorados e sincronização completa de fontes/IR.
