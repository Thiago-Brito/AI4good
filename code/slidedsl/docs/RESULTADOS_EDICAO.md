# Edição localizada de um slide na SlideDSL Alto (medido em 23/11/2026)

Scripts: `scripts/teste_edicao.py` (execução) e `scripts/analise_edicao.py` (análise a partir dos
arquivos salvos). Dados (não versionados): `outputs/teste_edicao/` (`base/`, `edicoes*/`,
`edicoes_v2.csv`, `edicoes_v3.csv`, `analise.json`).

## Protocolo

- Modelo: `qwen3:4b-instruct` via Ollama (RTX 3060), temperatura 0,2, mesmo modelo para gerar e editar.
- 4 decks base de 6 slides, um por tema (`*_detalhado` de `benchmark/format_requests.json`), com o dossiê
  fixo e a primeira semente válida entre 11, 22 e 33 (solar precisou da 2ª: a 1ª falhou por A005, valor
  de "números" longo demais; os outros, da 1ª).
- Em cada deck, no slide 3: 3 edições por IA (`refazer_slide`: "frases mais curtas", "transforme em
  comparação", "linguagem para ensino fundamental") e 3 determinísticas (`ajustar_alto`: tema escuro,
  mover para a posição 5, excluir). Até 1 reparo por edição.
- Rodada **v2**: código original (o esquema oferecia todos os tipos de slide). Rodada **v3**: após a
  correção que mantém o tipo atual salvo pedido explícito (`allowed_kinds` em `alto_edit.py`).
- Localidade em três níveis: fonte (texto Alto fora do slide editado idêntico byte a byte), conteúdo
  (textos visíveis dos outros slides idênticos) e visual (IR dos outros slides idêntica, ignorando só a
  linha/coluna de origem).

## Resultado (medido)

| Métrica (12 edições por IA) | v2 (antes) | v3 (depois) |
|---|---:|---:|
| Edição aceita pelo compilador | 12/12 | 11/12 |
| Fonte fora do slide idêntica | 12/12 | 11/11 |
| Textos dos outros slides idênticos | 12/12 | 11/11 |
| IR dos outros slides idêntica | 6/12 | 9/11 |
| Tipo pedido cumprido (manter, ou virar comparação) | **1/12** | **11/11** |
| Slide virou `secao` (só título) | **11/12** | **0/11** |
| Conteúdo (≥ 2 itens/valores) preservado | 1/12 | 11/11 |
| Fontes citadas mantidas | 1/12 | 11/11 |
| Tokens de entrada / saída por edição (média) | 4.973 / 206 | 4.381 / 384 |
| Tempo por edição (média) | 4,7 s | 8,1 s |
| Gerar o deck inteiro (média dos 4 decks) | 60.771 / 7.417 tokens; 120 s | 60.855 / 7.465; 120 s |

Edições determinísticas (v2 e v3 iguais): tema 4/4 válidas com todos os textos preservados; mover 4/4
com os textos de todos os slides na nova ordem (IR idêntica 0/4: ids `sN_` e número de página mudam por
construção, e a regra de ritmo pode trocar a variante visual); excluir 4/4; ~0,2 s e 0 tokens.

A falha da v3 (git, "virar comparação"): após 1 reparo um texto ficou com 85 caracteres (limite 80) e o
compilador recusou a edição; o deck original permaneceu intacto.

## Interpretação (separada do medido)

- A edição é localizada no texto e no conteúdo em todos os casos aceitos. Quando a IR de um vizinho muda,
  é a variante visual escolhida pela regra de ritmo do compilador, não o conteúdo.
- Com todos os tipos liberados, o modelo pequeno "fugia" para o tipo com menos campos (`secao`), perdendo
  itens e fontes mesmo quando a instrução pedia comparação. Restringir o esquema ao tipo atual (ou ao tipo
  pedido) resolveu 11/11 casos aceitos: outro exemplo de que a forma da restrição decide o resultado.
- Editar um slide custou ~7% dos tokens de entrada, ~5% dos de saída e ~7% do tempo de gerar o deck
  inteiro (v3). Amostra pequena (4 decks × 3 instruções, 1 modelo); não generalizar sem mais repetições.
