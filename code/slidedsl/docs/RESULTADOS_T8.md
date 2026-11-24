# Teste 8: Qwen3 0.6B com LoRA destilado do 4B × 0.6B sem treino × 1.7B (24/11/2026)

**Pergunta.** O Teste 7 mostrou que o 0.6B sem treino é cerca de 2× mais rápido que o 1.7B, mas escreve pior. Um LoRA treinado com saídas do Qwen3-4B, gravadas no próprio pipeline do app, aproxima o 0.6B do 1.7B (ou o supera) sem perder velocidade?

**Dados (não versionados).**
- `outputs/lora/` (documentos, pedidos, dataset, logs)
- `outputs/teste8_lora/`
- linhas de base `outputs/teste7_06b_dica/` (0.6B) e `outputs/teste6_17b_dica/` (1.7B)

**Modelo.**
- Arquivo: `D:\android\models\Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf` (396,7 MB).
- SHA-256: `a58cebfb0e26b7dc70e53f7388bae0df9112d98c6c91cb915f2c8b3ee0a77b53`.

## Como foi feito

1. **Documentos novos.** `scripts/lora_documentos.py` baixou 36 artigos da Wikipédia em português.
   - Nenhum dos temas da bancada (água, sono, git, solar) foi usado.
   - Cada texto foi cortado em 14 mil caracteres.
   - Saíram 107 pedidos nos níveis tema, detalhado e obrigatório. Os de nível tema também rodam sem fonte, o que dá 143 apresentações.
2. **Professor.** `mobile/app/bench/lora_dataset.mjs` roda o `generate()` do app com o Qwen3-4B-Instruct-2507 Q4_K_M no llama-server, no modo `gramatica_limites+frases`, com semente 7 e 5 ou 6 slides. Ele grava sistema, usuário e saída de cada chamada.
   - Entra no dataset apenas o que passa nas conferências do próprio app:
     - **slides:** só os que não foram montados pelo compilador (sem F001);
     - **roteiros:** todos;
     - **leitura por frases:** só as linhas aceitas pelo `verifyFact`.
   - Resultado: 143/143 apresentações sem erro e 1876 amostras (1116 slides, 143 roteiros, 617 leituras). Foram descartadas 30 chamadas.
3. **Limpeza.** `scripts/lora_limpar.py` trata os textos que o 4B deixou cortados no limite do compilador.
   - Critério de corte: o texto tem exatamente o tamanho de um limite A005, não tem pontuação final, e a última palavra não existe no vocabulário do dataset.
   - Correção: o texto é aparado na última frase ou palavra inteira, sem deixar "de", "o" etc. soltos no fim. Foram 161 textos.
   - Uma primeira regra, só por tamanho, aparava 868 textos e estragava frases completas.
   - Os roteiros foram reserializados compactos.
4. **Treino.** `scripts/lora_treino.py`, na RTX 3060 de 12 GB, levou 92 min.
   - **Configuração:**
     - LoRA r16 / alpha 32 em q, k, v, o, gate, up e down (10,1 M parâmetros, 1,7% do modelo);
     - AdamW com lr 2e-4 e cosseno;
     - 2 épocas, lote efetivo de 16 (222 passos);
     - perda só nos tokens da resposta.
   - **Validação separada por pedido** (6 pedidos, 104 amostras): **perda 0,982 → 0,570**. Ela estabilizou no 3º quarto do treino, sem subir, ou seja, sem sobreajuste.
   - **Dois problemas de memória resolvidos:**
     - **Logits.** Com o vocabulário de 151 mil tokens, os logits de 4096 posições estouravam a VRAM. A cabeça de saída agora é aplicada só nos tokens da resposta.
     - **Máscara de atenção.** Uma máscara explícita fazia o SDPA usar o caminho que materializa a matriz de atenção: pico de 14,5 GB com 2 mil tokens. Com lote 1 e sem máscara, o pico caiu para 4 GB.
     - **Efeito no Windows.** Passar da VRAM não gera erro: o driver transborda para a RAM e o treino fica cerca de 10× mais lento. Por isso o script limita o PyTorch a 80% da VRAM.
