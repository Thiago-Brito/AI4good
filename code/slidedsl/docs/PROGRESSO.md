# Progresso de implementação

## TCC — Fase 0: custo por chamada — 22/11/2026

Ponto de partida: `RecordedModel` já gravava tokens e segundos em `uso_chamadas.jsonl`, mas não os
tempos do servidor, e `chamadas.jsonl` não tinha uso. Implementado: durações do Ollama (ns → ms),
`timings` do llama.cpp (com contagens de reserva sem `usage`), `reasoning_tokens` da OpenAI,
`wall_ms` com `perf_counter`, `RecordedModel.last_usage()` copiado para `Call.usage` e `custo.json`
(`slidedsl.custo.v1`) com totais e etapas. Valores ausentes ficam `null`; somas informam quantas
chamadas não tinham o campo. **713 pytest passaram em 112 s** (`--basetemp` curto: o caminho longo
estourou o limite do Windows em `test_documentos_edicao_r7.py`), Ruff limpo, testes Node do
renderer passaram. Só servidores simulados: nada medido com modelo real ainda. `alto_generation.py`
já estava fora do `ruff format` antes desta fase e não foi reformatado.

## Rodada 4 de design — 10/11/2026

T1 concluída antes de alterar layouts: corpus congelado (16 decks, 89 slides),
15 PPTX válidos e um deck solar com A010 preexistente. Evidência:
`outputs/design_r4/20261110-234240/antes/`. Rodada offline, US$ 0.
T2–T6 implementadas; variantes e regressões em validação antes dos ciclos visuais.
T7/ciclo 1: 16 folhas abertas, 15/16 PPTX. Corrigido solar B+img; novo bloqueio
no marcador de etapas do Git identificado. Vãos tipográficos ainda exigem ajuste.
Revisão em `outputs/design_r4/20261110-234240/ciclo_1/REVISAO.md`.
T7/ciclo 2: 16 folhas abertas, 15/16 PPTX. Vãos diminuíram e Git passou;
comparação de microsserviços regrediu por rótulos estreitos. Ajuste de largura e
classificação visual da conclusão em curso antes do terceiro e último ciclo.

T7/T8 encerradas em 11/11/2026, pelo limite de três ciclos. Ciclo 3: **16/16 PPTX,
89 slides**, zero A010/A019/D010, oito A031. Foram abertas as 48 folhas dos três
ciclos. Comparação por deck em `outputs/design_r4/20261110-234240/comparacao/`:
nota média 0,7966 → 0,8353; ocupação 0,6079 → 0,4966 (faixas 0,1746–0,9213 →
0,1539–0,8771); variantes por deck 4,625 → 4,875; repetições consecutivas 3 → 0.
Antes não havia A030: variantes inferidas por cartões/tipo são aproximação;
A031 anterior não disponível, não evidência de resolução adequada.

**591 pytest passaram em 87,47 s**, um aviso preexistente Starlette/AnyIO;
`ruff check src tests scripts` limpo e **2 testes Node** passaram. JUnit em
`outputs/design_r4/20261110-234240/pytest_aprovacao.xml`. Corpus × seis estilos
testado sem overflow, sem alterar a gramática/IR. Editor não foi alterado nesta
rodada. Execução inteiramente offline, **US$ 0**, sem commit/push/stash.

Limitações observadas: predominam listas, photo40 venceu as dez imagens,
fotos pequenas/irrelevantes persistem, transições são esparsas, comparações densas
continuam em 16 pt e topos de rótulos podem variar para alinhar descrições.
Nota geométrica não é validação estética; aparência no Office não foi medida.
Detalhes e achados por ciclo em `ciclo_N/REVISAO.md`; regras em `REGRAS_DESIGN.md`.
Auditoria nativa adicional: 652 textos, 298 formas, 19 imagens nos 89 slides;
nenhuma divergência de família/tamanho entre IR e PPTX. Originais/cópias do corpus
conferidos por SHA-256. Python 3.12.10, Node v24.14.0. A remoção de
`outputs/_tmp_r4` foi rejeitada pela revisão automática (`blocked by policy`);
temporário preservado. Evidência consolidada em `auditoria_final.json` e `RELATORIO.md`.

## Rodada 5: modelo, imagens por IA e visual — 02/11/2026
Imagens geradas por IA como opção (só quando faltar foto livre ou sempre), com custo por
imagem no consumo; capa e conclusão em paleta invertida; correções de crédito, retratos,
maiúsculas e largura de rótulos; recomposição de slide de imagem que não cabe. gpt-5.4-mini
virou o padrão local após teste lado a lado. 467 testes; detalhes em
[CONTINUIDADE_API_VOZ_MOBILE.md](CONTINUIDADE_API_VOZ_MOBILE.md).

## Rodada 4: B-lote e correções editoriais — 01/11/2026
Planejador implementou: regras gerais no lugar das específicas dos temas, filtro de
tópicos estruturais, rótulos uniformes por grupo, comparação coerente, cartões ajustados
e modo B-lote. Lote `outputs/comparacao_alto_sld/20261101-2307_r4/` (US$ 0,3035):
B-lote 11/12 válidos, 83.866 tokens contra 141.151 de A (−41%), US$ 0,00096 por slide
válido contra 0,00174 (−45%). 458 testes; Ruff limpo. Detalhes e pendências em
[CONTINUIDADE_API_VOZ_MOBILE.md](CONTINUIDADE_API_VOZ_MOBILE.md).

## Rodada 3 de design e comparação com repetições — 01/11/2026
Corpo ≥ 16 pt, fotos na capa, caixa de frase, rótulos e ocupação revisados pelo Codex; lote
4 temas × 3 seeds × A/B/B+img em `outputs/comparacao_alto_sld/20261101-2227/` (US$ 0,3704).
B: 12/12 válidos, US$ 0,00143/slide válido, 22% mais tokens que A; A: 11/12, 91 avisos.
Codex parou por limite de uso antes de documentar; 452 testes e Ruff conferidos pelo planejador.
Detalhes e pendências em [CONTINUIDADE_API_VOZ_MOBILE.md](CONTINUIDADE_API_VOZ_MOBILE.md).

