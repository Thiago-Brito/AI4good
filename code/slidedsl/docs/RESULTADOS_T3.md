# Teste 3 (reduzido) — mecanismo de restrição da saída (medido em 23/11/2026)

Scripts: `scripts/teste3_restricao.py` (matriz), `scripts/analise_teste3.py` (análise),
`scripts/grammar_overhead.py` (microbenchmark). Dados (não versionados): `outputs/teste3/`
(`results.csv`, `analise.json`, `grammar_overhead.json`, `runs/`, `plano.json`, `maquina.json`).

## Configuração

- `llama-server` oficial do llama.cpp, build **b12648** (Windows, CUDA 12.4), GPU RTX 3060, `-ngl 99 -c 8192 --jinja`.
- Modelo: `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (unsloth), SHA-256
  `3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597` (conferido com o publicado).
- 12 pedidos de `benchmark/format_requests.json` (4 temas × 3 níveis), dossiês fixos, 6 slides, sementes 11 e 22,
  ordem sorteada com a semente 20261122. Pipeline Alto completo (roteiro, tópicos, slides, até 2 reparos,
  sustentação), igual nos três modos; só muda a restrição da escrita de cada slide:
  `json` (JSON Schema), `gramatica` (GBNF gerada da gramática Alto do tipo do slide), `direto` (texto Alto sem
  restrição, analisado depois).

## Resultado (medido) — 12 pedidos × 2 sementes (11 e 22) × 3 modos = 72 execuções, todas concluídas

| Modo | Válidos | Falhas de sintaxe | Slides aceitos de 1ª (média/6) | Reparos (média) | Tokens de saída (média, IC95%) | Tempo de geração (média) | Tempo total (média, IC95%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| JSON Schema | 19/24 | 0 | 1,71 | 11,4 | 9.816 (8.658–11.001) | 121,1 s | 141,0 s (124,9–157,7) |
| Gramática (GBNF) | 19/24 | 0 | 1,54 | 11,1 | 6.692 (5.707–7.769) | 83,3 s | 103,9 s (90,2–118,6) |
| Direto | 10/24 | 12 | 1,21 | 8,8 | 5.061 (3.938–6.207) | 62,7 s | 77,2 s (60,8–94,1) |

Motivos das falhas: direto — 12 × "Sintaxe inválida na SlideDSL Alto" após os reparos, 2 × A005; gramática — 5 × A005;
JSON — 5 × A005 (A005 = texto acima do limite do tipo de slide). Tokens de entrada (média): JSON 58.254; gramática
68.628; direto 51.324.

Validade (McNemar exato, pareado por pedido e semente, n = 24): gramática × direto 10–1, **p = 0,012**;
JSON × direto 12–3, **p = 0,035**; JSON × gramática 4–4, p = 1,0. Custo (Friedman, 3 modos, n = 24): tokens de
saída Q = 31,8, p ≈ 1,3 × 10⁻⁷; tempo de geração Q = 27,3, p ≈ 1,2 × 10⁻⁶; tempo total Q = 31,8, p ≈ 1,3 × 10⁻⁷.
Wilcoxon pareado (n = 24) JSON × gramática: tokens de saída p ≈ 9 × 10⁻⁵; tempo total p ≈ 1,6 × 10⁻⁴.

Com só a semente 11 (n = 12), os valores eram: válidos 11/10/5, sintaxe 0/0/6, McNemar gramática × direto p = 0,06.

Microbenchmark (mesmo pedido, 20 × cada condição, aquecimento descartado, 256 tokens no máximo): sem gramática
12,80 ms/token (78,2 tokens/s, mediana); com a GBNF da Alto 14,76 ms/token (67,8 tokens/s): **+15,4% por token**.

## Interpretação (separada do medido)

- A gramática eliminou as falhas de sintaxe (0 contra 12/24 no modo direto); as falhas restantes são de conteúdo
  (limites de texto), que a gramática não expressa.
- Apesar de cada token ficar ~15% mais lento, o modo gramática gerou ~32% menos tokens de saída e foi ~26% mais
  rápido no total que o modo JSON, com a mesma validade (19 de 24 em ambos). Isso é coerente com o Teste 1: escrever
  a intenção diretamente em Alto custa menos que embrulhá-la em JSON (aqui a diferença é maior que os 6% do
  Teste 1 porque o custo operacional inclui as respostas de reparo e as notas).
- **Correção (23/11, revisão do artigo):** em compensação, a gramática consumiu **18% mais tokens de entrada** que o
  JSON (68.628 × 58.254; Wilcoxon p = 0,012), porque nos modos de texto cada chamada de slide leva a gramática Alto
  inteira e um exemplo no prompt (`src/slidedsl/alto_generation.py`, `if mode != "json"`). Somando entrada e saída,
  a gramática usou ~11% **mais** tokens (75.320 × 68.070; p = 0,09, não significativo). Ela é mais rápida localmente
  porque o prefill é barato (5,4 s × 4,7 s) frente à geração (83 s × 121 s), mas **não** é mais econômica em tokens
  totais. Melhoria óbvia: no modo gramática, mandar só as regras do tipo do slide (a decodificação já impõe a sintaxe).
- O modo direto parece mais barato só porque falha cedo: com metade dos decks inválidos, custo por deck válido é
  pior. Com 24 pares as diferenças de validade em relação ao modo direto são significativas (p < 0,05); a amostra
  ainda é de um único modelo e duas sementes por pedido.
