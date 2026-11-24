# Teste 2 — modelo escrevendo python-pptx × SlideDSL (medido em 23/11/2026)

Scripts: `scripts/teste2_codigo.py` (grupo A), `scripts/teste2_minimo.py` (C-mínimo),
`scripts/pptx_checks.py` (verificador único), `scripts/recompilar_teste3.py`, `scripts/analise_teste2.py`.
Dados (não versionados): `outputs/teste2/` (A e `analise.json`), `outputs/teste2_minimo/`,
`outputs/teste3_recompilado/`. Testes: `tests/test_teste2.py`.

## Configuração

- Mesmo modelo e servidor do Teste 3: `Qwen3-4B-Instruct-2507-Q4_K_M` no `llama-server` b12648, RTX 3060
  (contexto 16384 em A e C-mínimo, porque a correção reenvia o programa; 8192 no Teste 3).
- 12 pedidos × sementes 11 e 22, dossiês fixos, 6 slides, temperatura 0,2, até 2 correções.
- **A — código direto:** o modelo escreve um programa python-pptx; conferência estática (só python-pptx e
  biblioteca padrão), execução isolada com `python -I` e 60 s; a correção devolve o erro de execução ou os
  bloqueios do verificador.
- **C-mínimo — SlideDSL no mesmo formato de uso (regra fixada antes de rodar):** uma chamada escreve o deck
  inteiro em Alto sob a GBNF da gramática Alto; o prompt tem os mesmos fatos, a gramática, um deck de exemplo e
  os limites gerais de texto; a correção devolve os erros do compilador.
- **C completo:** as execuções do Teste 3 (gramática e JSON), recompiladas com o compilador corrigido (abaixo).
- **Verificador único**, igual para todos: B1 número de slides; B2 slide sem texto; B3 forma fora do slide;
  B4 caixas de texto sobrepostas (>10% da menor); B5 (nível "estrito") texto maior que a caixa, medido com as
  funções de `text_metrics` que o compilador usa (largura por palavra com o arquivo da fonte, entrelinha 1,2,
  margens da caixa, 5% de tolerância). Sem tamanho declarado: título de placeholder 44 pt, corpo 32 pt, caixa
  18 pt; sem fonte declarada: Calibri (tema do python-pptx, conferido).

## Resultado (medido)

| Grupo | PPTX | Válidos (B1–B4) | Válidos estritos (B1–B5) | 1ª tentativa | Tokens entrada | Tokens saída | Tempo | Tokens / válido estrito | s / válido estrito |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A — python-pptx | 24 | **24/24** | **1/24** | 22 | 1.420 | 1.380 | 19,8 s | 67.195 | 476 |
| C-mínimo — Alto, 1 chamada | 13 | 13/24 | **13/24** | 8 | 6.967 | 1.344 | 19,6 s | **15.343** | **36** |
| C completo — gramática | 19 | 19/24 | 19/24 | — | 68.628 | 6.692 | 103,9 s | 95.142 | 131 |
| C completo — JSON | 19 | 19/24 | 19/24 | — | 58.254 | 9.816 | 141,0 s | 85.983 | 178 |

Médias por apresentação. Pareado por pedido e semente (n = 24):

- A × C-mínimo: estrutural 11–0 a favor de A (McNemar p ≈ 0,001); **estrito 13–1 a favor de C-mínimo
  (p ≈ 0,002)**. Tokens de saída iguais (Wilcoxon p = 0,98), tempo igual (p = 0,93); entrada maior em
  C-mínimo (p ≈ 2 × 10⁻⁵), por causa da gramática e do exemplo no prompt.
- A × C completo: estrutural 5–0 a favor de A (p = 0,06); estrito 18–0 a favor de C (p ≈ 8 × 10⁻⁶); C custa
  ~25× mais tokens e ~5–7× mais tempo.
- Estouro medido: A teve texto maior que a caixa em 23/24 decks (4,9 caixas por deck); C, em nenhum.
  A escreve mais texto visível (1.973 caracteres por deck, contra 1.465 em C-mínimo e 1.594–1.730 em C).
- Falhas de C-mínimo (11): 6 × A005 (texto acima do limite), 3 × A003 (quantidade de itens), 2 × deck com 7
  slides. **Falha de protocolo:** o prompt listava os limites gerais (rótulo 48 caracteres), mas a linha do
  tempo tem limite próprio de 36 (`alto.py`), causa de 2 das 6 falhas A005. Não se reexecutou para não ajustar a
  condição depois do resultado.

## Correção do compilador encontrada pelo verificador

Com o código do Teste 3, 4 dos 38 decks válidos tinham o bloco de cartões da conclusão sobre o número da
página (8 pt), o que as regras D001–D010 não detectavam: a altura dos cartões vinha do conteúdo e nada conferia
o limite inferior. `check_block_bottom` (em `alto_layout.py`) passa a emitir A010 e a variante é recusada (a
composição em linhas assume). Recompilando o mesmo texto Alto, sem chamar o modelo: validade igual (19/19/10) e
verificador 38/38. 727 pytest; porte TS regenerado, 44 testes TS, paridade 351/351.

## Interpretação (separada do medido)

- **Custo:** no mesmo formato de uso (uma chamada, deck inteiro), escrever Alto custa o mesmo que escrever
  python-pptx em saída e em tempo. A economia de 9× do Teste 1 compara a *mesma* apresentação final; o modelo,
  ao escrever código, não descreve a geometria — usa os layouts do modelo padrão e produz um deck mais simples.
  A afirmação "menos tokens que gerar o arquivo diretamente" não vale para o custo operacional.
- **O que a DSL compra:** garantia sobre o que é entregue. Todo deck aceito pelo compilador tem texto dentro
  das caixas (medido); o código direto quase sempre "funciona", mas entrega texto estourando. Por deck
  utilizável sob o critério estrito, C-mínimo custou ~4× menos tokens e ~13× menos tempo que A.
- **O pipeline completo** (tópicos, roteiro, uma chamada por slide, reparos, sustentação) eleva a validade de
  13 para 19 de 24, a ~5× o custo do C-mínimo. É uma troca, não um requisito da linguagem.
- **Ressalva do critério estrito:** o mestre do python-pptx liga ajuste automático (`normAutofit`) em título e
  corpo, sem fator de escala gravado; se e quando o texto é reduzido depende do programa que abre o arquivo
  (não verificado aqui). O encaixe dos decks do compilador não depende disso: o texto é medido antes de gravar.
  Conferência manual pendente: `outputs/teste2/conferir_no_powerpoint/`.
- Próximo passo natural: limites de texto e número de slides dentro da própria gramática (hoje só no
  compilador), o que atacaria as falhas restantes do C-mínimo.
