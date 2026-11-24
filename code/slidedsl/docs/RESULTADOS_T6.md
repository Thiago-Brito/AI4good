# Teste 6 — leitura do documento por frases numeradas (bancada do app no PC, 24/11/2026)

Código: `mobile/app/src/pipeline/sentences.ts`, `sources.ts` (`extractFacts`), `generate.ts` (`extractMode`),
`mobile/app/bench/app_bench.mjs` (sufixo `+frases`). Dados (não versionados): `outputs/teste6_frases/` (v1) e
`outputs/teste6_frases_v2/` (versão final).

## Motivação

Na bancada do Teste 5 (`gramatica_limites`), a leitura do documento custava ~32 min dos ~72 min projetados no
celular (44%). Na extração em JSON, o modelo devolve cada fato com o campo `trecho`, cópia literal de uma frase do
documento, que o app depois confere. A 1,5 token/s, o celular passava a maior parte desse tempo reescrevendo texto
que o app já tem.

## O que muda

O app quebra o trecho em frases numeradas (`[1] …`, `[2] …`). O modelo responde, sob GBNF, uma linha por fato:

    fato 3 afirmacao "resumo em até 25 palavras" tipo numero relevancia alta

- A citação é a frase original, copiada pelo programa: sempre literal.
- O valor (número principal) é calculado pelo programa: o primeiro número da afirmação que também está na frase.
- A gramática só aceita números de frase crescentes (sem repetir frase) e no máximo 6 linhas.
- A conferência `verifyFact` é a mesma do modo JSON.

## Configuração

A mesma do Teste 5 (`RESULTADOS_T5.md`): o pipeline do app (TypeScript) contra o llama-server b12648 imitando o
llama.rn, Qwen3-1.7B Q4_K_M (o arquivo do celular), cache esvaziado por geração, 12 pedidos × sementes 11 e 22,
5 slides, documento do tema. Escrita dos slides em `gramatica_limites` nas duas condições; só muda a leitura do
documento. O tempo no celular é projetado com as velocidades medidas no moto g(8) power lite.

## Versão 1 (descartada): campos posicionais

`fato 3 numero alta "afirmação" "valor" "autor"`. Em 24 pares: leitura −23%, total −11% (72,1 → 64,1 min); mas 2
apresentações falharam ("nenhum fato válido"), contra 0 no modo atual. Diagnóstico nos trechos que falharam:
- sem o nome dos campos, o 1.7B punha o tipo no lugar do valor e escrevia afirmações de 1–3 palavras (rejeitadas);
- com o valor obrigatório, o modelo preenchia o campo com palavras ou texto embaralhado;
- o modelo repetia a mesma frase em laço até o limite de linhas.

Correções: campos nomeados (como na Alto), valor calculado pelo programa, números de frase crescentes na gramática,
e linhas só de URL ou de título curto sem pontuação final deixam de ser candidatas.

## Resultado — versão final (24 pares, todos válidos nas duas condições)

| Medida (média por apresentação) | JSON (atual) | Frases | Variação | p (Wilcoxon) |
|---|---:|---:|---:|---:|
| Leitura do documento no celular (projetado) | 31,8 min | **13,8 min** | −56% | < 0,001 |
| Tokens gerados na leitura | 2.305 | **762** | −67% | < 0,001 |
| **Total no celular (projetado)** | **72,3 min** | **53,5 min** | **−26%** | < 0,001 |
| Slides (projetado) | 31,6 min | 30,9 min | −2% | 0,44 |
| Fatos aceitos | 7,9 | 15,5 | +97% | < 0,001 |
| Fatos rejeitados | 10,8 | 3,3 | −70% | < 0,001 |
| Slides montados pelo compilador | 0,7 | 0,6 | −12% | 0,77 |

- Apresentações válidas: 24/24 nas duas condições. Verificador estrito: 24/24 nas duas.
- Apresentações sem slide do compilador: 10 (JSON) × 14 (frases); McNemar 4 × 8, p = 0,39 (sem diferença
  significativa).
- Alinhamento afirmação × citação (proxy: menos de 1/3 das palavras da afirmação aparecem na citação): 48,7% dos
  fatos no JSON × 26,1% nas frases. No JSON, boa parte disso vem de o modelo citar a linha de título da fonte
  ("Fonte 6: …"), que é literal e passa na conferência.

## Limitações

- Tempo projetado na bancada; falta medir no celular.
- Linhas de título longas ("Fonte 3: …", com 10 palavras ou mais) ainda podem ser escolhidas. Isso vem do formato
  dos documentos de teste e afeta as duas condições.
- Em ~43% dos fatos a afirmação ainda é uma cópia da frase escolhida. Isso não custa tempo extra em relação ao JSON,
  mas mostra que o modelo resume pouco.
- O modelo usa muito `definicao` e `numero` como tipo.

## Decisão no app (0.5.0)

A chave "Gramática" na tela Modelo liga as duas mudanças juntas: slides em SlideDSL Alto com limites e leitura por
frases. Ela continua ligada por padrão; desligada, o app volta ao JSON nas duas etapas.