## Comparação — tarefa 3 — 01/11/2026
Criados `scripts/comparar_alto_vs_sld.py`, três briefs congelados em
`experiments/comparacao/briefs/`, registro prévio em `refs/COMPARACAO_ALTO_SLD.md`
e testes offline de orçamento, parâmetros e métricas. Todas as rodadas de A são
auditadas com RecordedModel; o teto global inclui tentativas anteriores e reserva
conservadora de chamadas sem uso. TLS permanece verificado.

Lote principal: `outputs/comparacao_alto_sld/20261101-2131/RELATORIO.md`, CSV/JSON,
auditoria, fontes/cru/validações, seis PPTX, 35 PNGs Pillow/IR e sete folhas de
contato inspecionadas. A: 19.094/8.292 tokens entrada/saída, US$ 0,0201368, 1/3
válidos, dois P001, oito D010 e um D008. B: 24.666/5.253, US$ 0,017964, 3/3,
zero ERRO/AVISO. B+img: 27.532/5.296, US$ 0,018872, 2/3, um A010. Zero imagens:
Commons recusou busca real com 403; fallback preservado. Economia de custo B
10,79%, B+img 6,28%; tokens totais aumentaram 9,25% e 19,87%. Não se demonstrou
redução de tokens nem equivalência factual/estética de conteúdo.

No experimento inteiro: 90 chamadas, 72 com uso conhecido e 18 sem uso;
US$ 0,0703364 conhecidos e teto conservador US$ 0,2325972. Total exato desconhecido,
nunca tratado como zero. Tentativas anteriores, diagnósticos e retomada preservados,
sem duplicar o custo do A copiado de 2125 para 2128. Lote principal tem custo
completamente conhecido (US$ 0,0569728). Nenhum novo gasto após a conclusão.

Limitações documentadas: dois A sem IR/PNGs; B+img solar sem PPTX por rótulo longo
após reparo; PNG não renderiza PPTX e mostra glifo subscrito ausente; repetição
semântica ainda possível apesar de Jaccard zero. Prévia e validade não comprovam
correção factual. Briefs têm o mesmo texto e os mesmos bytes congelados entre
condições; transporte A/CRLF e B/LF registrado, e harness corrigido para futuras
execuções sem conversão de newline. Sete folhas inspecionadas pelo executor,
sem avaliação humana cega. Regressão anterior 420 testes passou; verificação final
concluída abaixo. Próximo trabalho de produto continua sendo persistência com revisões,
sem novas despesas autorizadas por esta etapa.

