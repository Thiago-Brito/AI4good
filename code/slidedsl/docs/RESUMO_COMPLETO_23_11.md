# Resumo completo da madrugada — 23/11/2026

Para ler com calma. A versão curta está em [RESUMO_MANHA_23_11.md](RESUMO_MANHA_23_11.md).
Tudo o que é número abaixo foi medido e tem arquivo de origem; interpretações estão marcadas como tal.

## 1. Onde está cada coisa

| O quê | Onde |
|---|---|
| Artigo do TCC (LNCS, português) | Overleaf (o mesmo projeto de antes; o relatório Ordered GNN foi para `arquivo-ordered-gnn/`) e `academy/papers/artigo-overleaf/samplepaper.tex` |
| Código e documentação | GitHub, branch `feature/slidedsl-api-voz-mobile` (commits sem coautor) |
| APK atual | `D:\slidedsl-mobile\SlideDSL-release.apk` (181 MB) |
| Plano do TCC | [PLANO_TCC.md](PLANO_TCC.md) |
| Fila e registro da noite | [NOITE_23_11.md](NOITE_23_11.md) |
| Resultados medidos | [RESULTADOS_T1.md](RESULTADOS_T1.md), [RESULTADOS_EDICAO.md](RESULTADOS_EDICAO.md), [RESULTADOS_T3.md](RESULTADOS_T3.md) |

## 2. O que foi feito

### Artigo
- O Codex escreveu a introdução e a fundamentação (com bibliografia só de fontes conferidas) e atingiu o
  limite de uso por volta da 1h. Pela sua regra, **não usei mais o Codex**.
- Escrevi o resto: SlideDSL, versão móvel, método, resultados, discussão e conclusão. Revisei o PDF
  página por página e corrigi: resumo mais direto, E1–E11 definidos, figura com um deck gerado pelo
  Qwen3 4B e a tela do app, tabelas no lugar certo, fonte nítida.
- Cada número tem um comentário `% fonte:` no `.tex` apontando o arquivo de evidência.
- O que ainda está em vermelho (`[PENDENTE]`): só o Teste 4 (celular real).

### Teste 1 — custo do formato (sem IA)
- 127 decks, 694 slides, tokenizador do Qwen3. Para o mesmo slide final:
  texto visível 93 tokens/slide; **Alto 190 (2,04×)**; JSON 200 (2,15×); SlideDSL 1.1 850 (9,22×);
  **programa python-pptx 1.694 (18,45×)**. Wilcoxon p ≈ 10⁻²².
- Leitura: escrever código python-pptx custa ~9× os tokens da Alto. Ressalva: o pipeline pede JSON ao
  modelo (6% mais que Alto) e mede-se só a serialização final, não os reparos.

### Edição de um slide (o seu pedido)
- 4 decks gerados com Qwen3 4B local, 3 edições por IA e 3 sem IA em cada.
- **Achado:** o modelo, quando podia escolher o tipo, transformava 11 de 12 slides editados em
  "divisória de seção", jogando fora itens e fontes — até quando o pedido era "transforme em comparação".
- **Correção** (`alto_edit.allowed_kinds`): o tipo só muda quando a instrução pede. Depois: tipo cumprido
  **11/11**, conteúdo e fontes preservados **11/11**, resto do deck intacto.
- Editar um slide custa ~7% dos tokens e do tempo de gerar o deck inteiro.

### Teste 3 — gramática × JSON × direto
- `llama-server` oficial (b12648, CUDA) + Qwen3-4B-Instruct-2507 Q4_K_M (SHA-256 conferido) na RTX 3060.
- Microbenchmark: a gramática deixa a geração **~15% mais lenta por token** (78 → 68 tokens/s).
- Matriz 12 pedidos × 3 modos × **2 sementes** (72 execuções, todas concluídas):
  | Modo | Válidos | Erros de sintaxe | Tokens de saída | Tempo total |
  |---|---:|---:|---:|---:|
  | JSON Schema | 19/24 | 0 | 9.816 | 141 s |
  | Gramática | 19/24 | 0 | 6.692 | 104 s |
  | Direto | 10/24 | 12 | 5.061 | 77 s |