5. **Conversão.** O adaptador foi fundido ao modelo, convertido com `convert_hf_to_gguf.py` (llama.cpp b12648) em f16 e depois quantizado com `llama-quantize` em Q4_K_M.
6. **Bancada.** A mesma do Teste 7: 12 pedidos × sementes 11 e 22, 5 slides, `gramatica_limites+frases`, cache esvaziado. A velocidade estimada no celular é a do 0.6B (8,88 / 3,41 tok/s), porque a arquitetura é a mesma.

## Resultados (24 apresentações por modelo)

| | 1.7B | 0.6B | **0.6B + LoRA** |
|---|---|---|---|
| válidas | 24/24 | 24/24 | **24/24** |
| completas (nenhum slide do compilador) | 13 | 8 | **22** |
| slides montados pelo compilador | 12 | 20 | **2** |
| verificador estrito do PPTX | 24 | 24 | 24 |
| slides de seção (conteúdo vazio) | 12 | 41 | **2** |
| itens por slide | 2,9 | 2,33 | 2,63 |
| reparos por apresentação | 1,9 | 2,2 | **1,1** |
| textos repetidos no deck (>25 caracteres) | 41/558 | 117/456 | **13/595** |
| vocabulário visível (palavras distintas) | 1032 | 566 | 931 |
| fatos aceitos / rejeitados | 15,5 / 3,3 | 14,9 / 0,8 | 13,1 / 1,1 |
| tokens de saída | 2526 | 2423 | 1985 |
| tempo projetado no celular | 53,5 min | 24,4 min | **20,6 min** |

**Testes pareados (mesmo pedido e semente):**
- **LoRA × 0.6B.** Completas: 15 a 1 nos discordantes (McNemar exato, p = 0,0005). Tempo: Wilcoxon, p < 0,001.
- **LoRA × 1.7B.** Completas: 9 a 0 nos discordantes (p = 0,004). Tempo: −61%, Wilcoxon, p < 0,001.

## Leitura

- O LoRA resolveu o que faltava ao 0.6B: o formato e a disciplina de escrita.
  - Ele quase não falha a gramática nem os limites (2 slides do compilador contra 20).
  - Não repete frases (13 repetições contra 117).
  - Não copia marcadores.
  - Com isso supera até o 1.7B em apresentações completas, gastando cerca de 2/5 do tempo.
- O conteúdo ainda é mais raso que o do 1.7B:
  - menos fatos usados (13,1 contra 15,5);
  - vocabulário 10% menor;
  - nas notas do orador, ideias que voltam ("o ciclo é natural e essencial…").
- "como em F1" (identificador interno do fato) aparece no texto em 14 decks, igual ao 1.7B (14 decks). É um defeito do prompt, não do LoRA. Corrigir no prompt de conteúdo, junto com o vazamento "cresceu 30%".

## Limites

- O tempo no celular é projetado pela razão de tamanho de arquivo (Teste 7), não medido.
- O LoRA aprendeu com o 4B no mesmo pipeline e gramática: se o prompt do app mudar muito, é preciso gerar o dataset de novo (cerca de 2,5 h com o 4B) e treinar de novo (cerca de 1,5 h).
- Uma semente por pedido no dataset; uma rodada de treino, sem busca de hiperparâmetros.
- A bancada usa 4 temas. A qualidade foi avaliada pelos verificadores automáticos e pela leitura de alguns decks, sem avaliação humana cega.

## No app

App 0.6.0 lista "Qwen3 0.6B SlideDSL (LoRA)" como modelo só por importação (o arquivo não está publicado). Para usar:

1. Copiar `Qwen3-0.6B-SlideDSL-LoRA-Q4_K_M.gguf` para o celular.
2. Na tela de modelo, selecioná-lo e tocar em "Importar arquivo .gguf do aparelho". O app confere tamanho e SHA-256.
