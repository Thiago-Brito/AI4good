# Artigos para ler — DSL visual para orquestração de IA

**Minha recomendação: use ChainForge, InstructPipe e o artigo de Oakes et al. como núcleo de três trabalhos.** Para começar com algo mais concreto e curto, leia antes PromptChainer. A seleção combina programação visual, workflows de IA e engenharia de linguagens, porque seu tema fica na interseção dessas áreas.

Pesquisa realizada em **27/09/2026**. Este é um roteiro de leitura comentado, com consulta seletiva aos artigos; não é uma revisão sistemática nem uma análise integral de todos os resultados. [Método, referências completas e fontes verificadas](refs/BUSCA-ARTIGOS.md).

## 1. Visão geral da seleção

As classificações de proximidade e dificuldade abaixo são minha avaliação para orientar seu estudo.

| Artigo | Veículo e ano | Relação com seu tema | Prioridade |
| --- | --- | --- | --- |
| **PromptChainer** [A1] | CHI Extended Abstracts, 2022 | Autoria visual de cadeias de LLMs. | Porta de entrada; curto. |
| **ChainForge** [A2] | CHI, 2024 — artigo completo | Fluxos visuais para experimentar e avaliar LLMs. | Núcleo; dificuldade média. |
| **InstructPipe** [A3] | CHI, 2025 — artigo completo | Construção assistida de pipelines visuais de IA. | Núcleo; dificuldade média. |
| **Building Domain-Specific Machine Learning Workflows** [A4] | ACM TOSEM, 2024 | Ponte entre domínio, workflow e implementação. | Núcleo; leitura mais longa. |
| **AI Chains** [A5] | CHI, 2022 — artigo completo | Fundamentação do encadeamento e do controle pelo usuário. | Complemento próximo. |
| **Prompting Is Programming / LMQL** [A6] | PACMPL, edição PLDI, 2023 | Linguagem textual para programar interações com LLMs. | Aprofundamento técnico. |
| **When and how to develop domain-specific languages** [A7] | ACM Computing Surveys, 2005 | Fundamentos para decidir e projetar uma DSL. | Base conceitual. |

Os identificadores [A1]–[A7] correspondem às referências completas em `refs/BUSCA-ARTIGOS.md`; cada ficha abaixo também contém DOI e acesso ao texto.

## 2. Por que esses veículos?