## Comparação — tarefa 4 — 01/11/2026
Verificação final: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
--basetemp outputs\_pt --junitxml=outputs/comparacao_alto_sld/20261101-2131/pytest_final.xml`:
**421 passaram em 91,50 s**, com um aviso preexistente de depreciação Starlette/AnyIO.
`.\.venv\Scripts\python.exe -m ruff check src tests scripts`: **All checks passed**;
log em `20261101-2131/ruff_final.txt`. `git diff --check` sem apontamentos.
Auditoria independente conferiu nove execuções, hashes de briefs normalizados,
uso por chamada, reservas e seis ZIPs PPTX com cinco slides cada. O caminho absoluto
de `outputs/_pt` foi verificado dentro de outputs, mas as duas tentativas de remoção
PowerShell (a segunda com caminho literal absoluto) foram rejeitadas antes da
execução pela política do ambiente: `blocked by policy`. A pasta permanece; não
foi solicitado relaxamento da política nem usada outra via para contornar o bloqueio.
Branch preservada `feature/slidedsl-api-voz-mobile`, sem commit, push, stash ou
limpeza de arquivos preexistentes. O primeiro pytest concorrente sofreu colisão
de temporários; a regressão final foi executada sozinha. O mock antigo repetia
os itens na conclusão, passando a disparar corretamente o detector; fixture
ajustada para conteúdo distinto. Nenhum limite de design foi ampliado e nenhuma
saída paga foi editada manualmente para melhorar sua pontuação.

## Comparação — tarefas 1–2 — 01/11/2026
Lidos plano, norma, código e chamadores. `https.py` centraliza SSLContext com
CERT_REQUIRED para OpenAI, mídia e pesquisa. Busca real: TLS concluído, Commons
HTTP 403 por política de robôs; Openverse timeout. Evidências em
`outputs/comparacao_alto_sld/rede_20261101-211932/`. Não se declara busca funcional.
Autoria ausente do pedido é descartada; prompts recebem roteiro e itens anteriores;
Jaccard >=0,72 gera A017 e reparo dentro do limite existente. Imagem proposta no
roteiro com consulta em inglês; resolução restrita a Commons, fallback preservado.
A011 de download pendente deixa de provocar reescrita inútil. Nenhum limite visual
foi ampliado. `pytest tests/test_comparacao_quality.py -q -p no:cacheprovider
--basetemp outputs\_pt`: 11 passaram. Próximo: harness e experimento real.

## Piloto OpenAI remoto — 01/11/2026
Causa da falha HTTPS: o Kaspersky intercepta TLS e apresenta a raiz própria
(`Kaspersky Anti-Virus Personal Root Certificate`), confiada pelo Windows mas ausente do
`certifi` usado pelo HTTPX. `openai_model.py` passou a usar `ssl.create_default_context()`,
com verificação ativa; teste de regressão confere `CERT_REQUIRED`. Piloto pela API web
(`outputs/api_voz_mobile/piloto_5ab371e27016/`, job `5d620a2be1194525b62221b672260f70`):
`gpt-4.1-mini-2025-04-14`, 3 slides, 5 chamadas (roteiro, 3 slides, 1 reparo), 3.514
tokens de entrada, 877 de saída, sem cache, US$ 0,0028088 pela tarifa datada; PPTX
exportado (HTTP 200). Conteúdo genérico e repetição entre slides 2 e 3; autor inventado
na capa. 403 testes Python passaram; Ruff sem apontamentos.

## APIs e auditoria de consumo — 01/11/2026
Branch `feature/slidedsl-api-voz-mobile` criada antes das mudanças, base `168c29f`.
OpenAI integrada ao fluxo Alto web, com seleção de provedor/modelo, schema estrito
adaptado e validado localmente, recusa/interrupção explícitas e remoção do fallback por
TypeError. Auditoria inclui pesquisa, geração, verificações e falhas; uso ausente fica
desconhecido e chamadas em andamento são persistidas antes do HTTP. Interface exibe
consumo, limita chamadas/saída e começa com um candidato. `.env` local autorizado,
ignorado e não rastreado; não houve commit/push. Piloto remoto impedido por HTTPS
(WinError 10054, inclusive fora do sandbox), antes da geração. HTTP simulado gerou
PPTX editável real. Validação final: 402 testes Python, dois Node e 13 Playwright
passaram; cinco testes reais optativos omitidos. Ruff, ESLint, TypeScript, formatação
e build conferidos. Ver verificações, artefatos e próxima fase em
[CONTINUIDADE_API_VOZ_MOBILE.md](CONTINUIDADE_API_VOZ_MOBILE.md).

## Planejamento de APIs, voz e celular — 01/11/2026
Criado [PLANO_API_VOZ_MOBILE.md](PLANO_API_VOZ_MOBILE.md), após leitura da arquitetura,
adaptadores, fluxo Alto, API, editor e registros existentes. Fontes registradas em
[refs/PLANO_API_VOZ_FONTES.md](../refs/PLANO_API_VOZ_FONTES.md). O plano propõe completar
OpenAI com saída estruturada e uso por chamada, estado persistido com revisões, edição
localizada, interface móvel, voz e avaliação de custo por slide válido. A transcrição
fornecida pelo usuário orientou a comparação com Taiga-S1; o ZIP foi desconsiderado.
Referência visual do Claude indisponível. Etapa exclusivamente documental: sem branch,
alteração de código, testes de execução, chamadas pagas, commit, push ou publicação.

## Revisão e preparação do commit — 12/10/2026
Revisadas as mudanças do projeto SlideDSL: fluxo Alto, pesquisa local, verificação de
sustentação/cobertura, extensões da DSL 1.1, editor e planejamento conceitual/experimental.
388 testes Python, dois testes Node e 11 Playwright passaram; cinco testes reais de
interface permaneceram optativos. Ruff, ESLint, TypeScript/build e formatação conferidos.
Os testes antigos foram adaptados ao painel recolhido, ao status específico do editor
e à porta de API configurada. O segredo do SearXNG ficou no `.env` local ignorado pelo Git;
o script de início cria o arquivo em novas instalações. Compose e busca real validados.
README e registro do dia agora refletem os 12 pedidos/21 execuções/13 PPTX do lote
anterior aos últimos ajustes, cuja avaliação real continua pendente.

## Qualidade, SearXNG e documentação do TCC — 12/10/2026 (noite)
Testes reais multitemas com Qwen3 4B e SearXNG geraram PPTX com fatos de fontes reais e revelaram
cortes de título pelo decoder, fatos usados com outro sentido, citações mal atribuídas, itens do
pedido omitidos e fatos fora do assunto. Correções: limites folgados + A013, verificação de
sustentação (A014), citação literal (A015), cobertura de tópicos (A016), números por valor
inteiro, filtro de termos centrais, slides de dados condicionados a dados, layout (rodapé, 16 pt,
capas). SearXNG passou a ser o único buscador do painel e o padrão da CLI. README reescrito parte
por parte; registro em MUDANCAS_2026-10-12.md; referências em REFERENCIAS.md. 387 testes Python.

## SearXNG local — 12/10/2026
Docker Desktop já estava instalado (CLI/Engine 27.5.1). Aplicativo iniciado,
imagem `searxng/searxng:latest` baixada e contêiner `slidedsl-searxng` iniciado
com o Compose existente. `/healthz` respondeu HTTP 200 e a busca JSON por
`microsservicos` retornou 27 resultados. O Python do ambiente local confirmou
`provider_auto() == "searxng"` e URL `http://127.0.0.1:8888`.

## SlideDSL Alto, pesquisa e geração restrita — 12/10/2026
Diagnóstico: slides gerados corretos mas genéricos e visualmente repetitivos. Nova GLC de
alto nível compila para a SlideDSL 1.1 com 11 layouts; extensões de estilo na 1.1. Pesquisa
na internet produz fichas com trecho literal verificado; o roteiro e o conteúdo usam schemas
que só aceitam IDs de fatos reais; A007 acusa números ausentes das fontes. Modos JSON, GBNF
(conversor Lark→GBNF próprio, testado por reconhecedor) e direto, com reparo por campo e
best-of-N. Regressão: 372 Python (24 novos) e dois Node passaram no ambiente Linux de
desenvolvimento; Playwright/editor não executados nesta etapa. Sem SLM real nem rede externa
neste ambiente: medições com Qwen3 pendentes. Documentação em docs/SLIDEDSL_ALTO.md.

## Rastreabilidade e cobertura — 11/10/2026
Diagnóstico antes das alterações em INVESTIGACAO_COBERTURA.md, com snapshot B
preservado. Contrato tipado de cláusulas explícitas, origem por posições/trecho,
requirement_ids nos registros, rastro de campos por slide e C001–C005 serializáveis.
Recuperação acrescenta registros já produzidos, somente quando validadores de
geometria, contratos e requisitos permitem, sem perda de conteúdo ou novos sinais.
Flags experimentais CLI/API/editor; padrão histórico preservado. Integração inicial
passou 38 testes Python, incluindo PPTX nativo e perdas de campos na IR/PPTX.
Regressão completa e A/B/C congelado em execução em outputs/coverage/abc_02,
seeds 42/43, sem serviços de linguagem online. Retenção literal/IDs não comprovam
correção factual; avaliação independente permanece null. Sem commit/push.

