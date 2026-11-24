# Teste 5 — gramática Alto no app: bancada do pipeline móvel no PC (medido em 24/11/2026)

Código: `mobile/app/src/pipeline/altoText.ts`, `generate.ts` (`slideMode`), `mobile/app/bench/app_bench.mjs`,
`scripts/analise_teste5.py`. Dados (não versionados): `outputs/teste5_app/` (`results.csv`, `analise.json`,
`analise_sem_par_roteiro.json`, PPTX, decks e chamadas por geração). Registro: `docs/NOITE_24_11.md`.

## Configuração

- O mesmo `generate()` do aplicativo (TypeScript), contra `llama-server` b12648 (GPU) imitando o llama.rn:
  template de chat com raciocínio desligado, contexto 4096, `n_predict = min(1400, sobra)`, temperatura 0,2,
  cache de prefixo, uma geração por vez, **cache esvaziado antes de cada geração** (`--cache-ram 0`, erase do slot).
- Modelo: Qwen3-1.7B Q4_K_M — o mesmo arquivo do celular (SHA-256 `b139949c…`).
- 12 pedidos × sementes 11 e 22, documento do tema (`outputs/teste4/documentos/*.txt`, lido por `extractBytes` do
  app), 5 slides. Ordem sorteada (semente 20261122).
- Condições (só muda a escrita dos slides; leitura do documento e roteiro em JSON, idênticos):
  - `json`: JSON Schema (como o app 0.2/0.3);
  - `gramatica`: GBNF da SlideDSL Alto derivada do mesmo schema (mesmos campos e limites folgados);
  - `gramatica_limites`: a mesma GBNF com os limites de texto da validação A005 do compilador;
  - `gramatica_limites_reparo`: idem, e campo que chega ao limite (cortado) pede 1 reparo.
- **Tempo no celular projetado** = tokens de prompt processados / 3,88 tok/s + tokens gerados / 1,49 tok/s
  (medianas do moto g(8) power lite, `RESULTADOS_T4.md`). Validação: `json` em agua_detalhado projetou 66,1 min;
  o celular real levou 63,0 min (+5%).

## Resultado (24 pares; médias por apresentação)

| Condição | Decks gerados | Decks sem slide do compilador | Slides do compilador (de 115) | Tokens gerados nos slides | Prompt processado nos slides | Celular projetado (total) | Campos cortados no limite |
|---|---:|---:|---:|---:|---:|---:|---:|
| json | 23/24 | 1 | 52 | 2.131 | 3.606 | 80,1 min | 4/511 |
| gramatica | 23/24 | 2 | 41 | 1.686 | 3.721 | 75,6 min | 1/572 |
| **gramatica_limites** | 23/24 | **10** | **16** | **1.375** | 3.446 | **70,9 min** | 31/677 |
| gramatica_limites_reparo | 24/24* | 9 | 18 | 1.525 | 3.798 | 74,1 min | 31/696 |

\* com o porte de `fix_outline` (abaixo); nas outras três, o par solar_obrigatorio s11 falhou no roteiro.

Pareado (Wilcoxon / McNemar exato):
- gramatica × json: tokens gerados nos slides −21% (p = 0,008); celular projetado dos slides −11% (p = 0,08);
  slides do compilador −21% (p = 0,08).
- **gramatica_limites × json**: slides do compilador −69% (p = 0,0002); decks completos 10 × 1 (p = 0,012); tokens
  gerados nos slides −35% (p = 0,0002); celular projetado total −11% (80,1 → 70,9 min, p = 0,001), slides −23%.
- gramatica_limites × gramatica: slides do compilador −61% (p = 0,0003); decks completos 8 × 0 (p = 0,008).
- reparo × gramatica_limites (sem o par do roteiro, n = 23): cortes 28/673 × 31/677 (sem efeito); reparos +22%
  (p = 0,004); celular projetado +2,6% (p = 0,0004). **Resultado negativo: o reparo não ajuda.**

Causas dos slides montados pelo compilador: em `json` e `gramatica`, sobretudo A005 (texto acima do limite) — 58 e
43 ocorrências; em `gramatica_limites`, A005 desaparece e restam A010 (conteúdo não cabe em nenhuma variante) e
A012 (número sem fato citado).

Verificador único: 21/23 em `gramatica_limites` por B4 (bloco sobre o número da página) — o defeito corrigido no
núcleo em 23/11; a bancada usou a cópia do núcleo anterior à correção. Recompilados com o compilador atual, os 2
decks passam.

## Decisões no app (0.4.0)

- Escrita dos slides em SlideDSL Alto com gramática e limites do compilador **ligada por padrão** (chave na tela
  Modelo; desligada = JSON). Reparo de texto cortado disponível como opção, desligado.
- Porte de `fix_outline`: roteiro sem capa/conclusão é corrigido em vez de abortar o deck.
- Dica de formato do modo gramática reduzida a uma linha (decisão do piloto, antes da matriz).

## Interpretação

- A sintaxe sozinha (gramática com os limites folgados do JSON) reduz o texto gerado, mas pouco o tempo no celular,
  porque leitura do documento e roteiro (~55% do tempo) não mudam.
- O ganho grande vem de pôr **os limites do compilador na gramática**: a falha mais comum (A005) deixa de existir na
  decodificação, e a maioria dos slides que antes caíam no compilador passa a ser escrita pelo modelo.
- Custo: ~4,6% dos campos saem cortados no limite (ex.: "…Essa capac"); pedir reparo não resolve. Próximo passo:
  limites um pouco menores no prompt que na gramática, ou fim permitido só em fronteira de palavra.
- Tudo isto é bancada no PC com tempo projetado; a medição direta no celular é uma execução (`RESULTADOS_T4.md`).
