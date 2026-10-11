# Planejamento e revisão semântica — 11/10/2026

Snapshot inicial obrigatório: `64a49f4cdfc68ebe4614579dc8af74f93f74e13b`,
enviado a `origin/dsl-visual` antes de alterar código. Resultados históricos,
ambientes, caches e outros projetos ficaram fora do commit. Fontes consultadas
e evidências anteriores registradas em [FONTES](../refs/FONTES.md).

## Diagnóstico e arquitetura

A etapa [expressiva](EXPRESSIVIDADE_PLANEJAMENTO.md) separou rótulos e explicações,
mas não distinguiu categorias, componentes e afirmações. O resultado real incluiu
“Camadas” como entidade, critérios e entidades misturados na comparação, repetição
na conclusão e vantagens sem condições. Exportação válida e os critérios 2/2
(quantidade/margens) não detectaram esses problemas. `stack` também conectava
automaticamente vizinhos, sem uma relação editorial declarada.

Esta etapa acrescenta o protocolo opcional `semantic-planning-v1` ao percurso
existente. Não substitui gramática, AST/IR 1.1, parser, compilador, editor ou renderer.

```mermaid
flowchart LR
  A[Pedido e requisitos congelados] --> B[Qwen3 local: intenção]
  D[Documentos locais opcionais] --> E[Recuperação lexical por slide]
  B --> E
  E --> F[Qwen3: conteúdo tipado e relações]
  B --> F
  F --> G[Contrato e diagnóstico editorial]
  G --> H[Até duas revisões de campos afetados]
  H --> I[Candidato e rollback]
  I --> J[Geometria medida e DSL]
  J --> K[LALR, semântica, design e requisitos]
  K --> L[Editor e PPTX nativo]
```

Implementação incremental: contrato compatível; relações explícitas; revisão
localizada com aceitação conservadora; recuperação por slide; testes de etapa;
comparação A/B/C em quatro domínios. Resultados e limitações da execução serão
registrados abaixo após a conclusão, sem atribuir notas factuais à própria SLM.

## Contrato e relações

`ContentBlock` mantém `label`, `detail` e `explanation`, acrescentando `role`
opcional e IDs de fragmentos em `sources`. Serialização de planos antigos omite
os campos ausentes; `items` continua sendo a representação textual canônica.
O decoder antigo não recebe os novos campos. O decoder semântico limita os
papéis por família, sem exigir todos os tipos em um slide.

| Papel | Uso |
|---|---|
| concept | Definição ou conceito |
| component | Entidade do sistema, não vantagem/categoria |
| process_step | Etapa de um processo |
| relationship | Informação textual sobre uma relação |
| example | Caso concreto; sua relevância ainda exige inspeção |
| claim / evidence / condition | Afirmação, sustentação e limite |
| comparison_criterion | Mesmo critério nas duas alternativas |
| takeaway | Síntese contextual |

Referências posicionais `c1_i1`, `c1_i2` etc. apontam para os itens realmente
existentes. Não há IDs livres ou coordenadas fornecidas pelo modelo.

```json
{
  "semantic": true,
  "relationships": [
    {"source": "c1_i1", "target": "c1_i2", "type": "calls"},
    {"source": "c1_i2", "target": "c1_i3", "type": "accesses"}
  ]
}
```

Esse exemplo só compila se os três nós forem componentes existentes, consecutivos
e ordenados na mesma coluna. `calls`, `accesses` e `depends_on` ligam componentes;
`precedes` liga etapas. Setas e seus rótulos em português são objetos nativos,
com ancoragem OOXML já existente. Um `stack` sem relações não gera setas nesse
protocolo. O protocolo antigo mantém suas conexões anteriores.