## Investigação e planejamento conceitual — 11/10/2026
Base fea5a52; investigação registrada antes de alterar código. Duas chamadas
Qwen3 4B local: conteúdo conceitual sem geometria e seleção por slide. Projeção
preserva registros selecionados; alocação ainda pode omitir exemplos/síntese.
Revisor de um slide com feedback, critérios conservadores e rollback. Comparação
final: controle 3/6, conceitual 6/6 PPTX; seis propostas sobre B históricos rejeitadas.
Uma revisão lexical de título aceita em frações não corrige sua síntese. Não há
ganho geral de conteúdo demonstrado: integração de arquitetura, sequência/atores
e completude dos pedidos novos permanecem problemáticos. Casos novos UTF-8
repetidos sem alterar código; pilotos/entradas corrompidas preservados. Auditoria
confere fontes Python realmente usadas, HTTP/schema, 31 chamadas finais, 13 PPTX
incluindo download real do editor. Desenvolvimento: 86 chamadas, falhas incluídas.
325 Python, dois Node, dez Playwright ordinários; nova execução isolada passa
transporte e geração/exportação reais. Ruff/ESLint/Prettier/TypeScript/build passam.
Servidor antigo recusou campo novo; teste repetido na mesma origem isolada sem
interrompê-lo. Preview geométrico, Office indisponível, avaliação humana pendente.
Relatório em docs/EVOLUCAO_CONTEUDO.md. Sem commit/push; opção desativada por padrão.

## Planejamento semântico — 11/10/2026
Snapshot 64a49f4 enviado antes de editar. Contrato e revisão opcionais adicionados
ao planejamento expressivo; não geram setas sem relações declaradas nesse modo.
Comparação declarada em benchmark/semantic_requests.json: quatro domínios, A 1/4
e B/C 3/4 PPTX, mesmos planos B/C. Revisões finais: quatro regressões e duas
repetições rejeitadas; sem ganho semântico demonstrado. Código/artefatos históricos
preservados. 51 chamadas exploratórias totais, 22 únicas na comparação final.
Negação coordenada corrigida sem reescrever critérios congelados. Auditoria
conferiu bytes, parâmetros, snapshots, rollback e sete PPTX das condições.
Regressão final: 311 Python, dois Node e nove Playwright; quatro optativos omitidos.
Lint/build e cinco pares de previews passaram; Office/LibreOffice indisponíveis.
Resultados/falhas/limites documentados em docs/EVOLUCAO_SEMANTICA.md. Avaliação
humana e calibração do revisor permanecem pendentes.

## Expressividade do planejamento — 11/10/2026
Diagnóstico registrado antes de editar; percurso opcional expressive-planning-v1.
Campos tipados, variantes reais por família, capacidade concisa/detalhada, corpo
mínimo 22 pt, slots de mídia e medição local Arial/palavras com fallback conservador.
Compatibilidade, fontes restritas, requisitos, reparos e compilador preservados.
Onze respostas reais Qwen3, incluindo falhas e uma etapa parcial; before_01 e
after_05 exportaram, recompilação atual preserva conteúdo e tem zero D/V.
Comparações fixas/novas com cinco pares de capturas, zero corte no DOM/erro JS;
cinco famílias com imagens offline, créditos e objetos nativos verificados.
271 Python, dois Node e oito Playwright passaram; quatro optativos omitidos.
ESLint/Ruff/Prettier/TypeScript/build passaram. Renderização real indisponível.
Limitações de conteúdo e diagramas genéricos explicitadas em
docs/EXPRESSIVIDADE_PLANEJAMENTO.md; sem inferir beleza ou verdade da exportação.
HEAD/branch e alterações anteriores preservados, sem commit/push.

## Diagnóstico das próximas melhorias — 11/10/2026
PROXIMAS_MELHORIAS.md analisa o código em 22ebec4 e os artefatos existentes.
Prioriza contrato editorial/profundidade, variantes de composição e imagens
planejadas por função. Identifica evidências, módulos e sequência de implementação,
separando validade estrutural de estética e de limitações atribuíveis ao modelo.
Sem execuções Ollama, novas funcionalidades, commit/push ou alteração de resultados.

## Refinamento visual — 11/10/2026
Base f05fc8a4021b5169342c8498772956f5ccbe0d34 limpa e confirmada no remoto antes
de editar. Diagnóstico do PPTX histórico, fontes registradas e resultados preservados.
Refinamento após composição compara variantes de cards e reorganiza componentes
elegíveis, com conservação de conteúdo, requisitos congelados e rollback.
Hierarquia 42/24/22 pt e conexões OOXML nativas; gramática e AST/IR 1.1 preservadas.
Nova geração Qwen3 real_02: duas chamadas, 1538 tokens de saída/2776 de entrada.
Recompilação final delivery_04 usa exatamente seu plano; comparação histórica
fixed_07 conserva também as simplificações factuais antigas. Cinco pares de PNG
por comparação, auditorias de conteúdo/HTTP/hashes/textos/conexões; nenhum erro JS.
241 Python, dois Node e onze Playwright passaram; lint, formatação e build passaram.
COM/LibreOffice ausentes no Windows e Ubuntu WSL; previews são geométricos.
REFINAMENTO_VISUAL.md documenta o corte de Pagamentos encontrado nas capturas,
piloto rejeitado, correções, medidas e limites. Sem notas humanas ou beleza inferida
de pontuações; artefatos excluídos do Git, entrega preparada para commit/push.

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


## Rodada 2 de design - fase 1 (01/11/2026)

Implementadas regras editoriais locais em editorial.py/alto_layout.py: capa abstrata sem barras, composicao por densidade, topicos sem numeracao, etapas conservadoras, rotulos redundantes suprimidos preservando detalhes, escala por deck e quebra medida de titulos. Fotos em meia pagina com credito visivel e recorte central no renderer/previa. Prompts com perguntas distintas e contexto brasileiro. Filtro lexical de relevancia em media.py; glifo CO2 subscrito usa Segoe UI na previa. Testes offline adicionados em test_design_r2.py; regressao parcial identificou ajustes necessarios nos exemplos densos, corrigidos sem cortar textos. Experimentos em andamento em outputs/design_r2/20261101-2154/; teto compartilhado US$ 0,40. Sem commit/push/stash. Proxima fase: inspecionar PNGs dos quatro briefs e iterar ate tres ciclos.

