# Planejamento conceitual e investigação de conteúdo — 11/10/2026

**Resultado: o novo percurso exportou 6/6 apresentações, contra 3/6 do controle,
mas não demonstrou melhoria geral de conteúdo.** Frações ganhou um exemplo numérico
completo; conceitos deixaram de ser obrigatoriamente componentes. Permanecem
omissões, conclusões fracas e um critério problemático na comparação de arquitetura.
Nos mesmos planos históricos, as seis propostas do revisor foram rejeitadas.
O modo continua experimental, opcional e desativado por padrão.

A [investigação prévia](INVESTIGACAO_CONTEUDO.md) foi registrada antes das alterações.
Base de controle: `fea5a52fdfb7ed1bead88b81debefda537f93dc1`. Não houve commit/push
nesta etapa. Fontes de método/domínio estão em [FONTES](../refs/FONTES.md).
Resultados históricos não foram reescritos.

## Diagnóstico que motivou a implementação

O contrato anterior escolhia uma composição antes do conteúdo. `concept` com
`stack` virava arquitetura, admitindo somente componentes; um fluxo admitia
somente etapas. Numerador/denominador viraram componentes, e temperatura/exemplo/
condição viraram etapas nas evidências anteriores. Esses tipos não corrigiam
o significado de nomes como Camadas, Responsabilidade ou Exemplo.

Os seis patches históricos não foram descartados somente por um critério rígido:
arquitetura introduziu textos sem pontuação e novos avisos; frações conservou
pendências e acrescentou incoerência lexical; processos corrigiu uma garantia,
mas ultrapassou a capacidade geométrica. A revisão podia atingir vários slides
na mesma chamada e não explicava a rejeição anterior à tentativa seguinte.
São causas observadas no código/artefatos; carga de tarefa e limites intrínsecos
do modelo continuam hipóteses sem ablação causal.

## Percurso implementado

```mermaid
flowchart LR
  A[Pedido e requisitos congelados] --> B[Qwen3: conteúdo sem slides]
  B --> C[Integridade de referências e fontes]
  C --> D[Qwen3: seleção e distribuição por slide]
  D --> E[Projeção dos registros selecionados]
  E --> F[Diagnóstico e até duas revisões locais]
  F --> G[DSL, LALR, IR e validadores existentes]
  G --> H[Editor e PPTX nativo]
```

O protocolo opcional `conceptual-planning-v1` usa **duas chamadas de preparação**.
Não há terceira chamada para reescrever o conteúdo. A primeira separa definições,
entidades/responsabilidades, etapas, exemplos com cenário/observação, afirmações/
condições, alternativas/critérios e síntese com bases posicionais. Não contém
slides, coordenadas ou layouts. Um enum limita a forma das referências; auditoria
confere se elas existem e se fontes pertencem ao contexto fornecido.

A segunda chamada seleciona IDs desses registros, intenção, mensagem curta e
relações permitidas por slide. Variantes do schema relacionam intenção e papéis;
estruturas são derivadas pelo código. Comparações projetam o mesmo critério nas
duas alternativas, com alinhamento já existente. Relações desenhadas continuam
exigindo componentes/etapas reais, existentes, adjacentes e ordenados.

A projeção preserva literalmente cenário/observação e afirmação/condição dos
registros **selecionados**, sem cortar frases ou diminuir fontes. O rastro
`conceptual_projection.json` lista também os registros descartados. Preservação
literal não garante seleção completa: o caso reservado de pilhas/filas revelou
que exemplos corretos podem ficar fora dos slides. `based_on` verifica IDs,
não implicação lógica nem presença de todas as bases na apresentação.

Não se substituem gramática, AST/IR 1.1, parser, compilador, editor ou renderer.
O modo semântico anterior permanece disponível. O novo percurso é limitado a
apresentações nativas sem imagens, aliases ou layout imposto; não suporta modo
restrito extrativo. `grounded` conserva IDs dos fragmentos fornecidos ao plano
conceitual; associação não comprova sustentação. Não houve ensaio real novo
de fundamentação documental nesta comparação.

