# Teste 3 (reduzido) — mecanismo de restrição da saída (medido em 23/11/2026)

Scripts: `scripts/teste3_restricao.py` (matriz), `scripts/analise_teste3.py` (análise),
`scripts/grammar_overhead.py` (microbenchmark). Dados (não versionados): `outputs/teste3/`
(`results.csv`, `analise.json`, `grammar_overhead.json`, `runs/`, `plano.json`, `maquina.json`).

## Configuração

- `llama-server` oficial do llama.cpp, build **b12648** (Windows, CUDA 12.4), GPU RTX 3060, `-ngl 99 -c 8192 --jinja`.
- Modelo: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (unsloth), SHA-256
  `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` (conferido com o publicado).
- 12 pedidos de `benchmark/format_requests.json` (4 temas × 3 níveis), dossiês fixos, 6 slides, semente 11,
  ordem sorteada com a semente 20261122. Pipeline Alto completo (roteiro, tópicos, slides, até 2 reparos,
  sustentação), igual nos três modos; só muda a restrição da escrita de cada slide:
  `json` (JSON Schema), `gramatica` (GBNF gerada da gramática Alto do tipo do slide), `direto` (texto Alto sem
  restrição, analisado depois).

## Resultado (medido)

| Modo | Válidos | Falhas de sintaxe | Slides aceitos de 1ª (média/6) | Reparos (média) | Chamadas (média) | Tokens de saída (média, IC95%) | Tempo de geração (média) | Tempo total (média, IC95%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JSON Schema | 11/12 | 0 | 1,83 | 10,8 | 33,8 | 9.902 (8.165–11.543) | 122,8 s | 141,9 s (116,8–165,3) |
| Gramática (GBNF) | 10/12 | 0 | 1,58 | 11,0 | 32,4 | 6.945 (5.291–8.708) | 86,4 s | 108,5 s (86,8–131,9) |
| Direto | 5/12 | 6 | 1,08 | 8,4 | 23,9 | 5.183 (3.510–6.836) | 64,3 s | 78,8 s (54,6–102,9) |

Motivos das falhas: direto — 6 × "Sintaxe inválida na SlideDSL Alto" após os reparos, 1 × A005 (texto acima do
limite); gramática — 2 × A005; JSON — 1 × A005. Tokens de entrada (média): JSON 58.007; gramática 68.280; direto 50.786.

Validade (McNemar exato, pareado por pedido): gramática × direto 5–0, p = 0,0625; JSON × direto 7–1, p = 0,070;
JSON × gramática 2–1, p = 1,0. Custo (Friedman, 3 modos, n = 12): tokens de saída Q = 16,7, p = 0,00024; tempo
de geração Q = 15,2, p = 0,0005; tempo total Q = 18,5, p = 0,0001. Wilcoxon pareado (n = 12): JSON × gramática
p = 0,005 (tokens de saída e tempo de geração), p = 0,008 (tempo total).

Microbenchmark (mesmo pedido, 20 × cada condição, aquecimento descartado, 256 tokens no máximo): sem gramática
12,80 ms/token (78,2 tokens/s, mediana); com a GBNF da Alto 14,76 ms/token (67,8 tokens/s): **+15,4% por token**.

## Interpretação (separada do medido)

- A gramática eliminou as falhas de sintaxe (0 contra 6/12 no modo direto); as falhas restantes são de conteúdo
  (limites de texto), que a gramática não expressa.
- Apesar de cada token ficar ~15% mais lento, o modo gramática gerou ~30% menos tokens de saída e foi ~24% mais
  rápido no total que o modo JSON, com validade semelhante (10 × 11 de 12). Isso é coerente com o Teste 1: escrever
  a intenção diretamente em Alto custa menos que embrulhá-la em JSON (aqui a diferença é maior que os 6% do
  Teste 1 porque o custo operacional inclui as respostas de reparo e as notas).
- O modo direto parece mais barato só porque falha cedo: com metade dos decks inválidos, custo por deck válido é
  pior. Amostra pequena (12 pares, 1 semente, 1 modelo): as diferenças de validade não atingem p < 0,05.
