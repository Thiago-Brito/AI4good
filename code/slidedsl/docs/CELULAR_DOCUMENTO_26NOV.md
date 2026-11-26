# Leitura de documento no app: porte das correções do PC sem chamadas a mais (26/11/2026)

**Branch:** `exp/celular-documento` (a partir de `exp/noite-26nov`). O `artigo-v2` e o núcleo TS (`packages/slidedsl-core`) não mudaram.

## O que mudou (`mobile/app/src/pipeline`)

| Correção do PC | No app | Custo no celular |
|---|---|---|
| 1. Documento curto lido inteiro | `readingPlan`: até 9 mil caracteres, todos os trechos, na ordem, juntados em até 6 leituras de trechos vizinhos (o PC faz uma chamada por trecho) | as mesmas 6 chamadas ou menos |
| 2. Roteiro vê todos os fatos | `outlineFacts`: com mais de 32 fatos, todos (até 80), com a afirmação encurtada para caber nos mesmos 3.600 caracteres | nenhuma chamada |
| 4. Roteiro segue as seções | `outlineFromSections`, quando uma seção fica sem fato e as seções cabem (capa + uma por slide) | nenhuma chamada |
| 5. Resultados de cada seção | `factWeight` e `ensureSectionResults`; os resultados vão na frente, porque o slide é escrito com os 3 primeiros fatos | nenhuma chamada |
| (novo) Citação de número em qualquer campo | `citeNumberFacts` também nos textos (A012): se outro fato tem o número, ele entra nas fontes, em vez de pedir um reparo | uma chamada a menos quando acerta |

As seções agora valem também para pedidos específicos quando o documento é lido inteiro. Antes, só valiam para o pedido genérico, e o pedido do professor ficava sem seções.

Testes do app: 103/103. Inclui `test/documento-curto.test.mjs`, que é novo.

## Medição (motor do celular no PC, `scripts/bancada_documento.py`, uma execução por modelo)

O tempo é a soma do tempo das chamadas, sem contar a subida do servidor. No celular, o tempo segue sobretudo os tokens de saída.

**O `.md` do professor (8 slides).** Antes: bancada de 25/11, mesmo código do app de `artigo-v2`. Depois: `outputs/celular_documento/depois2`.

| Modelo | Seções | Números (de 9) | Chamadas | Tokens de saída | Tempo das chamadas |
|---|---|---|---|---|---|
| 0.6B LoRA | 2/7 → **6/7** | 0 → **4** | 19 → 16 | 4.120 → 3.402 | 19,7 → 15,0 s |
| 0.6B | 5/7 → 4/7 | 1 → 3 | 20 → 21 | 4.305 → 3.744 | 24,5 → 19,7 s |
| 1.7B | 6/7 → 6/7 | 1 → 2 | 20 → 17 | 5.013 → 4.606 | 35,6 → 32,3 s |
| 4B | 7/7 → 7/7 | 2 → **7** | 19 → 16 | 4.249 → 3.736 | 52,6 → 47,5 s |
| 4B LoRA | 5/7 → 6/7 | 2 → 4 | 16 → 17 | 3.300 → 3.605 | 40,8 → 45,7 s |

Todos os decks saíram válidos. Sobre a "frase invertida" do 0.6B ("economiza tokens"): o slide diz "**não** economiza tokens", como o documento; o avaliador não olha a negação.

**`agua.txt` (curto, sem seções, 6 slides).** Antes e depois rodaram hoje na mesma máquina.

| Modelo | Números do documento usados | Chamadas | Tokens de saída | Tempo das chamadas |
|---|---|---|---|---|
| 0.6B LoRA | 1 → 2 | 15 → 14 | 2.644 → 2.796 | 11,7 → 12,5 s |
| 1.7B | 0 → 0 | 14 → 14 | 2.897 → 3.030 | 20,0 → 22,3 s |
| 4B | 2 → 5 | 15 → 15 | 2.612 → 3.265 | 32,7 → 41,0 s |

Nenhum número fora do documento, antes ou depois.

## Leitura honesta

- **No `.md` do professor**, quatro dos cinco modelos ficaram mais rápidos e todos cobrem mais o documento. O 4B foi de 2 para 7 dos 9 números, e o 0.6B LoRA de 2/7 para 6/7 seções. O 4B LoRA ficou 12% mais lento.
- **No `agua.txt`**, os modelos pequenos ficaram 7% a 11% mais lentos e o 4B, 25%. O 4B leu mais fatos (19 contra 14) e montou um roteiro com ciclo e linha do tempo. Os dois reparos a mais foram números que nenhum fato tem ("2014", "20"), ou seja, a conferência funcionando.
- A leitura em si ficou mais barata: no `agua.txt`, 5 chamadas em vez de 6, com menos tokens de entrada. O custo extra vem do resto do deck, que agora tem mais conteúdo.
- Foi uma execução por modelo, então os números indicam a direção, não a taxa.

## Para levar ao celular

Gerar o APK a partir deste branch (`scripts/mobile_build.ps1`) e testar no aparelho com o mesmo `.md`.

## Segunda rodada: leitura literal, corte perto do limite e título copiado do prompt

Lendo os decks, apareceram quatro problemas no 0.6B LoRA. Três foram corrigidos:

| Problema | Causa | Correção |
|---|---|---|
| "o modelo de 4B foi treinado com 1.876 exemplos" (é o 0.6B, com exemplos escritos pelo 4B) | o 0.6B trocou o sujeito ao **resumir** a frase na leitura | leitura literal (`extractMode` `frases`): o modelo só escolhe a frase, o tipo e a relevância; a afirmação é a frase original, sem rótulos como "Resultado:". O modo antigo continua como `frases_resumo` |
| "24 apresentações por condi" | perto do limite de 48, a gramática fecha a string quando o próximo pedaço da palavra não cabe (47 de 48); o aparo só agia em 48 | `trimTruncated`: perto do limite, se a última palavra não existe inteira nos fatos nem no pedido, ela sai |
| título "Regras do tipo" | o modelo copiou um rótulo do prompt do slide | título igual a um rótulo do prompt vira a mensagem planejada para o slide |