- Leitura: a gramática garante a sintaxe; as falhas que sobram são de conteúdo (texto longo demais, A005).
  Restringir (gramática ou JSON) é significativamente mais válido que não restringir (p = 0,012 e 0,035). Mesmo
  com cada token 15% mais lento, a gramática gera ~32% menos tokens de saída e é ~26% mais rápida que JSON, com a mesma
  validade (p ≈ 10⁻⁴). **Correção:** ela usa 18% mais tokens de entrada; no total de tokens não é mais barata (+11%, n.s.). Detalhes: [RESULTADOS_T3.md](RESULTADOS_T3.md).

### APK
- O primeiro teste real no emulador falhou com `<think>` antes do JSON → corrigido (gramática estrita
  desde o primeiro token). Isso virou um parágrafo do artigo.
- O SHA-256 do modelo travava a cada geração → agora é conferido uma vez ao baixar/importar.
- Novo botão "Importar arquivo .gguf do aparelho" (instalar o modelo sem internet, por cabo).
- Rodada 3 (Codex, antes do limite): documento → slides (PDF via PdfBox, DOCX, TXT, MD,
  "Compartilhar → SlideDSL"), documento longo dividido em partes.
- Segundo teste no emulador: o roteiro passou e o app escreveu slides, mas a capa do Qwen3 0.6B
  continuou inválida após 1 reparo e a geração inteira abortava. **Correção:** quando a IA falha no
  reparo, o compilador monta o slide (capa com o título do roteiro; outros tipos como divisória), o deck
  segue e o caso fica registrado (`F001`) nos dados exportados.

- **Terceiro teste no emulador (com o fallback):** apresentação completa de 5 slides em 1.577 s, 10 chamadas
  (roteiro + 5 slides + 4 reparos), Qwen3 0.6B, só CPU, PPTX salvo. Porém 4 de 5 slides foram montados pelo
  compilador (A005: texto acima do limite mesmo após reparo). Conclusão: o fluxo funciona no aparelho; o 0.6B é
  fraco para os limites do formato → usar o 1.7B no celular. Corrigi também o título cortado do fallback, que
  terminava em preposição ("... para a"). Entrou no artigo como observação de emulador (não é o Teste 4).

### Infra
- Android SDK, JDK 17, Gradle e caches em `D:\android` (o C: tem ~4 GB livres). Gradle limitado a 1,5 GB.
- `scripts/memoria_livre.ps1`: nenhuma tarefa pesada começa com menos de 3 GB livres.
- SearXNG subiu e gerou os 12 dossiês; depois foi desligado.

## 3. Decisões que tomei sozinho (revise)
1. Artigo no lugar do relatório Ordered GNN no mesmo projeto Overleaf (você pediu); o antigo ficou arquivado.
2. Restrição de tipo na edição de slide (mudança de comportamento do produto, com testes).
3. Fallback do compilador no app (um slide ruim não derruba mais o deck; fica registrado).
4. Teste 3 com 2 sementes (não 5) para caber na noite.

## 4. O que falta até 27/11
- **Teste 4 no seu celular** (o mais importante que só você pode fazer): instalar o APK, importar ou
  baixar o modelo 0.6B ou 1.7B, gerar 3–5 apresentações e tocar em "Exportar dados do teste".
- Revisar o texto do artigo (estilo, nome do orientador/instituição, agradecimentos se houver).
- Opcional: mais sementes no Teste 3; Teste 2 (com × sem SlideDSL) se der tempo.

## 5. Como instalar o APK no celular
Mande `D:\slidedsl-mobile\SlideDSL-release.apk` para o celular (Drive ou WhatsApp como documento), abra,
permita "instalar apps desconhecidos" e instale. Na aba Modelo, baixe pelo Wi-Fi o Qwen3 0.6B (484 MB)
ou o 1.7B (1,1 GB, melhor com 6 GB+ de RAM).