## Revisão e aceitação

A revisão agora concentra uma chamada em um slide, prioriza bloqueios e permite
revisar campos dependentes do mesmo nó. A segunda tentativa recebe o diff
rejeitado e as regressões, sem substituir o estado preservado. Limites curtos
de detalhe/explicação reduzem o espaço de propostas. Não se modificam arrays,
quantidade, geometria ou outros slides. Orçamento máximo continua duas chamadas.

Q003 reconhece prefixos abstratos; Q008 cobre mais descrições genéricas. Q002
também sinaliza garantias em títulos. Condição deve aparecer no corpo: renomear
o rótulo para “Condição” ou citar “isolamento/contrato” não remove uma garantia.
Esse atalho foi observado no piloto pareado e fechado antes da bateria final.
K006 foi descrito com precisão: detecta ausência de pontuação final, não prova
que uma frase pontuada esteja completa.

Mantêm-se veto a novos diagnósticos/bloqueios, apagamento, perda de fonte ou de
requisito já atendido, e exigência de progresso. Não se relaxou a aceitação para
fabricar sucesso. A melhoria do protocolo não produziu reparo útil nos mesmos
planos históricos. No percurso novo, uma correção de título em frações foi aceita;
ela reduz um sinal lexical, mas deixa o conteúdo problemático da síntese.

## Protocolo experimental e integridade

