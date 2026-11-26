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
