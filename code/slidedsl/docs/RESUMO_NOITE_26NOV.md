# Resumo da noite de 26/11/2026: fluxo com documento em todos os modelos

**Branch:** `exp/noite-26nov`. O código do artigo continua congelado em `artigo-v2`; o app do celular e o branch `feature/slidedsl-api-voz-mobile` não mudaram. Registro volta a volta: `docs/NOITE_26NOV.md`. Plano: `docs/PLANO_NOITE_26NOV.md`.

## Em uma frase

O fluxo do PC com documento passou a ler o documento inteiro, a seguir as seções com os resultados de cada uma e a respeitar os limites do compilador na própria gramática (tamanho e quantidade). Com o seu `.md`, o GPT-5.4-mini foi de 38 fatos e slides inventados para 7/7 seções e 6–8 dos 9 números-chave, e todos os modelos locais, que antes falhavam ou nem terminavam, passaram a gerar decks válidos. A geração sem documento não piorou: os 12 pedidos do Teste 3 foram de 9/12 para 12/12 válidos, com o mesmo custo.

## O que mudou no código (fluxo do PC, `src/slidedsl`)

| # | Problema encontrado | Correção | Onde |
|---|---|---|---|
| 1 | Documento curto com muitas seções: só 12 trechos lidos | documento que cabe no limite é lido inteiro, na ordem | `documents.py` |
| 2 | Roteiro via só os 32 primeiros fatos | com mais de 32, todos, compactos | `facts_block` |
| 3 | 4 fatos por slide | 6 | `outline_schema`, `slide_schema` |
| 4 | Modelo deixava seções de fora | roteiro segue as seções quando elas cabem | `outline_from_sections` |
| 5 | Slide da seção sem os resultados; método e resultado se confundiam | peso do fato (resultado > número > sem número) e resultados na frente | `fact_weight`, `ensure_section_results` |
| 6 | 4B local recusado por rótulo longo (A005) | limites de tamanho do compilador na gramática do PC (porte do app) e corte na última pausa | `gbnf.alto_gbnf_limitada`, `trim_slide_limits` |
| 7 | Leitura inteira estourava o limite de chamadas | leituras extras fora do orçamento; padrão de 10 chamadas por slide (mín. 60) | `documents.py`, `default_max_calls` |
| 8 | No JSON (GPT) sobrava texto acima do limite depois dos reparos | o compilador apara na última pausa (F002) | `shorten_over_limit` |
| 9 | 4B escrevia palavras no valor do slide de números | valor começa por algarismo na gramática | `t-valor` em `gbnf.py` |
| 10 | 4B parafraseava o trecho e a conferência literal rejeitava fatos | leitura por frases numeradas para modelos com gramática (porte do app) | `frases.py` |
| 11 | 1.7B e 0.6B (Qwen3 híbridos) liam 0 fatos: abriam com `<think>`, que a gramática não permite | adaptador llama.cpp desliga o raciocínio | `models/llamacpp_model.py` |
| 12 | 1.7B fez gráfico de uma barra (A003) | quantidade de itens do compilador na gramática | `gbnf.py` |

pytest: 773/773 no fim da noite (758 no início). Cada mudança foi medida antes e depois; nenhuma piorou outro caso.

## Números

**O seu documento (`diferencial_v2.md`, 8 slides)**, avaliado por `scripts/avaliar_documento.py` (seções do documento cobertas, 9 números-chave, frases invertidas):

| Motor | Antes (25/11) | Depois |
|---|---|---|
| PC, GPT-5.4-mini | 6/7 seções, 3/9 números, título invertido | **válido, 7/7, 6–8 de 9** (3 execuções), sem invertidas, ~100 s, US$ 0,09 |
| PC, Qwen3 4B local | recusado (A005) ou parava no limite de chamadas | **válido, 6–7/7, 5–6 de 9**, ~276 s |
| PC, Qwen3 1.7B | lia 0 fatos | **válido, 5/7, 3/9**, 120 s |
| PC, 0.6B LoRA | lia 0 fatos | **válido, 6/7, 1/9**, 84 s |
| Motor do celular (código do app, sem mudança) | — | 0.6B LoRA 2/7 e 0/9 · 0.6B 5/7 e 1/9 · 1.7B 6/7 e 1/9 · 4B 7/7 e 2/9 · 4B LoRA 5/7 e 2/9 |

**Geração sem documento** (12 pedidos do Teste 3, semente 11, Qwen3 4B): válidas 9/12 → 12/12; reparos 11,67 → 11,42; tokens de saída 7.124 → 7.031; tempo 107,9 → 102,6 s.

**Outros documentos** (antes = código do início da noite):

| Documento | Motor | Chamadas | Tempo | Números do documento usados |
|---|---|---|---|---|
| `agua.txt` (curto, sem seções) | 4B local | 38 → 30 | 123 → 82 s | 6 → 7 |
| `agua.txt` | GPT-5.4-mini | 40 → 25 | 72 → 42 s (US$ 0,060 → 0,037) | 3 → 3 |
| PDF do artigo (longo) | 4B local | 51 → 48 | 238 → 163 s | 3 → 8 |
| PDF do artigo | GPT-5.4-mini | 37 → 37 | 74 → 80 s | 4 → 11 (antes inválido por A010, depois válido) |

**API:** US$ 0,70 de US$ 1,00.

## O que não funcionou ou ficou de fora

- O motor do celular (código do app) não recebeu nenhuma destas correções: ele lê no máximo 6 trechos e ainda cobre poucas seções e quase nenhum número. O mesmo 0.6B LoRA, no fluxo do PC, foi de 2/7 para 6/7 seções.
- O GPT varia entre execuções (6 a 8 de 9 números); os modelos locais ainda perdem números na leitura (ex.: "1 de 24" no 4B; o 0.6B LoRA usa só 1 dos 9).
- Comparações com 12 pedidos e 1–3 execuções por modelo: indicam direção, não taxa. O lado "antes" das comparações não gera o .pptx (a cópia antiga não tem `node_modules` do renderer); a validade dele vem do compilador.
- As horas das 5 primeiras linhas do registro foram estimadas; as demais vêm do relógio.

## Recomendação

1. **Levar o branch `exp/noite-26nov` para o `feature/slidedsl-api-voz-mobile`** depois de você conferir: as 12 correções são do fluxo do PC, com testes e medição antes e depois, sem piora na geração sem documento. O `artigo-v2` continua intacto.
2. **Para apresentar a partir de um documento seu, hoje:** GPT-5.4-mini pelo fluxo do PC (melhor conteúdo, ~US$ 0,09) ou o Qwen3 4B local (grátis, ~4,5 min, um pouco menos de números). Conferir os números antes de usar.
3. **Próximo passo de código:** portar para o app as correções 1, 2, 4 e 5 (leitura inteira de documento curto, roteiro com todos os fatos, seções e resultados). O app já tem 6, 9, 10 e 11; a bancada mostrou que o mesmo modelo no fluxo do PC cobre muito mais o documento.
4. **No artigo:** nada muda por enquanto; estas mudanças são posteriores ao código congelado e não alteram os números do T9.
