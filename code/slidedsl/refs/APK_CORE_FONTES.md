# Fontes de implementação e medição do núcleo APK

Registro de 22/11/2026, anterior ao relatório desta rodada. Não foram usadas
implementações de protótipos nem fontes externas para substituir o compilador.

- Contrato da rodada: `docs/PLANO_CODEX_TCC_APK1_CORE.md`, tarefas T1–T5.
- Entrada e validação: `src/slidedsl/alto.py` (`AltoDeck`, `validate_alto`).
- Orquestração de referência: `src/slidedsl/alto_compile.py` (`build_alto`).
- Layouts: `alto_layout.py`, `editorial.py`, `design_system.py`,
  `layout_score.py`, `layout_metrics.py` em `src/slidedsl/`.
- Modelos e semântica: `ast_nodes.py`, `ir.py`, `semantic.py`, `printer.py`,
  `geometry.py` e `design_rules.py` no mesmo diretório.
- Medição de texto: `text_metrics.py` e `layouts.py`. A exportação registra o
  arquivo e SHA-256 de cada fonte, o motor de layout Pillow e as medidas por raster.
- Regras e temas: `config/design_rules.yaml` e `config/themes.yaml`.
- Renderização de referência: `renderer/render.mjs`, PptxGenJS 4.0.1.
  Contrato `write({outputType:'arraybuffer'})`: tipos e implementação do pacote
  instalado em `packages/slidedsl-core/node_modules/pptxgenjs/`.
- Evidência gerada: `outputs/parity/manifest.json`, `outputs/parity/relatorio.json`,
  `outputs/apk-core-tests.log`, `outputs/apk-core-pytest.log`,
  `outputs/apk-core-render/`. Fixtures portáveis em
  `packages/slidedsl-core/test/fixtures/`.