`supports` associa exemplo/evidência/condição a afirmação/síntese; `contrasts`
associa critérios. Esses vínculos editoriais não viram setas de dependência.
Não há novo roteador de grafos: saltos, reversões e conexões cruzando colunas
recebem K004 para relações desenhadas. Referências inexistentes, duplicadas ou
circulares recebem K002; papéis incompatíveis recebem K003. Critérios de
comparação desalinhados recebem K005. Frases incompletas recebem K006,
permanecendo localizáveis para revisão, sem exportar texto cortado.

Os limites de caracteres/elementos e a medição de fontes da etapa expressiva
são mantidos. Espaço de 48 px acomoda rótulos dos conectores, reduzindo a
capacidade disponível; excesso continua gerando L004, sem diminuir o corpo
abaixo de 22 pt. Comparações por critérios usam linhas de alturas compartilhadas
para manter os pares alinhados. Mídia, créditos e seleção autorizada permanecem
no percurso existente; não se fazem pesquisas de imagens nestes ensaios.

## Revisão, preservação e fontes

`semantic_review_max` permite zero, uma ou duas chamadas. Zero ainda registra
diagnóstico. Heurísticas Q001–Q009 identificam repetição exata, nomes abstratos,
expressões absolutas, descrições genéricas, ausência de vínculo lexical entre
mensagem/exemplo/conclusão e conteúdo e fontes não declaradas. São sinais para
revisão, com falsos positivos e negativos, não demonstrações de erro factual.

A revisão recebe até 24 campos afetados, os nós necessários para entender o slide,
mensagens/conteúdo anterior pertinentes à síntese, requisitos e fragmentos
relevantes. O decoder final recebe um objeto `edits` com chaves fixas `field_1`,
`field_2` etc., associadas a caminhos autorizados; `null` mantém o campo.
A normalização converte esses valores em `edits: [{path,value}]`, reutilizando
o mecanismo existente. Os dois contratos são validados. Nome, função e mensagem
do mesmo slide podem ser revisados conjuntamente quando uma entidade abstrata
ou vantagem sem condições os afeta. Não pode
trocar arrays inteiros, alterar quantidade, geometria ou outros slides. Cada
tentativa consome orçamento, inclusive falhas; resposta vazia indica ausência
de alteração segura. Estados antes/candidato/depois, prompts, schemas, bytes
brutos, resposta HTTP, validações e decisões são preservados.

Aceitação exige redução dos sinais diagnosticados, sem novos bloqueios, perda
de requisito já atendido, novo diagnóstico ou esvaziamento de texto. A alteração
de um campo tipado recompõe somente seu `items` derivado. Esses controles não
provam equivalência semântica entre frases reescritas: o diff precisa de revisão
humana. Não se usa a opinião da própria SLM como certificado de verdade.

Na geração semântica, a primeira saída de conteúdo é um plano, sem compilar
PPTX auxiliar antes da revisão. Depois de resolver ativos locais, o plano segue
pela revisão e pela cadeia existente de validação/requisitos/exportação.

No modo `free`, anexos continuam ignorados. `grounded` recupera lexicalmente
por mensagem/foco de cada slide, compartilhando até oito fragmentos/6.000
caracteres. IDs de documento, trecho, origem e página permanecem nos registros.
O auditor associa cada nó às fontes declaradas e identifica IDs inexistentes
(F001) ou sustentação não declarada (Q009). Um vínculo existente não demonstra
implicação nem verdade documental. `supplement` continua sendo opção explícita.

`restricted` conserva o contrato extrativo anterior e não admite o novo modo:
a API recusa a combinação; o formulário desativa a opção ao escolher restrito.
Não se convertem citações literais em textos reescritos. Recuperação é limitada
e pode deixar slides sem trechos relevantes; não há RAG obrigatório nem embeddings.

