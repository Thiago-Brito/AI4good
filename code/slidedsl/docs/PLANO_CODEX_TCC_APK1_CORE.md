# Plano Codex — APK, rodada 1: núcleo SlideDSL em TypeScript com paridade

Contexto: [PLANO_TCC.md](PLANO_TCC.md) (F8) e [PLANO_TESTES_E_APK.md](PLANO_TESTES_E_APK.md) (Etapa 3).
Decisão de 22/11/2026: portar para TypeScript **só o caminho que o app usa**, sem Python no celular.
Chaquopy foi descartado por agora: depende de versões Android não oficiais de `pydantic-core`/`rpds-py` e
esta máquina não tem Android SDK para testar.

Caminho do app (modo celular):

```
LLM (llama.rn, JSON Schema → GBNF) → JSON do slide → AltoDeck → validate_alto (erros)
  → alto_layout (Builder/AST) → semântica → IR 1.1 → PptxGenJS
```

O texto Alto e o texto 1.1 **não** precisam ser impressos nem lidos no app nesta rodada: em TS, o
Builder do layout gera o AST e a semântica gera a IR diretamente. A paridade é verificada na IR.

## Regras

- Ler antes: `AGENTS.md`, `README.md`, `docs/SLIDEDSL_ALTO.md`, e o código de `src/slidedsl/alto.py`,
  `alto_layout.py`, `alto_compile.py`, `semantic.py`, `ir.py`, `ast_nodes.py`, `geometry.py`,
  `editorial.py`, `text_metrics.py`, `design_system.py`, `layout_score.py`, `layout_metrics.py`,
  `design_rules.py`, `svg_diagrams.py`, `config/*.yaml` e `renderer/render.mjs`.
- **Não alterar o comportamento do Python.** Só é permitido criar scripts novos em `scripts/` e,
  se indispensável, funções puras novas de exportação. A suíte pytest tem que continuar passando.
- Não editar `ROADMAP.md` nem `docs/PROGRESSO.md` (o revisor faz isso). Escrever o relatório em
  `docs/APK_CORE_RELATORIO.md`.
- Sem commit, push ou stash. Não apagar nada em `outputs/`.
- Dependências npm: apenas `typescript` e `pptxgenjs` (já usada no renderer), e `@types/node` em
  desenvolvimento. Testes com `node:test`. Node 22. Comandos compatíveis com Windows.
- pytest no Windows: `--basetemp=outputs/tests/t<hhmmss>` (caminho curto; o longo estoura 260 chars).
- Separar "implementado" de "medido" no relatório. Nada de declarar paridade sem número.

## Tarefas

### T1. Exportador de referência (Python) — `scripts/export_parity.py`

Para cada deck do corpus, gravar em `outputs/parity/<id>/`:
- `deck.json`: `AltoDeck` serializado (`model_dump(mode="json")`), entrada do TS;
- `facts.json`: fatos usados (do `dossie.json`/`relatorio` da mesma pasta, se houver; senão `{}`);
- `images.json`: largura/altura em px de cada `image_file` referenciado (o TS não abre imagens);
- `ir.json`: IR final de `build_alto(...).validation.ir` (`model_dump(mode="json")`);
- `diagnostics.json`: códigos e severidades de `build_alto`.

Corpus: `examples/alto/*.slda` + todos os `outputs/**/apresentacao.slda` (há cerca de 248), ignorando
os que não passam no parser hoje (listar no `manifest.json` com o motivo). Copiar um subconjunto
**pequeno e variado** (≤ 25 decks, cobrindo todos os tipos de slide e todas as famílias de fonte/
estilo encontradas) para `packages/slidedsl-core/test/fixtures/`, que é versionado.

Exportar também `packages/slidedsl-core/src/data/font_metrics.json`: largura de avanço por caractere,
para cada família de `text_metrics.FAMILIES` × normal/negrito, cobrindo Latin-1 + pontuação
tipográfica comum (— – “ ” ‘ ’ • … €) + os caracteres que aparecerem no corpus. Medir com a mesma
função que o Python usa (`text_width`/Pillow) num tamanho grande o bastante para não perder precisão,
e registrar como o Python trata kerning e arredondamento, para o TS reproduzir. Exportar ainda
`config/design_rules.yaml` e `config/themes.yaml` como JSON em `src/data/`.

### T2. Pacote `packages/slidedsl-core/` (TypeScript, ESM)

- `src/alto.ts`: tipos do AltoDeck/AltoSlide e `validateAlto` com os mesmos códigos A0xx e severidades.
- `src/textMetrics.ts`: largura e quebra de linha a partir de `font_metrics.json`.
- `src/layout.ts` (+ módulos auxiliares): porte fiel de `alto_layout.py` e dependências (editorial,
  design_system, layout_score, layout_metrics, svg_diagrams se usado pelo layout).
- `src/semantic.ts` / `src/ir.ts`: AST → IR 1.1 e regras D001–D010 (`design_rules.py`).
- `src/index.ts`: `buildAlto(deck, facts, images) → { ir, diagnostics }`, equivalente a `build_alto`.
- Nada de `fs`, `path` ou APIs de Node no código do pacote (vai rodar em React Native); I/O só nos
  testes e scripts.

### T3. Testes de paridade — `packages/slidedsl-core/test/parity.test.mjs`

- Para cada fixture: IR do TS == `ir.json` (números com tolerância absoluta 1e-6; strings, ids, ordem e
  z iguais) e mesmos códigos de diagnóstico.
- Script `npm run parity:full` que roda contra todo `outputs/parity/` e grava
  `outputs/parity/relatorio.json` (passaram / falharam, com a primeira diferença de cada falha).
- Meta: 100% das fixtures versionadas. No corpus completo, relatar a taxa real; cada classe de falha
  restante explicada no relatório.

### T4. Renderização sem Node — `packages/slidedsl-core/src/render.ts`

Extrair de `renderer/render.mjs` uma função `renderPptx(ir, { images }) → Promise<ArrayBuffer>`
(PptxGenJS `write({ outputType: 'arraybuffer' })`), sem `fs`. Imagens entram como data URI.
Teste: o PPTX do TS e o do renderer atual têm os mesmos textos e o mesmo número de formas por slide
(abrir o zip e comparar `ppt/slides/slide*.xml` por contagem de `<p:sp>`/`<p:pic>` e textos).
`renderer/render.mjs` continua funcionando como está.

### T5. Relatório

`docs/APK_CORE_RELATORIO.md`: o que foi portado, o que ficou de fora (e por quê), números de paridade
(fixtures e corpus completo), comandos para reproduzir e a próxima rodada sugerida (app React Native com
llama.rn). Rodar ao final: `pytest` completo, `npm test` em `renderer/` e no pacote novo.