Ciclo 1: quatro folhas efetivamente vistas, 1/4 válidos e US$ 0,0320992 conhecidos;
quatro chamadas iniciais sem uso mantidas como desconhecidas/reservadas.
Evidência e correções: `outputs/design_r2/20261101-2154/ciclo_1/REVISAO.md`.
Regressão intermediária: 432 passaram, uma falhou por fixture de mídia sem título;
fixture atualizada para fornecer título realista ao novo filtro de relevância.

Ciclo 2: 4/4 PPTX válidos, 0 ERRO/AVISO, uma imagem exportada; custo do ciclo
US$ 0,0261728. Quatro folhas inspecionadas, defeitos e próxima correção em
`outputs/design_r2/20261101-2154/ciclo_2/REVISAO.md`. Testes focados: 86 passaram.
Ciclo 3 em execução; repetição semântica e qualidade editorial seguem mensuradas
por inspeção, sem alegação de solução garantida pelos diagnósticos automáticos.

### Encerramento da rodada 2 — tarefas 2–4

Ciclo 3: 4/4 válidos, quatro imagens no PPTX, US$ 0,0300044. Quatro folhas
inspecionadas; gráfico estatístico indevido em Git levou a veto lexical antes
da comparação. Parada no terceiro ciclo conforme plano; revisão em
`outputs/design_r2/20261101-2154/ciclo_3/REVISAO.md`.

Comparação final em `outputs/comparacao_alto_sld/20261101-2203/`: 12 execuções,
11 PPTX/55 slides, 60 PNGs e 12 folhas efetivamente abertas. A 4/4, B 3/4,
B+img 4/4; custos próprios 0,0323660/0,0284724/0,0296364 USD e ERRO/AVISO
0/28, 1/2, 0/6. B/Internet falhou por A010; imagem de A é asset geométrico
inadequado ao exemplo, enquanto B+img exportou três fotos Commons licenciadas.
Git B+img não incluiu foto. Relatório contém valores individuais, médias,
custo por slide válido, limitações e comparação pareada com três temas da
rodada 1. Inspeção por tema/condição em `REVISAO_FINAL.md`.

Rodada toda: 207 chamadas, 203 conhecidas e quatro sem uso. US$ 0,1787512
conhecidos (ciclos 0,0882764 + lote final 0,0904748); total exato desconhecido,
teto conservador US$ 0,20175 < US$ 0,40. Ledger e hashes conferidos; fontes
registradas em `refs/DESIGN_RODADA2.md` antes dos relatórios. Execução remota
por stdin/runpy; nenhuma saída editada manualmente, nem commit/push/stash.

Comandos: `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp
outputs/_tmp_r2 --junitxml=outputs/comparacao_alto_sld/20261101-2203/pytest_final.xml`
passou **438 testes em 86,16 s**; um aviso preexistente Starlette/AnyIO.
`ruff check src tests scripts` limpo; `outputs/runtime/node.exe --test
renderer/render.test.mjs`: dois passaram. Cópia/hash do código em
`codigo_executado/` e `codigo_sha256.json`; auditoria em `auditoria_final_r2.json`.
Remoção do temporário rejeitada pela política automática com caminho verificado;
`outputs/_tmp_r2` permanece. Nenhuma alteração na pasta `_pt` antiga.

Restam repetição semântica, títulos longos/Title Case, rótulos genéricos,
omissões/afirmações factuais não verificadas, um caso A010 e dependência da
relevância lexical. As prévias são IR/Pillow, sem comprovar aparência no Office;
não houve avaliação humana cega nem demonstração de qualidade equivalente.

## Rodada 3 ? implementa??o local (01/11/2026)

Removida redu??o global de fontes; escala Alto 42/24/20 pt, m?nimos 32/20/16 pt (subt?tulo 18 pt). Cart?es ampliam altura; dois itens em duas colunas; ocupa??o por uni?o de caixas com aviso abaixo de 0,30. Repeti??o entre irm?os/r?tulos telegr?ficos orienta reparo existente. Capa em caixa de frase com foto/cr?dito e reutiliza??o de busca. Harness aceita seeds e relata m?dias/faixas. Valida??o offline e ciclos em andamento em `outputs/design_r3/20261101-2216`.

Rodada 3: 82 testes direcionados passaram; Ruff limpo. Compatibilidade densa resolvida com perfil 20/16 pt restrito ao slide denso; os demais preservam 24/20 pt. N?o h? redu??o abaixo dos m?nimos nem redu??o global por deck. Ciclo 1 em execu??o.

Rodada 3 ? ciclo 1 inspecionado: 3/4 v?lidos, USD 0,0341444 conhecidos, 3 fotos em PPTX v?lidos. Falha A010 Internet; inconsistencia foto da capa no roundtrip corrigida na gram?tica/printer e pr?-valida??o. R?tulo telegr?fico e conclus?o repetitiva motivam ciclo 2. Evid?ncia `outputs/design_r3/20261101-2216/ciclo_1/REVISAO.md`. Regress?o de fase 1: 446 pytest passaram em 77,47s.

Rodada 3 ? ciclo 2 inspecionado: 3/4 v?lidos, cinco fotos em PPTX, USD 0,0303072 pr?prios / 0,0644516 acumulados. Capas/roundtrip e conclus?o solar melhoraram; Git A010 por duas unidades e ?cone no lugar de foto motivam escolha adaptativa da largura e filtro fotogr?fico no ciclo 3. Revis?o em `outputs/design_r3/20261101-2216/ciclo_2/REVISAO.md`.

Rodada 3 ? ciclo 3 encerrado pelo limite: 4/4 v?lidos, tr?s fotos, USD 0,0325836 pr?prios / 0,0970352 acumulados conhecidos, zero uso desconhecido. Revis?o `outputs/design_r3/20261101-2216/ciclo_3/REVISAO.md`. Persistem repeti??o conceitual, t?tulos gen?ricos e conte?do n?o verificado. Corrigida espera do Commons antes do lote final de 36 execu??es.