[Manifesto final](../benchmark/content_final_requests.json): quatro pedidos
conhecidos — arquitetura (cinco slides), ciclo da água, frações e aprovação
(dois slides cada) — e dois novos, densidade e pilhas/filas. Uma seed 42,
temperatura 0,1, contexto 8192, saída máxima 4096, thinking desligado.
Exclusivamente `qwen3:4b-instruct` em Ollama loopback, versão 0.40.2; digest
observado `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Sem imagens, API de linguagem online ou reparos de requisitos (`repair_max=0`).

Controle executa os módulos Python congelados do commit base, sem revisão.
Tratamento executa módulos congelados atuais, com planejamento conceitual e
revisão. O runner registra o caminho dos módulos realmente importados, snapshots,
schemas, parâmetros, bytes HTTP/brutos e tokens. Portanto, não se atribui o
resultado do tratamento somente à decomposição: contratos, prompts e revisão
também mudaram. Mesmos pedidos, modelo e limites não são uma ablação.

Quatro pares conhecidos e revisões históricas estão em
[final_08](../outputs/conceptual/final_08/evaluation.json). A auditoria encontrou
caracteres `?` no lugar de acentos/`³` nos dois pedidos novos dessa pasta.
As execuções foram preservadas; repetiram-se somente os dois pares em
[final_11](../outputs/conceptual/final_11/evaluation.json), com UTF-8 correto.
Os hashes Python de ambos os snapshots são idênticos ao código entregue.
Não se ajustaram código ou instruções do modelo pelos resultados dos pedidos novos.
Essa repetição é uma correção de entrada, não uma nova avaliação cega independente.

Comparação final consolidada:
[auditoria](../outputs/conceptual/audit_12/audit.json) e
[texto integral antes/depois](../outputs/conceptual/audit_12/comparison.html).
São 12 gerações novas e quatro revisões de planos históricos. As quatro revisões
partem dos mesmos planos B de `experiment_02`, com conteúdo/SHA256 e requisitos
conferidos. Os critérios históricos incorretos de rodapé permanecem nesses quatro
ensaios; resultados de requisitos não equivalem a fidelidade ao pedido.

| Condição | Planos finais / casos | DSL parse/semântica | PPTX estrito | Revisões aceitas/tentadas |
|---|---:|---:|---:|---:|
| Controle semântico anterior, sem revisão | 6/6 | 6/6 | 3/6 | 0/0 |
| Conceitual + revisão localizada | 6/6 | 6/6 | 6/6 | 1/1 |
| Revisor atual nos mesmos B históricos | 4/4 | 4/4 | 3/4 | 0/6 |

| Domínio | Controle PPTX | Conceitual PPTX | Limite observado no novo percurso |
|---|---|---|---|
| Arquitetura | Sim | Sim | Entidades mais concretas; critério Integração problemático e condições fracas. |
| Ciclo da água | Sim | Sim | Definições como conceitos; sequência e causalidade incompletas. |
| Frações | Não | Sim | Exemplo 3/8 completo; local errado e explicação de partes iguais insuficiente. |
| Aprovação | Não | Sim | Termos como conceitos; ordem, atores e responsabilidades insuficientes. |
| Densidade (novo, UTF-8) | Sim | Sim | Cálculo correto; comparação de mesmo volume ausente. |
| Pilhas/filas (novo, UTF-8) | Não | Sim | LIFO/FIFO corretos; exemplos descartados, ordens explícitas e aplicações ausentes. |

Planos exportáveis não equivalem a apresentações completas. O reconhecedor
estrutural mede somente slides/margens em vários pedidos; `faithful=true` não
detectou as omissões de densidade/pilhas. Os pedidos conhecidos de ciências e
processos também deixaram requisitos estruturais de sequência/fluxo pendentes.

## Inspeção qualitativa independente do gerador

A [rubrica](../outputs/conceptual/final_08/human_rubric.json) separa completude,
correção, coerência, exemplos, relações, sustentação da síntese e revisão.
Não se pediu à SLM que certificasse sua resposta. A inspeção abaixo foi feita
pelo agente sobre texto/artefatos e fontes registradas; **não é avaliação cega
por especialistas ou estudo com leitores**. Notas humanas/factuais permanecem
`null`, inclusive na auditoria. Não se agregam proxies lexicais como qualidade.

**Arquitetura.** O controle mistura Camadas/Responsabilidade/Exemplo como
componentes. Depois, slide 2 nomeia Frontend, Backend e API Gateway, com funções
próprias; porém “Interfere com o usuário final” é redação inadequada. Slide 3
compara implantação pelo mesmo critério, mas atribui integração de “Maior
complexidade” ao monolítico e “Menor complexidade” aos microsserviços, sem contexto.
A documentação Microsoft aponta comunicação distribuída e complexidade operacional;
essa simplificação/inversão não passou por verificação factual. Benefícios continuam
com condições tautológicas ou recomendação pequeno/complexo. A conclusão repete
definição e manutenção/escala, sem sustentar a escolha. Não há dependências explícitas
entre os componentes. O layout alinhado melhora leitura da comparação, não sua verdade.

**Ciclo da água.** O controle classifica temperatura, exemplo e condição como
etapas e inventa um limiar de 20 °C. Depois, evaporação/condensação/precipitação
são conceitos, com frases completas, e um dia quente com solo seco serve de cenário
concreto. O limiar desaparece, mas “quando a temperatura do solo aumenta” é
condição pouco informativa; temperatura isolada não cobre fatores ambientais.
O pedido de sequência inicial não é cumprido por uma lista de definições sem
relações de ordem. A apresentação permanece coerente no assunto, mas incompleta
na explicação do ciclo e nas condições; não houve revisão nesse plano.

**Frações.** O controle tem cinco campos sem pontuação e vincula partes iguais
a justiça/equidade, sem uma fração numérica completa. Depois, numerador/denominador
são conceitos; o caso de oito pedaços iguais, três comidos, explicita numerador 3
e denominador 8. Esse exemplo melhora a concretude. “Bolo” permanece componente
com uma função de apresentação, e o exemplo vai ao slide 2 em vez do slide 1.
Não há aplicação distinta desenvolvida nem explicação suficiente da unidade de
medida das partes. A síntese mantém “justas e comparáveis”. O título com garantia
de equidade foi reescrito, mas a revisão aceita não resolveu esse problema conceitual.

**Aprovação.** O controle apresenta generalizações e texto não terminado; as
propostas sobre o plano histórico seguem sem ganho aceito. Depois, Registro,
Análise e Decisão têm frases completas como conceitos, sem relações de processo.
Um pedido de atualização de software ilustra o registro, mas não o percurso até
aprovar/rejeitar. Condições de clareza/completude repetem a afirmação, sem atores,
responsabilidades ou critério de decisão. Tema e títulos estão relacionados, mas
a progressão pedida e a conclusão operacional continuam insuficientes.

**Densidade, UTF-8.** Ambos calculam 20/10 = 2 g/cm³. O controle trata massa,
volume e densidade como componentes e organiza cálculo/comparação como etapas;
“densidade comparável” não explica a comparação. Depois, as definições são conceitos
e o cálculo é exemplo com cenário/observação, sem falsificar sequência. Massa e
densidade estão distinguidas por definição, mas a relação de mesmo volume — maior
massa implica maior densidade — não chega à conclusão. A síntese conceitual não
foi selecionada. Coerência temática melhora a classificação; completude continua
parcial e não há revisão nem relações explícitas.

**Pilhas/filas, UTF-8.** O controle explicita ordens 3→2→1 e 1→2→3 e aplicações
backtracking/atendimento, mas mistura aplicações com etapas, não termina frases
e ultrapassa a geometria. Depois, LIFO/FIFO são definições corretas. O slide 2
seleciona Elemento 1/2/3 como componentes de inserção, deixando de mostrar a remoção.
O plano conceitual tinha dois exemplos válidos de última/primeira entrada, mas
`unselected` contém `example_1`, `example_2` e `synthesis`. Aplicações adequadas já
faltavam no plano conceitual. É uma regressão de completude, apesar do PPTX válido;
sem sinal lexical, o revisor faz zero chamadas. A alocação precisa de controle de
cobertura, além de preservar o texto dos registros selecionados.

## Custo, tempo e resultados negativos preservados

| Condição final | Chamadas únicas | Tokens entrada | Tokens saída | Tempo de percurso | Tempo HTTP Ollama |
|---|---:|---:|---:|---:|---:|
| Controle, seis pedidos | 12 | 16.858 | 6.140 | 175,27 s | 114,80 s |
| Conceitual, seis pedidos | 13 | 14.022 | 5.170 | 192,19 s | 126,22 s |
| Revisão de quatro B históricos | 6 | 12.917 | 905 | 88,96 s | 70,66 s |

Comparação final: **31 chamadas, 43.797 tokens de entrada e 12.215 de saída**.
Não se somou novamente a geração histórica dos planos B. As 31 respostas terminaram
com `stop` e satisfizeram o schema bruto; isso não garantiu qualidade conceitual.
Tempos incluem carga/cache/compilação e não sustentam conclusão causal de desempenho.
Uma repetição/seed por pedido não sustenta ganho estatístico geral.

Desenvolvimento inteiro, incluindo pilotos, entradas corrompidas, falhas e o teste
real do editor: **86 chamadas, 115.995 tokens de entrada e 38.589 de saída**.
A auditoria lista custo por pasta; não conta essas tentativas como apresentações
independentes da comparação final.

| Pasta preservada | Limite/resultado |
|---|---|
| `experiment_01` | Primeiro contrato conceitual confundiu roteiro e etapas; referências/nomes falharam. |
| `experiment_02` | Plano conceitual somente orientativo; redação posterior ainda perdeu conteúdo e tipos. |
| `experiment_03` | Referências livres falharam; passagem para vocabulário posicional limitado. |
| `experiment_04` / `05` | Alocação incompatível com estrutura/papéis; variantes de schema ligadas à intenção. |
| `experiment_06` | Primeira bateria com fotossíntese/busca binária: tratamento 3/6; erro de exemplo central e ausência de ganho geral. Atalho de rótulo/condição observado no revisor pareado. |
| `experiment_07` | Repetição de ciências, exportação válida mas sequência pendente. |
| `final_08` | Código congelado; 5/6 tratamento. Densidade excedeu capacidade; pilhas tinha ordens melhores, mas pedidos novos estavam corrompidos. |
| `final_11` | Repetição UTF-8 dos dois pares, mesmos hashes; ambos exportam, omissões persistem. |

Não houve edição de código durante as chamadas finais. Os dois pedidos reservados
iniciais foram inspecionados após o piloto e não são apresentados como nova evidência
cega no fechamento. Novos pedidos corrigidos também não são múltiplas seeds.

## Verificação e uso

Regressão: **325 Python**, dois Node, dez Playwright ordinários passaram; cinco
testes com geração real são optativos. Mais dois testes do novo arquivo passaram
na execução isolada: transporte simulado e geração local real. São 14 casos Python
novos. Ruff, ESLint, Prettier, TypeScript e build passaram. Aviso transitivo
AnyIO/Starlette permanece. Evidências:
[Python](../outputs/tests/content-final-02.xml),
[UI ordinária final](../outputs/conceptual/ui-tests-13/results.json),
[UI real](../outputs/conceptual/ui-real-10/results.json).

O primeiro teste real reutilizou uma API antiga, que respondeu 422 ao novo campo;
o segundo, em porta distinta de desenvolvimento, foi bloqueado pela proteção de
origem. Ambos preservados em `ui-real-08/09`, sem chamadas SLM. A repetição usou
API/editor compilado na mesma origem local isolada e passou, sem interromper o
servidor existente nem remover a proteção de origem.

[Execução pelo editor](../outputs/generation_jobs/795b8bf9346d4ed3a28d84c8355936e4/run/ui_evidence.json):
duas chamadas de preparação e uma revisão; DSL e PPTX baixados pelo navegador,
dois slides nativos, zero erro JavaScript. A auditoria confere 12 PPTX das condições
finais mais esse download, textos iguais à IR e quantidade de conectores ancorados.
Esse teste confirma integração, não resolve o conteúdo de frações.

[Cinco pares de capturas de arquitetura](../outputs/conceptual/captures_08/comparison.html):
fonte exibida igual à salva, zero overflow DOM/erro JavaScript. São conteúdos
diferentes e previews geométricos; não é comparação causal de estética.
[Renderização opcional](../outputs/conceptual/rendering_08/rendering.json) retornou
`engine=geometric`, `rendered=false`: PowerPoint/LibreOffice indisponíveis.

No editor, reinicie a API para carregar a alteração; abra opções avançadas, marque
**Planejamento conceitual**, selecione orçamento de revisão e desative imagens
automáticas/pesquisa. A opção implica planejamento semântico. Confira o conteúdo
antes de exportar. Pela CLI:

```powershell
.\.venv\Scripts\slidedsl.exe generate-contextual --conceptual-planning --semantic-review-max 2 --model qwen3:4b-instruct --strategy C --repair-max 0 --prompt-file benchmark/prompts/arquitetura_software.txt --out outputs/conceptual/nova_geracao
.\.venv\Scripts\python.exe scripts/evaluate_content_planning.py --requests-file benchmark/content_final_requests.json --out outputs/conceptual/novo_experimento --mode control
.\.venv\Scripts\python.exe scripts/evaluate_content_planning.py --requests-file benchmark/content_final_requests.json --out outputs/conceptual/novo_experimento --mode after
.\.venv\Scripts\python.exe scripts/evaluate_content_planning.py --out outputs/conceptual/novo_experimento --mode review
.\.venv\Scripts\python.exe scripts/evaluate_content_planning.py --out outputs/conceptual/novo_experimento --mode summarize
```

A API aceita `context: {conceptual_planning: true, semantic_review_max: 2,
research: "off"}`. O runner retoma somente pastas ausentes; use pasta nova para
uma repetição independente. Reprodução histórica usa seus snapshots.

## Continuidade orientada pelos resultados

A decomposição separou contratos e reduziu coerções comprovadas, sem produzir a
experiência ideal de conteúdo completo/correto. Próxima prioridade: contrato de
cobertura por seção do pedido e fiscalização da seleção de exemplos/síntese,
sem completar faltas com texto genérico. Depois: critérios de domínio e fontes
por afirmação, rubrica com avaliadores independentes, mais seeds/pedidos e
ablação da revisão. Frases pontuadas, IDs válidos e ausência de sinal não são
garantias factuais. Renderização real e avaliação com leitores continuam pendentes.
