# Teste 1 — custo de representação por formato (medido em 23/11/2026)

Script: `scripts/format_cost.py`. Saídas completas (não versionadas): `outputs/teste1/format_cost.csv`,
`outputs/teste1/resumo.json`, `outputs/teste1/tabela.md`. Tokenizador: `Qwen/Qwen3-4B` `tokenizer.json`
(SHA-256 `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`), `tokenizers` 0.23.3,
sem tokens especiais. python-pptx 1.0.2.

## Corpus

Decks de `outputs/parity/` com IR: **127 decks únicos, 694 slides**. Excluídos: 65 duplicados (mesmo
texto Alto em pastas de teste diferentes) e 55 com imagem (o arquivo da imagem não está no corpus,
então o programa python-pptx não pode ser executado). **Nenhum** deck foi excluído por falha do
exportador: os 127 programas python-pptx executaram e o PPTX resultante bateu com a IR (número de
formas, textos e posições com tolerância de 1 EMU).

## Resultado (medido)

| Formato | Tokens/slide (média) | IC95% (bootstrap) | Multiplicador vs texto (IC95%) | Instruções do formato (tokens) |
|---|---:|---:|---:|---:|
| Texto puro (régua) | 93,4 | 90,6–96,2 | 1,00 | 0 |
| SlideDSL Alto | 190,1 | 183,6–196,0 | 2,04 (1,99–2,08) | 619 (gramática .lark) |
| JSON do conteúdo | 200,5 | 194,0–206,4 | 2,15 (2,11–2,20) | 1.146 (JSON Schema) |
| SlideDSL 1.1 | 850,5 | 828,3–872,8 | 9,22 (9,03–9,42) | 1.039 (gramática .lark) |
| python-pptx | 1.693,5 | 1.658,0–1.728,7 | 18,45 (18,05–18,89) | 0 |

Razões pareadas em relação à Alto (média por deck): JSON 1,059 (JSON maior em 127/127 decks);
SlideDSL 1.1 4,64; python-pptx 9,30. Wilcoxon pareado (por deck, tokens/slide) de cada formato contra
a Alto: n = 127, z ≈ 9,78, p ≈ 1,3 × 10⁻²² em todos.

## Interpretação (separada do medido)

- Para chegar ao mesmo slide final, escrever o programa python-pptx exige ~9× os tokens da Alto, e a
  camada geométrica ~4,6×. Isso quantifica a "renderização adiada" (Agyemang et al.): o compilador
  expande a descrição compacta.
- Alto e JSON têm custo próximo (6%). O pipeline atual pede JSON (para usar JSON Schema) e converte para
  Alto; portanto paga o custo do JSON, não o da Alto. Gerar Alto diretamente com a gramática economizaria
  esses ~6% e ~527 tokens de instrução.
- Mesmo sem instruções, o python-pptx perde já no primeiro slide (≈ 1.500 tokens a mais por slide).
- Limitações: custo de *serialização* do resultado final, não custo operacional (tentativas, reparos);
  corpus de decks gerados pelo próprio projeto; decks com imagem excluídos.
