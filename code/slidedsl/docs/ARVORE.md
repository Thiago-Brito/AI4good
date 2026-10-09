# Arquivos criados e mantidos

Inventário dos fontes, configurações, testes e referências do projeto, incluindo a evolução incremental SLM. Ambientes e artefatos gerados ficam separados.

```text
code/slidedsl/
  .env.example
  .gitattributes
  .gitignore
  AGENTS.md
  LICENSE
  README.md
  ROADMAP.md
  api/main.py
  assets/LICENCA.md
  assets/imagem_demo.png
  benchmark/prompts/demo_slm_local.txt
  benchmark/prompts/tarefa_cinco_slides.txt
  benchmark/rubric.yaml
  benchmark/run.py
  config/design_rules.yaml
  config/models.yaml
  config/themes.yaml
  docs/ANALISE_TEXPACE.md
  docs/ARVORE.md
  docs/DEFESA_PROFESSOR.md
  docs/DIAGNOSTICO_OLLAMA.md
  docs/EDITOR.md
  docs/EXPERIMENTO.md
  docs/GRAMATICA.md
  docs/MATRIZ_CAPACIDADES.csv
  docs/METAMODELO.md
  docs/OLLAMA_LOCAL.md
  docs/PESQUISA_FERRAMENTAS.md
  docs/PROGRESSO.md
  docs/REGRAS_DESIGN.md
  docs/RESULTADOS.md
  docs/RESULTADOS_INCREMENTAIS.md
  docs/RESULTADOS_OLLAMA.md
  docs/SEMANTICA.md
  docs/SLM_LOCAL_FUNCIONAL.md
  editor/eslint.config.js
  editor/index.html
  editor/package-lock.json
  editor/package.json
  editor/playwright.config.ts
  editor/src/App.tsx
  editor/src/Preview.tsx
  editor/src/api.ts
  editor/src/graph.tsx
  editor/src/main.tsx
  editor/src/style.css
  editor/src/types.ts
  editor/tests/editor.spec.ts
  editor/tests/slm.spec.ts
  editor/tsconfig.json
  editor/vite.config.ts
  examples/cinco_slides.sld
  examples/introducao.sld
  examples/minimo.sld
  examples/negativo_fora.sld
  examples/negativo_id_duplicado.sld
  examples/negativo_oclusao.sld
  examples/operacoes.sld
  prompts/incremental_direct.txt
  prompts/incremental_json.txt
  prompts/system_dsl.txt
  pyproject.toml
  refs/FONTES.md
  refs/spacemantics-tree.json
  refs/texpace/LICENSE
  refs/texpace/bench/CONTEXT.md
  refs/texpace/checker/CONTEXT.md
  refs/texpace/dsl/SPEC.md
  refs/texpace/tests/CONTEXT.md
  renderer/package-lock.json
  renderer/package.json
  renderer/render.mjs
  renderer/render.test.mjs
  requirements-lock.txt
  scripts/_common.ps1
  scripts/analyze_incremental.py
  scripts/checkpoint.py
  scripts/create_asset.py
  scripts/demo_slm_windows.ps1
  scripts/demo_windows.ps1
  scripts/diagnose_ollama.py
  scripts/download_wheels.py
  scripts/inspect_delivery.py
  scripts/inspect_slm_delivery.py
  scripts/normalize_artifact_access.py
  scripts/preview_powerpoint.ps1
  scripts/provision_node.py
  scripts/research_matrix.py
  scripts/setup_windows.ps1
  scripts/test_windows.ps1
  src/slidedsl/__init__.py
  src/slidedsl/ast_nodes.py
  src/slidedsl/benchmarking.py
  src/slidedsl/cli.py
  src/slidedsl/compiler.py
  src/slidedsl/design_rules.py
  src/slidedsl/diagnostics.py
  src/slidedsl/generation.py
  src/slidedsl/geometry.py
  src/slidedsl/grammar/slidedsl.lark
  src/slidedsl/incremental.py
  src/slidedsl/ir.py
  src/slidedsl/models/__init__.py
  src/slidedsl/models/base.py
  src/slidedsl/models/factory.py
  src/slidedsl/models/mock_model.py
  src/slidedsl/models/ollama_model.py
  src/slidedsl/models/openai_model.py
  src/slidedsl/parser.py
  src/slidedsl/paths.py
  src/slidedsl/pipeline.py
  src/slidedsl/preview.py
  src/slidedsl/printer.py
  src/slidedsl/schemas/ir.schema.json
  src/slidedsl/semantic.py
  src/slidedsl/serializer.py
  src/slidedsl/server.py
  src/slidedsl/structured_slide.py
  tests/conftest.py
  tests/test_api.py
  tests/test_benchmark_mock.py
  tests/test_cli.py
  tests/test_compile_pptx.py
  tests/test_design.py
  tests/test_extensions.py
  tests/test_geometry.py
  tests/test_grammar.py
  tests/test_incremental.py
  tests/test_ir_roundtrip.py
  tests/test_models.py
  tests/test_regressions.py
  tests/test_semantic.py
```

Total: 132 arquivos de fonte/configuração/testes/referências.

Artefatos atuais em outputs/:

- readme/: validação estrita, AST, IR e PPTX do exemplo didático introducao.sld.
- diagnostico_ollama/: tabela e evidence.json das 30 respostas históricas.
- demo_local/windows_direct_final/: comando Windows completo, cinco slides sem diagnósticos, PPTX, AST, IR, auditoria e editor em produção.
- demo_local/direct_demonstracao/: raw/HTTP por slide, presentation.sld, AST, IR, diagnósticos, PPTX, audit.json e editor/preview.
- demo_local/windows_strict/: demonstração JSON, um reparo, PPTX e edição no navegador.
- demo_local/pilot_*: tentativas de desenvolvimento preservadas, fora das taxas finais.
- evaluation_incremental/: configuração, runs.json, evaluation.json/CSV, relatórios e execução por modelo/modo/repetição.
- reports_ollama_20261008/: conjunto original A/B/C inalterado.
- tests/pytest.xml e ui-tests/results.json: regressão executada.
- artifact_access_*.json: conservação dos hashes ao corrigir herança de acesso dos PPTX.

Apresentação manual histórica: outputs/apresentacao.pptx; sua rubrica e métricas não são atribuídas ao SLM.