Testes do app: 105/105.

**O `.md` do professor.** Primeira rodada (`depois2`) → segunda rodada (`depois3`):

| Modelo | Seções | Números (de 9) | Tokens de saída | Tempo das chamadas |
|---|---|---|---|---|
| 0.6B LoRA | 6/7 → 6/7 | 4 → **6** | 3.402 → 2.455 | 15,0 → 11,7 s |
| 0.6B | 4/7 → 4/7 | 3 → 2 | 3.744 → 2.754 | 19,7 → 16,0 s |
| 1.7B | 6/7 → 5/7 | 2 → 4 | 4.606 → 3.785 | 32,3 → 28,0 s |
| 4B | 7/7 → 7/7 | 7 → **8** | 3.736 → 2.867 | 47,5 → 38,5 s |
| 4B LoRA | 6/7 → 6/7 | 4 → 5 | 3.605 → 2.647 | 45,7 → 34,7 s |

**`agua.txt`**, comparado com o código **anterior** a este branch:

| Modelo | Números do documento usados | Tempo das chamadas |
|---|---|---|
| 0.6B LoRA | 1 → 2 | 11,7 → 8,8 s |
| 1.7B | 0 → 2 | 20,0 → 15,8 s |
| 4B | 2 → 3 | 32,7 → 24,8 s |

A leitura caiu de cerca de 1.300 para cerca de 340 tokens de saída, porque o modelo não escreve mais a afirmação. Com isso, todos os modelos ficaram mais rápidos que **antes** deste branch, nos dois documentos. Nenhum número fora do documento.

**O que continua no 0.6B LoRA** (deck `depois3`): os erros que sobraram nascem na **escrita do slide**.
- No slide de comparação, inverteu o custo: "1.380 tokens de entrada e 1.344 de saída". O documento diz 1.380 tokens com código e 1.344 com SlideDSL.
- Pôs "GPU RTX 3060" no slide do Teste 1.
- Escreveu rótulos estranhos, como "Aguarde 1 de 24 apresentações".

O deck do 4B não tem esses erros. Próximo passo possível: no modelo pequeno, o detalhe do item passa a ser a frase do fato citado, e o modelo escreve só o rótulo.

## Terceira rodada: detalhe literal nos modelos pequenos e texto copiado do prompt

**Detalhe literal** (`literalDetails`). Vale só para os modelos pequenos: no app, 0.6B e 1.7B (arquivo menor que 2 GB); no PC, o campo `detalhe_literal` de `config/modelos_locais.json`, que vira `--detalhe-literal` no `motor_pc.mjs`.
- O modelo escreve o slide como antes. Em seguida, o detalhe de cada item, lado, marco e legenda de valor é trocado pela frase do fato que mais combina com ele, por palavras e números em comum, um fato por campo.
- Limite: o do compilador com até 3 itens (170 caracteres; 80 na comparação), 110 com mais itens e 70 no slide de imagem.
- Frase longa termina na última pausa, sem deixar parêntese aberto.
- Item cujo detalhe não combina com nenhum fato sai, se sobrarem 2 itens.

**Texto copiado do prompt** (`promptLeak`, vale para todos os modelos). Título, subtítulo ou item igual a um rótulo do prompt, ou começando por "rótulo:" ("Regras do tipo: …", "Fatos para este slide:", "SlideDSL Alto: …"), é tratado assim: o título vira a mensagem planejada para o slide, o subtítulo sai e o item sai.

Testes do app: 109/109. O `tsc` do app inteiro passa.

**O `.md` do professor**, rodada anterior (`depois3`) → esta rodada (`depois7`):

| Modelo | Seções | Números (de 9) | Tempo das chamadas |
|---|---|---|---|
| 0.6B LoRA | 6/7 → **7/7** | 6 → 5 | 11,7 → 11,2 s |
| 0.6B | 4/7 → 4/7 | 2 → 3 | 16,0 → 16,0 s |
| 1.7B | 5/7 → 5/7 | 4 → 5 | 28,0 → 20,3 s |
| 4B (sem detalhe literal) | 7/7 → 7/7 | 8 → 8 | 38,5 → 37,5 s |
| 4B LoRA (sem detalhe literal) | 6/7 → 6/7 | 5 → 5 | 34,7 → 34,4 s |

No `agua.txt`: 0.6B LoRA usou 2 → 3 números do documento em 8,4 s; 1.7B, 2 → 3 em 17,5 s; 4B, 3 → 3 em 24,7 s. Nenhum número fora do documento.

**Lendo os decks:**
- **0.6B LoRA e 1.7B:** os detalhes passaram a ser frases do documento, e as inversões sumiram. Antes, o deck dizia "1.380 tokens de entrada e 1.344 de saída"; agora diz "1.380 tokens escrevendo código e 1.344 escrevendo SlideDSL".
- **O que sobra nesses dois:** rótulos fracos e itens em seção errada (a "GPU RTX 3060" no Teste 1). Quando o slide tem só um item com fato, o outro item fica com o texto do modelo; no 1.7B, sobrou "os custos totais do modelo pequeno ainda não foram medidos", que o documento não diz.
- **0.6B base** (sem treino): continua fraco. Repete o mesmo item, usa rótulos tirados das regras do tipo ("2 a 5 itens paralelos") e escreve "Fontes" e "Notas" como texto.