Rodada 3 ? quality gates finais: 452 pytest em 82,90s, Ruff limpo, 2 testes Node. Evid?ncia `outputs/design_r3/20261101-2216/pytest_final.xml`. Lote final `outputs/comparacao_alto_sld/20261101-2227/` em andamento com c?digo fixo; seed 42 registra P001 em A/Internet e A010 em B+img/solar, al?m de grafo de hyperlinks indevidamente aceito pela relev?ncia lexical. Sa?das preservadas e limita??es ser?o incorporadas ? an?lise final.

# Rodada 5 de design — fase de implementação (11/11/2026)

**Concluída:** ciclo 3 atingiu (a)–(e): 16/16 PPTX/89 slides, zero A010/A019/D010,
ocupação 0,6294, rows 7/30 (23,3%), fotos grandes em photo40 0, eixos mistos 0.
Repetição imediata 0; variantes/deck 4,9375; 14/15 conclusões em colunas numeradas.
48 folhas abertas. Comparação tripla e relatório em `outputs/design_r5/20261111-001430/`.
614 pytest passaram em 90,59 s; Ruff limpo; 2 testes Node passaram. ZIP/XML confirmou
629 textos editáveis, 332 formas e 19 imagens, sem divergência de texto/família/tamanho.
Gramática Alto e corpus inalterados; US$ 0, sem APIs/commit/push/stash.
Calibragem e tabela óptica em `REGRAS_DESIGN.md`. Restam fotos pequenas/retrato
irrelevante, transições esparsas e hierarquia menor nas comparações densas.

Registro das fases anteriores (abaixo) preservado como histórico.

Ciclo 2: ocupação 0,6352, 16/16 válidos, 14/15 conclusões em colunas. Todas as
16 folhas abertas. Catálogo repete cards porque a alternativa rows ainda exigia
gap mínimo de 24; terceiro ciclo corrigirá o intervalo denso e arredondamento.

Ciclo 1 concluído: 16/16 PPTX, 89 slides, ocupação 0,6288, tópicos em rows 6/30,
zero A010/A019/D010 e nenhuma foto grande paisagem/quadrada em photo40.
16 folhas abertas; conclusões regrediram para listas em oito decks.
Segundo ciclo recuperará colunas e compactará a comparação densa.

Plano e bases r4 lidos; corpus de 16 decks copiado sem alteração para
`outputs/design_r5/20261111-001430/corpus/`. Código de entrada e hashes preservados.
Rodada offline/US$ 0, sem commit/push/stash. Calibragem de ocupação, escala por altura-x,
preferência por fotos e cartões e eixo comum em implementação; testes de geometria
exercitam os seis estilos. Fontes locais registradas em `refs/DESIGN_RODADA5.md`.


## Rodada 6 — Parte A concluída; Parte B bloqueada por autenticação (11/11/2026)

Plano: `docs/PLANO_CODEX_RODADA6_DESIGN.md`; fontes: `refs/DESIGN_RODADA6.md`.
Código: `alto_layout.py`, `design_system.py`; testes r3/r4/r5 atualizados e
`test_design_r6.py`, `test_reais_r6.py` adicionados. Harness pago:
`scripts/testes_reais_r6.py`; comparação offline: `scripts/comparar_design_r6.py`.

Parte A offline, US$ 0: dois ciclos, 32 folhas abertas. Critérios (a)–(e)
preservados: 16/16 PPTX, 89 slides, ocupação 0,6294→0,6664, tópicos em rows
7/30→4/30, zero A010/A019/D010/eixo misto/repetição imediata. Dez fotos internas
em photo50; oito A031 mantidos. Quinze conclusões em colunas com número interno.
Rótulos/descrições compartilham topos; cartões têm altura natural + padding32;
centro útil −5%, limitado pelo topo. Fontes começam no maior perfil válido.
Fotos ≥600 px têm variante única independente de estilo; <600 px usam texto,
inclusive capa. Transições curtas: 48–54 pt, bloco de um terço e motivo da família.

Evidências: `outputs/design_r6/20261111-004533/RELATORIO.md`, `comparacao/`,
`ciclo_1/REVISAO.md`, `ciclo_2/REVISAO.md`. Corpus idêntico por SHA-256 à r5;
gramática Alto, IR e roundtrip preservados. Refinamento de capa <600 px não
altera o corpus inspecionado: IR finais reconstruídas e comparadas, sem diferença.
Auditoria PPTX: 629 textos, 345 formas, 19 imagens, 89 slides; zero divergência
de fonte/texto. **640 pytest passaram em 156,28 s**, Ruff limpo e dois Node.
Um aviso Starlette/AnyIO preexistente; editor/renderer não alterados nesta rodada.
Temporários preservados; nenhum commit, push ou stash.

Parte B: modelo **gpt-5.4-mini**, tarifa configurada (somente presença verificada;
nenhum valor do .env exibido), seis pedidos/estilos, seis slides/seed42,
imagens livres habilitadas, pesquisa desligada, sem imagens por IA.
**6/6 tentativas recusadas com HTTP 401 antes do roteiro. Nenhum deck novo foi
gerado:** sem PPTX/SLDA/PNG de slide. Os seis contato.png e a galeria são painéis
de falha explicitamente identificados; não são folhas de decks reais.
Nenhuma busca de fotos foi alcançada. Credencial local carregada; sem chave
herdada. Não se modificou .env nem se imprimiram seu conteúdo ou a chave.

Pasta: `outputs/testes_reais/20261111-0050/`, com `INDICE.md`, `galeria.png`,
`resultados.json`, `orcamento.json`, diagnóstico e uso por tentativa.
ULTIMO.txt aponta para essa execução. Seis painéis e galeria abertos.
Gasto conhecido **US$ 0,00000000**; seis usos/custos desconhecidos; total exato
**desconhecido**; reserva conservadora **US$ 0,09354600**, dentro de US$ 0,50.
Não declarar custo total zero. Não houve retries pagos após as seis falhas.

