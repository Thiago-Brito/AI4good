# Resultados reais dos Qwen3 — 08/10/2026

Este documento descreve o protocolo histórico com geração integral do deck.
A evolução incremental já gerou um PPTX real por qwen3:4b-instruct; ver
[fluxo e reprodução](SLM_LOCAL_FUNCIONAL.md) e [auditoria das falhas](DIAGNOSTICO_OLLAMA.md).
[Comparação incremental concluída](RESULTADOS_INCREMENTAIS.md): três modelos,
dois modos, cinco repetições por configuração, com resultados separados da demo.
O resultado histórico 0/5 abaixo não foi substituído ou recalculado.

Fontes registradas em [refs/FONTES.md](../refs/FONTES.md). Evidência principal:
[benchmark.json](../outputs/reports_ollama_20261008/benchmark.json),
[análise automática](../outputs/reports_ollama_20261008/ANALISE.md) e
[CSV](../outputs/reports_ollama_20261008/benchmark.csv).
Instalação, hardware e reprodução: [OLLAMA_LOCAL.md](OLLAMA_LOCAL.md).

Ollama 0.40.1 foi instalado e os dois modelos foram baixados na máquina. Ambos
responderam localmente, com execução observada na RTX 3060 de 12 GiB. Não houve
falha de transporte nas chamadas incluídas no conjunto final. O status dos dois
passou de NAO_EXECUTADO para EXECUTADO; isso significa que o experimento rodou,
não que as respostas foram aprovadas.

## Resultado

| Tag | Repetições | Parse inicial | Parse após até 2 reparos (C) | PPTX final (C) | Reparos recebidos | Tempo inicial médio |
|---|---:|---:|---:|---:|---:|---:|
| qwen3:0.6b | 5 | 0/5 | 0/5 | 0/5 | 10 | 63,503 s |
| qwen3:4b | 5 | 0/5 | 0/5 | 0/5 | 10 | 111,633 s |

A/B compartilham cada geração inicial; C usa a mesma resposta antes dos reparos.
Portanto, existem dez gerações iniciais reais e vinte reparos, não trinta gerações
iniciais independentes. Há 50 arquivos raw na árvore de tentativas porque a resposta
inicial aparece nas três condições. Todos têm `is_mock=false`. Nenhum PPTX de modelo
foi produzido nesse conjunto; o PPTX de cinco slides entregue anteriormente continua
sendo o gabarito manual, com sua auditoria separada.

Toda tentativa falhou no parser (P001). Análise semântica e regras geométricas não
foram alcançadas. A cobertura registrada como 0/17 é o resultado do avaliador sem
IR válida, não uma inspeção do conteúdo factual do texto. A ausência de diagnósticos
D001–D010 nesses casos não indica design aprovado.

## Erros observados

- 0.6b: em todas as rodadas, usou `adicionar_imagem` no lugar de `adicionar imagem`;
  o primeiro erro está na linha 4, coluna 14. Também repetiu comandos até o limite
  de geração. O feedback não corrigiu o erro inicial nesse protocolo.
- 4b: na primeira repetição, omitiu `arquivo` antes do caminho da imagem. Outras
  respostas usaram `trazer_frente id img1 para frente` ou `trazer frente id imagem`,
  em vez da produção suportada `trazer ID para frente`. Houve respostas vazias e
  uma resposta interrompida no meio de um comando. Os reparos mudaram algumas
  falhas, mas nenhuma rodada final passou no parser.

Cada erro pode ser conferido nos `diagnostics.json`, `raw.txt` e `attempt.json`
por modelo, repetição, condição e rodada. As respostas não foram corrigidas à mão,
recortadas ou normalizadas para aumentar a taxa de sucesso.

## Controles e limitações

Pedido literal e prompt técnico idênticos, temperatura 0, seed 42, contexto 16384,
orçamento de saída 8192 tokens e timeout por chamada de 300 segundos. Os dois
digests completos estão no relatório. Os detalhes retornados pelo serviço, inclusive
quantização e tamanho declarado, foram preservados; as tags são identificadores,
não uma medição independente do número de parâmetros.

A tag 0.6b permite `think=false`; a tag 4b instalada declara somente `think=true`.
O adaptador registra valor solicitado, efetivo e controles suportados. A primeira
tentativa do 4b com o parâmetro incompatível ficou arquivada e excluída das taxas.
As cinco repetições completas do 0.6b foram retomadas sem regerar ou alterar bytes;
o relatório informa `reused_completed_repetitions=5` e mantém as durações originais.
O 4b foi executado novamente com o controle suportado. Isso não isola o efeito do
tamanho: regimes de thinking, templates e pesos também diferem.

No conjunto final, 15/15 respostas do 0.6b e 11/15 do 4b terminaram com
`done_reason=length`; quatro respostas do 4b terminaram com `stop`. O orçamento
afeta a geração e, no 4b, inclui o trabalho de thinking. Há erros sintáticos antes
dos pontos de truncamento, mas esses dados não demonstram a capacidade máxima dos
modelos com outro orçamento ou outro prompt.

Cada modelo apresentou dois hashes distintos entre suas cinco respostas iniciais.
Repetições sob seed fixa não são amostras independentes. O tempo da primeira chamada
do 0.6b foi 124,76 s e o das seguintes, aproximadamente 48 s; duração inclui o
serviço e seus estados de carregamento/cache. Não é uma comparação causal de
velocidade entre tamanhos de modelos.

Não houve ganho de parsing ou compilação com os reparos nesta tarefa/configuração.
Isso não prova que feedback seja inútil em outras condições. Novos experimentos
devem variar orçamento e apresentação da gramática, com protocolo e prompts
versionados, mantendo os dados atuais como referência. Avaliação espacial exige
primeiro obter IR válida. OpenAI continua pendente de credencial/acesso.

## Verificação do código após o experimento

`scripts/test_windows.ps1` passou: 108 testes Python (4,39 s, um aviso transitivo),
dois testes Node, três Playwright (8,2 s), Ruff, ESLint, Prettier e build TypeScript/Vite.
Os três testes novos cobrem o controle de thinking obrigatório e a retomada que
preserva respostas e rejeita prompts alterados. Artefatos ficam em `outputs/`.
