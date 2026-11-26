# Resumo da noite de 26/11/2026: fluxo com documento em todos os modelos

**Branch:** `exp/noite-26nov`. O código do artigo continua congelado em `artigo-v2`; o app do celular e o branch `feature/slidedsl-api-voz-mobile` não mudaram. Registro volta a volta: `docs/NOITE_26NOV.md`. Plano: `docs/PLANO_NOITE_26NOV.md`.

## Em uma frase

O fluxo do PC com documento passou a ler o documento inteiro, a seguir as seções com os resultados de cada uma e a respeitar os limites do compilador na própria gramática. Com o mesmo `.md`, o GPT-5.4-mini foi de 38 fatos lidos e slides inventados para 7/7 seções e 6–8 dos 9 números-chave, e o Qwen3 4B local, que nem terminava, passou a gerar decks válidos com 5–6 dos 9 números. A geração sem documento não piorou: os 12 pedidos do Teste 3 foram de 9/12 para 12/12 válidos.

## O que mudou no código (fluxo do PC, `src/slidedsl`)

| # | Problema encontrado | Correção | Onde |
|---|---|---|---|
| 1 | Documento curto com muitas seções: só 12 trechos lidos | documento que cabe no limite é lido inteiro, na ordem | `documents.py` |
| 2 | Roteiro via só os 32 primeiros fatos | com mais de 32, todos, compactos | `alto_generation.py` (`facts_block`) |
| 3 | 4 fatos por slide | 6 | `outline_schema`, `slide_schema` |
| 4 | Modelo deixava seções de fora | roteiro segue as seções quando elas cabem | `outline_from_sections` |
| 5 | Slide da seção sem os resultados; método e resultado se confundiam | peso do fato (resultado > número > sem número) e resultados na frente | `fact_weight`, `ensure_section_results` |
| 6 | 4B local recusado por rótulo longo (A005) | limites do compilador na gramática do PC (porte do app) e corte na última pausa | `gbnf.alto_gbnf_limitada`, `trim_slide_limits` |
| 7 | Leitura inteira estourava o limite de chamadas | leituras extras fora do orçamento; padrão de 10 chamadas por slide (mín. 60) | `documents.py`, `default_max_calls` |
| 8 | No JSON (GPT) sobrava texto acima do limite depois dos reparos | o compilador apara na última pausa (F002) | `shorten_over_limit` |
| 9 | 4B escrevia palavras no valor do slide de números | valor começa por algarismo na gramática | `t-valor` em `gbnf.py` |
| 10 | 4B parafraseava o trecho e a conferência literal rejeitava fatos | leitura por frases numeradas para modelos com gramática (porte do app) | `frases.py` |

pytest: 772/772 no fim da noite (era 758 no início).

## Números

**Documento `diferencial_v2.md`, 8 slides** (avaliação automática: `scripts/avaliar_documento.py`):

| | início da noite (25/11) | fim da noite |
|---|---|---|
| GPT-5.4-mini | 6/7 seções, 3/9 números, slide de custo invertido | 7/7 e 6, 8, 8 de 9 em 3 execuções, sem invertidas, válidas |
| Qwen3 4B local (PC) | recusado (A005) | válido, 7/7 ou 6/7 seções, 5–6 de 9 números, ~276 s |
| Motor do celular (0.6B LoRA … 4B) | — | 2/7 a 7/7 seções, 0–2 de 9 números (código do app, não mudou) |

**Geração sem documento** (12 pedidos do Teste 3, semente 11, Qwen3 4B): válidas 9/12 → 12/12; reparos 11,67 → 11,42; tokens de saída 7.124 → 7.031; tempo 107,9 → 103,3 s.

**Outros documentos, 4B local** (T9): `agua.txt` 38 → 30 chamadas, 123 → 82 s, números do documento usados 6 → 7; PDF do artigo 51 → 48 chamadas, 238 → 163 s, 3 → 8 números.

PREENCHER: T9 com o GPT-5.4-mini.

**API:** PREENCHER de US$ 1,00.

## O que não funcionou ou ficou de fora

- O motor do celular (código do app) lê no máximo 6 trechos do documento e ainda cobre poucas seções e quase nenhum número. A correção é a mesma do item 1, mas fica para quando o app puder mudar.
- O GPT varia entre execuções (6 a 8 de 9 números); o 4B local ainda perde alguns números na leitura (ex.: "1 de 24").
- Comparações com 12 pedidos e 1–3 execuções por modelo: indicam direção, não taxa.

## Recomendação

PREENCHER.
