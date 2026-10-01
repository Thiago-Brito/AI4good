# DSL visual para orquestração de IA: começando do básico

Este guia é para entender o tema antes de escolher ferramentas, veículos ou artigos. Você pode começar sem instalar nada. Leia as seções 1 a 4, assista aos primeiros vídeos e tente desenhar um fluxo no papel.

**Seu tema, em linguagem simples:** estudar uma linguagem de blocos e conexões com regras próprias para descrever e executar tarefas que combinam modelos de IA, dados e outras ferramentas.

Data: 27/09/2026. [Registro das fontes e limites da consulta](refs/FONTES.md).

## 1. O que é DSL?

**DSL** significa *Domain-Specific Language*: **linguagem específica de domínio**. “Domínio” é a classe de problemas que ela atende. SQL, por exemplo, permite expressar consultas a dados; CSS descreve apresentação de páginas. Uma linguagem de propósito geral, como Python, atende a muitos tipos de problema. [Fowler — definição de DSL](https://www.martinfowler.com/bliki/DomainSpecificLanguage.html).

Pense em uma linguagem criada para montar assistentes que consultam documentos. Ela poderia oferecer palavras ou blocos como `Pergunta`, `BuscarDocumentos`, `GerarResposta` e `Mostrar`. Esses nomes pertencem ao problema que queremos resolver.

Exemplo didático de uma possível DSL textual, inventado apenas para este guia:

```text
fluxo responder_duvida:
    receber pergunta
    buscar trechos usando pergunta
    gerar resposta usando pergunta e trechos
    mostrar resposta
```

Isso ainda não é uma ferramenta funcionando. Para virar uma linguagem utilizável, precisamos definir exatamente o que cada comando significa, quais combinações são válidas e como executar o programa.

O ganho que buscamos é poder expressar uma tarefa com conceitos próximos do problema. Se isso reduz esforço ou erros no seu caso será uma pergunta de pesquisa, não uma conclusão antecipada.

## 2. O que muda quando a DSL é visual?

Em vez de escrever todos os comandos, a pessoa manipula elementos gráficos. Por exemplo:

```text
[Pergunta] ──texto──> [Buscar documentos] ──trechos──> [Montar prompt]
     └──────────────────pergunta original──────────────────┘
                                                         │
                                                         ▼
                                                       [LLM]
                                                         │
                                                         ▼
                                                  [Mostrar resposta]
```

DSLs podem ser textuais ou gráficas. Também podem ser internas, expressas dentro de uma linguagem hospedeira, ou externas, com sintaxe própria. “Visual/textual” e “interna/externa” descrevem aspectos diferentes. [Fowler](https://www.martinfowler.com/bliki/DomainSpecificLanguage.html).

Para projetar nosso exemplo, precisaríamos decidir:

| Elemento | Pergunta concreta |
| --- | --- |
| Vocabulário | Quais blocos existem? Busca? Modelo? Condição? |
| Sintaxe concreta | Como o usuário vê e conecta os blocos? |
| Sintaxe abstrata | Como nós, conexões e parâmetros são representados internamente? |
| Semântica | O que cada bloco e conexão significa na execução? |
| Restrições | É permitido ligar uma imagem a uma entrada que aceita apenas texto? |

Essas perguntas são uma aplicação didática da separação entre notação, modelo e ferramentas discutida por Fowler em [Language Workbenches](https://martinfowler.com/articles/languageWorkbench.html).

**Um desenho com setas, sozinho, não basta para especificar uma DSL executável.** No nosso projeto, seria necessário dizer se a seta transfere dados, determina uma ordem de execução ou faz ambas as coisas.

## 3. Linguagem, editor e motor: três partes diferentes

Imagine que você desenhou o fluxo anterior:

| Parte | Papel no exemplo |
| --- | --- |
| Linguagem | Define os blocos disponíveis e o significado de suas combinações. |
| Editor visual | Permite arrastar, conectar, configurar e inspecionar os blocos. |
| Modelo do fluxo | Guarda a estrutura montada, independentemente da posição dos blocos na tela. |
| Validador | Detecta problemas definidos pelas regras, como uma entrada obrigatória desconectada. |
| Motor de execução (*runtime*) | Executa as operações, transporta os resultados e trata o andamento do fluxo. |

Essa divisão é uma arquitetura ilustrativa, não uma implementação obrigatória. Um ambiente pode integrar várias dessas responsabilidades. *Language workbench* é o nome usado para ambientes que ajudam a construir linguagens e as ferramentas para utilizá-las. [Fowler — Using Language Workbenches](https://www.informit.com/articles/article.aspx?p=1592379&seqNum=6).

O fluxo pode ser interpretado por um motor ou transformado em código executável. São possibilidades de implementação de DSLs. [Fowler — DSL](https://www.martinfowler.com/bliki/DomainSpecificLanguage.html).

## 4. O que significa orquestrar IA?

Aqui, vamos usar **orquestração** para designar a coordenação das etapas: quem executa, com quais entradas, em que condições e o que acontece depois.

Exemplo próprio: um sistema recebe uma pergunta sobre uma apostila. Primeiro busca trechos relevantes, depois monta a entrada do modelo, solicita uma resposta e a mostra ao usuário. A busca e a exibição não precisam ser executadas por um modelo de IA.

Orquestrar esse sistema exige responder perguntas como:

- A geração espera a busca terminar?
- O que fazer quando a busca retorna zero trechos?
- Se a chamada do modelo falhar, repetimos ou encerramos?
- Qual resultado de cada etapa será guardado para depuração?

**Workflow** é um fluxo de trabalho. Na distinção adotada pela Anthropic, workflows seguem caminhos definidos previamente, enquanto agentes dão ao modelo mais controle sobre como conduzir o processo e usar ferramentas. Um fluxo com um LLM não é automaticamente um agente autônomo. [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents).

Para começar, estude um workflow simples. Ele permite discutir linguagem e execução sem precisar resolver também planejamento autônomo.

## 5. Onde seu tema fica na área?

![Mapa conceitual da interseção entre linguagens, orquestração de IA e interação visual](outputs/diagrama-area.svg)

*Mapa didático próprio, baseado nos conceitos de [DSLs](https://www.martinfowler.com/bliki/DomainSpecificLanguage.html), [ferramentas de linguagem](https://martinfowler.com/articles/languageWorkbench.html), [fluxos de IA](https://www.anthropic.com/engineering/building-effective-agents) e [edição visual no Langflow](https://docs.langflow.org/). Não é uma taxonomia exaustiva da área.*

A interseção reúne três preocupações: o que a linguagem consegue expressar; como executar as operações de IA; e como uma pessoa entende e modifica o fluxo visualmente.

**Escopo provisório para orientar o estudo:** investigar como uma linguagem visual pode permitir que pessoas especifiquem, validem e compreendam fluxos de aplicações de IA, combinando operações de dados, chamadas de modelos e regras de execução. O público e o tipo de fluxo ainda precisam ser delimitados.

**Fora desse recorte inicial:** treinar um novo modelo de linguagem do zero; criar apenas um chatbot sem estudar a linguagem; fazer somente um editor de diagramas sem definir o significado dos fluxos. São decisões propostas de escopo, a discutir com o orientador.

## 6. Palavras que você precisa entender

### Primeiro: a linguagem e o fluxo

O quadro abaixo usa definições introdutórias e exemplos próprios, orientados pela discussão de modelos e linguagens de [Fowler](https://martinfowler.com/articles/languageWorkbench.html).

| Termo | Em palavras simples | Exemplo no nosso fluxo |
| --- | --- | --- |
| Domínio | Conjunto de problemas que a linguagem atende. | Compor aplicações que consultam documentos e usam IA. |
| Abstração | Forma de representar algo sem expor todos os detalhes. | `BuscarDocumentos` esconde detalhes da consulta. |
| Nó (*node*) | Elemento de um grafo; neste exemplo, representa uma operação. | Bloco `MontarPrompt`. |
| Aresta (*edge*) | Conexão entre elementos. | Ligação que transporta os trechos encontrados. |
| Porta (*port*) | Ponto de entrada ou saída de um bloco. | Entrada `pergunta: texto`. |
| Tipo | Categoria de valor que uma entrada aceita ou uma saída produz. | Texto, número, lista de documentos. |
| Fluxo de dados | Caminho percorrido pelos valores. | Trechos da busca chegam à montagem do prompt. |
| Fluxo de controle | Regras que determinam o que executa em seguida. | Sem trechos, seguir para uma mensagem alternativa. |
| Estado | Informação mantida durante o processo. | Pergunta recebida e resultados intermediários. |
| DAG | Grafo dirigido sem ciclos. | Etapas sem caminho que volte a um nó anterior. |
| Ciclo | Caminho que pode retornar a uma etapa anterior. | Revisar e gerar novamente, com limite de tentativas. |
| Metamodelo | Descrição dos tipos de elementos e relações admitidos em modelos. | Um fluxo contém nós; conexões ligam portas compatíveis. |

Não suponha que todo workflow é um DAG: se sua linguagem permitir retornos, você precisará definir quando eles terminam. Essa é uma decisão de projeto do exemplo.

### Depois: os componentes de IA

| Termo | O que significa para este estudo |
| --- | --- |
| LLM | *Large Language Model*: modelo de linguagem de grande porte, usado aqui para gerar texto. |
| Prompt | Entrada fornecida ao modelo, com instruções e contexto. |
| Inferência | Uso de um modelo já treinado para produzir uma saída. |
| RAG | Recuperar informações externas e usá-las como contexto para a geração. |
| Chunk | Trecho em que um documento é dividido para processamento e recuperação. |
| Embedding | Representação numérica utilizada, por exemplo, para comparar textos em uma busca. |
| Retriever | Componente que recupera informações relevantes para uma consulta. |
| Ferramenta (*tool*) | Operação que o sistema pode chamar, como uma consulta ou um cálculo. |

Para RAG e seus componentes, use a [explicação em português da IBM](https://www.ibm.com/br-pt/think/topics/retrieval-augmented-generation) e o [tutorial do Langflow](https://docs.langflow.org/chat-with-rag). Para ferramentas e agentes, use [Anthropic](https://www.anthropic.com/engineering/building-effective-agents).

RAG não significa retreinar o modelo e não garante respostas corretas. Ele acrescenta informações recuperadas ao contexto de geração. [IBM](https://www.ibm.com/br-pt/think/topics/retrieval-augmented-generation).

### Termos para reconhecer, sem aprofundar agora

*Low-code* indica desenvolvimento com menor necessidade de escrever código; *no-code* enfatiza construção por configuração e interfaces. Isso descreve a experiência de desenvolvimento, enquanto DSL descreve uma linguagem especializada. O [Node-RED](https://nodered.org/docs/tutorials/) e o [Langflow](https://docs.langflow.org/) são exemplos úteis para observar edição por fluxos, sem assumir que toda interface visual tem o mesmo desenho de linguagem.

**API** é uma interface para um programa solicitar operações a outro. **JSON** é um formato de representação de dados: salvar um fluxo em JSON não define, por si só, como ele será executado. No exemplo deste guia, essa interpretação seria responsabilidade do motor.

## 7. Um exemplo para explicar bloco por bloco

**Tarefa:** responder “Qual é o prazo do trabalho?” consultando uma apostila fictícia.

Em uma implementação de RAG vetorial, há normalmente uma preparação dos documentos e um caminho de consulta. O tutorial do [Langflow](https://docs.langflow.org/chat-with-rag) mostra essa separação.

```text
Preparação: documento → dividir em trechos → representar e indexar trechos

Consulta: pergunta → recuperar trechos → montar prompt → LLM → resposta
              └── pergunta original ────────┘
```

No nosso exemplo didático, assumimos que a preparação já ocorreu:

| Bloco | Recebe | Produz | Pergunta para conferir se entendeu |
| --- | --- | --- | --- |
| Pergunta | Texto digitado. | `Qual é o prazo do trabalho?` | A pergunta será preservada até a geração? |
| Buscar | Pergunta e acesso à base. | Lista de trechos, com identificação da origem. | O que acontece se a lista estiver vazia? |
| Montar prompt | Pergunta original e trechos. | Instrução com contexto. | Onde cada entrada aparece no texto enviado ao modelo? |
| LLM | Prompt montado. | Resposta candidata. | A resposta é sustentada pelos trechos? |
| Mostrar | Resposta candidata. | Texto exibido. | O usuário consegue conferir a origem da informação? |

**Erro proposital para estudar:** conectar diretamente a lista de documentos à entrada textual de um bloco que exige uma string. Uma DSL com tipos poderia rejeitar a ligação ou exigir uma conversão explícita. Isso é uma regra proposta para nosso exemplo, não uma garantia sobre todas as ferramentas.

**Outra situação:** todos os tipos estão corretos, mas o modelo responde com um prazo inexistente. A validação estrutural passou; a qualidade da resposta ainda precisa ser avaliada. São problemas distintos.

## 8. Vídeos: por onde começar

Os materiais abaixo foram selecionados por pertinência e autoria. Consultei páginas e descrições, mas não assisti integralmente aos vídeos. Não confirmei legendas ou duração. Os recursos selecionados são em inglês; se disponível, ative legendas e tradução automática. A leitura da IBM acima oferece apoio em português.

| Ordem | Material | Formato e nível | O que observar | Exercício depois |
| --- | --- | --- | --- | --- |
| 1 | [Domain-Specific Languages with Martin Fowler — OnSoftware](https://www.youtube.com/watch?v=ZfdAwV0HlEU) | Vídeo direto; introdução conceitual. | A ideia de uma linguagem voltada a um problema. | Explique DSL em duas frases e dê um exemplo. |
| 2 | [Introduction — Node-RED Essentials](https://www.youtube.com/watch?v=ksGeUD26Mw0) | Vídeo direto; entrada para a série. | A proposta de programar com fluxos. | Desenhe três blocos e diga o que passa entre eles. |
| 3 | [Node-RED — canal oficial](https://www.youtube.com/channel/UCQaB8NXBEPod7Ab8PPCLLAA) | Canal/série, não vídeo único; básico. | Procure a série **Essentials**, indicada pela [documentação oficial](https://nodered.org/docs/tutorials/). Observe editor, nós e mensagens. | Distinga a configuração de um nó do dado recebido durante a execução. |
| 4 | [What is Retrieval-Augmented Generation (RAG)? — IBM Technology](https://www.youtube.com/watch?v=T-D1OfcDW1M) | Vídeo direto; introdução a IA aplicada. | A relação entre recuperação e geração. | Explique por que a busca ocorre antes da resposta. |
| 5 | [Langflow — canal oficial](https://www.youtube.com/@Langflow) | Canal, não vídeo único; aplicação prática. | Escolha uma introdução a fluxos ou chatbots. Identifique entrada, modelo, prompt e saída. | Refaça o desenho e anote o tipo de dado em cada conexão. |

Os dois primeiros vídeos foram localizados pela busca, mas sua abertura direta falhou nesta consulta. Para Node-RED, a [página oficial de tutoriais](https://nodered.org/docs/tutorials/) oferece o caminho alternativo para o canal. Não há timestamps inventados neste roteiro.

O canal do Langflow está vinculado pelo [site oficial](https://www.langflow.org/blog/langflow-micro-tutorials-multiple-sources/). Tutoriais antigos podem mostrar telas diferentes; compare com a [documentação atual](https://docs.langflow.org/).

**Como assistir:** pause sempre que aparecer uma seta nova. Escreva: “sai ___ do bloco ___ e entra em ___”. Se não conseguir preencher, volte ao trecho antes de continuar.

## 9. Uma trilha curta de estudo

Os tempos abaixo são sugestões de dedicação, não a duração dos vídeos.

| Sessão | Dedicação sugerida | Atividade | Entrega pessoal |
| --- | --- | --- | --- |
| 1 — entender a linguagem | 30–45 min | Seções 1–3 e vídeo de Fowler. | Definição própria de DSL e dois exemplos. |
| 2 — entender os fluxos | 45–60 min | Node-RED Essentials e glossário de nós/conexões. | Fluxo no papel com entradas e saídas. |
| 3 — conectar com IA | 45–60 min | Vídeo de RAG e seção 7. | Explicação de cada bloco sem ler o guia. |
| 4 — observar uma ferramenta | 45–60 min | Demonstração no canal do Langflow. | Comparação entre o fluxo visto e seu desenho. |
| 5 — formular uma dúvida de pesquisa | 30–45 min | Revisar o mapa e listar dificuldades. | Um problema específico que uma DSL poderia ajudar a resolver. |

Você não precisa começar por instalação, compiladores, cálculo de redes neurais ou sistemas multiagentes. Primeiro consiga explicar o comportamento de um fluxo pequeno.

## 10. Palavras-chave para a pesquisa posterior

Comece com expressões existentes nas fontes deste guia: `domain-specific language`, `graphical DSL`, `language workbench`, `workflow`, `LLM`, `retrieval-augmented generation` e `AI agents`. Os links conceituais estão nas seções anteriores.

Consultas candidatas — combinações propostas para testar nas bases, ainda sem contagem de resultados:

```text
"domain-specific language" AND "artificial intelligence"
"graphical DSL" AND workflow
"visual programming" AND "large language models"
"workflow orchestration" AND "machine learning"
"domain-specific modeling" AND "AI"
```

As duas últimas também ajudam a explorar termos vizinhos. Registre base, consulta exata, filtros, data e total encontrado. **Ainda não foi verificado o requisito de pelo menos 20 resultados por palavra-chave em uma base de literatura revisada por pares.**

## 11. Como destravar um termo, figura ou tabela

Use este procedimento de estudo:

1. Copie o termo e registre página, seção ou número da figura.
2. Leia a legenda e procure a definição no próprio artigo.
3. Para figuras, identifique entradas, saídas, setas e legenda visual; simule um exemplo pequeno.
4. Para tabelas, identifique linhas, colunas, unidade, métrica e se maior ou menor é melhor.
5. Se continuar confuso, consulte a referência citada pelos autores ou documentação primária. Use vídeos como apoio à compreensão.
6. Registre a dúvida, a fonte que ajudou e sua explicação com palavras próprias. Mantenha como pendente o que não conseguiu confirmar.

Modelo de anotação:

```text
Artigo/material:
Página e figura/tabela:
Termo ou seta que não entendi:
Minha hipótese inicial:
Fonte consultada:
Explicação após a consulta:
Exemplo que consigo percorrer:
O que ainda falta entender:
```

## 12. Quando avançar para os artigos e veículos

- [ ] Consigo definir DSL e domínio sem consultar o guia.
- [ ] Sei distinguir linguagem, editor e motor de execução.
- [ ] Consigo explicar cada seta do exemplo.
- [ ] Sei diferenciar um erro de ligação de um erro na resposta do modelo.
- [ ] Consigo dizer o que minha pesquisa pretende estudar e o que fica fora.
- [ ] Tenho uma dúvida concreta, como: “tipos nas conexões ajudam usuários a detectar fluxos inválidos?”.

Depois dessa base, retome a entrega maior: consolidar o diagrama; levantar os principais veículos com fonte, período e contexto da classificação Qualis, incluindo BRACIS; e selecionar três artigos desses veículos para estudar profundamente suas figuras e tabelas. A lista de veículos e a análise dos artigos **ainda não foram realizadas nesta etapa introdutória**.

O roteiro de continuidade está no [ROADMAP.md](../../ROADMAP.md). A leitura aprofundada do PDF de Oakes et al. está no [guia detalhado](../02-workflows-ml/GUIA-DETALHADO.md).
