# Teste 9: bancada do app 0.7.5 contra T7/T8 (25/11/2026)

**Pergunta:** as correções feitas depois do teste com o PDF do TCC e do teste no celular melhoram as apresentações dos modelos do celular sem custar tempo demais? O teste do TCC está em `docs/TESTE_TCC_DOCUMENTO_LONGO.md`; o do celular, em `outputs/celular_25nov/`.

## O que mudou no app (0.7.3 → 0.7.5)

1. **Roteiro:** vê todos os fatos (até 32, só afirmação e valor), como o PC. Antes via só os 3 primeiros.
2. **Fatos por slide:** depois do roteiro, cada slide recebe fatos diferentes, com prioridade para os não usados (`distributeFacts`).
3. **Pedido de cada slide:** lista os itens já escritos nos outros slides, com "não repita".
4. **Gramática:** aceita só os caracteres que o compilador mede (sem CJK).
5. **Números:** em `numeros`/`grafico`, número fora dos fatos citados bloqueia depois do reparo, e o slide vira tópicos com os fatos.
   - Se o número está em outro fato, o compilador cita esse fato (`citeNumberFacts`) e o slide não é bloqueado.
6. **Texto cortado no limite da gramática:** termina na última pausa da frase, ou ao menos na palavra inteira (`trimTruncated`).
7. **Slide que só falha por tamanho** (A005/A010): os detalhes são encurtados (110, depois 80 caracteres) e, em último caso, ficam 4 itens (`shortenDetails`). Fica o conteúdo da IA (F002).
8. **Item com o mesmo texto de outro no slide:** pede reparo; se persistir, a cópia sai (P004).
9. **PDF:** hifenização, cabeçalhos corridos, seções e referências. Não afeta esta bancada, que usa TXT.

## Montagem

- É a mesma do T7/T8: `mobile/app/bench/app_bench.mjs`, 12 pedidos (4 temas × 3 níveis) × sementes 11 e 22, 5 slides, `gramatica_limites+frases`, cache esvaziado a cada geração, llama-server na RTX 3060.
- **Tempo no celular:** projetado com as velocidades medidas no moto g(8) power lite.
  - 1.7B: 3,88 / 1,49 tok/s.
  - 0.6B e LoRA: 8,88 / 3,41 tok/s.
- **Linhas de base:**
  - 0.6B LoRA: `outputs/teste8_lora`;
  - 0.6B: `outputs/teste7_06b_dica`;
  - 1.7B: `outputs/teste6_17b_dica`.
- **Dados novos:** `outputs/teste9_v075_*`, mais a rodada intermediária `teste9_v074_*`.
- **Análise:** `scripts/analise_teste9.py`, que recalcula as métricas do antes e do depois com o mesmo código.

## Resultado (24 apresentações por modelo)

| | LoRA T8 | **LoRA 0.7.5** | 0.6B T7 | **0.6B 0.7.5** | 1.7B T6 | **1.7B 0.7.5** |
|---|---|---|---|---|---|---|
| válidas | 24 | 24 | 24 | 24 | 24 | 24 |
| completas (nenhum slide do compilador) | 22 | 20 | 8 | **16** | 13 | **17** |
| slides do compilador | 2 | 4 | 20 | **11** | 12 | **7** |
| slides de seção (conteúdo vazio) | 2 | **0** | 41 | **14** | 12 | **0** |
| pares de slides parecidos (Jaccard ≥ 0,3) | 12 | **6** | 37 | 35 | 2 | 1 |
| textos repetidos no deck (>25 caracteres) | 24/475 | 26/501 | 149/349 | 206/517 | 59/439 | 44/518 |
| **fatos citados por deck** | 2,88 | **7,67** | 2,42 | **5,29** | 2,29 | **6,04** |
| itens por slide de conteúdo | 1,73 | 1,90 | 1,31 | 2,17 | 2,18 | 2,68 |
| vocabulário visível | 899 | 899 | 541 | 702 | 1002 | 1065 |
| reparos por apresentação | 1,12 | 1,17 | 2,25 | 2,54 | 1,92 | 1,83 |
| tokens de saída | 1985 | 2140 | 2423 | 2646 | 2526 | 2654 |
| **tempo projetado no celular** | 20,6 min | 22,9 min | 24,4 min | 27,1 min | 53,5 min | 58,9 min |

**Rodada intermediária (0.7.4, sem as correções 5b e 7):**
- O LoRA caiu para 13 apresentações completas, com 12 slides do compilador.
- As causas, nos 11 casos refeitos com `motor_pc.mjs`:
  - **A007, 6 casos:** em parte número certo citado com o fato errado, em parte número inventado;
  - **A010, 5 casos:** 5 itens com detalhes longos, que nenhum layout comporta.
- As correções 5b e 7 trataram esses casos: completas voltaram a 20 e slides do compilador, a 4, sem mudar o tempo (23,1 → 22,9 min).

**Versão final congelada (0.7.6):** a bancada foi repetida (`outputs/teste9_v076f_*`) e deu os mesmos números do 0.7.5 em todas as métricas, com o mesmo tempo projetado. A única mudança do 0.7.6 tira cópias de itens idênticos curtos, o que é raro. Os números da tabela valem para o 0.7.6.