| Veículo | Por que é pertinente e uma boa referência |
| --- | --- |
| **ACM CHI** | Conferência central de interação humano-computador, apresentada como principal conferência internacional da área pela [organização oficial](https://chi2025.acm.org/). Faz sentido quando sua contribuição envolve compreensão, edição visual e avaliação com usuários. |
| **ACM TOSEM** | Periódico de engenharia de software. O [editorial de 2025](https://abhikrc.com/pdf/TOSEMeditorial2025.pdf) o caracteriza como periódico de referência da ACM nessa área. É pertinente à modelagem, transformação e implementação de workflows. |
| **PLDI / PACMPL** | Referência para investigar linguagens, semântica e implementação. Consulte o [evento oficial](https://pldi23.sigplan.org/). O artigo de LMQL foi publicado em PACMPL, na edição associada a PLDI. |
| **ACM Computing Surveys** | Veículo adequado a sínteses e fundamentos. Seu destaque bibliométrico foi documentado em [comunicado oficial da ACM de 2024](https://www.acm.org/binaries/content/assets/press-releases/2024/july/news-release_impact_factors_2024_final.pdf); isso é evidência histórica, não uma classificação de 2026. |

**Qualis:** não atribuí estratos nesta busca; a classificação com fonte e período continua pendente. A qualidade e a adequação de cada artigo também precisam ser examinadas pelo método e pelos resultados, além do nome do veículo.

## 3. As fichas de leitura

### A1 — PromptChainer: sua primeira leitura

**Wu et al. (2022). _PromptChainer: Chaining Large Language Model Prompts through Visual Programming._ CHI Extended Abstracts.**

[DOI](https://doi.org/10.1145/3491101.3519729) · [PDF da autora, 10 páginas](https://www.cs.cmu.edu/~sherryw/assets/pubs/2022-promptchainer.pdf) · [Apresentação no canal ACM SIGCHI](https://www.youtube.com/watch?v=DLDomQSi_8g)

Investiga como pessoas constroem cadeias de chamadas a modelos por uma interface visual, incluindo transformação de resultados intermediários e depuração. É um dos trabalhos mais próximos da parte “blocos e conexões” do seu tema.

**Por onde ler:** resumo → Figuras 1 e 2 → descrição dos nós → estudos de caso. Na **Figura 2, página 3 do PDF**, acompanhe as ramificações e diferencie operações de LLM, processamento e avaliação.

**Pergunta para anotar:** que informação cada conexão transporta, e como o usuário percebe um erro intermediário?

**Limite:** é um trabalho de *Late-Breaking Work*, com estudos de caso com quatro pessoas. Use como referência próxima de design, sem tratá-lo como uma avaliação ampla de eficácia. A associação ao CHI não o torna equivalente a um artigo completo da trilha principal.

### A2 — ChainForge: fluxos visuais para experimentar e avaliar

**Estudo aprofundado concluído em 01/10/2026:** [guia detalhado do PDF fornecido, com as 7 figuras, 3 tabelas e relação com a organização espacial dos blocos](../03-chainforge/GUIA-DETALHADO.md).

**Arawjo et al. (2024). _ChainForge: A Visual Toolkit for Prompt Engineering and LLM Hypothesis Testing._ CHI.**

[DOI](https://doi.org/10.1145/3613904.3642016) · [PDF do laboratório, 18 páginas](https://glassmanlab.seas.harvard.edu/papers/chainforge.pdf)

Apresenta um ambiente visual para comparar prompts e modelos, avaliar respostas e explorar hipóteses. Para seu projeto, ajuda a pensar em como tornar resultados intermediários e avaliações visíveis.

**Leia primeiro:** seções 3 e 4; depois o estudo com usuários.

- **Figura 2, página 3:** organiza ferramentas em dois eixos: exploração versus avaliação sistemática, e interfaces textuais versus gráficas. Pode inspirar seu diagrama da área, identificando a origem da adaptação.
- **Tabela 1, página 8:** relaciona objetivos de design às funcionalidades implementadas. É uma tabela de decisões de projeto, não um ranking experimental.

**Pergunta para anotar:** que recurso da minha linguagem permitiria verificar o comportamento de um fluxo, além de executá-lo?

**Limite:** a avaliação é principalmente qualitativa, e o foco é experimentação com LLMs. Não interprete o artigo como prova de superioridade universal nem como especificação de uma DSL formal completa.

### A3 — InstructPipe: gerar um fluxo e permitir que a pessoa o ajuste

**Estudo aprofundado concluído em 01/10/2026:** [guia do PDF fornecido, com 15 figuras, 4 tabelas e algoritmo](../04-instructpipe/GUIA-DETALHADO.md). Rumo: **como transformar a intenção do usuário em um fluxo visual que ele consiga compreender, corrigir e completar**.

**Zhou et al. (2025). _InstructPipe: Generating Visual Blocks Pipelines with Human Instructions and LLMs._ CHI.**

[DOI e registro ACM](https://doi.org/10.1145/3706598.3713905) · [PDF dos autores, 22 páginas](https://www.olwal.com/projects/research/instructpipe/zhou_instructpipe_chi_2025.pdf)

Gera pipelines visuais a partir de instruções em linguagem natural. A pessoa pode revisar o resultado. É especialmente próximo se você quiser combinar edição visual com auxílio de IA.

**Leia primeiro:** seção 3 → Figuras 2 e 3, página 4 → seções 5.2 e 6.

**Tabela 1, página 8:** mostra a razão estimada de interações para completar o grafo gerado, comparada à criação do zero. A média geral é **18,9%**, com desvio-padrão de **20,3 pontos percentuais**. Menor é melhor nessa métrica. Ela conta adições/remoções de nós e arestas; não significa automaticamente redução equivalente no tempo real.

**Limite importante:** o sistema gera a estrutura do DAG; o ajuste dos parâmetros permanece com o usuário.

**Pergunta:** na sua proposta, a IA ajudaria a criar o programa ou seria apenas um componente executado por ele?

Use a publicação completa de 2025; há uma demonstração anterior, com outro título, nos Extended Abstracts de 2024.

### A4 — Workflows específicos de domínio: a ponte com engenharia de software

**Oakes, Famelis e Sahraoui (2024). _Building Domain-Specific Machine Learning Workflows: A Conceptual Framework for the State-of-the-Practice._ ACM TOSEM, 33(4).**

[DOI](https://doi.org/10.1145/3638243) · [Registro institucional e acesso ao texto](https://publications.polymtl.ca/57010/) · [Manuscrito dos autores](https://bentleyjoakes.github.io/assets/publications/Oakes2023%20-%20Building%20Domain-Specific%20Machine%20Learning%20Workflows%3A%20A%20Conceptual%20Framework%20for%20the%20State-of-the-Practice.pdf)

Organiza a passagem de um problema de domínio para um workflow e uma implementação. Ajuda a justificar o papel da sua DSL para além da interface.

**Comece pela seção 3 e Figura 4, página 11 do manuscrito:** há três camadas — problema, solução em workflow e implementação — e dimensões de especificidade de domínio e complexidade de ML. As classificações são conceituais, não medidas precisas de desempenho.

Depois examine as transformações entre camadas e as tabelas de comparação dos sistemas.

**Pergunta:** sua contribuição melhora a descrição do problema, a construção do fluxo, a tradução para execução ou a relação entre essas etapas?

**Limite:** aborda ML de forma ampla, sem se restringir a LLMs. A publicação é de 2024; o manuscrito vinculado tem 49 páginas, enquanto o registro final indica 50. A localização acima refere-se ao manuscrito.

### A5 — AI Chains: por que decompor a tarefa?

**Wu, Terry e Cai (2022). _AI Chains: Transparent and Controllable Human-AI Interaction by Chaining Large Language Model Prompts._ CHI.**

[DOI](https://doi.org/10.1145/3491102.3517582) · [PDF dos autores, 22 páginas](https://arxiv.org/pdf/2110.01691)

Estuda encadeamento de etapas com resultados intermediários editáveis. Oferece base para discutir transparência e controle do usuário em sua linguagem.

**Comece pela Figura 1, página 2:** compare uma chamada única com três etapas para reformular feedback. Identifique onde a informação é separada, expandida e recombinada. Depois leia o estudo com 20 participantes e a comparação entre condições com e sem encadeamento.

**Pergunta:** quais resultados intermediários sua interface precisa mostrar para que uma pessoa consiga diagnosticar o fluxo?

**Limite:** os resultados dependem das tarefas e condições estudadas. O artigo não demonstra que encadear sempre é melhor. Também não confunda um programa com várias chamadas com pedir uma explicação passo a passo dentro de uma única chamada.

O preprint começou em 2021; a referência de publicação no CHI é de 2022.

### A6 — LMQL: a parte “linguagem” aplicada a LLMs

**Beurer-Kellner, Fischer e Vechev (2023). _Prompting Is Programming: A Query Language for Large Language Models._ PACMPL, 7, PLDI, artigo 186.**

[DOI](https://doi.org/10.1145/3591300) · [Registro e versões](https://arxiv.org/abs/2212.06094) · [PDF](https://arxiv.org/pdf/2212.06094)

Propõe LMQL, combinando prompts, programação e restrições sobre a saída. É útil para pensar no significado e na execução das construções de uma linguagem para IA.

**Como ler:** comece pela motivação e pelos exemplos de programas. Marque separadamente texto do prompt, variáveis, controle e restrições. Deixe os detalhes de implementação para uma segunda leitura.

**Pergunta:** como representar essas intenções em blocos visuais preservando seu significado?

**Limite:** é uma linguagem textual. Sua inclusão complementa a dimensão de engenharia de linguagens; não é evidência de usabilidade de uma DSL visual. Restrições sobre saídas também não equivalem, por si só, à veracidade factual das respostas.

O preprint começou em 2022; a publicação associada a PLDI é de 2023.

### A7 — Quando faz sentido criar uma DSL?

**Mernik, Heering e Sloane (2005). _When and how to develop domain-specific languages._ ACM Computing Surveys, 37(4), 316–344.**

[DOI](https://doi.org/10.1145/1118890.1118892) · [PDF em página acadêmica, 29 páginas](https://people.cs.ksu.edu/~schmidt/505f11/Lectures/WhenDSL.pdf)

Organiza decisões, análise, design e implementação de DSLs. É a leitura para perguntar se você precisa de uma nova linguagem, quais conceitos ela deve oferecer e quais custos sua criação traz.

**Como ler:** introdução e seções sobre padrões de desenvolvimento. Construa uma tabela própria com quatro linhas: decisão, análise, design e implementação. Em cada linha, registre uma decisão necessária para seu projeto.

**Pergunta:** o que minha DSL expressaria de maneira mais adequada ao domínio, e como eu verificaria essa vantagem?

**Limite:** é anterior aos LLMs atuais e exclui linguagens visuais específicas de domínio de seu escopo principal. Serve como fundamento de engenharia de DSL, não como levantamento do estado atual da orquestração visual de IA.

## 4. Quais três escolher para apresentar?

Minha sugestão inicial é **ChainForge + InstructPipe + Oakes et al.** As fichas A2–A4 sustentam esta escolha; a combinação é uma recomendação minha:

| Trabalho | Papel na sua apresentação | Questão de discussão |
| --- | --- | --- |
| ChainForge | Mostrar como um fluxo pode apoiar experimentação e avaliação. | Como observar o que o sistema produz? |
| InstructPipe | Mostrar autoria assistida de pipelines visuais. | Como ajudar a pessoa a construir o fluxo? |
| Oakes et al. | Organizar o problema como engenharia de workflows de domínio. | Como passar da intenção à implementação? |

Se o orientador enfatizar **semântica, restrições ou compilação da DSL**, considere trocar InstructPipe por **LMQL**. Se enfatizar **interação e controle humano**, considere **AI Chains**. PromptChainer continua sendo uma ótima leitura inicial, com seu tipo de publicação explicitado.

## 5. O que observar para encontrar um problema de pesquisa

Estas são perguntas propostas para sua leitura, não lacunas já demonstradas:

- **Expressividade:** que fluxos a linguagem permite descrever? Existem condições, repetição e composição de subfluxos?
- **Validação:** quais erros podem ser identificados antes de chamar o modelo?
- **Depuração:** como descobrir o primeiro ponto em que a execução se desviou do esperado?
- **Compreensão:** quem é o usuário e o que precisa saber para interpretar as conexões?
- **Avaliação:** a ferramenta melhora conclusão de tarefas, tempo, erros, compreensão ou apenas satisfação percebida?
- **Reprodução:** quais configurações e resultados precisam ser registrados para repetir um experimento?

Evite começar com “vou criar blocos para conectar IA”. Transforme isso em uma pergunta investigável. Exemplo proposto: **“Como informações de tipo nas conexões afetam a identificação de erros em workflows visuais de IA?”** A novidade dessa pergunta ainda precisa ser verificada na literatura.

## 6. Como ler sem travar

Faça três passagens, sem tentar compreender tudo de uma vez:

1. **Orientação:** título, resumo, introdução e conclusão. Anote problema, proposta e contribuição.
2. **Funcionamento:** acompanhe um exemplo completo, usando figuras e legendas. Escreva a entrada e a saída de cada etapa.
3. **Evidência:** examine método, participantes ou tarefas, métricas, tabelas e limitações. Diferencie demonstração de funcionamento de comparação experimental.

Ficha para preencher:

```text
Artigo e versão do PDF:
Problema investigado:
Quem usa a ferramenta:
O que a proposta acrescenta:
Figura/tabela escolhida e página:
O que significa cada seta, eixo ou coluna:
Exemplo concreto que percorre a figura:
Como os autores avaliaram:
O que os resultados sustentam:
O que os resultados não permitem concluir:
Relação com minha DSL:
Termo que não entendi e fonte que esclareceu:
```

Para dúvidas conceituais, retorne ao [guia inicial](GUIA-INICIAL.md). Nas tabelas, confira unidade, direção da métrica, dispersão e condições comparadas antes de interpretar um número.

## 7. BRACIS e próximos passos

A busca exploratória por BRACIS não levou, nesta seleção, a um artigo suficientemente próximo de **DSL/programação visual para orquestração**. Isso não significa que não exista; o levantamento dedicado dos anais continua pendente. Não acrescentei um artigo apenas por usar IA ou LLMs.

Esta etapa entrega a seleção e o roteiro de leitura. Permanecem para a sequência: confirmação de Qualis com período e fonte; seleção final com o orientador; e leitura integral dos três escolhidos, aprofundando suas figuras e tabelas.