Foi solicitada atualização local da credencial, sem enviá-la no chat.
Após corrigir a credencial, retomar da raiz em nova pasta automática:

```powershell
.\.venv\Scripts\python.exe scripts/testes_reais_r6.py --carry-budget outputs/testes_reais/20261111-0050/orcamento.json
```

O ledger conserva as seis reservas no MESMO teto total de US$ 0,50; preflight
por deck e reserva antes de cada chamada. Não iniciar outro lote com orçamento
zerado. Retomada dentro do teto já autorizado exige credencial válida, sem nova
autorização de gasto. **Parte B permanece pendente, não concluída.**

Limitações: nota geométrica caiu 0,8023→0,7048, apesar dos critérios explícitos;
vazios externos, recorte/nitidez das fotos e grafo irrelevante do corpus antigo
persistem. Sem validação Office, avaliação humana cega ou pesquisa factual.
Conteúdo gerado não foi editado à mão para esconder falhas.

## Rodada 7 — fase 1: documentos e edição (11/11/2026)
Fontes registradas em refs/DOCUMENTOS_EDICAO_R7.md. Implementados extração DOCX limitada,
dossiê documental, prioridade documental sobre suplementos web, estilo auto, substituição
local de bloco Alto, CLI/API e histórico de revisões com consumo acumulado. Interface em
integração; testes ainda não executados nesta fase. Próximo: regressão, testes UI e lote real
com teto independente autorizado de US$ 0,60, sem imagens por IA. Sem commit/push/stash.

## Rodada 7 — fase 2: verificação e primeiro lote (11/11/2026)
672 pytest passaram em 117,82 s, Ruff limpo, dois Node; build npm com --configLoader
native passou (configuração padrão do esbuild não lê um ancestral no sandbox). Os dois
novos testes Playwright passaram; encerramento da suíte UI ainda em análise.
Primeiro lote falhou no transporte: cinco chamadas sem uso conhecido e reserva
US$ 0,08191650, preservadas no ledger. Retomada via stdin/runpy alcançou a API:
primeiro deck válido, DOCX inválido por A005. Custo conhecido até aí US$ 0,13237410,
limite com reservas US$ 0,21429060. Folha mostrou foto de evento irrelevante e recuperação
excessiva de exemplos CLI. Reforçados veto de eventos e prioridade a trechos narrativos
(resumo/introdução/objetivos/resultados/limitações). Nova execução em andamento, com
ledger acumulado; não declarar conclusão antes da inspeção dos artefatos finais.

## Rodada 7 — concluída em 11/11/2026

Plano: docs/PLANO_CODEX_RODADA7_DOCUMENTOS_EDICAO.md. Fontes previamente registradas em
refs/DOCUMENTOS_EDICAO_R7.md. Alterações anteriores preservadas; sem commit, push, stash,
imagens por IA, exposição de chave ou conteúdo do .env. TLS permaneceu verificado.

- T1: TXT/MD/PDF textual e DOCX sem dependência nova, até oito arquivos, 2 MiB por arquivo
  e 5 MiB para DOCX; macros/cifra recusadas. Dossiê local com trecho literal verificado,
  fontes documento:nome#trecho-N, prioridade documental e internet opt-in; CLI/API/UI.
- T2: refazer_slide troca somente o bloco selecionado; valida gramática/check_slide,
  no máximo um reparo. Ajustes sem modelo de estilo/foto/ordem/exclusão, histórico em
  outputs/criar/<id>/versoes e desfazer persistido; consumo inclui falhas e versões desfeitas.
- T3: Commons com categorias/extmetadata, consulta central preservada nos fallbacks,
  veto de retratos/eventos/diagramas e fallback de imagem sem foto em cartões/destaque.
  Revisão conservadora rejeita PNGs da busca fotográfica e metadados sem descrição
  suficiente. Buscas adicionais de foto sem inferência obtiveram varanda e roteador.
- T4: estilo auto determinístico, padrão na UI/CLI; público infantil e contexto acadêmico
  precedem tema técnico. Regra e limites em docs/REGRAS_DESIGN.md; troca sem modelo.
- T5: 678 pytest passaram em 112,72 s (um aviso Starlette/AnyIO preexistente), Ruff limpo,
  dois Node, npm build e lint passaram. Build usou --configLoader native por restrição
  do esbuild no sandbox. Playwright final: 15 passaram em 17,1 s, cinco testes locais
  opcionais pulados; inclui upload real e edição com modelo simulado. A primeira suíte
  exigiu encerrar sua própria árvore de servidor na porta 8777; a final usou servidor
  separado na porta 8778 e encerrou os testes normalmente. Logs em outputs/rodada7/.
- T6: seis PPTX finais, 42 slides, duas fotos Commons. Folhas finais, galeria e comparação
  antes/depois abertas. Original de documento/DOCX desta execução falhou em A005/A010;
  os slides 1/6 e 5 foram refeitos em pastas novas, sem editar o texto manualmente.
  Slide 3 refeito em uma chamada por US$ 0,00516750; outros sete blocos idênticos em bytes.

Evidência principal: outputs/testes_reais/20261111-0131_r7/INDICE.md, galeria.png,
03_refeito_revisado/antes_depois_slide3.png e preservacao.json. Antes em antes.slda e
antes.pptx; depois em apresentacao.slda e apresentacao.pptx na mesma pasta de edição.
ULTIMO.txt aponta para essa execução. ARQUIVOS_ALTERADOS.md e manifesto_sha256.json
relacionam arquivos e artefatos. Auditoria do deck do projeto encontrou zero números
visíveis ausentes dos fatos e conferiu os nomes técnicos; não prova toda paráfrase.

| Caso final | Válido | Fatos documentais usados | Fotos | Chamadas | USD |
|---|---|---:|---:|---:|---:|
| Artigo + README | sim | 19 | 0 | 37 | 0,06522735 |
| DOCX do artigo | sim | 19 | 0 | 34 | 0,06548055 |
| Refazer slide 3 | sim | 20 | 0 | 1 | 0,00516750 |
| Git | sim | 0 | 0 | 8 | 0,01478985 |
| Horta | sim | 0 | 1 | 7 | 0,01352625 |
| Internet | sim | 0 | 1 | 10 | 0,01797705 |