**Versão do artigo (0.7.7, tag `artigo-v2`, branch `congelado/artigo-v2`):** a bancada foi repetida em 25/11 à tarde (`outputs/teste9_v077_*`, `scripts/bancada_077.sh`).
- O 0.7.7 só muda a posição do texto na capa centralizada, que a bancada não mede.
- LoRA e 1.7B: resultado idêntico ao 0.7.6, caso a caso.
- 0.6B: variação de casas decimais, por não determinismo da GPU (reparos 2,54 → 2,50; textos repetidos 206/517 → 207/519; vocabulário 702 → 706).
- Testes pareados (`scripts/estatistica_teste9.py`, saída em `outputs/teste9_v077_estatistica.json`):

| comparação | completas | McNemar exato | tempo médio projetado | Wilcoxon (tempo) |
|---|---|---|---|---|
| LoRA × 0.6B | 20 × 16 (discordantes 6 × 2) | p = 0,29 | 22,9 × 27,1 min | p = 0,001 |
| LoRA × 1.7B | 20 × 17 (5 × 2) | p = 0,45 | 22,9 × 58,9 min | p < 0,001 |
| 0.6B × 1.7B | 16 × 17 (4 × 5) | p = 1,0 | 27,1 × 58,9 min | p < 0,001 |

- **Leitura:** no T8, o LoRA tinha vantagem significativa em apresentações completas (22 × 13 contra o 1.7B, p = 0,004). As correções do 0.7.x ajudaram mais os modelos sem ajuste, e essa diferença deixou de ser significativa.
- O que continua significativo é o tempo: o LoRA faz o mesmo com 39% do tempo do 1.7B e 84% do tempo do 0.6B.
- O LoRA também repete muito menos que o 0.6B: 6 × 35 pares de slides parecidos.

## Experimento descartado: pedidos mais curtos (0.7.6)

Tentativa de recuperar o tempo encurtando o que vai no pedido:
- trecho do fato: 300 → 200 caracteres;
- itens já escritos: 320 → 200;
- afirmações no roteiro: 220 → 160.

Resultado na mesma bancada (`outputs/teste9_v076_*`):
- **Tempo:** não caiu. LoRA 22,9 → 23,4 min, 0.6B 27,1 → 28,2, 1.7B 58,9 → 58,8.
- **Reparos:** aumentaram (LoRA 1,17 → 1,58 por apresentação) e anularam a economia de leitura.
- **Qualidade:** mista. No 1.7B, os pares de slides parecidos subiram de 1 para 7.
- **Decisão:** a mudança foi desfeita, e o código segue no 0.7.5.

## Celular real (moto g(8) power lite, 0.6B LoRA, `agua.txt`, 5 slides)

| versão | tempo | chamadas | reparos | observação |
|---|---|---|---|---|
| 0.7.1 (modo JSON por engano) | 48,0 min | 16 | 4 | 2 slides de divisória vazia |
| 0.7.2 | **17,8 min** | 12 | 0 | 3 slides repetiam evaporação/condensação |
| 0.7.4 | 20,7 min | 13 | 1 | menos repetição; título cortado ("e volta ao"), corrigido no 0.7.5 |

## Emulador (APK 0.7.5, x86_64, CPU)

Rodado pela interface com `scripts/emulador_teste.py`, sem fonte. O pedido foi "Ciclo da agua para alunos do ensino fundamental", com 5 slides.

| modelo | tempo | chamadas | reparos | observação |
|---|---|---|---|---|
| 0.6B base | 19,0 min | 9 | 3 | 2 itens iguais (A023) no slide 4, corrigido no 0.7.6 |
| 0.6B LoRA (importado) | 20,5 min | 7 | 1 | slide 5 montado pelo compilador (A010) |

Os dados estão em `outputs/teste_emulador_075_06b_base/` e `outputs/teste_emulador_075_lora/`. A tela nova de resultado e edição abriu normalmente nos dois testes.

## Leitura

- **Ganho principal:** o deck usa 2 a 3 vezes mais fatos do documento.
  - Os slides de seção vazios quase somem: o compilador monta tópicos com os fatos.
  - O 0.6B e o 1.7B terminam mais apresentações sem slides do compilador.
  - No LoRA, os pares de slides parecidos caem à metade.
- **Custo:** cerca de 10% a mais de tempo projetado (+2,3 min no LoRA, +5,4 min no 1.7B).
  - Vem do roteiro com todos os fatos (≈ +300 tokens de entrada) e de slides com mais itens (+150 tokens de saída).
  - O celular mostrou a mesma direção: 17,8 min no 0.7.2 e 20,7 min no 0.7.4.
  - A troca é deliberada: mais conteúdo do documento por cerca de 2 minutos.
- **Repetição no 0.6B base:** continua alta (35 pares e textos repetidos). Só a distribuição de fatos não basta para o modelo sem ajuste; o LoRA e o 1.7B respondem melhor.
- **O que nenhuma regra resolve:** o 0.6B ainda escreve afirmações erradas ("a água condensa em vapor com temperatura alta"). O compilador confere forma, números e citação, não a verdade de uma frase.
- **Avaliação cega:** os decks da avaliação são do código anterior a estas correções (protocolo registrado antes das respostas). Os resultados dela valem para aquela versão.