| Módulo | Alteração |
|---|---|
| `planning.py` | Papéis, fontes de nó e relações opcionais compatíveis |
| `semantic_planning.py` | Contrato, auditoria, patches e aceitação/rollback |
| `visual_planning.py` | Decoder reutiliza campos tipados com suas restrições |
| `expressive_composition.py` / `layouts.py` | Relações declaradas, rótulos e critérios alinhados |
| `documents.py` | Recuperação lexical por necessidade do slide |
| `contextual.py` / `evolution.py` | Plano antes da compilação, revisão e contagem de chamadas |
| `cli.py` / `generation_jobs.py` | Ativação e relatório persistido na API |
| `ContextPanel.tsx` / `GenerationPanel.tsx` | Opções e diagnóstico editorial no editor existente |

Exclusivamente `qwen3:4b-instruct` em Ollama loopback neste protocolo, inclusive
na revisão chamada diretamente. Não há novo serviço de linguagem online.

## Avaliação real e falhas preservadas

Manifesto: [semantic_requests.json](../benchmark/semantic_requests.json).
Quatro domínios: arquitetura de software (cinco slides), ciclo da água, frações
e aprovação de solicitações (dois slides cada). Uma repetição, seed 42,
temperatura 0,1, contexto 8192, saída máxima 4096 por chamada, thinking desligado.
Qwen3 4B local/Ollama 0.40.2, digest observado na geração inicial:
`0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
Pesquisa de imagens desativada; nenhum modelo online.

| Condição | Contrato de conteúdo normalizado aceito /4 | PPTX estrito /4 | Tentativas finais | Aceitas |
|---|---:|---:|---:|---:|
| A: expressivo anterior | 1 | 1 | 0 | 0 |
| B: expressivo com papéis/relações | 4 | 3 | 0 | 0 |
| C: mesmo plano B, revisão localizada | 4 | 3 | 6 | 0 |

Dados finais: [evaluation.json](../outputs/semantic/review_05/evaluation.json),
[auditoria detalhada](../outputs/semantic/audit_05/audit.json) e
[CSV](../outputs/semantic/audit_05/audit.csv).
São 12 avaliações; os quatro pares B/C compartilham exatamente os planos
iniciais e os critérios, conferidos por conteúdo e SHA256. A/B foram gerados
em [experiment_02](../outputs/semantic/experiment_02/evaluation.json).
`review_05` preserva esses planos/DSL/IR/PPTX byte a byte e executa apenas C,
com o contrato final de revisão. Não são oito novas gerações.

| Domínio | A exportou? | B exportou? | C exportou? | Observação da condição final |
|---|---|---|---|---|
| Arquitetura | Sim | Sim | Sim | As duas propostas adicionaram frases incompletas e sinais de título sem vínculo lexical; rollback. Categorias e afirmações problemáticas permanecem. |
| Ciências | Não | Sim | Sim | Plano B sem sinais detectados; zero chamadas de revisão. Duas relações `precedes` explícitas exportadas. Isso não verifica o conteúdo científico. |
| Educação | Não | Não | Não | B contém cinco frases incompletas K006. C removeu algumas pendências mas introduziu Q006; primeira tentativa rejeitada e repetição encerrada. |
| Processos | Não | Sim | Sim | Há uma afirmação absoluta Q002. A proposta prejudicou a geometria; rollback e encerramento por repetição. Dois conectores explícitos no processo. |

**Não houve ganho observado do revisor final.** B também continuou usando nomes
abstratos mesmo com `role=component`; os tipos não verificam o significado do
nome. A comparação de arquitetura contém recomendações simples/complexo no lugar
de funções de entidades. Benefícios foram classificados como exemplos apesar
de serem generalizações. A auditoria marca cinco papéis `example` em B/C; esse
número não demonstra relevância dos exemplos. A inspeção de conteúdo e os
referenciais de arquitetura em [FONTES](../refs/FONTES.md) indicam a necessidade
de condições de contratos, dependências e isolamento. Não foi atribuída uma nota
de correção conceitual por avaliadores; esses campos continuam `null`.

Os termos declarados no manifesto, verificados sobre a IR emitida, somaram
A 4/17 e B/C 13/17. São proxies lexicais: “compara” não aparece necessariamente
em uma comparação válida, e escrever “conclusão” não comprova sustentação.
Os critérios reconhecidos originais somaram A 2/13 e B/C 10/13, mas esse
denominador inclui um erro do reconhecedor: os três pedidos “sem imagens ou
rodapé” criaram indevidamente um requisito positivo de rodapé. Os arrays
congelados não foram alterados; portanto, **essas taxas não representam fielmente
o atendimento ao pedido**. O tratamento de negações coordenadas foi corrigido
e testado depois dos ensaios, para gerações novas. Na arquitetura, 2/2 continua
significando somente quantidade e margens. `faithful` não significa verdade factual.

### Custo e auditabilidade

Os planos A/B exigiram 16 chamadas reais: 20.282 tokens de entrada e 8.694 de
saída. C final acrescentou seis chamadas: 13.474 de entrada e 1.322 de saída.
A comparação final corresponde a **22 chamadas únicas, 33.756 tokens de entrada
e 10.016 de saída**. Não somar novamente o custo inicial compartilhado em C.
Todas essas respostas terminaram com `stop` e atenderam ao schema bruto enviado;
isso não garantiu frases completas, contrato posterior ou PPTX.

Tempos agregados observados: A 67,40 s, B 96,38 s; C 32,68 s adicionais sobre
os planos B. Incluem compilação/cache/carregamento e não demonstram superioridade
causal. A/B têm contextos e contratos diferentes. Uma seed por domínio não
sustenta conclusão estatística geral nem comparação de capacidade intrínseca
do Qwen3 4B.

Desenvolvimento inteiro: **51 chamadas, 74.222 tokens de entrada e 22.056 de
saída**, contando falhas e revisões anteriores, sem contá-las como novas
apresentações independentes. Pastas preservadas:

| Execução | Chamadas | Resultado/limite |
|---|---:|---|
| `experiment_01` | 17 | Frases cortadas e referências a coluna inexistente. Código foi editado enquanto o processo estava em andamento; snapshots posteriores por geração não garantem os módulos já carregados. Apenas evidência exploratória, fora da comparação final reproduzível. |
| `experiment_02` | 19 | Código congelado durante as chamadas; A/B atuais e C inicial. Revisão só de rótulo expôs incoerência com funções. |
| `review_03` | 3 | Reutiliza A/B; nomes e funções conjuntos. Propostas sem progresso ou com novos sinais rejeitadas. |
| `review_04` | 6 | Regex junto ao array heterogêneo de patches produziu JSON/caminhos inválidos. Contrato experimental abandonado; respostas preservadas. |
| `review_05` | 6 | Chaves fixas convertidas a patches existentes. Seis respostas brutas válidas; quatro regressões e duas repetições, todas preservando o estado anterior. |

`audit_semantic_planning.py` conferiu bytes brutos contra HTTP, schemas enviados,
parâmetros, hashes dos snapshots, planos/critério compartilhados, rollback e
textos/conectores nativos de sete PPTX das condições finais. Não são sete
gerações independentes: três PPTX C recompilam os estados B preservados.

Os snapshots antecedem cada execução congelada. Ajustes posteriores de metadados,
contagem de chamadas em indisponibilidade, classificação dos diagnósticos K,
negações coordenadas e reparo de sources vazio não reescrevem os resultados.
A revisão final do prompt substituiu a instrução antiga `edits=[]` por campos
`null` no objeto fixo e explicitou que condições de contratos/isolamento são
exemplos de software, não condições universais. Esses dois ajustes não tiveram
nova chamada real nem ganho medido. Reprodução histórica deve
usar seus snapshots; execução com código atual usa pasta nova.

## Verificações e utilização

Regressão final: **311 Python**, dois Node e nove Playwright passaram; quatro
testes optativos com novas gerações reais foram omitidos. São 40 casos Python
novos de tipos, relações/referências, ancoragem nativa/PPTX, patches, conservação,
requisitos, rollback, fontes, capacidade, frases completas, limites, disponibilidade
e negações coordenadas. Transporte da opção no editor é simulado e está separado
das chamadas Ollama reais. Ruff, ESLint, Prettier, TypeScript e build passaram.
Permanece o aviso transitivo AnyIO/Starlette.

Evidências: [Python](../outputs/tests/semantic-final-05.xml),
[Playwright](../outputs/semantic/ui-tests-final-02/results.json).
O teste novo de negação singular encontrou um erro no regex da própria correção;
foi corrigido antes da regressão final. Uma execução elevada de pytest falhou
por permissões nas pastas temporárias/cache; a repetição com pastas novas dentro
de `outputs/` passou. Logs anteriores foram preservados, sem convertê-los em sucesso.

[Cinco pares de capturas](../outputs/semantic/captures_05/comparison.html)
comparam A e C no pedido de arquitetura: fonte exibida idêntica à fonte salva,
zero overflow no DOM e zero erro JavaScript. Os conteúdos A/C são diferentes;
não é uma comparação causal de estética. B/C finais ficaram iguais após rollback.
São previews geométricos. [Renderização opcional](../outputs/semantic/rendering_05/rendering.json)
retornou `engine=geometric`, `rendered=false`: PowerPoint/LibreOffice indisponíveis.

```powershell
.\.venv\Scripts\slidedsl.exe generate-contextual --semantic-planning --semantic-review-max 2 --model qwen3:4b-instruct --strategy C --repair-max 0 --prompt-file benchmark/prompts/arquitetura_software.txt --out outputs/semantic/nova_geracao
.\.venv\Scripts\python.exe scripts/evaluate_semantic_planning.py --out outputs/semantic/novo_experimento
.\.venv\Scripts\python.exe scripts/evaluate_semantic_planning.py --reuse-existing outputs/semantic/experiment_02 --out outputs/semantic/nova_revisao
.\.venv\Scripts\python.exe scripts/audit_semantic_planning.py outputs/semantic/review_05 --out outputs/semantic/nova_auditoria
```

A API recebe `context: {semantic_planning: true, semantic_review_max: 2}`.
No editor existente, marque **Planejamento semântico** e selecione o orçamento.
O diagnóstico editorial mostra caminhos, sinais e decisões com o limite factual
explícito. A opção exige Qwen3 4B instalado e permanece desativada por padrão.

## Limitações e continuidade

O revisor atual combina sinais determinísticos e propostas locais da SLM; não
interpreta arbitrariamente todo o conteúdo nem detecta todas as oito classes de
problemas. Ausência de sinal não significa mensagem sustentada, exemplo pertinente
ou conclusão correta. O critério conservador também pode rejeitar uma correção
útil por novo aviso lexical: o caso de frações demonstra esse limite.

Não há ontologia de entidades, verificação de implicação, prova factual ou
comparação por especialistas. Sem documentos, conhecimento da SLM é não verificado.
Mesmo com documentos, IDs existentes não garantem que um trecho sustente a
afirmação. Recuperação por slide continua lexical e limitada pelo orçamento.
O contrato `relationship` está disponível como texto no mapa conceitual; grafos
arbitrários, ligações reversas e roteamento permanecem fora da capacidade atual.
Intenção `image`/overrides históricos sem composição expressiva devem continuar
no percurso anterior; os slots de mídia nas famílias expressivas são preservados.

A prioridade seguinte é calibrar os sinais e o critério de aceitação com uma
rubrica independente de conteúdo, revisar fontes por afirmação e testar mais
pedidos/seeds. Renderização real e avaliação de conteúdo/clareza com leitores
continuam pendentes. Esta entrega amplia contratos, diagnóstico e proteção,
**sem demonstrar ganho geral de qualidade semântica ou estética**.
