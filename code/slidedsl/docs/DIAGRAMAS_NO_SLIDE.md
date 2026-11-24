# Diagramas no próprio slide (24/11/2026)

**O que mudou.** Antes, o desenhista SVG do Seminário 3 (`src/slidedsl/svg_diagrams.py`, comando `alto-svg`) gerava arquivos soltos. No PowerPoint, etapas e ciclo saíam como uma lista numerada. Agora o compilador desenha os diagramas dentro do slide, com a mesma geometria do SVG e em formas editáveis. O resultado é igual no PC e no celular, e a paridade de IR é de 356/356 decks.

**Etapas (2 a 5).**
- Caixas iguais lado a lado, cada uma com o número num selo, o rótulo e o detalhe.
- Setas → entre as caixas.

**Ciclo (3 ou 4 fases; bloco `ciclo` = etapas com `cycle`).**
- Caixas numa elipse, no sentido horário a partir do topo.
- Setas no trecho livre entre as bordas: → ↘ ↓ ↙ ← ↖ ↑ ↗.
- A última seta volta à primeira caixa.

**Gráfico de barras.** Já era desenhado no slide, com altura proporcional ao valor.

**Regras.**
- **Seta como caractere:** o IR só tem seta para baixo, e o caractere aparece igual no PowerPoint, no Google Slides e no celular.
- **Mesma escala de fonte dos outros slides:** só reduz até os mínimos (rótulo 20 pt, detalhe 16 pt) se for preciso.
- **Volta para a lista numerada** se o texto não couber, se uma palavra for mais larga que a caixa, se as caixas do ciclo se sobrepuserem ou se uma seta encostar numa caixa. O ciclo de 5 fases não cabe no slide e sai como lista.

**Geração.** O roteiro pode escolher o tipo `ciclo` ("processo que se repete em 3–5 fases"), tanto no PC quanto no celular, pelos prompts exportados.

**Código.**
- Desenho: `src/slidedsl/alto_layout.py` (`diagram_etapas`, `diagram_ciclo`, `ciclo_geometry`), traduzido para `packages/slidedsl-core/src/port.ts` por `scripts/port_core.py`.
- Exemplo: `examples/alto/diagramas.slda`.
- Testes: `tests/test_diagramas_slide.py`, `mobile/app/test/diagrams.test.mjs`.

**Seminário 3.** O teste A × B de 25/11 mede o SVG solto e usa o código marcado na tag `sem3-svg-congelado`. Esta mudança não altera `svg_diagrams.py`.
