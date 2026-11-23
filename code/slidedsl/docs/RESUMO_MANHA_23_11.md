# Resumo rápido — manhã de 23/11

**Artigo:** completo no Overleaf (13 páginas, LNCS, português). Só falta 1 resultado em vermelho: o
**Teste 4 no seu celular**. Detalhes em [RESUMO_COMPLETO_23_11.md](RESUMO_COMPLETO_23_11.md).

**Medido esta noite (tudo no artigo):**
- **Teste 1:** escrever o slide em SlideDSL Alto custa **~9× menos tokens** que código python-pptx (127 decks).
- **Teste 3:** a **gramática zerou os erros de sintaxe** (0 contra 6/12 sem restrição) e gastou **30% menos
  tokens** que JSON. Válidos: JSON 11/12, gramática 10/12, sem restrição 5/12.
- **Edição de 1 slide:** achei e corrigi um defeito (a IA apagava o conteúdo do slide). Agora 11/11 certos, e
  editar custa **~7%** de gerar tudo de novo.

**APK:** gerou uma apresentação **completa** no emulador (5 slides, 26 min, só CPU, modelo 0.6B) e salvou o
.pptx. Mas o 0.6B não respeitou o tamanho dos textos em 4 de 5 slides, e o compilador montou esses slides
(simples, só título). **No celular, use o modelo 1.7B.**

**Você precisa fazer (só você pode):**
1. Instalar `D:\slidedsl-mobile\SlideDSL-release.apk` no celular, baixar o **Qwen3 1.7B**, gerar 3–5 apresentações e tocar em
   **"Exportar dados do teste"** → me mande os arquivos. Isso preenche o Teste 4.
2. Ler o artigo no Overleaf e me dizer o que mudar.

**Codex:** bateu o limite à 1h; não usei mais. Está livre para você.
**Git:** tudo commitado e enviado (sem coautor), branch `feature/slidedsl-api-voz-mobile`.
