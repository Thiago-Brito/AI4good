# Avaliação cega v2: comparação de versões (registrado em 25/11/2026, antes das respostas)

**Por que uma v2.** A v1 (`docs/AVALIACAO_CEGA_PROTOCOLO.md`) usa apresentações do app anteriores às correções de 25/11 (roteiro com todos os fatos, distribuição de fatos, recusa de números inventados, detalhes encurtados). O artigo afirma, pela bancada automática, que essas correções aumentaram os fatos usados e reduziram slides vazios. A v2 pergunta se **pessoas** percebem diferença entre as versões. A v1 fica como está: sua página e seu protocolo não mudam.

**Situação da v1 neste registro:** a página da v1 tem 1 resposta, de 24/11 às 22h, dada à versão de 12 apresentações (antes de entrar o externo), com 6 a 32 s por apresentação. Parece um teste e não entra em nenhuma análise da v2.

**Página da avaliação v2:** https://claude.ai/artifact/CM46v1oCCCsM41tUpbZ2xA (privada; compartilhar com os avaliadores pelo menu Compartilhar, como Editor para gravar no servidor; sem isso, a página mostra um código `SLDA2:…` para colar no painel do dono). Mesmas regras de acesso da v1: cada avaliador lê e grava só a própria resposta.

**Preparação:** `scripts/avaliacao_cega_v2_preparar.py` (semente 20261125, códigos `B###`).
- Dados em `outputs/avaliacao_cega_v2/`, fora do git.
- Gabarito código → condição só em `gabarito.json`, nunca publicado.

## Material

23 apresentações de 5 slides: 4 temas × 6 condições, menos água × PC 4B (sem versão válida, como na v1). Mesmo pedido (nível detalhado), mesmo documento-fonte e semente 11 em todas as condições do celular.

| Condição | Origem |
|---|---|
| celular 0.6B LoRA, app 0.6 (versão da v1) | `outputs/teste8_lora` |
| celular 0.6B LoRA, app 0.7.7 (congelado, `artigo-v2`) | `outputs/teste9_v077_lora06` |
| celular 1.7B, app 0.5 (versão da v1) | `outputs/teste6_17b_dica` |
| celular 1.7B, app 0.7.7 | `outputs/teste9_v077_q17` |
| PC 4B (referência; igual à v1) | `outputs/avaliacao_cega/pc4b` |
| externo GPT-4.1-mini (referência; igual à v1) | `outputs/avaliacao_cega/externo` |

As condições SlideDSL são renderizadas pelo mesmo compilador (versão congelada). A externa mantém o visual do python-pptx e pode ser reconhecida; a página pede que se avalie o conteúdo.

## Avaliadores, tarefa e rubrica

Iguais à v1: 3 colegas voluntários, maiores de 18 anos, sem dado pessoal, com consentimento na página. Cada um avalia as 23 apresentações em ordem sorteada por avaliador (cerca de 45 minutos; o progresso fica salvo e dá para parar e continuar). Rubrica: clareza (1–5), erro (não / sim com trecho / não sei), repetição (não / um pouco / muito), utilidade (1–5), comentário opcional; o tempo por apresentação é registrado.

## Hipóteses (definidas antes das respostas)

- **V1.** Para cada modelo do celular, a versão 0.7.7 tem utilidade maior ou igual à versão antiga (a bancada mostrou 2–3× mais fatos usados e menos slides vazios).
- **V2.** A versão 0.7.7 tem menos "repete muito" que a antiga no 1.7B e no LoRA (distribuição de fatos e itens já escritos no pedido).
- **V3.** A proporção de afirmações marcadas como erradas não cai entre as versões: as correções tratam forma, números e repetição, não a verdade das frases.
- **V4.** Na versão 0.7.7, o LoRA não é pior que o 1.7B em clareza e utilidade (a bancada mostrou apresentações completas sem diferença significativa).
- **V5.** O externo e o PC 4B ficam acima das condições do celular em utilidade; o que se mede é a distância.

## Análise

- Unidade: média dos 3 avaliadores por apresentação.
- Concordância: alfa de Krippendorff ordinal em clareza e utilidade; abaixo de 0,4, concordância fraca.
- Versões (V1, V2, V3): para cada modelo, pares por tema (antiga × 0.7.7), teste do sinal; com 4 temas o poder é baixo, e o resultado é descritivo. Também por avaliação (12 pares por modelo), Wilcoxon pareado como apoio.
- V4 e V5: pares por tema, descritivo.
- Erro e repetição: proporção de "sim" e de "muito" por condição, por avaliação (12 por condição; 9 no PC 4B).
- Script: `scripts/avaliacao_cega_analisar.py outputs/avaliacao_cega_v2/respostas outputs/avaliacao_cega_v2` (pares V1, V4 e V5 já implementados; testado com respostas sintéticas antes de qualquer resposta real).

## Ressalvas registradas

- 4 temas, 1 semente, estudantes como juízes; mede impressão de qualidade, não aprendizagem.
- As apresentações antigas e novas do mesmo modelo e tema podem parecer parecidas; a ordem sorteada separa as duas na maioria dos casos, mas não sempre.
- O documento-fonte é opcional para o avaliador.
