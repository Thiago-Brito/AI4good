# Investigação de conteúdo — 11/10/2026

Base: `fea5a52fdfb7ed1bead88b81debefda537f93dc1`. Diagnóstico e protocolo
registrados antes de alterar código. Fontes em [FONTES](../refs/FONTES.md).
Evidências históricas permanecem em `outputs/semantic/review_05` e `experiment_02`.

## Percurso reconstruído

Editor `ContextPanel` → `generation_jobs` → `GenerationContext` → requisitos
congelados → recuperação local opcional → `plan_visual` (intenção/mensagem e
estrutura) → `constrain_visual_schema` → `expressive_schema` → `semantic_schema`
→ decoder de campos fixos → `generate_strategy(plan_only=True)` → normalização
`items/content` → ativos locais → `review_plan` → `run_reliability` →
`plan_to_dsl` → LALR → análise semântica/IR → geometria/design/requisitos →
PptxGenJS → editor/exportação. A gramática valida operações, não fatos do domínio.

## Causas verificadas e hipóteses

| Evidência/code path | Conclusão permitida |
|---|---|
| `layout_for_intent`, `semantic_schema`: stack de concept vira architecture; arquitetura admite só component; flow só process_step | Layout precede conteúdo e restringe papéis. Frações B tem numerador, denominador e exemplo como componentes; ciências B slide 2 tem temperatura, exemplo e condição como etapas. Coerção de tipos comprovada; não prova incapacidade do modelo. |
| Arquitetura B: Camadas/Responsabilidade/Exemplo; comparação Estrutura/Aplicação/Serviços/Escalabilidade | Enum role não verifica identidade. Q003 reconhece nomes exatos; “Camadas de arquitetura” deixa de disparar sem resolver o problema. |
| Arquitetura C, ambas tentativas | Três K006 e dois Q006 novos. Candidatos ainda generalizam isolamento de falhas. Rollback evita nova exportação inválida. |
| Frações C | Cinco K006 permanecem; Q002 some mas Q006 aparece. Revisão não completou frases e manteve explicação baseada em justiça. Não é correção conceitual demonstrada rejeitada somente por aviso. |
| Processos C | Q002 removido; L004 e três D001 novos. Uma correção mais concisa poderia caber; hipótese a testar. |
| `review_plan`: até 24 campos de vários slides; segunda chamada sem informação do candidato rejeitado | Frações/processos repetem valores. Ausência de feedback comprovada; efeito causal exige comparação. |
| K006 procura somente pontuação final | Contrato de término, não detector linguístico de completude. Acrescentar ponto não corrige oração truncada. |

Q001–Q009 são sinais lexicais. Ausência de sinal em ciências não valida o limiar
inventado de 20 °C nem o exemplo. Conteúdo e layout/exportação serão registrados
separadamente. Prompts extensos e tarefas simultâneas são hipóteses de carga;
nenhuma ablação atribui erros à capacidade intrínseca do Qwen3 4B.

## Plano priorizado e critérios congelados

1. Revisão de um slide, priorizando bloqueios e permitindo campos dependentes
   do mesmo nó. Manter título salvo sinal específico, duas chamadas, fontes,
   requisitos e rollback. Informar diff rejeitado e regressões na tentativa
   seguinte. Manter veto a novos erros/sinais. Comparar planos B idênticos.
2. Plano conceitual opcional: chamada adicional sem layout, geometria ou slides;
   separar definições, entidades/responsabilidades, etapas, cenários concretos,
   afirmações/condições e bases da síntese. Alimentar escolha visual/redação;
   não tratar saída como fonte factual. Preservar modo extrativo/histórico.
3. Rubrica independente do gerador: completude, correção, coerência, cenário e
   resultado do exemplo, significado das relações e base da síntese. Texto e
   evidência por julgamento. Avaliação humana permanece pendente; inspeção do
   agente não é avaliação cega por especialistas.

Comparação: controle semântico anterior sem revisão versus conceitual com revisão,
mesmos pedidos/seed/modelo/limites e compilador. Quatro pedidos conhecidos e dois
reservados (fotossíntese e busca binária), seed 42. Controle novo com snapshot
antigo, sem reescrever históricos. Revisão pareada dos planos B é separada.
Congelar código durante chamadas; preservar raw/HTTP/schema/hashes/custo/falhas.
Não ajustar prompts usando os pedidos reservados. Não apresentar sinais lexicais
como correção nem exportação como qualidade. Resultado negativo impede recomendar
ativação por padrão. Office e avaliação humana são necessários à conclusão geral.

## Fechamento da etapa

Implementação/resultados em [EVOLUCAO_CONTEUDO](EVOLUCAO_CONTEUDO.md). O piloto
mostrou que orientar uma terceira redação ainda perdia cenário/condição; o percurso
final usa duas chamadas e projeção literal dos registros selecionados. Fotossíntese
e busca binária ficam como evidência exploratória. Densidade e pilhas/filas foram
reservados depois dos pilotos e repetidos com UTF-8 correto, sem modificar código
pelos resultados. Controle 3/6, conceitual 6/6 PPTX; seis revisões históricas rejeitadas.
Omissões e erros permanecem: não houve ganho geral de conteúdo demonstrado.