A tabela soma geração e reparos por caso; refazer é apenas o custo adicional de edição.
Casos finais US$ 0,18216855; tentativas anteriores US$ 0,13237410. Rodada inteira:
176 tentativas, 171 com uso conhecido; US$ 0,31454265 conhecidos. Cinco falhas iniciais
no transporte têm uso/custo desconhecidos, reserva US$ 0,08191650. Total exato desconhecido;
limite com reservas US$ 0,39645915 <= teto US$ 0,60. Nenhuma chamada de imagem por IA.
Ledgers anteriores preservados e acumulados, nunca reiniciados. Não houve HTTP 401 nesta
rodada. Retomada via stdin/runpy funcionou; causa das falhas de transporte não foi comprovada.
Lote encerrado: não fazer novas inferências para melhorar a amostra sem outra solicitação.

Continuam ruins: filtros lexicais perdem fotos úteis; a foto do roteador tem recorte apertado
com marca em destaque, e a varanda contém plantas ornamentais. Há comparações de aspectos
não equivalentes, repetição e generalizações (por exemplo, modelos menores e conexão sempre
ativa). O RAG inicial recuperava comandos CLI demais; priorizar trechos narrativos melhorou
o assunto, mas oito passagens não cobrem todo o artigo. Verificação por modelo tem falsos
positivos e custa chamadas. Validade formal não implica sustentação semântica nem beleza.
Prévias IR/Pillow, sem validação Office ou avaliação humana cega. Git/horta/internet não
usaram pesquisa factual. Projeto com IDs estáveis, reabertura pela UI, voz e celular
continuam como etapas futuras do plano maior; o histórico desta rodada é específico dos jobs Alto.

## Seminário 2 — 11/11/2026
Ajustes pequenos para slides de uma ideia: comparação com 1–4 itens por lado, avisos A023/A024,
rodapé com rótulo próprio e nome do documento. 684 testes passaram, Ruff limpo. Medição real com
`scripts/medir_execucao.py` em `outputs/sem2/` (medicao.json: artigo, inválido, 298 s;
medicao_demo.json: documento do sem2, válido, 160 s). Deck final em `outputs/sem2/demo_sem2_v4/`.
Documento de entrada em `academy/ai4good/va2/sem2_slidedsl.md`.
Depois: correção do verificador que vinha só com o veredito ("parcial") deixou de ser aplicada
como texto; 685 testes. API paga no mesmo documento (medicao_api.json): 65,7 s, 29 chamadas, US$ 0,051;
local: 160 s, 44 chamadas, 70.154/10.901 tokens, US$ 0. Deck de 6 slides em outputs/sem2/demo_sem2_v5/.
Google Slides: src/slidedsl/google_slides.py, /api/google/{status,login,slides}, botão no editor e
comando google-slides; 690 testes, Ruff, build e ESLint ok. Envio real depende da credencial do usuário
(docs/GOOGLE_SLIDES.md); ainda não testado contra o Google de verdade.

## Seminário 3 — diagramas SVG pelo compilador — 18/11/2026
Novo `src/slidedsl/svg_diagrams.py`: o compilador desenha em SVG os blocos `etapas` (fluxo),
`ciclo` (novo bloco da gramática, lido como etapas com `cycle=True`) e `grafico` (barras com
altura exatamente proporcional). Texto medido com `text_metrics`; aviso quando não cabe.
Comando `slidedsl alto-svg arquivo.slda --out pasta`. Testes em `tests/test_svg_diagrams.py`;
suíte completa: 703 passaram (uma falha só por caminho > 260 caracteres no basetemp, repetida
com caminho curto e aprovada).
Teste do sem3: `experiments/svg/pedidos.json` (12 pedidos com gabarito), `scripts/teste_svg.py`
(A: IA escreve o SVG; B: IA escreve o bloco, compilador desenha) e `scripts/conferir_svg.mjs`
(renderiza no Chrome e confere elementos, ordem, sobreposição, bordas, setas sobre texto,
contraste ≥ 3:1 e proporção das barras ≤ 2%).
Teste pequeno (3 pedidos, seed 42): OpenAI respondeu 401 (chave recusada); rodou com
qwen3:4b-instruct local. A 0/3, B 2/3 (`outputs/sem3/teste_svg/piloto3_qwen_20261118/`).
O que quebrou: o conferidor aprovava um ciclo ilegível (passou a checar círculos, setas e
contraste); o modelo escreveu `ciclo`, ausente da gramática (virou bloco). Ensaio, não resultado.
Deck do seminário: gerado com o Qwen local em `outputs/sem3/gerado_v1/` (faltou o competidor e
inventou "estudantes reais" nas notas) e versão final editada à mão em `outputs/sem3/final/`
(sem3.slda, sem3.pptx, prévia). Roteiro em `academy/ai4good/va2/sem3_slidedsl.md`.
Depois (18/11): chave nova da API; teste pequeno com gpt-4.1-mini: A 0/3 (US$ 0,0051), B 3/3
(US$ 0,0007), em `outputs/sem3/teste_svg/piloto_api_20261118/`. Deck v2 gerado nos dois modos a partir
do roteiro atualizado (local 200 s; API 172 s, US$ 0,038) e revisado; ambos omitiram o competidor.
Registro completo, decks e diffs em `academy/ai4good/va2/sem3/REGISTRO.md`.
Depois (18/11, à noite): deck do sem3 saiu fora do tema pela interface. Correções (não commitadas, dependem
do trabalho de documentos ainda não commitado): `documents.document_sections` liga cada fato à seção `##`
do documento; `generate_alto(sections=...)` torna as seções tópicos obrigatórios do roteiro, na ordem, e
aceita a primeira seção na capa; trecho que é título de seção não vira fato. Testes em
`tests/test_document_sections.py`; suíte completa: 707 passaram. v3 pela API seguiu as 6 seções do roteiro.
