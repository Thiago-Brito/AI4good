# Entendendo o ChainForge: programação visual para experimentar e avaliar LLMs

**A mensagem principal:** quando você tem vários prompts, entradas e modelos de IA, o problema deixa de ser apenas gerar uma resposta. Você precisa organizar as combinações, saber de onde cada resposta veio, avaliar resultados e comparar alternativas. O ChainForge usa uma interface de blocos e conexões para apoiar esse trabalho.

Este guia acompanha **o PDF de 18 páginas que você forneceu**. Explica as nove seções, os dois apêndices, as sete figuras e as três tabelas. O foco para sua pesquisa é entender **como a representação visual do fluxo e dos resultados apoia a investigação**, incluindo dificuldades de organização dos blocos na tela. Os exemplos próprios e as propostas de pesquisa estão identificados.

**Referência:** Arawjo, Ian; Swoopes, Chelse; Vaithilingam, Priyan; Wattenberg, Martin; Glassman, Elena L. *ChainForge: A Visual Toolkit for Prompt Engineering and LLM Hypothesis Testing*. CHI 2024, 18 páginas. [DOI](https://doi.org/10.1145/3613904.3642016) · [PDF local](refs/3613904.3642016.pdf) · [Fontes, versão e limites da leitura](refs/FONTES.md).

**Paginação:** “p. 5” significa a quinta página física desse PDF. O corpo principal termina na p. 14; as referências ocupam partes das pp. 14–15; os apêndices ficam nas pp. 15–18. Os nomes dos modelos e os recursos descritos pertencem à época do artigo. Não são recomendações atuais de modelos.

## Como usar este guia

Na primeira leitura, percorra as seções 1–4 deste guia e as Figuras 1, 3 e 4. Na segunda, estude as avaliações e a diferença entre observação, opinião e resultado experimental. Na terceira, volte à seção 10 para relacionar o artigo com a organização dos blocos na sua DSL.

- [1. O problema e a contribuição](#1-o-problema-e-a-contribuição)
- [2. Vocabulário para não se perder](#2-vocabulário-para-não-se-perder)
- [3. Um fluxo explicado do começo ao fim](#3-um-fluxo-explicado-do-começo-ao-fim)
- [4. Combinações, metadados e encadeamento](#4-combinações-metadados-e-encadeamento)
- [5. O artigo seção por seção](#5-o-artigo-seção-por-seção)
- [6. As sete figuras explicadas](#6-as-sete-figuras-explicadas)
- [7. As três tabelas explicadas](#7-as-três-tabelas-explicadas)
- [8. Como interpretar os números](#8-como-interpretar-os-números)
- [9. O que o artigo sustenta e seus limites](#9-o-que-o-artigo-sustenta-e-seus-limites)
- [10. Relação com sua DSL e a organização espacial](#10-relação-com-sua-dsl-e-a-organização-espacial)
- [11. Dúvidas e pontos de atenção](#11-dúvidas-e-pontos-de-atenção)
- [12. Exercícios, roteiro e fichamento](#12-exercícios-roteiro-e-fichamento)

## 1. O problema e a contribuição

### 1.1 Por que conversar com um modelo não resolve tudo?

Imagine que você está desenvolvendo uma ferramenta para reescrever e-mails. Você experimenta uma instrução e a resposta parece boa. Mas surgem perguntas: funciona para outros e-mails? Outro modelo seria mais adequado? O resultado continua bom quando a geração é repetida? O texto é profissional, curto e sem explicações extras?

Esse é um **exemplo didático inspirado na tarefa estruturada do estudo**. Ele mostra a passagem de uma impressão sobre uma resposta para uma comparação entre várias condições. O artigo procura apoiar essa comparação sem exigir que cada pessoa programe toda a infraestrutura de consultas, avaliações e gráficos. [Artigo, seções 1 e 3, pp. 2 e 4.](refs/3613904.3642016.pdf#page=2)

### 1.2 O que os autores entregam?

O trabalho combina três contribuições:

1. **Um sistema implementado:** ambiente visual para construir experimentos com prompts e modelos.
2. **Estudos de uso:** investigação em laboratório e entrevistas com pessoas que já utilizavam a ferramenta ou seu código.
3. **Uma interpretação dos processos observados:** três modos de uso — exploração oportunista, avaliação limitada e refinamento iterativo.

O ChainForge não é apresentado como um novo modelo de IA. A contribuição está no ambiente que permite consultar modelos e compreender seus resultados. [Artigo, seção 1, p. 2.](refs/3613904.3642016.pdf#page=2)

### 1.3 O que muda em relação ao artigo de Oakes?

| Sua leitura anterior: Oakes et al. | Esta leitura: ChainForge |
| --- | --- |
| Organiza problema, workflow e implementação em um framework conceitual. | Apresenta uma ferramenta concreta para experimentar com LLMs. |
| Ajuda a situar a transformação que uma ferramenta pretende apoiar. | Ajuda a examinar decisões de interface e práticas de uso. |
| Analisa ferramentas e estudos da literatura. | Relata estudos próprios com participantes. |
| Discute ML e especificidade de domínio de forma ampla. | Foca prompts, comparação de modelos e avaliação de respostas. |

Essa comparação é uma **síntese didática**, baseada no [guia anterior](../02-workflows-ml/GUIA-DETALHADO.md) e nas seções 1 e 5 deste artigo. Oakes ajuda a formular “onde minha proposta entra”; ChainForge ajuda a perguntar “como as pessoas trabalham com um ambiente desse tipo?”.

## 2. Vocabulário para não se perder

As definições abaixo são explicações introdutórias aplicadas ao sistema das seções 3–4 e à lista de nós do apêndice B. [Artigo, pp. 4–7 e 18.](refs/3613904.3642016.pdf#page=4)

| Termo | Em palavras simples | Exemplo |
| --- | --- | --- |
| **LLM** | Modelo de linguagem de grande porte, usado aqui para gerar texto. | Modelo que reescreve um e-mail. |
| **Prompt** | Entrada enviada ao modelo, com instruções e dados. | “Reescreva de maneira profissional: …”. |
| **Prompt template** | Molde de prompt com partes variáveis. | `Reescreva {email} com tom {tom}`. |
| **Variável** | Espaço nomeado a ser preenchido. | `{email}` recebe diferentes mensagens. |
| **Metadado** | Informação que acompanha um resultado e permite situá-lo. | Modelo usado e valores que preencheram o template. |
| **Metavariável** | Forma de acessar informação associada ao dado, mesmo quando ela não entrou diretamente no prompt. | Resposta esperada armazenada em uma coluna da tabela. |
| **Nó / bloco** | Elemento da interface com uma operação ou papel. | `Prompt Node`, `Simple Evaluator`. |
| **Aresta / conexão** | Ligação pela qual os dados de um nó chegam a outro. | Respostas do modelo seguem para o avaliador. |
| **Upstream / downstream** | Antes/depois no caminho das dependências. | Entradas ficam a montante; avaliação, a jusante. |
| **Evaluator / scorer** | Operação que atribui uma medida ou categoria a uma resposta. | Verificar presença de uma palavra ou medir comprimento. |
| **Ground truth** | Resposta de referência adotada para comparar o resultado. | Gabarito de uma pergunta aritmética. |
| **Cache** | Reuso de resultados já coletados. | Alterar um gráfico sem gerar novamente as respostas. |
| **Combinatorial power** | Capacidade de testar muitas combinações de entradas, prompts e modelos. | Dois templates aplicados a cinco entradas em dois modelos. |
| **Response Inspector** | Visualização para examinar respostas e seus agrupamentos. | Comparar saídas lado a lado. |
| **Toolkit** | Conjunto de recursos combináveis para diferentes tarefas. | Nós de entrada, geração, avaliação e visualização. |
| **LLMOps** | Termo usado no artigo para o conjunto de atividades e ferramentas em torno do uso de LLMs. | Experimentação, testes e avaliação. |

**Uma distinção importante:** modelo de IA, modelo conceitual e modelo do fluxo são sentidos diferentes de “modelo”. Aqui, “comparar modelos” normalmente significa comparar os LLMs que geram as respostas.

No estudo, **teste de hipóteses** é usado em sentido amplo: investigar uma suposição sobre o comportamento do modelo. Isso não implica que cada usuário tenha formulado uma hipótese nula e realizado um teste estatístico formal. Veja os modos da seção 6 do artigo e o caso A.3. [Artigo, pp. 9–10 e 17.](refs/3613904.3642016.pdf#page=9)

## 3. Um fluxo explicado do começo ao fim

### 3.1 O desenho básico

Este esquema é próprio, inspirado no funcionamento descrito pelo artigo:

```text
[Instruções alternativas] ── instrução ──┐
                                       ├──> [Prompt + modelos] ──> [Avaliador] ──> [Gráfico]
[E-mails de exemplo] ───────── email ────┘             │
                                                     └──> [Inspeção das respostas]
```

**Tarefa didática:** comparar duas instruções para reescrever três e-mails, usando dois modelos e pedindo duas respostas para cada combinação. Não executamos esse experimento.

| Etapa | O que entra | O que acontece | O que sai |
| --- | --- | --- | --- |
| Entradas | Duas instruções e três e-mails. | A pessoa fornece os valores para as variáveis. | Conjuntos de textos. |
| Prompt | Template, valores e escolha dos modelos. | O sistema instancia os prompts e solicita respostas. | Respostas acompanhadas de informação sobre sua origem. |
| Avaliador | Cada resposta. | Aplica um critério definido pela pessoa. | Medida ou valor booleano associado à resposta. |
| Visualização | Resultados e medidas. | Organiza comparações por modelo ou variável. | Gráfico ou inspeção detalhada. |
| Revisão humana | Respostas e medidas. | A pessoa interpreta os compromissos entre critérios. | Decisão de alterar instrução, dado, modelo ou avaliação. |

A arquitetura visual combina geração, avaliação e inspeção. Os dados que circulam são tipicamente respostas com metadados; nós de entrada fornecem texto. [Artigo, seção 4.1, p. 5.](refs/3613904.3642016.pdf#page=5)

### 3.2 Como uma métrica pode enganar?

Suponha que um avaliador meça apenas o comprimento. A resposta “Não.” é muito curta, mas provavelmente não reescreve o e-mail de maneira útil. **Medir concisão não mede automaticamente adequação, profissionalismo ou fidelidade ao conteúdo.** Esse é um contraexemplo didático; o estudo mostra que participantes pesam diferentes critérios e às vezes discordam mesmo diante das mesmas respostas. [Artigo, seção 7.1, pp. 10–11.](refs/3613904.3642016.pdf#page=10)

Por isso, mantenha três perguntas separadas: o fluxo executou? O avaliador mediu o que foi programado? Essa medida representa o objetivo da tarefa?

## 4. Combinações, metadados e encadeamento

### 4.1 De onde vêm tantas respostas?

O artigo resume aproximadamente a quantidade de gerações como:

```text
P × M × N × max(1, C)

P = número de prompts instanciados pelas combinações de entradas
M = número de modelos/provedores considerados
N = respostas solicitadas por prompt e modelo
C = históricos de conversa considerados
```

Em um `Prompt Node`, o artigo usa `C = 0`; o fator `max(1, C)` evita zerar a expressão. A fórmula é uma aproximação de planejamento, não uma fórmula exata de custo financeiro nem do número de novas requisições após reuso do cache. [Artigo, seção 4.1 e nota 5, p. 5.](refs/3613904.3642016.pdf#page=5)

No nosso exemplo: `2 instruções × 3 e-mails = 6 prompts`. Com dois modelos e duas respostas por condição: `6 × 2 × 2 = 24 respostas`. Essas repetições são gerações adicionais, não pessoas adicionais no estudo.

No exemplo da Figura 1: `3 comandos × 4 entradas × 4 modelos × 3 respostas = 144 respostas`. O artigo explicita essa conta. Quanto mais dimensões variam, maior é a necessidade de manter a origem de cada resposta visível.

### 4.2 Produto cartesiano versus linhas que permanecem juntas

Com duas listas independentes, as possibilidades se cruzam:

```text
tons = [formal, amigável]
mensagens = [A, B]

Combinações: (formal,A), (formal,B), (amigável,A), (amigável,B)
```

Já uma tabela pode ter valores relacionados por linha:

| Pergunta | Gabarito |
| --- | --- |
| 2 + 2 | 4 |
| 3 + 3 | 6 |

O `Tabular Data` preserva as associações dos valores da mesma linha ao preencher múltiplas variáveis. Tratar pergunta e gabarito como listas independentes criaria pares incorretos. A regra de “seguir junto” está na seção 4.1 e na Tabela 3. A tabelinha acima é um exemplo próprio. [Artigo, pp. 5 e 18.](refs/3613904.3642016.pdf#page=18)

### 4.3 Por que carregar metadados?

Na Figura 5, a coluna `Ideal` guarda a resposta esperada. Ela acompanha o exemplo como informação associada e pode ser usada pelo avaliador, mesmo sem ser colocada na entrada do modelo. Assim, o resultado continua ligado ao seu gabarito. [Artigo, seção 4.1, p. 6.](refs/3613904.3642016.pdf#page=6)

Para sua DSL, a pergunta é: **depois de passar por vários blocos, ainda consigo descobrir qual entrada e configuração originaram este resultado?** Isso diz respeito ao significado e ao rastreamento dos dados, além da posição dos blocos na tela.

### 4.4 Encadear templates não é o mesmo que encadear modelos

- **Encadear templates:** compor moldes de texto antes da consulta. Na Figura 3, a variável de jogo preenche duas instruções; essas instruções preenchem outro template.
- **Encadear chamadas:** usar uma resposta gerada como entrada de uma etapa posterior.
- **Continuar conversa:** usar `Chat Turn` para incluir histórico e enviar uma nova mensagem.

São recursos distintos. Um `TextFields` com template não significa que houve geração por IA naquele nó. [Artigo, seção 4.1, Figura 3 e Tabela 3.](refs/3613904.3642016.pdf#page=5)

## 5. O artigo seção por seção

### Seção 1 — Introduction · p. 2

Apresenta a dificuldade de caracterizar o comportamento de LLMs e a proposta de um ambiente acessível para comparar respostas. Explicita o sistema, os estudos de uso e as implicações de projeto como contribuições. O objetivo inclui experimentar hipóteses abertas, além de encontrar um prompt para uma tarefa fixa. [Ler p. 2.](refs/3613904.3642016.pdf#page=2)

**Pergunta de leitura:** qual é o problema da pessoa que a ferramenta tenta resolver? Resposta: organizar a experimentação e a avaliação, não apenas enviar uma mensagem a um modelo.

### Seção 2 — Related Work · pp. 2–3

Situa ferramentas de descoberta de prompts, avaliação sistemática e ambientes visuais. A Figura 2 organiza esse espaço em dois eixos. Os autores distinguem construir aplicações com LLMs de investigar o comportamento dos modelos, destacando a necessidade de testar combinações. [Ler p. 3.](refs/3613904.3642016.pdf#page=3)

**Cuidado temporal:** afirmações sobre recursos e disponibilidade de outras ferramentas descrevem o panorama do artigo. Não use a seção como comparação atualizada de produtos.

### Seção 3 — Design Goals and Motivation · p. 4

Os quatro objetivos de design são:

| Objetivo | Tradução para uma necessidade concreta |
| --- | --- |
| D1 — seleção de modelos | Comparar alternativas para um caso de uso. |
| D2 — design de templates | Testar instruções que precisam funcionar com várias entradas. |
| D3 — avaliação sistemática | Gerar, medir e organizar muitas respostas segundo critérios próprios. |
| D4 — improvisação | Alterar rapidamente uma hipótese, entrada, modelo ou avaliação. |

D3 e D4 criam uma tensão: a pessoa quer testar com organização, mas também explorar rapidamente sem preparar um experimento rigoroso a cada alteração. Os autores esclarecem que o foco é apoiar avaliações sob demanda. Também mencionam teorias de aprendizagem por variação e analogia como motivação para comparações entre casos. Isso é fundamentação do design; o artigo não realiza um teste isolado dessas teorias. [Ler p. 4.](refs/3613904.3642016.pdf#page=4)

### Seção 4 — ChainForge · pp. 4–7

Começa com o cenário de Farah, que compara modelos para um assistente de escrita. O teste verifica se textos fornecidos como conteúdo conseguem desviar o modelo de sua instrução. Depois explica nós, combinações, inspeção e metadados.

**4.1 — Design Overview:** quatro famílias principais de nós e o problema de navegar muitas respostas. **4.2 — desenvolvimento iterativo:** experiências do laboratório, cinco estudos piloto e comentários de usuários contribuíram para os recursos. **4.3 — implementação:** descreve React, TypeScript, Python, ReactFlow, Mantine e Flask, além de consultas assíncronas, controle de taxa e tratamento de erros. Essas são decisões da implementação relatada, não requisitos de toda DSL visual. [Ler pp. 5–7.](refs/3613904.3642016.pdf#page=5)

Os números de instalações, estrelas e acessos da seção 4.2 são sinais históricos de alcance. Não equivalem a quantidade de usuários ativos atuais nem comprovam eficácia.

### Seção 5 — Evaluation Rationale, Design, and Context · pp. 7–9

Os autores optam por avaliação principalmente qualitativa: querem saber o que as pessoas conseguem investigar, quais dificuldades encontram e como a ferramenta se encaixa em suas atividades. Não apresentam uma comparação controlada de produtividade entre ChainForge e outra ferramenta.

| Aspecto | Estudo em laboratório | Entrevistas com usuários reais |
| --- | --- | --- |
| Participantes | 21 pessoas. | 8 pessoas em 6 entrevistas. |
| Experiência com a ferramenta | Novos usuários no estudo. | Já haviam usado a interface ou o código. |
| Duração | Sessão de 75 minutos por participante. | Entrevistas de aproximadamente 60 minutos. |
| Atividade | Tarefa estruturada e exploração de uma ideia própria. | Mostrar e explicar um uso anterior. |
| Apoio | Vídeo introdutório e pesquisador disponível para ajudar. | Entrevista com compartilhamento de tela. |
| Evidência | Ações, falas, dificuldades e avaliação subjetiva. | Casos reais, necessidades, adaptações e resultados relatados. |

Na tarefa estruturada, todos começam com as mesmas respostas em cache, na mesma ordem, de três modelos para reescrita de e-mails. Primeiro escolhem um modelo; depois variam os prompts e acrescentam avaliação de comprimento. Na parte aberta, investigam uma questão de interesse próprio com apoio do pesquisador. [Artigo, pp. 8–9.](refs/3613904.3642016.pdf#page=8)

O grupo de laboratório inclui 14 homens e 7 mulheres; grande parte tem formação em computação, engenharia ou ciências naturais. Duas pessoas não tinham experiência em programação. Isso importa ao discutir generalização para iniciantes.

**Como os dados viraram achados:** os autores transcreveram aproximadamente 32 horas de gravações e fizeram análise temática indutiva, agrupando observações relacionadas em diagramas de afinidade. No laboratório, três coautores começaram com transcrições separadas e discutiram os agrupamentos; nas entrevistas, o primeiro autor fez o agrupamento. Não confunda esses diagramas de análise qualitativa com o layout de nós da interface. [Artigo, seção 5.1, p. 9.](refs/3613904.3642016.pdf#page=9)

### Seção 6 — Modes of Prompt Engineering and LLM Hypothesis Testing · pp. 9–10

| Modo | O que ainda está em aberto? | Ciclo de trabalho |
| --- | --- | --- |
| **Exploração oportunista** | A pergunta, os prompts e as hipóteses. | Consultar → inspecionar → rever a ideia. |
| **Avaliação limitada** | Como transformar uma intenção em critérios e verificações. | Consultar → avaliar → visualizar → revisar. |
| **Refinamento iterativo** | Como melhorar um fluxo cujos critérios já estão relativamente estáveis. | Alterar → testar → refinar. |

Esses modos são interpretações dos autores sobre o uso observado. Não são etapas obrigatórias nem níveis universais de maturidade. É possível voltar à exploração. “Limitada” pode significar um critério aproximado, como verificar formato em vez de factualidade. [Artigo, seção 6.](refs/3613904.3642016.pdf#page=9)

### Seção 7 — In-Lab Study Findings · pp. 10–11

**7.1 — decisões sobre modelos e prompts:** não houve consenso sobre o melhor modelo para os e-mails. As pessoas valorizavam propriedades diferentes. Inspeção textual e gráficos ofereciam perspectivas complementares.

**7.2 — variedade de usos:** apareceram auditoria, testes de comportamento e refinamento de prompts existentes. Algumas pessoas trouxeram planilhas ou buscaram fontes externas para conferir respostas.

**7.3 — entendimento sobre IA:** 15 participantes disseram que a experiência afetou sua compreensão. É uma percepção relatada, não uma medição objetiva de aprendizagem.

**7.4 — dificuldades:** mover nós para abrir espaço, conectar blocos e excluir arestas; também houve problemas para entender variáveis, descobrir recursos e ampliar uma avaliação para muitas entradas. Este é um trecho central para seu recorte espacial. [Artigo, pp. 10–11.](refs/3613904.3642016.pdf#page=11)

### Seção 8 — Interviews with Real-World Users · pp. 11–13

O uso real acrescenta demandas pouco visíveis no laboratório: exportar resultados, compartilhar fluxos, adaptar código e processar dados. Dos oito entrevistados, dois tinham como interação principal a adaptação do código; seis eram usuários da interface. Cinco entrevistados estavam prototipando pipelines de processamento de dados. [Artigo, seção 8 e Tabela 2.](refs/3613904.3642016.pdf#page=12)

- **8.1:** prompts e seleção de modelos frequentemente eram subtarefas de um objetivo maior de processamento de dados.
- **8.2:** exportar para outros ambientes e compartilhar com colegas ou clientes importava. O `Inspect Node` foi valorizado em usos reais, embora nenhum participante do laboratório o tenha usado ou mencionado.
- **8.3:** alguns recursos existiam, mas eram difíceis de descobrir. Usuários queriam ver respostas no contexto do fluxo com menos ações.
- **8.4:** acesso ao código permitiu adaptar provedores e construir outro projeto de pesquisa.

**Lição para sua leitura:** observar uma sessão curta e acompanhar uso real podem revelar necessidades diferentes. Não conclua que um recurso é dispensável apenas porque ninguém o utilizou em uma tarefa de laboratório.

### Seção 9 — Discussion and Conclusion; 9.1 — Limitations · pp. 13–14

Os autores discutem processamento de dados, modos de uso, múltiplas representações e apoio à construção de avaliações mais sistemáticas. Sugerem considerar interfaces ou layouts adequados a diferentes modos. Essa é uma oportunidade de design, não uma solução experimentalmente validada no artigo. [Artigo, pp. 13–14.](refs/3613904.3642016.pdf#page=13)

As limitações explícitas incluem avaliação qualitativa, sessões curtas e viés de autoseleção nas entrevistas. Os autores propõem estudos quantitativos controlados sobre partes da interface e acompanhamento mais prolongado. [Artigo, seção 9.1, p. 14.](refs/3613904.3642016.pdf#page=14)

### Apêndice A — três casos de uso · pp. 15–17

| Caso | Atividade | Por que representa aquele modo? |
| --- | --- | --- |
| A.1 — P15 | Comparar respostas sobre participação no ensino superior da Indonésia, variando idioma e fonte solicitada. | Novas hipóteses surgem ao inspecionar resultados; não há ainda uma avaliação estabilizada. |
| A.2 — P18 | Consultar estimativas de condutividade e extrair números com um LLM Scorer. | A pessoa passa da inspeção manual à construção de um avaliador e gráfico. |
| A.3 — P8 | Refinar um prompt de uma aplicação de comércio eletrônico em alemão. | O participante já chega com dados, template e critérios; altera partes específicas. |

Esses casos ilustram processos de uso. Não demonstram correção científica das respostas dos modelos nem superioridade geral de um modelo. No caso A.3, a fala sobre “significância estatística” não é acompanhada por um teste estatístico reportado. [Artigo, apêndice A.](refs/3613904.3642016.pdf#page=15)

### Apêndice B — List of Nodes · p. 18

É o inventário de nós da versão apresentada. Use a Tabela 3 como dicionário operacional enquanto acompanha os diagramas. Ela não substitui uma especificação formal de tipos, semântica e execução. [Artigo, p. 18.](refs/3613904.3642016.pdf#page=18)

## 6. As sete figuras explicadas

As imagens abaixo são recortes do PDF de Arawjo et al. (2024), com as legendas originais preservadas para estudo. Clique no link da página para conferir o contexto. As explicações são paráfrases e interpretações do guia.

### Figura 1 — visão geral de um experimento · p. 1

![Figura 1 do ChainForge: entradas, modelos, avaliador e gráfico](outputs/figuras-tabelas/figura-01.png)

**Leia da esquerda para a direita:** o nó superior fornece três comandos de escrita; o inferior, quatro textos de teste; ambos preenchem o `Prompt Node`. Quatro modelos geram respostas, com três gerações por combinação. Um avaliador verifica se a saída começa com `LOL`; o gráfico agrega o resultado. A explicação do cenário está nas pp. 4–5. [Figura e página original.](refs/3613904.3642016.pdf#page=1)

**Como ler o gráfico:** eixo vertical = modelos; horizontal = percentual de `true`. Neste experimento, `true` significa que o teste de desvio foi satisfeito. Assim, **uma barra maior indica maior sucesso do ataque definido pelo avaliador**, e não melhor robustez. Não há regra universal de que verde ou `true` signifique qualidade.

**O que a imagem sustenta:** é possível representar entradas, execução, critério e resultado em um fluxo. **O que não sustenta:** ranking atual de segurança dos modelos ou resistência geral a qualquer ataque. O teste usa um critério específico e versões históricas dos modelos.

**Para sua pesquisa:** observe o espaço ocupado por entradas, configuração e resultado. A imagem dá um exemplo de composição da interface; não compara experimentalmente layouts alternativos.

### Figura 2 — mapa conceitual da área · p. 3

![Figura 2: exploração versus avaliação e interface gráfica versus textual](outputs/figuras-tabelas/figura-02.png)

O eixo horizontal vai de exploração/descoberta a avaliação/teste. O vertical distingue interação textual/código de interface gráfica. O marcador do sistema procura ocupar uma posição gráfica que conecte descoberta e avaliação. [Figura e discussão.](refs/3613904.3642016.pdf#page=3)

**Não é um gráfico de desempenho:** não há unidade numérica, pontuação ou distância quantitativamente validada entre ferramentas. As posições representam uma organização conceitual dos autores. Também não são um levantamento atualizado de todos os sistemas.

**Exercício:** localize sua proposta nesse mapa e explique qual tarefa ela apoiaria. A posição seria sua interpretação, a justificar, não um resultado do ChainForge.

### Figura 3 — templates encadeados · p. 5

![Figura 3: cinco jogos, duas instruções e dois modelos](outputs/figuras-tabelas/figura-03.png)

O `CSV Node` fornece cinco nomes de jogos. O `TextFields Node` contém dois templates que usam `{game}`. Essas dez combinações preenchem `{command}` no `Prompt Node`, que acrescenta uma instrução para responder a alguém que não joga. [Figura e seção 4.1.](refs/3613904.3642016.pdf#page=5)

**Conta:** `5 jogos × 2 templates = 10 prompts por modelo`. Com dois modelos e uma resposta por condição, são 20 respostas. O aviso na imagem informa dez novas requisições **por LLM**; isso é compatível com vinte no total nesse exemplo.

**O que passa nas conexões:** primeiro nomes de jogos; depois textos produzidos pelo preenchimento dos templates. A consulta ao modelo acontece no nó gerador. A ligação entre dois nós de template não implica duas chamadas de IA.

**Para sua DSL:** a interface precisa comunicar tanto as dependências quanto a multiplicação de combinações. Um fluxo com poucos blocos pode representar muitas execuções.

### Figura 4 — organizar respostas para comparar · p. 6

![Figura 4: lista agrupada, grupos recolhíveis e organização tabular](outputs/figuras-tabelas/figura-04.png)

- **A — Grouped List:** quatro modelos aparecem lado a lado, com duas respostas por prompt no exemplo. Os agrupamentos seguem `command` e depois `input`.
- **B — expandir/recolher:** a pessoa abre os grupos que deseja comparar e fecha outros.
- **C — Table:** respostas são organizadas em uma grade; a variável usada nas colunas pode ser alterada.

As cores identificam os modelos e são consistentes na aplicação. Cor, aqui, não é por si só nota de qualidade. [Figura e seção 4.1, pp. 5–6.](refs/3613904.3642016.pdf#page=6)

**Relação espacial mais direta:** alinhamento lado a lado, agrupamento hierárquico e recolhimento mudam como os resultados são apresentados. Isso é organização espacial das respostas, que deve ser distinguida da organização dos nós no editor.

**Limite:** o artigo relata preferências de usuários por diferentes visualizações, mas não apresenta nessa figura um experimento controlado que prove qual layout é superior.

### Figura 5 — avaliação com gabarito · p. 7

![Figura 5: tabela de entrada, instruções, avaliador e contagem de resultados](outputs/figuras-tabelas/figura-05.png)

**A:** tabela com perguntas e respostas esperadas (`Ideal`). **B:** duas instruções alternativas. **C:** o `Simple Evaluator` verifica se a resposta contém o valor esperado, acessado como metadado. **D:** o gráfico compara os resultados por instrução e por modelo. [Figura e descrição, pp. 6–7.](refs/3613904.3642016.pdf#page=7)

**Leia os eixos com cuidado:** o horizontal mostra **número de valores `true`**, não necessariamente percentual de acurácia. As barras empilham contagens identificadas por modelo. Para comparar taxas, seria necessário conhecer também quantas respostas foram avaliadas em cada condição.

**Limitação do critério:** conter a resposta esperada não implica acertar todo o raciocínio. Exemplo próprio: a saída “4, ou talvez 5” contém “4”, mas é ambígua. Um avaliador simples deve ser interpretado conforme o que efetivamente verifica.

**Para sua DSL:** preservar a associação pergunta–gabarito e tornar acessíveis os metadados pode ser tão importante quanto desenhar conexões legíveis.

### Figura 6 — comprimento das respostas · p. 10

![Figura 6: três boxplots de comprimento para instruções diferentes](outputs/figuras-tabelas/figura-06.png)

Cada linha representa uma instrução para reescrever e-mails. O eixo horizontal representa comprimento; a segunda instrução produz respostas visualmente mais curtas e menos dispersas no exemplo de P17. Isso ajuda a participante a pensar sobre concisão. [Figura e seção 7.1, pp. 10–11.](refs/3613904.3642016.pdf#page=10)

**Como ler um boxplot:** a linha interna marca a mediana e a caixa vai do primeiro ao terceiro quartil, resumindo os 50% centrais. O intervalo da caixa ajuda a comparar dispersão. Existem diferentes convenções para os bigodes e pontos; não assuma a configuração exata sem documentação. [NIST — Box Plot.](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm)

**Cuidado com a unidade:** a figura e sua legenda não explicitam se o comprimento está em caracteres, palavras ou tokens. Portanto, o guia não atribui uma unidade específica nem extrai valores exatos do desenho.

**O que concluir:** naquele caso, a representação quantitativa complementou a leitura das respostas. Texto menor não é automaticamente texto melhor; a decisão dependia dos demais critérios da participante.

### Figura 7 — extrair números e plotar · p. 16

![Figura 7: consulta sobre polímeros, extração com LLM Scorer e visualização](outputs/figuras-tabelas/figura-07.png)

O fluxo de P18 recebe um polímero-base e quatro tipos de aditivo. Um modelo produz estimativas; o `LLM Scorer` extrai o número mencionado; o `Vis Node` mostra os valores por aditivo. Um segundo polímero foi desativado na captura para exibir o gráfico inicial. [Figura e caso A.2.](refs/3613904.3642016.pdf#page=16)

**Eixos:** no vertical estão os aditivos; no horizontal, o valor numérico extraído como `score`. A instrução ao extrator pede retirar unidades. Isso reduz a informação dimensional visível: não é apropriado inferir a unidade ou a interpretação física exata apenas pelas barras.

Aqui, `score` é um campo numérico usado para registrar uma grandeza extraída. **Não é uma nota de correção do modelo.** O relato de que os valores pareciam aproximadamente corretos é uma avaliação informal do participante, não validação científica das propriedades do material.

Ao adicionar outra base, P18 desejou agrupar os resultados simultaneamente por base e aditivo e encontrou uma limitação na visualização. Isso mostra uma necessidade concreta que aparece quando o fluxo passa a ter mais dimensões.

## 7. As três tabelas explicadas

### Tabela 1 — objetivos e funcionalidades · p. 8

![Tabela 1: relações entre quatro objetivos e recursos implementados](outputs/figuras-tabelas/tabela-01.png)

Cada linha relaciona um objetivo de design a recursos do sistema. D1 inclui consulta a vários modelos e comparação lado a lado; D2, variáveis e templates encadeados; D3, avaliadores e gráficos; D4, alterações de entradas, ramificações e cache. [Tabela original.](refs/3613904.3642016.pdf#page=8)

**Como ler:** escolha uma necessidade e percorra as funcionalidades que procuram atendê-la. A tabela não tem pontuação e não demonstra que cada objetivo foi plenamente atingido. É uma ponte entre intenção de projeto e implementação.

**Aplicação didática:** você pode construir uma tabela semelhante para sua DSL: “acompanhar dependências → destacar conexões”; “organizar fluxos grandes → agrupar blocos”. Essas ideias precisariam de avaliação própria.

### Tabela 2 — participantes das entrevistas · p. 13

![Tabela 2: participantes, contextos, tarefas, recursos e resultados relatados](outputs/figuras-tabelas/tabela-02.png)

As colunas indicam identificador, localização, contexto acadêmico/industrial, descoberta da ferramenta, caso de uso, recursos utilizados e resultado relatado. Há seis linhas de casos, mas **oito pessoas**, porque Q1–Q2 e Q5–Q6 são pares. [Tabela original.](refs/3613904.3642016.pdf#page=13)

| Caso | O que você deve guardar |
| --- | --- |
| Q1–Q2 | Adaptaram código para uma ferramenta de prototipação com modelos de imagem. O benefício relatado inclui viabilizar seu projeto de pesquisa. |
| Q3 | Usou o sistema para apoiar análise de requisitos em testes de software e discutir resultados com desenvolvedores. |
| Q4 | Investigou viés de gênero e refinou templates de um pipeline em Python. |
| Q5–Q6 | Trabalharam com síntese/extração de documentos e comunicação dos resultados a cliente. |
| Q7 | Investigou limpeza de dados tabulares e concluiu que LLMs não eram confiáveis o suficiente para sua tarefa. |
| Q8 | Investigou extração/formatação de metadados de podcasts e encontrou resultados insuficientes nos modelos testados. |

**Uma ferramenta de avaliação pode ser útil quando ajuda a decidir não usar um modelo.** Esse é um ponto ilustrado pelos resultados de Q7 e Q8. A tabela não é ranking, taxa de sucesso ou comparação causal de produtividade.

### Tabela 3 — inventário dos nós · p. 18

![Tabela 3: tipos de nós, uso e recursos especiais](outputs/figuras-tabelas/tabela-03.png)

A tabela reúne 11 nós em quatro famílias; a legenda acrescenta o `Comment Node`. O resumo abaixo acompanha a versão do artigo. [Tabela original.](refs/3613904.3642016.pdf#page=18)

| Família | Nó | Função e detalhe importante |
| --- | --- | --- |
| Entrada | TextFields | Fornece valores e aceita templates para encadeamento. |
| Entrada | CSV | Fornece listas de valores separados por vírgula; chaves nos dados são escapadas por padrão. |
| Entrada | Tabular Data | Importa/cria tabelas e mantém valores da mesma linha associados. |
| Geração | Prompt | Consulta um ou mais modelos, com variáveis e múltiplas gerações. |
| Geração | Chat Turn | Continua uma conversa com histórico, podendo alterar o modelo. |
| Avaliação | JavaScript Evaluator | Executa uma função sobre cada resposta e associa a pontuação. |
| Avaliação | Python Evaluator | Papel semelhante, com recursos de Python. |
| Avaliação | LLM Scorer | Usa um modelo para atribuir/extrair uma medida, anexada à resposta existente. |
| Avaliação | Simple Evaluator | Aplica condições simples, como conter um valor ou começar por certo texto. |
| Visualização | Vis | Plota avaliações numéricas e booleanas. |
| Visualização | Inspect | Exibe respostas dentro do fluxo, em lista agrupada. |
| Complementar | Comment | Permite escrever comentários sobre o fluxo. |

**Diferença que costuma confundir:** no `LLM Scorer`, o resultado da avaliação anota a resposta; no encadeamento de prompts, uma geração alimenta outra etapa de geração. A tabela explicita essa distinção.

## 8. Como interpretar os números

| Número do artigo | Significado | Conclusão que deve ser evitada |
| --- | --- | --- |
| 21 participantes | Tamanho do grupo do laboratório. | Representatividade de todos os usuários de ferramentas visuais. |
| 8 pessoas / 6 entrevistas | Participantes do estudo de uso real. | Oito sessões independentes de entrevista. |
| 75 minutos | Duração de cada sessão de laboratório. | Uso prolongado ou domínio completo da ferramenta. |
| 4,19/5; desvio-padrão 0,66 | Avaliação subjetiva média da interface. | “83,8% de produtividade”, acurácia ou nota SUS. |
| 18 interessados em usar novamente | Intenção relatada; cinco se manifestaram antes da pergunta explícita. | Retenção ou adoção futura comprovada. |
| 8 PaLM2, 7 GPT-4, 6 Claude-2 | Escolhas na tarefa estruturada de e-mails. | Ranking objetivo ou atual de qualidade dos modelos. |
| 15 relataram mudança de compreensão | Percepção após a experiência. | Aprendizagem mensurada por teste pré/pós. |
| 144 respostas na Figura 1 | Combinações de comandos, entradas, modelos e repetições. | 144 observações independentes para qualquer teste estatístico. |

Os dados estão nas seções 4.1, 5.1 e 7. [Artigo, pp. 5 e 9–11.](refs/3613904.3642016.pdf#page=9)

**Média e dispersão:** 4,19 resume a avaliação, enquanto 0,66 descreve sua variação. Esse desvio-padrão não é margem de erro nem intervalo de confiança. O artigo usa a pergunta de avaliação da interface em escala de 1 a 5; não identifica essa nota como um instrumento SUS.

**Contas didáticas:** `18/21 ≈ 85,7%` declararam interesse em voltar a usar; `15/21 ≈ 71,4%` relataram mudança de compreensão. São proporções desse grupo, calculadas a partir das contagens, e não efeitos causais ou estimativas generalizáveis sem mais pressupostos.

**Quatro medidas visualmente parecidas, mas diferentes:** Figura 1 = percentual de sucesso do teste de ataque; Figura 5 = contagem de verificações verdadeiras; Figura 6 = comprimento; Figura 7 = valor extraído de uma resposta. Antes de dizer “melhor”, identifique a unidade e o sentido desejável da medida.

## 9. O que o artigo sustenta e seus limites

### 9.1 Afirmações que você pode defender

- Os autores implementaram um ambiente visual para comparar prompts/modelos, avaliar saídas e visualizar resultados. [Seção 4.](refs/3613904.3642016.pdf#page=5)
- Os estudos documentam tarefas, estratégias e dificuldades de pessoas usando a ferramenta. [Seções 5–8.](refs/3613904.3642016.pdf#page=8)
- Usuários reais destacaram exportação, compartilhamento e processamento de dados, ampliando a compreensão dos objetivos iniciais do sistema. [Seção 8.](refs/3613904.3642016.pdf#page=12)
- Foram relatadas dificuldades concretas de manipulação dos nós e de compreensão dos recursos de parametrização. [Seção 7.4.](refs/3613904.3642016.pdf#page=11)

### 9.2 Afirmações fortes demais

| Afirmação inadequada | Formulação sustentada pela leitura |
| --- | --- |
| “Interfaces de blocos são mais rápidas que código.” | Alguns participantes perceberam benefícios de rapidez; o artigo não mediu superioridade causal geral contra código. |
| “A disposição espacial melhorou a compreensão.” | O sistema oferece representações espaciais e há relatos de uso; não foi isolado o efeito de um layout. |
| “Qualquer iniciante consegue usar sem ajuda.” | O grupo tinha perfis variados e recebeu apoio; houve barreiras conceituais. |
| “O LLM Scorer determina a verdade.” | Ele produz avaliações/extrações que também precisam ser conferidas. |
| “O artigo prova que a engenharia de prompts nunca será automatizada.” | Os autores defendem uma posição ampla a partir da subjetividade observada; isso não demonstra uma impossibilidade universal. |
| “Os três modos são etapas fixas.” | São padrões interpretativos e não necessariamente lineares. |

O artigo reconhece limites da metodologia e sugere estudos quantitativos focados. Além disso, a mesma ordem inicial de respostas e a assistência dos pesquisadores devem ser consideradas ao interpretar escolhas e facilidade de uso; o trabalho não isola esses efeitos. [Artigo, seções 5, 7.4, 9 e 9.1.](refs/3613904.3642016.pdf#page=14)

### 9.3 Viés e alcance

As entrevistas podem favorecer quem já encontrou utilidade na ferramenta. O recrutamento do laboratório ao redor de uma universidade e a concentração de participantes com formação técnica limitam a extrapolação. As sessões de 75 minutos não mostram manutenção de fluxos por meses. Essas condições não invalidam os relatos, mas delimitam quais perguntas eles respondem. [Artigo, seções 5.1 e 9.1.](refs/3613904.3642016.pdf#page=9)

## 10. Relação com sua DSL e a organização espacial

### 10.1 Onde o seu interesse aparece no artigo?

Você esclareceu que quer estudar a **organização dos blocos na tela**. O ChainForge oferece observações relevantes para esse recorte:

| Evidência no artigo | Relação com organização visual | Possível pergunta para sua pesquisa |
| --- | --- | --- |
| Usuários precisaram mover nós para abrir espaço e tiveram dificuldades com conexões — seção 7.4. | Manipulação do espaço e das relações entre blocos. | Como reduzir o esforço para inserir um bloco preservando a leitura do fluxo? |
| Entrevistados mantinham regiões separadas de exploração e avaliação — seção 6. | Organização do espaço por atividade. | Agrupamentos explícitos ajudam a identificar a finalidade de cada região? |
| Lista agrupada e tabela apresentam respostas de maneiras diferentes — Figura 4. | Organização espacial dos resultados. | Qual representação apoia melhor uma tarefa específica de comparação? |
| Usuários queriam inspeção mais imediata no contexto — seção 8.3. | Proximidade entre operação e resultado. | Mostrar a saída junto ao bloco ajuda a localizar sua origem? |
| Os autores sugerem interfaces/layouts por modo de uso — seção 9. | Adequação do espaço ao estágio da atividade. | Como alternar entre exploração e avaliação sem perder contexto? |

**As perguntas da última coluna são propostas deste guia**, não lacunas já comprovadas. [Trechos principais: p. 11](refs/3613904.3642016.pdf#page=11), [p. 12](refs/3613904.3642016.pdf#page=12), [p. 14](refs/3613904.3642016.pdf#page=14).

### 10.2 Três coisas para manter separadas

1. **Linguagem:** quais operações, conexões e regras o fluxo admite.
2. **Organização espacial do editor:** onde os blocos ficam, como são agrupados e como as conexões são apresentadas.
3. **Visualização dos resultados:** como respostas, metadados e medidas são organizados para comparação.

Essa separação é uma interpretação didática para seu projeto. Um problema de descobrir uma metavariável não é necessariamente resolvido alinhando blocos. Do mesmo modo, colocar nós em posições diferentes não significa mudar a semântica do fluxo. Sua DSL precisa definir explicitamente quando uma relação espacial tem significado e quando é apenas uma decisão de apresentação.

### 10.3 Uma pergunta de pesquisa mais delimitada

**Proposta a investigar:** “Como o agrupamento visual de blocos por etapa afeta a identificação de dependências em workflows de IA por estudantes iniciantes?”

Um estudo possível manteria o mesmo fluxo, nomes, conexões e dados, alterando apenas a forma de agrupamento. As tarefas poderiam ser identificar a entrada de um nó, explicar a origem de uma saída ou localizar uma ligação incorreta. Medidas possíveis: acertos, tempo e erros de interpretação. A ordem das versões deveria ser alternada para reduzir efeitos de aprendizagem.

Isso é um **desenho preliminar de avaliação**, não experimento realizado nem comprovação de novidade. A escolha de participantes, número de tarefas e análise precisaria ser planejada depois de delimitar o público e consultar a literatura específica de layouts e compreensão de grafos.

### 10.4 Como os dois artigos podem trabalhar juntos?

Use Oakes para situar o artefato e a transformação: por exemplo, ajudar uma pessoa a compreender ou modificar uma solução em workflow. Use ChainForge para examinar um ambiente concreto, decisões de interface e dificuldades observadas. Sua contribuição pode então ser uma mudança específica de representação, acompanhada da evidência necessária para avaliá-la. [Guia de Oakes](../02-workflows-ml/GUIA-DETALHADO.md) · [ChainForge, seções 7.4 e 9.1.](refs/3613904.3642016.pdf#page=11)

## 11. Dúvidas e pontos de atenção

### “O ChainForge é uma DSL?”

Os autores o apresentam como toolkit/ambiente de programação visual. Ele tem um vocabulário de nós e regras de composição relevantes ao seu tema. Para chamá-lo de DSL em uma análise, explicite qual domínio, sintaxe e semântica você está considerando. Não atribua ao artigo uma contribuição de formalização completa de linguagem que ele não reivindica. [Artigo, seções 1 e 4.](refs/3613904.3642016.pdf#page=2)

### “É um construtor de agentes ou de aplicações?”

O foco original é experimentar, comparar e avaliar. Os usuários também prototiparam processamento de dados. O texto mostra a passagem posterior para implementação em outros ambientes e registra preocupação de um entrevistado com o aumento de complexidade se a ferramenta tentasse cobrir tudo. [Artigo, pp. 5 e 12, nota 10.](refs/3613904.3642016.pdf#page=12)

### “Por que inspecionar o texto se já tenho um gráfico?”

Porque o gráfico resume uma medida escolhida. Ele pode mostrar comprimento sem explicar se o conteúdo foi preservado. O texto permite examinar casos e entender por que uma pontuação parece inadequada. A seção 7.1 descreve como as duas representações participam das decisões. [Artigo, pp. 10–11.](refs/3613904.3642016.pdf#page=10)

### “O avaliador é sempre outra IA?”

Não. Há critérios simples, funções em JavaScript/Python e um LLM Scorer. A escolha depende do que você quer medir. Um teste de presença de palavra pode ser implementado sem modelo; uma avaliação semântica pode usar um modelo, mas isso não a torna infalível. [Tabela 3.](refs/3613904.3642016.pdf#page=18)

### “O cache garante reprodução?”

O cache permite reinspecionar os resultados coletados e reduzir consultas repetidas. Repetir uma coleta do zero é outra questão. Para uma comparação reproduzível, seria necessário registrar entradas, templates, configurações, versões e critérios. Essa última lista é uma recomendação metodológica do guia, motivada pela multiplicidade de condições descritas na seção 4.1. [Artigo, p. 5.](refs/3613904.3642016.pdf#page=5)

### “Os dados da Indonésia e dos polímeros foram confirmados aqui?”

Não. O guia relata os casos do artigo. Não realizou auditoria das fontes estatísticas consultadas pela participante nem validação física das estimativas de condutividade. Nos dois casos, o objetivo da leitura é entender as ações dos usuários e os limites dos avaliadores.

### Pontos editoriais e ambiguidades

- **A.1, p. 15:** o caso começa com P15, mas um parágrafo usa P9; a seção 7.3 também associa esse caso a P15. O guia segue essa identificação e registra a divergência como aparente inconsistência editorial.
- **Figura 6:** não explicita unidade de comprimento. Não afirmar “tokens” ou “palavras” sem outra evidência.
- **A.3, p. 17:** a linguagem de significância estatística é fala do participante; o caso não apresenta um teste que a fundamente.
- **Figura 7:** o campo chamado `score` contém um valor extraído. A palavra não implica probabilidade, confiabilidade ou correção.
- **Tabela 2:** seis linhas não significam seis entrevistados; são oito pessoas em seis entrevistas.

### Materiais de apoio

| Dúvida | Onde consultar |
| --- | --- |
| DSL, linguagem, editor e motor | [Guia inicial](../01-fundamentos/GUIA-INICIAL.md). |
| Situação do workflow entre problema e implementação | [Guia de Oakes](../02-workflows-ml/GUIA-DETALHADO.md). |
| Nós, templates e inspeção na ferramenta | [Documentação oficial do ChainForge](https://chainforge.ai/docs/). Recursos atuais podem diferir do PDF. |
| Mediana, quartis e boxplots | [NIST — Box Plot](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm). |
| Continuar a leitura de trabalhos próximos | [Seleção comentada de artigos](../01-fundamentos/ARTIGOS-PARA-LER.md). |

Não é necessário instalar o ChainForge ou pagar chamadas de modelos para estudar este guia. Os exercícios abaixo usam o PDF e exemplos no papel.

## 12. Exercícios, roteiro e fichamento

### 12.1 Confira se entendeu

1. Explique qual problema o ChainForge resolve em duas frases, sem dizer apenas “conecta modelos”.
2. Percorra cada conexão da Figura 3 e diga o que ela transporta.
3. Calcule as respostas para três templates, quatro entradas, dois modelos e duas gerações por condição, sem histórico e sem reuso de cache.
4. Explique por que pergunta e gabarito não devem virar combinações independentes.
5. Na Figura 1, uma barra maior é desejável para quem quer robustez? Por quê?
6. Diferencie a medida da Figura 5 da Figura 7.
7. Explique por que a nota 4,19 não prova ganho de produtividade.
8. Diga o que diferencia os três modos de uso.
9. Cite uma dificuldade de organização de blocos e uma dificuldade conceitual relatadas.
10. Proponha uma alteração visual e descreva como compará-la mantendo o comportamento do fluxo.

**Respostas-chave:** na questão 3, `3 × 4 × 2 × 2 = 48`. Na 4, o gabarito pertence à sua pergunta/linha. Na 5, não: a barra mede sucesso do teste de ataque. Na 6, a Figura 5 conta verificações verdadeiras; a 7 mostra valores extraídos de respostas. Na 7, trata-se de avaliação subjetiva sem comparação causal de produtividade. Na 9, mover nós para abrir espaço é uma dificuldade de interface; compreender e declarar variáveis é uma dificuldade conceitual.

### 12.2 Roteiro para explicar ao orientador

1. **Problema:** comparar várias condições e compreender resultados de LLMs.
2. **Proposta:** mostrar o fluxo da Figura 1 e as famílias de nós.
3. **Funcionamento:** usar a Figura 3 para explicar templates e combinações.
4. **Representação:** usar a Figura 4 para distinguir fluxo de execução e organização das respostas.
5. **Evidência:** explicar laboratório com 21 participantes e entrevistas com oito pessoas, incluindo apoio e limitações.
6. **Achados:** apresentar os três modos e a demanda real por processamento/exportação de dados.
7. **Seu recorte:** citar a seção 7.4 e formular uma pergunta delimitada sobre organização dos blocos.
8. **Limite:** deixar claro que o artigo não isola causalmente o efeito do layout.

### 12.3 Fichamento iniciado

| Campo | Registro |
| --- | --- |
| Problema | Apoiar experimentação e avaliação de respostas de LLMs em tarefas abertas. |
| Tipo de contribuição | Sistema, estudos qualitativos e implicações de design. |
| Recursos centrais | Combinações de entradas/prompts/modelos, metadados, avaliadores e inspeção visual. |
| Participantes | 21 no laboratório; 8 pessoas em 6 entrevistas de uso real. |
| Figuras para começar | 1, 3 e 4. |
| Tabela para projetar uma ferramenta | Tabela 1: necessidade e recurso correspondente. |
| Tabela para entender os blocos | Tabela 3: nós e funções. |
| Achado central | Diferentes modos de investigação e necessidades adicionais no uso real. |
| Ligação direta ao seu foco | Manipulação dos nós, espaço, conexões e inspeção no contexto. |
| Limite metodológico | Não há comparação controlada que isole benefícios de layout ou produtividade. |
| Próximo passo | Definir uma tarefa de compreensão e uma mudança de organização visual para investigar. |

**Você entendeu o essencial quando consegue percorrer a Figura 3, interpretar corretamente as medidas das Figuras 1 e 5 e explicar por que os relatos sobre mover blocos motivam uma pesquisa espacial, mas ainda não demonstram qual organização é melhor.**
